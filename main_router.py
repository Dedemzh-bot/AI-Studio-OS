"""
Main Router (核心中枢 / 24h 常驻守护进程)
职责：基于状态机轮询 task_status.json 调度所有子 Agent 和 Guards。

状态流转（碎片化 HITL 审批 / 环形永不退出）：
  idle --> pending_classification
    |--> (skill) pending_design --> pending_schema_approval --> pending_execution
    |         --> pending_validation --> pending_audit --> pending_data_approval
    |         --> pending_assets --> completed --> idle
    |
    |--> (system) system_planner(MD) --> pending_design_approval(3选项)
              --> pending_schema_translate --> pending_numerical
              --> pending_numerical_approval --> completed(归档) --> idle
"""

import json
import os
import subprocess
import sys
import time

# ---- Windows 控制台 UTF-8 适配 ----
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from Guards.schema_validator import SchemaValidator

# ---- 配置 ----
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
STATUS_FILE = os.path.join(WORKSPACE_DIR, "task_status.json")
RESULT_FILE = os.path.join(WORKSPACE_DIR, "current_result.json")
SCHEMA_FILE = os.path.join(WORKSPACE_DIR, "active_schema.json")
CONCEPT_FILE = os.path.join(WORKSPACE_DIR, "concept_brief.md")
AUDIT_FILE = os.path.join(WORKSPACE_DIR, "audit_feedback.json")
ROUTE_FILE = os.path.join(WORKSPACE_DIR, "task_route.json")
BOSS_FEEDBACK_FILE = os.path.join(WORKSPACE_DIR, "boss_feedback.txt")
PROJECT_DB_DIR = os.path.join(WORKSPACE_DIR, "project_db")
POLL_INTERVAL = 2


def read_state() -> str:
    data = read_state_raw()
    return data.get("current_state", "idle")


def read_state_raw() -> dict:
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[Router][错误] 文件不存在，尝试读取路径: {STATUS_FILE}")
        return {"current_state": "idle"}
    except json.JSONDecodeError as e:
        print(f"[Router][错误] JSON 解析失败，文件路径: {STATUS_FILE}")
        print(f"[Router][错误] 详细原因: {e}")
        return {"current_state": "idle"}


def write_state(state: str, **extra):
    try:
        data = {"current_state": state}
        data.update(extra)
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[Router][警告] 无法写入状态文件: {STATUS_FILE}")
        print(f"[Router][警告] 详细原因: {e}")


def require_human_approval(agent_name: str, artifact_paths: list[str],
                           next_state: str, reject_state: str) -> str:
    """
    通用 HITL 审批函数：阻塞等待老板验收 Agent 产物。
    返回 next_state（通过）或 reject_state（打回）。
    """
    print("\033[93m" + "=" * 60 + "\033[0m")
    print(f"\033[93m[审批节点] 等待老板验收 {agent_name} 的产物:\033[0m")
    for p in artifact_paths:
        print(f"[审批节点]   - {p}")
    print("\033[93m" + "=" * 60 + "\033[0m")

    user_input = input("[审批节点] 输入 'y' 通过，或输入修改意见打回: ").strip()

    if user_input.lower() == "y":
        print(f"\033[92m[审批节点] 老板放行！{agent_name} 产物已验收。\033[0m")
        return next_state
    else:
        print(f"\033[91m[审批节点] 老板打回！意见: {user_input}\033[0m")
        try:
            with open(BOSS_FEEDBACK_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{agent_name}] {user_input}\n")
            print(f"[审批节点] 修改意见已追加至: {BOSS_FEEDBACK_FILE}")
        except Exception as e:
            print(f"[审批节点][警告] 无法保存反馈: {e}")
        return reject_state


