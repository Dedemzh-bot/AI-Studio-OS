"""
Main Router (核心中枢 / 24h 常驻守护进程)
职责：基于状态机轮询 task_status.json 调度所有子 Agent 和 Guards。

状态流转（环形，永不退出）：
    idle --> pending_design --> pending_validation --> pending_execution --> completed
      ^                                                                          |
      +--------------------------------------------------------------------------+
                              (自动归位 idle，等待下一张工单)
"""

import json
import os
import sys
import time

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

    while True:
        # 1. 读取当前状态
        current_state = read_state()
        print(f"[Router][心跳] 当前状态: {current_state}")

        # 2. 根据状态执行对应分支
        if current_state == "idle":
            # 空闲状态：什么都不做，等待外部触发
            pass

        elif current_state == "pending_design":
            """
            设计阶段：唤醒主策划 Agent 制定 Schema 和 Blueprint。
            当前为骨架 MVP，仅打印提示并直接跳入下一状态。
            """
            print("[Router] 正在唤醒主策划 Agent 制定 Schema...")
            # TODO: 后续接入 lead_planner.py 的实际调用
            time.sleep(1)  # 模拟 Agent 工作耗时
            print("[Router] Schema 与 Blueprint 产出完毕。")
            write_state("pending_validation")

        elif current_state == "pending_validation":
            """
            校验阶段：调用 schema_validator.py 对产出数据进行强校验。
            校验通过 → pending_execution
            校验失败 → 回退到 pending_design 触发重试
            """
            print("[Router] 正在执行 JSON Schema 强校验...")
            try:
                # 从黑板加载当前产出的数据和生效的 Schema（均使用绝对路径）
                with open(RESULT_FILE, "r", encoding="utf-8") as f:
                    business_data = json.load(f)
                with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
                    schema_data = json.load(f)

                # 执行校验（抛出 ValueError 即表示不通过）
                passed, errors = validator.validate(business_data, schema_data)

                if passed:
                    print("[Router] [PASS] 校验通过，放行至执行阶段。")
                    write_state("pending_execution")
                else:
                    print(f"[Router] [FAIL] 校验不通过: {errors}")
                    print("[Router] 回退至设计阶段，等待主策划修正...")
                    write_state("pending_design")

            except FileNotFoundError as e:
                print(f"[Router] [FAIL] 校验文件不存在: {e}")
                print(f"[Router] 尝试读取 result 路径: {RESULT_FILE}")
                print(f"[Router] 尝试读取 schema 路径: {SCHEMA_FILE}")
                print("[Router] 数据文件尚未就绪，回退至设计阶段。")
                write_state("pending_design")
            except json.JSONDecodeError as e:
                print(f"[Router] [FAIL] JSON 解析失败: {e}")
                print("[Router] 回退至设计阶段，等待修正...")
                write_state("pending_design")
            except ValueError as e:
                print(f"[Router] [FAIL] 校验异常: {e}")
                print("[Router] 回退至设计阶段，等待修正...")
                write_state("pending_design")

        elif current_state == "pending_execution":
            """
            执行阶段：将校验通过的设计数据分发给 CodeAgent 进行代码翻译。
            骨架 MVP 中仅提示即标记完成。
            """
            print("[Router] 正在分发具体执行任务给 CodeAgent...")
            # TODO: 后续接入 code_agent.py 的实际调用
            time.sleep(1)  # 模拟代码生成耗时
            print("[Router] 代码产出完毕。")
            write_state("completed")

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
