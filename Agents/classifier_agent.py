"""
Classifier Agent (前置路由器 / 需求分类器)
职责：分析概念简案，判断开发类别（skill 或 system），输出路由指令。
输出：task_route.json
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
CONCEPT_FILE = os.path.join(WORKSPACE_DIR, "concept_brief.md")
OUTPUT_FILE  = os.path.join(WORKSPACE_DIR, "task_route.json")
STATUS_FILE  = os.path.join(WORKSPACE_DIR, "task_status.json")

RED   = "\033[91m"
RESET = "\033[0m"


def loud_fail(msg: str):
    print(f"{RED}========== [Classifier Agent] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}================================================={RESET}")
    sys.exit(1)


def main():
    # ========== 1. 读取概念简案 ==========
    try:
        if not os.path.exists(CONCEPT_FILE):
            loud_fail(f"概念简案文件不存在: {CONCEPT_FILE}")

        with open(CONCEPT_FILE, "r", encoding="utf-8") as f:
            concept_text = f.read().strip()

        if not concept_text:
            loud_fail("概念简案内容为空，无法分类")

        print(f"[Classifier Agent] 已读取概念简案 ({len(concept_text)} 字符)")

    except Exception:
        loud_fail(f"读取概念简案失败: {CONCEPT_FILE}")

    # ========== 2. 构建项目经理人设提示词 ==========
    system_prompt = """你是一位游戏开发项目经理。请分析老板传入的设计需求，判断它属于哪种开发类别。

分类标准：
- "skill": 单体技能、Buff、Debuff、状态效果、技能图标、技能数值配置
- "system": 通行证系统、养成系统、经济循环、抽卡机制、公会系统、任务链、排行榜、大局玩法机制

只能输出纯 JSON，格式为:
{"task_type": "skill"}
或
{"task_type": "system"}

最高指令：
1. 禁止废话，禁止解释
2. 只输出上述纯 JSON 格式"""

    user_prompt = f"""以下是老板的设计需求：

---
{concept_text}
---

请判断以上需求属于 skill 还是 system 类别。直接输出 JSON。"""

    # ========== 3. 调用大模型 ==========
    print("[Classifier Agent] 正在呼叫大模型分类需求...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt)
    except Exception:
        loud_fail("大模型调用失败")

    print("=" * 60)
    print("【大模型原始返回】:")
    print(llm_response)
    print("=" * 60)

    # ========== 4. 正则精准提取 JSON ==========
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", llm_response, re.DOTALL)

    if json_match:
        clean_json_str = json_match.group(1).strip()
    else:
        clean_json_str = llm_response.strip()

    try:
        route_data = json.loads(clean_json_str)
    except json.JSONDecodeError:
        loud_fail(f"大模型返回的不是合法 JSON！完整原始返回:\n{llm_response}")

    # ========== 5. 保存路由指令 ==========
    task_type = route_data.get("task_type", "unknown")
    if task_type not in ("skill", "system"):
        loud_fail(f"未知的任务类别: '{task_type}'，仅支持 skill / system")

    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(route_data, f, ensure_ascii=False, indent=2)
        print(f"[Classifier Agent] 路由指令已保存: {OUTPUT_FILE}")
        print(f"[Classifier Agent] 任务类别: {task_type}")
    except Exception:
        loud_fail(f"写入路由指令失败: {OUTPUT_FILE}")

    # ========== 6. 推动流水线 ==========
    try:
        if not os.path.exists(STATUS_FILE):
            loud_fail(f"任务状态文件不存在: {STATUS_FILE}")

        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status_data = json.load(f)

        current_state = status_data.get("current_state", "")
        status_data["current_state"] = "classified"

        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)

        print(f"[Classifier Agent] 任务状态已更新: {current_state} -> classified")
        print("[Classifier Agent] 需求分类完成。")

    except Exception:
        loud_fail(f"更新任务状态失败: {STATUS_FILE}")


if __name__ == "__main__":
    main()
