"""
Main Router (核心中枢 / 24h 常驻守护进程)
职责：基于状态机轮询 task_status.json 调度所有子 Agent 和 Guards。

状态流转（碎片化 HITL 审批 / 环形永不退出）：
  idle --> pending_classification
    |--> (skill) pending_design --> pending_schema_approval --> pending_execution
    |         --> pending_validation --> pending_audit --> pending_data_approval
    |         --> pending_assets --> completed --> idle
    |
    |--> (system) pending_system_design --> pending_system_approval
              --> pending_numerical --> pending_numerical_approval
              --> completed --> idle
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


def main():
    print("[Router] AI Studio OS 调度中枢已启动（常驻守护模式）...")
    print(f"[Router] 监听文件: {STATUS_FILE}")
    print(f"[Router] 轮询间隔: {POLL_INTERVAL} 秒")
    print("[Router] 按 Ctrl+C 可停止调度中枢\n")

    validator = SchemaValidator()

    try:
        last_concept_mtime = os.path.getmtime(CONCEPT_FILE)
        print(f"[Router] 概念简案已就绪: {CONCEPT_FILE}")
        print(f"[Router] 基准 mtime: {last_concept_mtime}（修改文件后自动触发）\n")
    except FileNotFoundError:
        last_concept_mtime = 0
        print(f"[Router] 概念简案尚未创建，等待老板编写: {CONCEPT_FILE}\n")

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
                            write_state("pending_system_design")
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
                    write_state("idle")
            except FileNotFoundError as e:
                print(f"\033[91m[安检拦截] 文件不存在: {e}\033[0m")
                write_state("idle")
            except json.JSONDecodeError as e:
                print(f"\033[91m[安检拦截] JSON 解析失败: {e}\033[0m")
                write_state("idle")
            except ValueError as e:
                print(f"\033[91m[安检拦截] 校验异常: {e}\033[0m")
                write_state("idle")

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
        elif current_state == "pending_system_design":
            print("[Router] 系统架构图已就绪，推进至架构审批...")
            write_state("pending_system_approval")

        elif current_state == "pending_system_approval":
            # HITL: 系统架构验收
            result = require_human_approval(
                agent_name="SystemPlanner (系统架构)",
                artifact_paths=[
                    os.path.join(WORKSPACE_DIR, "system_flow.mmd"),
                    os.path.join(WORKSPACE_DIR, "system_schema.json"),
                ],
                next_state="pending_numerical",
                reject_state="pending_system_design",
            )
            write_state(result)

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
                ],
                next_state="completed",
                reject_state="pending_numerical",
            )
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
