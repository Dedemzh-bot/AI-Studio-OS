"""
Main Router (核心中枢 / 24h 常驻守护进程)
职责：基于状态机轮询 task_status.json 调度所有子 Agent 和 Guards。

状态流转（环形，永不退出）：
    idle --> pending_classify --> (skill) pending_design --> pending_execution --> pending_validation
      ^                              |                                                            |
      |                              +--> (system) idle [占位]                                    |
      |                                                                                           |
      +-- pending_audit --> pending_assets --> completed <--------------------------------------+
      |        | 打回                          |
      +--------+-- pending_execution <---------+
                              (自动归位 idle，等待下一张工单)
"""

import json
import os
import subprocess
import sys
import time

# ---- Windows 控制台 UTF-8 适配 ----
# 中文 Windows 默认使用 GBK 编码输出，会导致中文乱码或打印失败
# 须在所有 print 之前执行，否则首个打印会按 GBK 输出变成乱码
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass  # 控制台不支持 UTF-8 时静默降级，优先保证脚本能启动

# 确保项目根目录在 sys.path 中，方便引入 Guards 模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from Guards.schema_validator import SchemaValidator

# ---- 配置 ----
# 以 main_router.py 自身所在目录为基准，拼接所有文件的绝对路径
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
STATUS_FILE = os.path.join(WORKSPACE_DIR, "task_status.json")
RESULT_FILE = os.path.join(WORKSPACE_DIR, "current_result.json")
SCHEMA_FILE = os.path.join(WORKSPACE_DIR, "active_schema.json")
CONCEPT_FILE = os.path.join(WORKSPACE_DIR, "concept_brief.md")
AUDIT_FILE = os.path.join(WORKSPACE_DIR, "audit_feedback.json")
ROUTE_FILE = os.path.join(WORKSPACE_DIR, "task_route.json")
POLL_INTERVAL = 2  # 轮询间隔（秒）


def read_state() -> str:
    """
    安全读取 task_status.json 中的 current_state 字段。
    如果文件不存在或 JSON 结构异常，打印真实错误信息和绝对路径，
    然后返回默认状态 "idle"，绝不静默吞错。
    """
    try:
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("current_state", "idle")
    except FileNotFoundError:
        print(f"[Router][错误] 文件不存在，尝试读取路径: {STATUS_FILE}")
        return "idle"
    except json.JSONDecodeError as e:
        print(f"[Router][错误] JSON 解析失败，文件路径: {STATUS_FILE}")
        print(f"[Router][错误] 详细原因: {e}")
        return "idle"