def _upsert_archive(workspace_dir: str, db_dir: str):
    """
    读取 system_numerical_data.json → 按顶级模块拆分 → Upsert 到 project_db/
    同名模块深合并：同 ID 覆盖，新 ID 追加。
    """
    data_file = os.path.join(workspace_dir, "system_numerical_data.json")
    if not os.path.exists(data_file):
        print("[Router][警告] system_numerical_data.json 不存在，跳过归档")
        return

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[Router][警告] 无法读取 {data_file}: {e}")
        return

    if not isinstance(data, dict):
        print("[Router][警告] 数据格式非 dict，跳过归档")
        return

    os.makedirs(db_dir, exist_ok=True)
    merged_count = 0
    new_count = 0

    for module_name, module_data in data.items():
        if not isinstance(module_data, dict):
            continue

        module_file = os.path.join(db_dir, f"{module_name}.json")

        # 将嵌套结构展平为记录列表（处理 discrete_milestones 等层级）
        records = _flatten_records(module_data)

        if not records:
            continue

        # 加载旧数据
        old_records = []
        if os.path.exists(module_file):
            try:
                with open(module_file, "r", encoding="utf-8") as f:
                    old_records = json.load(f)
                if not isinstance(old_records, list):
                    old_records = []
            except Exception:
                old_records = []

        # 建立旧数据 ID 索引
        old_index = {}
        for i, rec in enumerate(old_records):
            pid = _get_primary_id(rec)
            if pid is not None:
                old_index[pid] = i

        # 合并：同 ID 覆盖，新 ID 追加
        for rec in records:
            pid = _get_primary_id(rec)
            if pid is not None and pid in old_index:
                old_records[old_index[pid]] = rec
                merged_count += 1
            else:
                old_records.append(rec)
                new_count += 1

        # 落盘
        with open(module_file, "w", encoding="utf-8") as f:
            json.dump(old_records, f, ensure_ascii=False, indent=2)

        print(f"[Router]   {module_name}.json: 更新 {merged_count} 条, 新增 {new_count} 条 -> {module_file}")

    print(f"[Router] 归档完成: {merged_count} 条更新, {new_count} 条新增")


def _flatten_records(data: dict) -> list[dict]:
    """将嵌套的模块数据展平为记录列表。自动穿透 discrete_milestones 等中间层。"""
    # 如果包含 discrete_milestones 子键，钻入
    if "discrete_milestones" in data and isinstance(data["discrete_milestones"], dict):
        return list(data["discrete_milestones"].values())

    # 如果 value 全是 dict 且至少有一个含 _id 字段，视为记录集
    if all(isinstance(v, dict) for v in data.values()):
        has_ids = any(_get_primary_id(v) is not None for v in data.values())
        if has_ids:
            return list(data.values())

    # 兜底：尝试展平一层
    result = []
    for v in data.values():
        if isinstance(v, dict):
            result.append(v)
    return result if result else [data]


def _get_primary_id(record: dict):
    """从记录中提取主键 ID 值（优先 _id 结尾的字段）。"""
    if not isinstance(record, dict):
        return None
    # 优先匹配 *_id 结尾
    for key, value in record.items():
        if key.endswith("_id") and isinstance(value, (str, int)):
            return value
    # 兜底：id 字段
    for key in ("id", "_id"):
        if key in record and isinstance(record[key], (str, int)):
            return record[key]
    return None


