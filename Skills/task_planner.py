"""
Task Planner (Skill B / PM)
职责：读取终审通过的 system_design_draft.md + 团队花名册 → WBS 任务拆解
输出：task_plan.md
"""

import json
import os
import re
import sys
import traceback

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(FILE_DIR)
sys.path.insert(0, ROOT_DIR)

from Skills.llm_client import ask_llm

WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
KNOWLEDGE_DIR = os.path.join(WORKSPACE_DIR, "knowledge")
DRAFT_FILE     = os.path.join(WORKSPACE_DIR, "system_design_draft.md")
CAPABILITIES_FILE = os.path.join(KNOWLEDGE_DIR, "team_capabilities.md")
PLAN_OUTPUT    = os.path.join(WORKSPACE_DIR, "task_plan.md")
FEEDBACK_FILE  = os.path.join(WORKSPACE_DIR, "boss_feedback.txt")
STATUS_FILE    = os.path.join(WORKSPACE_DIR, "task_status.json")

RED   = "\033[91m"
GRN   = "\033[92m"
RESET = "\033[0m"


def load_file(path: str) -> str:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return ""


def main():
    # ========== 1. 读取输入 ==========
    draft = load_file(DRAFT_FILE)
    capabilities = load_file(CAPABILITIES_FILE)
    feedback = load_file(FEEDBACK_FILE)

    if not draft:
        print(f"{RED}设计草案不存在: {DRAFT_FILE}{RESET}")
        sys.exit(1)

    print(f"[TaskPlanner] 已读取设计草案 ({len(draft)} 字符)")

    # ========== 2. PM 提示词 ==========
    system_prompt = f"""你是一位资深游戏开发项目经理 (PM)。

请根据终审通过的系统设计草案，以及下游团队的能力花名册，进行 WBS（工作分解结构）拆解。

下游团队能力：
{capabilities}

请输出一份详尽的 Markdown 任务拆解计划，包含：

## 1. 任务分解
- 为每个下游 Agent 明确列出具体任务、输入文件、产出文件

## 2. 执行顺序与依赖
- 标注哪些任务可以并行，哪些必须串行

## 3. 风险提示
- 指出可能的阻塞点和跨团队依赖冲突

最高指令：
1. 禁止废话
2. 输出纯 Markdown 格式"""

    user_prompt = f"以下是终审通过的设计草案：\n\n{draft}"

    if feedback:
        user_prompt = f"【老板修改意见】: {feedback}\n\n{user_prompt}"

    # ========== 3. 调用 ==========
    print("[TaskPlanner] 正在呼叫大模型进行任务拆解...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt)
    except Exception:
        traceback.print_exc()
        sys.exit(1)

    print("=" * 60)
    print("【大模型原始返回】:")
    print(llm_response[:500])
    if len(llm_response) > 500:
        print(f"... (共 {len(llm_response)} 字符)")
    print("=" * 60)

    # ========== 4. 保存 ==========
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    with open(PLAN_OUTPUT, "w", encoding="utf-8") as f:
        f.write(llm_response.strip())

    print(f"{GRN}[TaskPlanner] 任务拆解计划已保存: {PLAN_OUTPUT} ({len(llm_response)} 字符){RESET}")

    # 推进状态
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                sd = json.load(f)
            sd["current_state"] = "pending_plan_approval"
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(sd, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    print("[TaskPlanner] 任务拆解完成，等待老板审批排期计划。")


if __name__ == "__main__":
    main()