def write_state(state: str):
    """
    将新的 current_state 写入 task_status.json。
    写入失败时会打印详细警告（含绝对路径），不会导致调度器崩溃。
    """
    try:
        # 确保 .agent_workspace 目录存在（使用绝对路径）
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump({"current_state": state}, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[Router][警告] 无法写入状态文件: {STATUS_FILE}")
        print(f"[Router][警告] 详细原因: {e}")


def main():
    """
    核心调度循环（24h 常驻守护进程）。
    每隔 POLL_INTERVAL 秒读取一次 task_status.json，
    根据 current_state 决定下一步操作。
    工单完成后自动归位 idle，永不 break 退出。
    """
    print("[Router] AI Studio OS 调度中枢已启动（常驻守护模式）...")
    print(f"[Router] 监听文件: {STATUS_FILE}")
    print(f"[Router] 轮询间隔: {POLL_INTERVAL} 秒")
    print("[Router] 按 Ctrl+C 可停止调度中枢\n")

    validator = SchemaValidator()  # 防线一：JSON Schema 强校验器

    # 初始化概念简案的最后修改时间，用于自动触发检测
    # 取实际 mtime 为基准，只在文件被修改后触发（首次需 Ctrl+S 激活）
    try:
        last_concept_mtime = os.path.getmtime(CONCEPT_FILE)
        print(f"[Router] 概念简案已就绪: {CONCEPT_FILE}")
        print(f"[Router] 基准 mtime: {last_concept_mtime}（修改文件后自动触发）\n")
    except FileNotFoundError:
        last_concept_mtime = 0
        print(f"[Router] 概念简案尚未创建，等待老板编写: {CONCEPT_FILE}\n")

    while True:
        # 1. 读取当前状态
        current_state = read_state()
        print(f"[Router][心跳] 当前状态: {current_state}")

        # 2. 根据状态执行对应分支
        if current_state == "idle":
            # 空闲状态：监听《概念简案》文件是否被老板更新
            try:
                current_mtime = os.path.getmtime(CONCEPT_FILE)
            except FileNotFoundError:
                current_mtime = 0

            if current_mtime > last_concept_mtime:
                last_concept_mtime = current_mtime
                print("\033[93m[Router]\033[0m 检测到老板更新了《概念简案》，自动触发新一轮设计流水线！")
                # 清理旧轮次文件，防止干扰新任务
                for f in [AUDIT_FILE, ROUTE_FILE]:
                    if os.path.exists(f):
                        os.remove(f)
                        print(f"[Router] 已清理旧文件: {os.path.basename(f)}")
                write_state("pending_classify")

        elif current_state == "pending_classify":
            """
            前置路由：调用分类器判断需求的开发类别（skill / system）
            """
            print("[Router] 正在调用前置分类器判断需求类别...")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "classifier_agent.py")],
                    check=True,
                    cwd=ROOT_DIR,
                )
                print("[Router] 分类器执行完毕，正在读取路由指令...")

                if not os.path.exists(ROUTE_FILE):
                    print("\033[91m[Router][错误] 路由文件未生成，打回至 idle\033[0m")
                    write_state("idle")
                else:
                    with open(ROUTE_FILE, "r", encoding="utf-8") as f:
                        route_data = json.load(f)

                    task_type = route_data.get("task_type", "unknown")
                    print(f"[Router] 需求类别判定: {task_type}")

                    if task_type == "skill":
                        print("[Router] 进入「技能」开发流水线...")
                        write_state("pending_design")
                    elif task_type == "system":
                        print("\033[93m[Router][系统管线占位]\033[0m 检测到「系统」类需求，该管线尚未实现。")
                        print("[Router] 建议：通行证/养成/经济等系统需专门的 system_planner 处理。")
                        write_state("idle")
                    else:
                        print(f"\033[91m[Router][错误] 非法的任务类别: '{task_type}'\033[0m")
                        write_state("idle")

            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router][错误] ClassifierAgent 执行失败（退出码 {e.returncode}）\033[0m")
                write_state("idle")
            except FileNotFoundError:
                print(f"\033[91m[Router][错误] 找不到 classifier_agent.py\033[0m")
                write_state("idle")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"\033[91m[Router][错误] 路由文件解析失败: {e}\033[0m")
                write_state("idle")

        elif current_state == "pending_design":
            print("[Router] 正在真实唤醒主策划 Agent...")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "lead_planner.py")],
                    check=True,
                    cwd=ROOT_DIR,
                )
                print("[Router] 主策划 Agent 执行完毕，交接至 Combat Agent 生成数值。")
                write_state("pending_execution")
            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router][错误] 主策划 Agent 执行失败（退出码 {e.returncode}）\033[0m")
                print(f"\033[91m[Router][错误] stderr: {e.stderr}\033[0m")
                print("[Router] 保持 pending_design 状态，等待下轮重试...")
                continue
            except FileNotFoundError:
                print(f"\033[91m[Router][错误] 找不到 lead_planner.py，请确认文件路径\033[0m")
                continue

        elif current_state == "pending_validation":
            print("[Router] 正在执行 JSON Schema 强校验...")
            try:
                # 从黑板加载当前产出的数据和生效的 Schema（均使用绝对路径）
                with open(RESULT_FILE, "r", encoding="utf-8") as f:
                    business_data = json.load(f)
                with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
                    schema_data = json.load(f)

                # 提取 payload 作为实际业务数据（current_result.json 含 source_agent/task_id 包装）
                payload = business_data.get("payload", business_data)

                # 执行校验
                passed, errors = validator.validate(payload, schema_data)

                if passed:
                    print("\033[92m[安检通过] 数据完美符合契约！\033[0m")
                    write_state("pending_audit")
                else:
                    print(f"\033[91m[安检拦截] 数据校验不通过，以下字段存在错漏:\033[0m")
                    for err in errors:
                        print(f"\033[91m  -> {err}\033[0m")
                    print("\033[91m[安检拦截] 已打回至 idle，请检查数据后重新触发。\033[0m")
                    write_state("idle")

            except FileNotFoundError as e:
                print(f"\033[91m[安检拦截] 校验文件不存在: {e}\033[0m")
                write_state("idle")
            except json.JSONDecodeError as e:
                print(f"\033[91m[安检拦截] JSON 解析失败: {e}\033[0m")
                write_state("idle")
            except ValueError as e:
                print(f"\033[91m[安检拦截] 校验异常: {e}\033[0m")
                write_state("idle")

        elif current_state == "pending_audit":
            """
            数值审查阶段：语法安检通过后，交由主编审查数值平衡性。
            通过 → pending_assets（继续资产生成）
            驳回 → pending_execution（打回重写数值）
            """
            print("[Router] 语法安检通过，正在交由主编进行数值逻辑审查...")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "audit_agent.py")],
                    check=True,
                    cwd=ROOT_DIR,
                )
                print("[Router] 主编审查执行完毕，正在读取判决结果...")

                # 读取审查反馈
                if not os.path.exists(AUDIT_FILE):
                    print("\033[91m[Router][错误] 审查反馈文件未生成，打回至 idle\033[0m")
                    write_state("idle")
                else:
                    with open(AUDIT_FILE, "r", encoding="utf-8") as f:
                        audit_data = json.load(f)

                    is_pass = audit_data.get("is_pass", False)
                    critique = audit_data.get("critique", "无详细原因")

                    if is_pass:
                        print(f"\033[92m[主编放行] {critique}\033[0m")
                        write_state("pending_assets")
                    else:
                        print(f"\033[91m[主编打回] 理由: {critique}\033[0m")
                        print("\033[91m[主编打回] 已将工单退回至 Combat Agent 重写数值。\033[0m")
                        write_state("pending_execution")

            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router][错误] AuditAgent 执行失败（退出码 {e.returncode}）\033[0m")
                print("[Router] 打回至 idle 等待排查。")
                write_state("idle")
            except FileNotFoundError:
                print(f"\033[91m[Router][错误] 找不到 audit_agent.py\033[0m")
                write_state("idle")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"\033[91m[Router][错误] 审查反馈解析失败: {e}\033[0m")
                write_state("idle")

        elif current_state == "pending_assets":
            """
            资产生成阶段：数值已通过安检+主编审查，同时唤醒 Code Agent 和 UI Agent。
            """
            print("[Router] 数据已通过安检，正在同时唤醒 Code Agent (底层) 和 UI Agent (表现)...")

            code_ok = False
            ui_ok = False

            # ---- Code Agent：底层 GDScript 翻译 ----
            print("[Router] --- [1/2] 启动 Code Agent ---")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "code_agent.py")],
                    check=True,
                    cwd=ROOT_DIR,
                )
                print("[Router] [OK] Code Agent 执行成功。")
                code_ok = True
            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router][错误] CodeAgent 执行失败（退出码 {e.returncode}）\033[0m")
            except FileNotFoundError:
                print(f"\033[91m[Router][错误] 找不到 code_agent.py\033[0m")

            # ---- UI Agent：前端表现配置设计 ----
            print("[Router] --- [2/2] 启动 UI Agent ---")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "ui_agent.py")],
                    check=True,
                    cwd=ROOT_DIR,
                )
                print("[Router] [OK] UI Agent 执行成功。")
                ui_ok = True
            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router][错误] UIAgent 执行失败（退出码 {e.returncode}）\033[0m")
            except FileNotFoundError:
                print(f"\033[91m[Router][错误] 找不到 ui_agent.py\033[0m")

            # ---- 判定 ----
            if code_ok and ui_ok:
                print("[Router] Code Agent + UI Agent 均已完成，流水线终结。")
                write_state("completed")
            else:
                print("\033[91m[Router][错误] 资产生成阶段失败，打回至 idle 等待排查。\033[0m")
                write_state("idle")

        elif current_state == "pending_execution":
            """
            数值重新生成阶段：主编打回后，强制 Combat Agent 根据驳回意见重写数值。
            """
            print("[Router] 正在唤醒战斗数值执行策划 Agent（重写模式）...")
            try:
                subprocess.run(
                    [sys.executable, os.path.join(ROOT_DIR, "Agents", "combat_agent.py")],
                    check=True,
                    cwd=ROOT_DIR,
                )
                print("[Router] 战斗数值 Agent 执行完毕，等待下次心跳校验。")
            except subprocess.CalledProcessError as e:
                print(f"\033[91m[Router][错误] CombatAgent 执行失败（退出码 {e.returncode}）\033[0m")
                print("[Router] 保持 pending_execution 状态，等待下轮重试...")
                continue
            except FileNotFoundError:
                print(f"\033[91m[Router][错误] 找不到 combat_agent.py，请确认文件路径\033[0m")
                continue

        elif current_state == "completed":
            """
            终态：本次流水线任务全部执行完毕。
            自动归位到 idle，继续监听下一张工单，永不退出。
            """
            print("[Router] 本次流水线任务全部完成，进入待机摸鱼模式...")
            write_state("idle")

        else:
            # 未知状态：打印警告并重置为空闲
            print(f"[Router][警告] 遇到未知状态: '{current_state}'，重置为 idle")
            write_state("idle")

        # 3. 等待下一次轮询
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
