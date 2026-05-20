"""
Schema Translator (格式翻译器)
职责：读取人类确认的 system_design_draft.md → 翻译为结构化 system_schema.json
不做任何业务逻辑修改，只做格式转换。
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
DRAFT_FILE    = os.path.join(WORKSPACE_DIR, "system_design_draft.md")
SCHEMA_OUTPUT = os.path.join(WORKSPACE_DIR, "system_schema.json")
STATUS_FILE   = os.path.join(WORKSPACE_DIR, "task_status.json")

RED   = "\033[91m"
GRN   = "\033[92m"
RESET = "\033[0m"


def loud_fail(msg: str):
    print(f"{RED}========== [Schema Translator] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}=================================================={RESET}")
    sys.exit(1)


def main():
    # ========== 1. 读取已确认的设计草案 ==========
    try:
        if not os.path.exists(DRAFT_FILE):
            loud_fail(f"设计草案不存在: {DRAFT_FILE}")
        with open(DRAFT_FILE, "r", encoding="utf-8") as f:
            draft_text = f.read().strip()
        if not draft_text:
            loud_fail("设计草案内容为空")
        print(f"[Schema Translator] 已读取设计草案 ({len(draft_text)} 字符)")
    except Exception:
        loud_fail(f"读取草案失败: {DRAFT_FILE}")

    # ========== 2. 翻译提示词 ==========
    system_prompt = """你是一个精准的格式翻译器。

请读取已经过人类最终确认的系统设计草案（Markdown 格式），将其严格翻译为结构化的 JSON 数据模块定义。

要求：
1. 输出纯 JSON 数组，每个元素是一个模块定义
2. 每个模块包含：module_name、continuous_fields（连续成长的字段列表）、discrete_fields（离散解锁的字段列表）
3. 不要改变任何业务逻辑，只做格式转换
4. 字段名保持英文 snake_case
5. 禁止包含运行时状态字段

最高指令：
1. 禁止废话，禁止解释
2. 只输出 `json ... ` 包裹的纯 JSON"""

    user_prompt = f"以下是人类确认的设计草案：\n\n---\n{draft_text}\n---\n\n请翻译为 system_schema.json 格式。直接输出 JSON 数组。"

    # ========== 3. 调用大模型 ==========
    print("[Schema Translator] 正在呼叫大模型翻译 MD -> JSON...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt)
    except Exception:
        loud_fail("大模型调用失败")

    print("=" * 60)
    print("【大模型原始返回】:")
    print(llm_response[:500])
    if len(llm_response) > 500:
        print(f"... (共 {len(llm_response)} 字符)")
    print("=" * 60)

    # ========== 4. 正则提取 JSON ==========
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", llm_response, re.DOTALL)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_str = llm_response.strip()

    try:
        schema_data = json.loads(json_str)
    except json.JSONDecodeError:
        loud_fail(f"翻译结果不是合法 JSON！\n{json_str[:500]}")

    # ========== 5. 保存 ==========
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(SCHEMA_OUTPUT, "w", encoding="utf-8") as f:
            json.dump(schema_data, f, ensure_ascii=False, indent=2)
        print(f"{GRN}[Schema Translator] system_schema.json 已生成: {SCHEMA_OUTPUT} ({len(json.dumps(schema_data))} 字符){RESET}")
    except Exception:
        loud_fail(f"写入失败: {SCHEMA_OUTPUT}")

    print("[Schema Translator] 翻译完成，等待 Router 审批流转。")


if __name__ == "__main__":
    main()
