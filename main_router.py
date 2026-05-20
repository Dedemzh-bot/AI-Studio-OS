"""
Main Router (核心中枢 / 24h 常驻守护进程)
职责：基于状态机轮询 task_status.json 调度所有子 Agent 和 Guards。

状态流转（碎片化 HITL 审批 / 环形永不退出）：
  idle --> pending_classification
    |--> (skill) pending_design --> pending_schema_approval --> pending_execution
    |         --> pending_validation --> pending_audit --> pending_data_approval
    |         --> pending_assets --> completed --> idle
    |
    |--> (system) system_visionary --> clarifying_requirements
              --> pending_design_approval --> pending_plan_approval
              --> pending_system_approval --> pending_schema_translate
              --> pending_translate_approval --> pending_numerical
              --> pending_numerical_approval --> completed(归档) --> idle
"""

import json
import os
import re
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
CONCEPT_CACHE_FILE = os.path.join(WORKSPACE_DIR, ".concept_brief_cache.txt")
DRAFT_CACHE_FILE = os.path.join(WORKSPACE_DIR, ".draft_cache.md")
RETRY_COUNT_FILE = os.path.join(WORKSPACE_DIR, ".retry_count.json")
POLL_INTERVAL = 2

YEL_COLOR = "\033[93m"
GRN_COLOR = "\033[92m"
RED_COLOR = "\033[91m"
RESET_CLR = "\033[0m"


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


def _save_draft_snapshot():
    """保存 system_design_draft.md 的快照副本，用于后续智能剪裁比对。"""
    draft_path = os.path.join(WORKSPACE_DIR, "system_design_draft.md")
    if os.path.exists(draft_path):
        try:
            with open(draft_path, "r", encoding="utf-8") as f:
                content = f.read()
            with open(DRAFT_CACHE_FILE, "w", encoding="utf-8") as f:
                f.write(content)
            print("[Router] 已保存草案快照 (.draft_cache.md)")
        except Exception as e:
            print(f"[Router][警告] 无法保存草案快照: {e}")


