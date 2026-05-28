"""
Combat Agent (战斗数值执行策划)
职责：读取概念简案 + 当前 Schema → 生成符合契约的战斗数值 JSON → 推动流水线至校验阶段
"""

import json
import os
import re
import sys
import traceback

# ---- 强制绝对路径：基于本文件位置推算项目根目录 ----
FILE_DIR = os.path.dirname(os.path.abspath(__file__))       # Agents/
ROOT_DIR = os.path.dirname(FILE_DIR)                         # 项目根目录
sys.path.insert(0, ROOT_DIR)

from Skills.llm_client import ask_llm
from Skills.rag_loader import load_knowledge_with_context

# ---- 所有读写目标均拼装为绝对路径 ----
WORKSPACE_DIR = os.path.join(os.environ.get("AI_STUDIO_DATA_DIR", ROOT_DIR), ".agent_workspace")
CONCEPT_FILE  = os.path.join(WORKSPACE_DIR, "concept_brief.md")
SCHEMA_FILE   = os.path.join(WORKSPACE_DIR, "active_schema.json")
RESULT_FILE   = os.path.join(WORKSPACE_DIR, "current_result.json")
STATUS_FILE   = os.path.join(WORKSPACE_DIR, "task_status.json")
AUDIT_FILE    = os.path.join(WORKSPACE_DIR, "audit_feedback.json")

RED   = "\033[91m"
RESET = "\033[0m"


def loud_fail(msg: str):
    """大声打印红色错误 + 完整 Traceback，然后 sys.exit(1) 通知 Router"""
    print(f"{RED}========== [Combat Agent] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}============================================{RESET}")
    sys.exit(1)


def main():
    # ========== 1. 读取双重上下文 ==========
    # 1a. 读取概念简案
    try:
        if not os.path.exists(CONCEPT_FILE):
            loud_fail(f"概念简案文件不存在: {CONCEPT_FILE}")

        with open(CONCEPT_FILE, "r", encoding="utf-8") as f:
            concept_text = f.read().strip()

        if not concept_text:
            loud_fail("概念简案内容为空，无法继续")

        print(f"[Combat Agent] 已读取概念简案 ({len(concept_text)} 字符)")
        print(f"[Combat Agent] 文件路径: {CONCEPT_FILE}")

    except Exception:
        loud_fail(f"读取概念简案失败: {CONCEPT_FILE}")

    # 1b. 读取当前生效的 JSON Schema 契约
    try:
        if not os.path.exists(SCHEMA_FILE):
            loud_fail(f"Schema 文件不存在: {SCHEMA_FILE}")

        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            schema_text = f.read().strip()

        print(f"[Combat Agent] 已读取 JSON Schema ({len(schema_text)} 字符)")
        print(f"[Combat Agent] 文件路径: {SCHEMA_FILE}")

    except Exception:
        loud_fail(f"读取 JSON Schema 失败: {SCHEMA_FILE}")

    # ========== 2. 构建极严提示词 ==========
    system_prompt = """你是一个严谨的战斗数值执行策划。你需要为概念简案设计具体的数值。

最高指令：
1. 输出必须是合法的、纯粹的 JSON 格式数据，不得包含任何 Markdown 标记或解释性文字
2. 绝对严格遵循提供的 JSON Schema 契约，字段名、类型、结构一个都不能错
3. 禁止添加 Schema 中未定义的额外字段
4. 禁止缺失任何必填（required）字段
5. 数值设计必须合理：伤害值应在游戏平衡范围内，冰冻持续时间应符合实际游戏体验
6. 务必填充因果追踪链数据，确保触发来源标签完整，防范地图边缘无限刷怪漏洞

你是数据产出机器，不是聊天机器人。请直接输出 JSON，不要有任何前缀或后缀。"""

    user_prompt = f"""以下是老板的概念简案：

---
{concept_text}
---

以下是必须严格遵守的 JSON Schema 契约：

---
{schema_text}
---

请根据以上需求，生成一份完全符合 Schema 契约的 JSON 战斗数值数据。直接输出 JSON，不要加 ```json 标记。"""

    # ========== 2.5. 检查主编打回意见 ==========
    if os.path.exists(AUDIT_FILE):
        try:
            with open(AUDIT_FILE, "r", encoding="utf-8") as f:
                audit_data = json.load(f)
            is_pass = audit_data.get("is_pass", True)
            critique = audit_data.get("critique", "")

            if not is_pass and critique:
                print(f"{RED}[Combat Agent] 检测到主编打回意见！{RESET}")
                print(f"{RED}[Combat Agent] 驳回原因: {critique}{RESET}")

                rejection_clause = (
                    "\n\n"
                    f"【主编打回意见】：你上一次生成的数值被驳回了，原因是：{critique}\n"
                    "请你务必根据这个意见重新调整数值！不得生成与上一次相同的数据。"
                )
                user_prompt += rejection_clause
            else:
                print("[Combat Agent] 主编审查反馈: 已通过，无需修正。")

        except (json.JSONDecodeError, KeyError) as e:
            print(f"[Combat Agent][警告] 无法解析审查反馈文件: {e}")
    else:
        print("[Combat Agent] 未发现审查反馈文件，按正常流程生成。")

    # ========== 3. 注入 RAG 知识上下文 ==========
    rag_context = load_knowledge_with_context(ROOT_DIR, task_domain="数值架构")
    if rag_context:
        user_prompt += f"\n\n{rag_context}"
        print(f"[Combat Agent] 已注入 RAG 上下文 ({len(rag_context)} 字符)")

    # ========== 4. 调用大模型 ==========
    print("[Combat Agent] 正在呼叫大模型...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt)
    except Exception:
        loud_fail("大模型调用失败（网络超时 / API Key 无效 / 服务不可用）")

    # 不管返回什么，先强制打印原始返回值
    print("=" * 60)
    print("【大模型原始返回】:")
    print(llm_response)
    print("=" * 60)
    print(f"[Combat Agent] 大模型返回完成 ({len(llm_response)} 字符)")

    # ========== 4. 解析与清理（极其强壮） ==========
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", llm_response, re.DOTALL)

    if json_match:
        clean_json_str = json_match.group(1).strip()
    else:
        clean_json_str = llm_response.strip()

    try:
        data_obj = json.loads(clean_json_str)
    except json.JSONDecodeError:
        loud_fail(f"大模型返回的不是合法 JSON！完整原始返回:\n{llm_response}")

    # ========== 5. 按宪法格式封装并落盘 ==========
    result = {
        "source_agent": "combat_agent",
        "task_id": "task_001",
        "payload": data_obj,
    }

    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[Combat Agent] 战斗数据生成并解析成功，已落盘至: {RESULT_FILE}")
    except Exception:
        loud_fail(f"写入 current_result.json 失败: {RESULT_FILE}")

    # ========== 6. 推动流水线 → pending_validation ==========
    try:
        if not os.path.exists(STATUS_FILE):
            loud_fail(f"任务状态文件不存在: {STATUS_FILE}")

        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status_data = json.load(f)

        current_state = status_data.get("current_state", "")
        status_data["current_state"] = "pending_validation"

        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)

        print(f"[Combat Agent] 任务状态已更新: {current_state} -> pending_validation")
        print("[Combat Agent] 战斗数值策划工作完成，流水线已推进至校验阶段。")

    except Exception:
        loud_fail(f"更新任务状态失败: {STATUS_FILE}")


if __name__ == "__main__":
    main()
