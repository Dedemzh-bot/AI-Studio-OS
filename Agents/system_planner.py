"""
System Planner (系统架构师)
职责：分析系统玩法需求（公会、通行证、经济循环等），梳理运转流程与核心数据模块。
产出：system_flow.mmd（Mermaid 流程图）+ system_schema.json（数据模块定义）
"""

import json
import os
import re
import sys
import traceback

# ---- 强制绝对路径 ----
FILE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(FILE_DIR)
sys.path.insert(0, ROOT_DIR)

from Skills.llm_client import ask_llm

# ---- 所有读写目标均拼装为绝对路径 ----
WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
CONCEPT_FILE    = os.path.join(WORKSPACE_DIR, "concept_brief.md")
FLOW_OUTPUT     = os.path.join(WORKSPACE_DIR, "system_flow.mmd")
SCHEMA_OUTPUT   = os.path.join(WORKSPACE_DIR, "system_schema.json")
STATUS_FILE     = os.path.join(WORKSPACE_DIR, "task_status.json")

RED   = "\033[91m"
GRN   = "\033[92m"
RESET = "\033[0m"


def loud_fail(msg: str):
    print(f"{RED}========== [System Planner] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}=============================================={RESET}")
    sys.exit(1)


def main():
    # ========== 1. 读取概念简案 ==========
    try:
        if not os.path.exists(CONCEPT_FILE):
            loud_fail(f"概念简案文件不存在: {CONCEPT_FILE}")

        with open(CONCEPT_FILE, "r", encoding="utf-8") as f:
            concept_text = f.read().strip()

        if not concept_text:
            loud_fail("概念简案内容为空，无法设计")

        print(f"[System Planner] 已读取概念简案 ({len(concept_text)} 字符)")
        print(f"[System Planner] 文件路径: {CONCEPT_FILE}")

    except Exception:
        loud_fail(f"读取概念简案失败: {CONCEPT_FILE}")

    # ========== 2. 构建系统架构师人设提示词 ==========
    system_prompt = """你是一位顶级游戏系统架构师。请分析老板传入的系统玩法需求（如公会、通行证、经济循环）。

你需要做两件事：

第一，梳理系统的运转流程。
用 Mermaid 的 stateDiagram-v2 或 flowchart，直观展示该玩法的逻辑闭环和条件流转。
必须用 ```mermaid ... ``` 代码块包裹。

第二，定义系统所需的核心数据模块。
列出该系统的核心模块及所需的数值字段（例如产出、消耗、等级上限、货币类型、冷却时间、解锁条件等）。
必须用 ```json ... ``` 代码块包裹，输出纯 JSON 数组，每个元素是一个模块定义。

最高指令：
1. 必须同时包含 mermaid 和 json 两个代码块，缺一不可
2. 禁止废话，禁止解释，禁止问候语
3. Mermaid 语法必须正确可渲染
4. JSON 必须是合法的纯 JSON 数组"""

    user_prompt = f"""以下是老板的系统玩法需求：

---
{concept_text}
---

请梳理该系统的运转流程（Mermaid 状态图/流程图），并定义核心数据模块（JSON 数组）。同时输出 mermaid 和 json 代码块。"""

    # ========== 3. 调用大模型 ==========
    print("[System Planner] 正在呼叫大模型设计系统架构...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt)
    except Exception:
        loud_fail("大模型调用失败（网络超时 / API Key 无效 / 服务不可用）")

    print("=" * 60)
    print("【大模型原始返回】:")
    print(llm_response)
    print("=" * 60)
    print(f"[System Planner] 大模型返回完成 ({len(llm_response)} 字符)")

    # ========== 4. 双重正则提取 ==========
    # 4a. 提取 Mermaid 代码块
    mermaid_match = re.search(
        r"```mermaid\s*([\s\S]*?)\s*```",
        llm_response,
        re.DOTALL,
    )

    if mermaid_match:
        mermaid_content = mermaid_match.group(1).strip()
        print(f"[System Planner] 正则成功提取 Mermaid 流程图 ({len(mermaid_content)} 字符)")
    else:
        loud_fail("未能从大模型回答中提取 Mermaid 代码块！请检查 ```mermaid ``` 标记")

    # 4b. 提取 JSON 代码块
    json_match = re.search(
        r"```json\s*([\s\S]*?)\s*```",
        llm_response,
        re.DOTALL,
    )

    if json_match:
        json_str = json_match.group(1).strip()
        print(f"[System Planner] 正则成功提取 JSON 数据 ({len(json_str)} 字符)")
    else:
        loud_fail("未能从大模型回答中提取 JSON 代码块！请检查 ```json ``` 标记")

    # 验证 JSON 合法性
    try:
        schema_data = json.loads(json_str)
    except json.JSONDecodeError:
        loud_fail(f"提取的 JSON 不合法！原始 JSON 片段:\n{json_str[:500]}")

    # ========== 5. 保存产出文件 ==========
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)

        # 5a. 保存 Mermaid 流程图
        with open(FLOW_OUTPUT, "w", encoding="utf-8") as f:
            f.write(mermaid_content)
        print(f"{GRN}[System Planner] Mermaid 流程图已保存: {FLOW_OUTPUT}{RESET}")

        # 5b. 保存系统数据 Schema
        with open(SCHEMA_OUTPUT, "w", encoding="utf-8") as f:
            json.dump(schema_data, f, ensure_ascii=False, indent=2)
        print(f"{GRN}[System Planner] 系统数据 Schema 已保存: {SCHEMA_OUTPUT}{RESET}")

    except Exception:
        loud_fail(f"写入产出文件失败")

    # ========== 6. 推动流水线 → pending_numerical ==========
    try:
        if not os.path.exists(STATUS_FILE):
            loud_fail(f"任务状态文件不存在: {STATUS_FILE}")

        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status_data = json.load(f)

        current_state = status_data.get("current_state", "")
        status_data["current_state"] = "pending_numerical"

        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)

        print(f"[System Planner] 任务状态已更新: {current_state} -> pending_numerical")
        print("[System Planner] 系统架构设计完成，等待数值填表。")

    except Exception:
        loud_fail(f"更新任务状态失败: {STATUS_FILE}")


if __name__ == "__main__":
    main()