def _extract_section(md_text: str, section_title: str) -> str:
    """从 Markdown 文本中提取指定标题的章节内容。"""
    import re
    pattern = rf"^#+\s*{re.escape(section_title)}.*$"
    match = re.search(pattern, md_text, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    # 从该节之后找下一个同级或更高级标题
    level = len(re.match(r"^#+", md_text[start:]).group())
    remaining = md_text[start + len(match.group()):]
    next_match = re.search(rf"^#{{{1,{level}}}}\s", remaining, re.MULTILINE)
    if next_match:
        return md_text[start:start + len(match.group()) + next_match.start()]
    else:
        return md_text[start:]


def _trim_open_questions_if_unchanged():
    """
    智能剪裁：如果"六、待确认风险与疑点"未被人工修改，则删除该节及之后内容。
    返回是否执行了剪裁。
    """
    draft_path = os.path.join(WORKSPACE_DIR, "system_design_draft.md")
    if not os.path.exists(draft_path) or not os.path.exists(DRAFT_CACHE_FILE):
        print("[Router] 缺少草案或快照文件，跳过智能剪裁")
        return False

    try:
        with open(draft_path, "r", encoding="utf-8") as f:
            current_text = f.read()
        with open(DRAFT_CACHE_FILE, "r", encoding="utf-8") as f:
            snapshot_text = f.read()
    except Exception as e:
        print(f"[Router][警告] 读取草案/快照失败: {e}")
        return False

    section_title = "六、待确认风险与疑点"
    current_section = _extract_section(current_text, section_title)
    snapshot_section = _extract_section(snapshot_text, section_title)

    if not current_section:
        print("[Router] 草案中未找到疑点章节，无需剪裁")
        return False

    # 比对：标准化（去空格）后判断是否一致
    current_norm = "".join(current_section.split())
    snapshot_norm = "".join(snapshot_section.split())

    # 相似度阈值：差异小于 5% 视为未修改
    max_len = max(len(current_norm), len(snapshot_norm)) or 1
    similarity = 1.0 - (abs(len(current_norm) - len(snapshot_norm)) / max_len)

    if similarity > 0.95:
        # 老板未修改 → 删除疑点节及之后所有内容
        import re
        pattern = rf"^#+\s*{re.escape(section_title)}.*$"
        match = re.search(pattern, current_text, re.MULTILINE)
        if match:
            trimmed = current_text[:match.start()].rstrip() + "\n"
            with open(draft_path, "w", encoding="utf-8") as f:
                f.write(trimmed)
            print("\033[93m[智能剪裁] 疑点章节未修改，已自动擦除，保护下游数据纯净。\033[0m")
            return True
    else:
        print("\033[92m[智能剪裁] 检测到疑点章节已被人工修改，予以保留。\033[0m")

    return False


def _save_retry_count(count: int):
    """保存当前 Agent 的重试计数。"""
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(RETRY_COUNT_FILE, "w", encoding="utf-8") as f:
            json.dump({"count": count}, f)
    except Exception:
        pass


def _clear_retry_count():
    """清除重试计数。"""
    if os.path.exists(RETRY_COUNT_FILE):
        try:
            os.remove(RETRY_COUNT_FILE)
        except Exception:
            pass


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

    # ---- 基于内容的缓存机制 ----
    concept_current = ""
    try:
        with open(CONCEPT_FILE, "r", encoding="utf-8") as f:
            concept_current = f.read().strip()
    except FileNotFoundError:
        pass

    concept_cache = ""
    try:
        with open(CONCEPT_CACHE_FILE, "r", encoding="utf-8") as f:
            concept_cache = f.read().strip()
    except FileNotFoundError:
        pass

    if concept_current:
        print(f"[Router] 概念简案已就绪: {CONCEPT_FILE} ({len(concept_current)} 字符)")
        if concept_current == concept_cache:
            print("[Router] 内容与缓存一致（旧需求/已处理），保持 idle 监听。\n")
        else:
            print("[Router] 检测到新需求（内容与缓存不一致）。\n")
    else:
        print(f"[Router] 概念简案为空，等待老板编写: {CONCEPT_FILE}\n")

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
        # ===== 0. 每次循环从硬盘读取概念简案内容 =====
        try:
            with open(CONCEPT_FILE, "r", encoding="utf-8") as f:
                concept_current = f.read().strip()
        except FileNotFoundError:
            concept_current = ""

        # ===== 0.5 基于内容的严格比对 =====
        concept_changed = (concept_current and concept_current != concept_cache)

        if concept_changed:
            print("\033[93m[Router]\033[0m 检测到老板更新了《概念简案》内容！自动触发分发器...")
            # 立即更新缓存快照，防止重启误触发
            try:
                with open(CONCEPT_CACHE_FILE, "w", encoding="utf-8") as f:
                    f.write(concept_current)
                concept_cache = concept_current
            except Exception as e:
                print(f"[Router][警告] 无法更新缓存: {e}")
            # 清理旧轮次文件
            for f in [AUDIT_FILE, ROUTE_FILE, BOSS_FEEDBACK_FILE,
                      os.path.join(WORKSPACE_DIR, "system_design_draft.md"),
                      os.path.join(WORKSPACE_DIR, "task_plan.md")]:
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
                        print("[Router] \U0001f3d7\uFE0F 识别为玩法系统需求，进入知识驱动管线。")
                        try:
                            subprocess.run(
                                [sys.executable, os.path.join(ROOT_DIR, "Skills", "system_visionary.py")],
                                check=True, cwd=ROOT_DIR,
                            )
                            print("[Router] Visionary Agent 执行完毕。")
                            write_state("clarifying_requirements")
                        except subprocess.CalledProcessError as e:
                            print(f"\033[91m[Router] Visionary 失败（{e.returncode}）\033[0m")
                            write_state("idle")
                        except FileNotFoundError:
                            print("\033[91m[Router] 找不到 Skills/system_visionary.py\033[0m")
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

        # ============================== 系统管线 (三重状态机) ==============================
        elif current_state == "clarifying_requirements":
            """
            追问闭环：Visionary 判断需求是否完备。
            若返回 need_info → 暂停打印追问 → 等老板回复 → 重跑 Visionary
            若返回 draft_ready → 推进至草案审批
            """
            print("[Router] 正在运行 Visionary 审核需求...")
            try:
                result = subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Skills", "system_visionary.py")],
                    capture_output=True, text=True, cwd=ROOT_DIR,
                )
                output = result.stdout + result.stderr

                # 解析 JSON 状态（健壮提取：先剥掉可能的 markdown 包裹）
                output_clean = re.sub(r"```[a-z]*\s*|\s*```", "", output)
                json_match = re.search(r'\{"status"\s*:\s*"(need_info|draft_ready)"[^}]*\}', output_clean)
                status_data = None
                if json_match:
                    try:
                        status_data = json.loads(json_match.group(0))
                    except json.JSONDecodeError:
                        status_data = None
                if not status_data:
                    # 兜底：从第一个 { 到最后一个 }
                    start = output_clean.find('{"status"')
                    if start >= 0:
                        end = output_clean.rfind('}') + 1
                        json_str = output_clean[start:end]
                        try:
                            status_data = json.loads(json_str)
                        except json.JSONDecodeError:
                            status_data = None
                if status_data:
                    st = status_data.get("status")
                    if st == "need_info":
                        question = status_data.get("question", "")
                        print(f"\n{YEL_COLOR}============================================================{RESET_CLR}")
                        print(f"{YEL_COLOR}[主策追问] {question}{RESET_CLR}")
                        print(f"{YEL_COLOR}============================================================{RESET_CLR}")
                        user_reply = input("[Router] 请输入您的回复（补充需求信息）: ").strip()
                        if user_reply:
                            try:
                                # 成对记录：AI 问题 + 老板回答，防止上下文丢失
                                qa_block = (
                                    f"\n\n> [主策追问] {question}\n"
                                    f"> [老板指示] {user_reply}\n"
                                )
                                with open(CONCEPT_FILE, "a", encoding="utf-8") as f:
                                    f.write(qa_block)
                                print(f"[Router] 已将问答对追加至概念简案。")
                                # 同步更新缓存，防止下轮心跳误判为"新需求触发"
                                with open(CONCEPT_FILE, "r", encoding="utf-8") as f:
                                    new_content = f.read().strip()
                                with open(CONCEPT_CACHE_FILE, "w", encoding="utf-8") as f:
                                    f.write(new_content)
                                concept_cache = new_content
                            except Exception as e:
                                print(f"[Router][警告] 无法追加/更新缓存: {e}")
                        # 保持 clarifying_requirements，下一轮心跳自动重新运行 Visionary
                        write_state("clarifying_requirements")
                    elif st == "draft_ready":
                        print(f"{GRN_COLOR}[Router] 需求已完备，设计草案已生成！{RESET_CLR}")
                        # 保存快照副本，用于后续智能剪裁比对
                        _save_draft_snapshot()
                        write_state("pending_design_approval")
                else:
                    print(f"\033[91m[Router] 无法解析 Visionary 输出状态\033[0m")
                    write_state("idle")
            except Exception as e:
                print(f"\033[91m[Router] Visionary 执行异常: {e}\033[0m")
                write_state("idle")

        elif current_state == "pending_design_approval":
            """
            草案审查黑板：审阅 system_design_draft.md → 通过后进入 PM 排期
            """
            draft_path = os.path.join(WORKSPACE_DIR, "system_design_draft.md")

            print("\033[93m" + "=" * 60 + "\033[0m")
            print(f"\033[93m[草案审查] 设计草案已生成于: {draft_path}\033[0m")
            print("[草案审查] 您可以直接修改该文件，或在下方输入修改意见打回。若确认无误，请输入 'y' 进入任务拆解：")
            print("\033[93m" + "=" * 60 + "\033[0m")

            user_input = input("[草案审查] 请输入: ").strip()

            if user_input.lower() == "y" or "已手动修改" in user_input:
                print(f"\033[92m[草案审查] 老板放行！设计草案已确认。\033[0m")
                # ---- MD 智能阅卷与剪裁 ----
                _trim_open_questions_if_unchanged()
                # ---- 进入 PM 任务拆解 ----
                try:
                    subprocess.run(
                        [sys.executable, os.path.join(ROOT_DIR, "Skills", "task_planner.py")],
                        check=True, cwd=ROOT_DIR,
                    )
                    print("[Router] Task Planner 执行完毕。")
                    # task_planner 内部已写 pending_plan_approval
                except subprocess.CalledProcessError as e:
                    print(f"\033[91m[Router] TaskPlanner 失败（{e.returncode}）\033[0m")
                    write_state("idle")
                except FileNotFoundError:
                    print("\033[91m[Router] 找不到 Skills/task_planner.py\033[0m")
                    write_state("idle")
            else:
                print(f"\033[91m[草案审查] 老板打回！意见: {user_input}\033[0m")
                try:
                    with open(BOSS_FEEDBACK_FILE, "w", encoding="utf-8") as f:
                        f.write(user_input)
                except Exception as e:
                    print(f"[草案审查][警告] 无法保存反馈: {e}")
                # 打回 Visionary 重写 MD
                try:
                    subprocess.run(
                        [sys.executable, os.path.join(ROOT_DIR, "Skills", "system_visionary.py")],
                        check=True, cwd=ROOT_DIR,
                    )
                    print("[Router] Visionary 已根据反馈重新生成草案。")
                except subprocess.CalledProcessError as e:
                    print(f"\033[91m[Router] Visionary 重试失败（{e.returncode}）\033[0m")
                    write_state("idle")
                except FileNotFoundError:
                    print("\033[91m[Router] 找不到 system_visionary.py\033[0m")
                    write_state("idle")

        elif current_state == "pending_plan_approval":
            """
            计划审查黑板：审阅 task_plan.md → 通过后进入执行阶段
            """
            plan_path = os.path.join(WORKSPACE_DIR, "task_plan.md")

            print("\033[93m" + "=" * 60 + "\033[0m")
            print(f"\033[93m[计划审查] 任务拆解计划已生成于: {plan_path}\033[0m")
            print("[计划审查] 输入修改意见重新排期，或输入 'y' 正式派发给子 Agent 团队执行：")
            print("\033[93m" + "=" * 60 + "\033[0m")

            user_input = input("[计划审查] 请输入: ").strip()

            if user_input.lower() == "y":
                print(f"\033[92m[计划审查] 老板放行！进入系统设计最终验收。\033[0m")
                write_state("pending_system_approval")
            else:
                print(f"\033[91m[计划审查] 老板打回！意见: {user_input}\033[0m")
                try:
                    with open(BOSS_FEEDBACK_FILE, "w", encoding="utf-8") as f:
                        f.write(user_input)
                except Exception as e:
                    print(f"[计划审查][警告] 无法保存反馈: {e}")
                # 打回 Task Planner 重新排期
                try:
                    subprocess.run(
                        [sys.executable, os.path.join(ROOT_DIR, "Skills", "task_planner.py")],
                        check=True, cwd=ROOT_DIR,
                    )
                    print("[Router] Task Planner 已重新排期。")
                except subprocess.CalledProcessError as e:
                    print(f"\033[91m[Router] TaskPlanner 重试失败（{e.returncode}）\033[0m")
                    write_state("idle")
                except FileNotFoundError:
                    print("\033[91m[Router] 找不到 task_planner.py\033[0m")
                    write_state("idle")

        elif current_state == "pending_system_approval":
            """
            系统设计最终验收：老板审阅完整设计草案 + 任务拆解计划，确认后进入执行。
            """
            draft_path = os.path.join(WORKSPACE_DIR, "system_design_draft.md")
            plan_path = os.path.join(WORKSPACE_DIR, "task_plan.md")

            print("\033[93m" + "=" * 60 + "\033[0m")
            print("\033[93m[系统验收] 系统策划已完成详细玩法设计与脑暴。\033[0m")
            if os.path.exists(draft_path):
                print(f"[系统验收] 设计草案: {draft_path} ({os.path.getsize(draft_path)} 字节)")
            if os.path.exists(plan_path):
                print(f"[系统验收] 任务拆解: {plan_path} ({os.path.getsize(plan_path)} 字节)")
            print("[系统验收] 请输入您的修改意见打回重做；或输入 'y' 批准该设计，正式进入 Schema 翻译与数值配置阶段：")
            print("\033[93m" + "=" * 60 + "\033[0m")

            user_input = input("[系统验收] 请输入: ").strip()

            if user_input.lower() == "y":
                print(f"\033[92m[系统验收] 老板批准！进入 Schema 翻译与数值配置阶段。\033[0m")
                write_state("pending_schema_translate")
            else:
                print(f"\033[91m[系统验收] 老板打回！意见: {user_input}\033[0m")
                try:
                    with open(BOSS_FEEDBACK_FILE, "w", encoding="utf-8") as f:
                        f.write(user_input)
                except Exception as e:
                    print(f"[系统验收][警告] 无法保存反馈: {e}")
                # 打回 Visionary 基于已有草案 + 反馈重写
                try:
                    subprocess.run(
                        [sys.executable, os.path.join(ROOT_DIR, "Skills", "system_visionary.py")],
                        check=True, cwd=ROOT_DIR,
                    )
                    print("[Router] Visionary 已根据验收反馈重新生成草案。")
                except subprocess.CalledProcessError as e:
                    print(f"\033[91m[Router] Visionary 重试失败（{e.returncode}）\033[0m")
                    write_state("idle")
                except FileNotFoundError:
                    print("\033[91m[Router] 找不到 system_visionary.py\033[0m")
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
                print("[Router] Schema 翻译完毕，等待老板审批。")
                write_state("pending_translate_approval")
            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router] SchemaTranslator 失败（{e.returncode}）\033[0m")
                write_state("idle")
            except FileNotFoundError:
                print("\033[91m[Router] 找不到 schema_translator.py\033[0m")
                write_state("idle")

        elif current_state == "pending_translate_approval":
            """
            Schema 翻译审批：审阅 system_schema.json → 通过后进入数值填表
            """
            schema_path = os.path.join(WORKSPACE_DIR, "system_schema.json")

            print("\033[93m" + "=" * 60 + "\033[0m")
            print(f"\033[93m[翻译审批] Schema 翻译完成，产出文件: {schema_path}\033[0m")
            print("[翻译审批] 输入修改意见打回重做，或输入 'y' 确认通过并流转至数值填表：")
            print("\033[93m" + "=" * 60 + "\033[0m")

            user_input = input("[翻译审批] 请输入: ").strip()

            if user_input.lower() == "y":
                print(f"\033[92m[翻译审批] 老板放行！进入数值填表阶段。\033[0m")
                write_state("pending_numerical")
            else:
                print(f"\033[91m[翻译审批] 老板打回！意见: {user_input}\033[0m")
                try:
                    with open(BOSS_FEEDBACK_FILE, "w", encoding="utf-8") as f:
                        f.write(user_input)
                except Exception as e:
                    print(f"[翻译审批][警告] 无法保存反馈: {e}")
                # 打回 Schema Translator 重做
                try:
                    subprocess.run(
                        [sys.executable, os.path.join(ROOT_DIR, "Agents", "schema_translator.py")],
                        check=True, cwd=ROOT_DIR,
                    )
                    print("[Router] Schema Translator 已重新翻译。")
                except subprocess.CalledProcessError as e:
                    print(f"\033[91m[Router] SchemaTranslator 重试失败（{e.returncode}）\033[0m")
                    write_state("idle")
                except FileNotFoundError:
                    print("\033[91m[Router] 找不到 schema_translator.py\033[0m")
                    write_state("idle")

        elif current_state == "pending_numerical":
            # 读取重试计数
            retry_count = 0
            if os.path.exists(RETRY_COUNT_FILE):
                try:
                    with open(RETRY_COUNT_FILE, "r", encoding="utf-8") as f:
                        retry_count = json.load(f).get("count", 0)
                except Exception:
                    pass

            print(f"[Router] 正在唤醒 Numerical Planner 进行数值曲线推演... (第 {retry_count + 1} 次)")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "numerical_planner.py")],
                    check=True, cwd=ROOT_DIR,
                )
                print("[Router] 数值推演完毕，进入数值审批。")
                _clear_retry_count()
                write_state("pending_numerical_approval")
            except subprocess.CalledProcessError as e:
                if e.returncode == 2 and retry_count < 2:
                    # JSON 截断 → 自动重试
                    retry_count += 1
                    _save_retry_count(retry_count)
                    print(f"\033[93m[Router] NumericalPlanner JSON 被截断，自动重试 ({retry_count}/2)...\033[0m")
                    # 保持 pending_numerical，下轮心跳重试
                elif e.returncode == 2 and retry_count >= 2:
                    # 重试耗尽 → 人工介入
                    _clear_retry_count()
                    print(f"\033[91m[Router] NumericalPlanner 重试 {retry_count} 次仍失败（JSON 截断）\033[0m")
                    print("\033[93m[Router] 数值策划生成数据表失败（可能因为内容过长）。\033[0m")
                    user_input = input("[Router] 按 'y' 再次重试，或按 'n' 打回至主策划重新拆解: ").strip()
                    if user_input.lower() == "y":
                        write_state("pending_numerical")
                    else:
                        write_state("pending_schema_translate")
                else:
                    # 其他错误
                    _clear_retry_count()
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