def main():
    print("[Router] AI Studio OS 调度中枢已启动（常驻守护模式）...")
    print(f"[Router] 监听文件: {STATUS_FILE}")
    print(f"[Router] 轮询间隔: {POLL_INTERVAL} 秒")
    print("[Router] 按 Ctrl+C 可停止调度中枢")

    os.makedirs(PROJECT_DB_DIR, exist_ok=True)
    print(f"[Router] 归档仓库已就绪: {PROJECT_DB_DIR}\n")

    validator = SchemaValidator()

    try:
        last_concept_mtime = os.path.getmtime(CONCEPT_FILE)
        print(f"[Router] 概念简案已就绪: {CONCEPT_FILE}")
        print(f"[Router] 基准 mtime: {last_concept_mtime}（修改文件后自动触发）\n")
    except FileNotFoundError:
        last_concept_mtime = 0
        print(f"[Router] 概念简案尚未创建，等待老板编写: {CONCEPT_FILE}\n")

    # ---- 开机清理 ----
    print("[Router] 正在执行开机清理...")
    # 1. 强制重置状态为 idle
    write_state("idle")
    current_state = "idle"

    # 2. 清理上一炉的旧文件（仅限 workspace 根目录，严禁触碰 project_db/）
    files_to_clean = [
        "task_route.json",
        "system_schema.json",
        "system_flow.mmd",
        "system_design_draft.md",
        "system_numerical_docs.json",
        "system_numerical_data.json",
        "audit_feedback.json",
        "guild_design_data.json",
    ]
    for f in files_to_clean:
        filepath = os.path.join(WORKSPACE_DIR, f)
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"[Router] 已清理历史遗留文件: {f}")

    print("[Router] AI Studio OS 调度中枢已就绪（等待修改概念简案）...\n")

    while True:
        try:
            current_mtime = os.path.getmtime(CONCEPT_FILE)
        except Exception:
            current_mtime = last_concept_mtime

        if current_mtime > last_concept_mtime:
            print("\033[93m[Router]\033[0m 检测到老板更新了《概念简案》！自动触发分发器...")
            last_concept_mtime = current_mtime
            for f in [AUDIT_FILE, ROUTE_FILE, BOSS_FEEDBACK_FILE]:
                if os.path.exists(f):
                    os.remove(f)
                    print(f"[Router] 已清理旧文件: {os.path.basename(f)}")
            write_state("pending_classification")
            current_state = "pending_classification"
        else:
            current_state = read_state()

        print(f"[Router][心跳] 当前状态: {current_state}")

        # ============================== 分类 ==============================
        if current_state == "idle":
            pass

        elif current_state == "pending_classification":
            print("[Router] 正在调用前置分类器判断需求类别...")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "classifier_agent.py")],
                    check=True, cwd=ROOT_DIR,
                )
                if not os.path.exists(ROUTE_FILE):
                    print("\033[91m[Router][错误] 路由文件未生成\033[0m")
                    write_state("idle")
                else:
                    with open(ROUTE_FILE, "r", encoding="utf-8") as f:
                        route_data = json.load(f)
                    task_type = route_data.get("task_type", "unknown")
                    reason = route_data.get("reason", "未提供")
                    print(f"[Router] 需求类别判定: {task_type} | {reason}")

                    # ---- 构建全局项目记忆 (Project Codex) ----
                    print("[Router] 正在唤醒档案管理员，构建全局项目记忆 (Project Codex)...")
                    try:
                        subprocess.run(
                            [sys.executable, os.path.join(ROOT_DIR, "Skills", "build_memory_codex.py")],
                            check=True, cwd=ROOT_DIR,
                        )
                        print("[Router] 项目记忆 Codex 构建完成。")
                    except subprocess.CalledProcessError as e:
                        print(f"\033[91m[Router][警告] Codex 构建失败（{e.returncode}），继续执行\033[0m")
                    except FileNotFoundError:
                        print("\033[91m[Router][警告] 找不到 build_memory_codex.py，跳过\033[0m")

                    if task_type == "skill":
                        print("[Router] \U0001f3af 识别为单体技能需求，进入技能管线。")
                        write_state("pending_design")
                    elif task_type == "system":
                        print("[Router] \U0001f3d7\uFE0F 识别为玩法系统需求，进入系统管线。")
                        try:
                            subprocess.run(
                                [sys.executable, os.path.join(ROOT_DIR, "Agents", "system_planner.py")],
                                check=True, cwd=ROOT_DIR,
                            )
                            print("[Router] System Planner 执行完毕。")
                            # system_planner 内部已写 pending_design_approval
                        except subprocess.CalledProcessError as e:
                            print(f"\033[91m[Router] SystemPlanner 失败（{e.returncode}）\033[0m")
                            write_state("idle")
                        except FileNotFoundError:
                            print("\033[91m[Router] 找不到 system_planner.py\033[0m")
                            write_state("idle")
                    else:
                        print(f"\033[91m[Router] 非法类别: '{task_type}'\033[0m")
                        write_state("idle")
            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router] Classifier 失败（{e.returncode}）\033[0m")
                write_state("idle")
            except FileNotFoundError:
                print("\033[91m[Router] 找不到 classifier_agent.py\033[0m")
                write_state("idle")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"\033[91m[Router] 路由解析失败: {e}\033[0m")
                write_state("idle")

        # ============================== 技能管线 ==============================
        elif current_state == "pending_design":
            print("[Router] 正在唤醒主策划 Agent...")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "lead_planner.py")],
                    check=True, cwd=ROOT_DIR,
                )
                print("[Router] 主策划 Agent 执行完毕，进入 Schema 审批。")
                write_state("pending_schema_approval")
            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router] LeadPlanner 失败（{e.returncode}）\033[0m")
                continue
            except FileNotFoundError:
                print("\033[91m[Router] 找不到 lead_planner.py\033[0m")
                continue

        elif current_state == "pending_schema_approval":
            # HITL: 主策划 Schema 验收
            result = require_human_approval(
                agent_name="LeadPlanner (主策划 Schema)",
                artifact_paths=[SCHEMA_FILE, os.path.join(WORKSPACE_DIR, "review_board.md")],
                next_state="pending_execution",
                reject_state="pending_design",
            )
            write_state(result)

        elif current_state == "pending_execution":
            print("[Router] 正在唤醒战斗数值策划 Agent...")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "combat_agent.py")],
                    check=True, cwd=ROOT_DIR,
                )
                print("[Router] Combat Agent 执行完毕，等待校验。")
            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router] CombatAgent 失败（{e.returncode}）\033[0m")
                continue
            except FileNotFoundError:
                print("\033[91m[Router] 找不到 combat_agent.py\033[0m")
                continue

        elif current_state == "pending_validation":
            print("[Router] 正在执行 JSON Schema 强校验...")
            try:
                with open(RESULT_FILE, "r", encoding="utf-8") as f:
                    business_data = json.load(f)
                with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
                    schema_data = json.load(f)
                payload = business_data.get("payload", business_data)
                passed, errors = validator.validate(payload, schema_data)
                if passed:
                    print("\033[92m[安检通过] 数据完美符合契约！\033[0m")
                    write_state("pending_audit")
                else:
                    print("\033[91m[安检拦截]\033[0m")
                    for err in errors:
                        print(f"\033[91m  -> {err}\033[0m")
                    print("\033[91m[安检] 已回滚至 pending_execution，触发自动重试...\033[0m")
                    write_state("pending_execution")
            except FileNotFoundError as e:
                print(f"\033[91m[安检拦截] 文件不存在: {e}\033[0m")
                write_state("pending_execution")
            except json.JSONDecodeError as e:
                print(f"\033[91m[安检拦截] JSON 解析失败: {e}\033[0m")
                write_state("pending_execution")
            except ValueError as e:
                print(f"\033[91m[安检拦截] 校验异常: {e}\033[0m")
                write_state("pending_execution")

        elif current_state == "pending_audit":
            print("[Router] 正在交由主编进行数值逻辑审查...")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "audit_agent.py")],
                    check=True, cwd=ROOT_DIR,
                )
                if not os.path.exists(AUDIT_FILE):
                    print("\033[91m[Router] 审查文件未生成\033[0m")
                    write_state("idle")
                else:
                    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
                        audit_data = json.load(f)
                    is_pass = audit_data.get("is_pass", False)
                    critique = audit_data.get("critique", "")
                    if is_pass:
                        print(f"\033[92m[主编放行] {critique}\033[0m")
                        write_state("pending_data_approval")
                    else:
                        print(f"\033[91m[主编打回] {critique}\033[0m")
                        write_state("pending_execution")
            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router] AuditAgent 失败（{e.returncode}）\033[0m")
                write_state("idle")
            except FileNotFoundError:
                print("\033[91m[Router] 找不到 audit_agent.py\033[0m")
                write_state("idle")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"\033[91m[Router] 审查解析失败: {e}\033[0m")
                write_state("idle")

        elif current_state == "pending_data_approval":
            # HITL: 战斗数值验收
            result = require_human_approval(
                agent_name="CombatAgent + Audit (数值与审查)",
                artifact_paths=[RESULT_FILE, AUDIT_FILE],
                next_state="pending_assets",
                reject_state="pending_execution",
            )
            write_state(result)

        elif current_state == "pending_assets":
            print("[Router] 正在同时唤醒 Code Agent 和 UI Agent...")
            code_ok = False
            ui_ok = False
            print("[Router] --- [1/2] Code Agent ---")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "code_agent.py")],
                    check=True, cwd=ROOT_DIR,
                )
                print("[Router] [OK] Code Agent 执行成功。")
                code_ok = True
            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router] CodeAgent 失败（{e.returncode}）\033[0m")
            except FileNotFoundError:
                print("\033[91m[Router] 找不到 code_agent.py\033[0m")
            print("[Router] --- [2/2] UI Agent ---")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "ui_agent.py")],
                    check=True, cwd=ROOT_DIR,
                )
                print("[Router] [OK] UI Agent 执行成功。")
                ui_ok = True
            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router] UIAgent 失败（{e.returncode}）\033[0m")
            except FileNotFoundError:
                print("\033[91m[Router] 找不到 ui_agent.py\033[0m")
            if code_ok and ui_ok:
                print("[Router] Code + UI 均已完成，流水线终结。")
                write_state("completed")
            else:
                print("\033[91m[Router] 资产生成失败，打回 idle。\033[0m")
                write_state("idle")

        # ============================== 系统管线 ==============================
        elif current_state == "pending_design_approval":
            """
            双轨审批：系统设计草案 (system_design_draft.md) 已生成。
            选项 A (y) = 直接通过
            选项 B (已手动修改) = 通过
            选项 C (其他) = 反馈重写
            """
            draft_path = os.path.join(WORKSPACE_DIR, "system_design_draft.md")

            print("\033[93m" + "=" * 60 + "\033[0m")
            print(f"\033[93m[审批节点] 系统设计草案已生成于: {draft_path}\033[0m")
            print("[审批节点] 请打开上述文件审阅设计内容。")
            print("\033[93m" + "=" * 60 + "\033[0m")
            print("[审批节点] \U0001f449 选项 A (直接通过): 输入 'y'")
            print("[审批节点] \U0001f449 选项 B (手动修改通过): 如果您已直接在 MD 文件中修改完毕，请输入 '已手动修改，请继续'")
            print("[审批节点] \U0001f449 选项 C (对话让 AI 改): 直接输入您的修改意见（例如：'加上公会等级限制'），AI 将重写文档")
            print("\033[93m" + "=" * 60 + "\033[0m")

            user_input = input("[审批节点] 请输入: ").strip()

            if user_input.lower() == "y" or "已手动修改" in user_input:
                print(f"\033[92m[审批节点] 老板放行！设计草案已确认。\033[0m")
                # 如果是手动修改，重新读取 MD（用户已编辑）
                if "已手动修改" in user_input:
                    print("[审批节点] 检测到手动修改，将以当前 MD 文件内容为准。")
                write_state("pending_schema_translate")
            else:
                print(f"\033[91m[审批节点] 老板打回！意见: {user_input}\033[0m")
                try:
                    with open(BOSS_FEEDBACK_FILE, "w", encoding="utf-8") as f:
                        f.write(user_input)
                    print(f"[审批节点] 修改意见已保存至: {BOSS_FEEDBACK_FILE}")
                except Exception as e:
                    print(f"[审批节点][警告] 无法保存反馈: {e}")
                # 打回 system_planner 重写 MD
                try:
                    subprocess.run(
                        [sys.executable, os.path.join(ROOT_DIR, "Agents", "system_planner.py")],
                        check=True, cwd=ROOT_DIR,
                    )
                    print("[Router] System Planner 已根据反馈重新生成草案。")
                        # system_planner 内部会写回 pending_design_approval
                except subprocess.CalledProcessError as e:
                    print(f"\033[91m[Router] SystemPlanner 重试失败（{e.returncode}）\033[0m")
                    write_state("idle")
                except FileNotFoundError:
                    print("\033[91m[Router] 找不到 system_planner.py\033[0m")
                    write_state("idle")

        elif current_state == "pending_schema_translate":
            """
            静默翻译：MD 草案 → system_schema.json
            """
            print("[Router] 正在调用 Schema Translator 将 MD 翻译为结构化 JSON...")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "schema_translator.py")],
                    check=True, cwd=ROOT_DIR,
                )
                print("[Router] Schema 翻译完毕，推进至数值填表。")
                # schema_translator 内部已写 pending_numerical
            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router] SchemaTranslator 失败（{e.returncode}）\033[0m")
                write_state("idle")
            except FileNotFoundError:
                print("\033[91m[Router] 找不到 schema_translator.py\033[0m")
                write_state("idle")

        elif current_state == "pending_numerical":
            print("[Router] 正在唤醒 Numerical Planner 进行数值曲线推演...")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "numerical_planner.py")],
                    check=True, cwd=ROOT_DIR,
                )
                print("[Router] 数值推演完毕，进入数值审批。")
                write_state("pending_numerical_approval")
            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router] NumericalPlanner 失败（{e.returncode}）\033[0m")
                write_state("idle")
            except FileNotFoundError:
                print("\033[91m[Router] 找不到 numerical_planner.py\033[0m")
                write_state("idle")

        elif current_state == "pending_numerical_approval":
            # HITL: 数值成长表验收
            result = require_human_approval(
                agent_name="NumericalPlanner (数值成长表)",
                artifact_paths=[
                    os.path.join(WORKSPACE_DIR, "system_numerical_data.json"),
                    os.path.join(WORKSPACE_DIR, "system_numerical_docs.json"),
                ],
                next_state="completed",
                reject_state="pending_numerical",
            )

            if result == "completed":
                _upsert_archive(WORKSPACE_DIR, PROJECT_DB_DIR)
                print(f"\033[92m[Router] 核心数据已永久归档至 Project DB！\033[0m")
                # 立即刷新全局记忆库，确保 Codex 与 Registry 同步
                try:
                    subprocess.run(
                        [sys.executable, os.path.join(ROOT_DIR, "Skills", "build_memory_codex.py")],
                        check=True, cwd=ROOT_DIR,
                    )
                    print("[Router] 全局记忆库 (Codex + Registry) 已刷新。")
                except subprocess.CalledProcessError as e:
                    print(f"\033[91m[Router][警告] Codex 构建失败（{e.returncode}），数据已归档但记忆未刷新\033[0m")
                except FileNotFoundError:
                    print("\033[91m[Router][警告] 找不到 build_memory_codex.py，跳过记忆刷新\033[0m")

            write_state(result)

        # ============================== 终态 ==============================
        elif current_state == "completed":
            print("[Router] 本次流水线任务全部完成，进入待机摸鱼模式...")
            write_state("idle")

        else:
            print(f"[Router][警告] 遇到未知状态: '{current_state}'，重置为 idle")
            write_state("idle")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
