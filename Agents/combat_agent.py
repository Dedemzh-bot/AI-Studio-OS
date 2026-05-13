"""
Combat Agent (战斗数值执行策划)
职责：读取概念简案 + 当前 Schema → 生成符合契约的战斗数值 JSON → 推动流水线至校验阶段
"""

import json
import os
import re
import sys

# 将项目根目录加入 sys.path，确保能导入 Skills 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Skills.llm_client import ask_llm

# ---- 路径配置（全部使用绝对路径） ----
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
CONCEPT_FILE = os.path.join(WORKSPACE_DIR, "concept_brief.md")
SCHEMA_FILE = os.path.join(WORKSPACE_DIR, "active_schema.json")
RESULT_FILE = os.path.join(WORKSPACE_DIR, "current_result.json")
STATUS_FILE = os.path.join(WORKSPACE_DIR, "task_status.json")


def print_error(msg: str):
    """打印红色错误信息（ANSI 转义码）"""
    print(f"\033[91m[CombatAgent][错误] {msg}\033[0m")


def main():
    # ========== 1. 读取双重上下文 ==========
    # 读取老板原始需求
    if not os.path.exists(CONCEPT_FILE):
        print_error(f"概念简案文件不存在: {CONCEPT_FILE}")
        sys.exit(1)

    with open(CONCEPT_FILE, "r", encoding="utf-8") as f:
        concept_text = f.read().strip()

    if not concept_text:
        print_error("概念简案内容为空，无法继续")
        sys.exit(1)

    print(f"[CombatAgent] 已读取概念简案 ({len(concept_text)} 字符)")

    # 读取当前生效的 JSON Schema 契约
    if not os.path.exists(SCHEMA_FILE):
        print_error(f"Schema 文件不存在: {SCHEMA_FILE}")
        sys.exit(1)

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_text = f.read().strip()

    print(f"[CombatAgent] 已读取 JSON Schema ({len(schema_text)} 字符)")

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

    # ========== 3. 调用大模型 ==========
    print("[CombatAgent] 正在调用大模型生成战斗数值...")
    try:
        response = ask_llm(system_prompt, user_prompt)
    except Exception as e:
        print_error(f"大模型调用失败: {e}")
        sys.exit(1)

    print(f"[CombatAgent] 大模型返回完成 ({len(response)} 字符)")

    # ========== 4. 解析与清理 ==========
    # 清理首尾空白
    json_str = response.strip()

    # 移除可能包裹的 ```json ... ``` 代码块标记
    code_block_match = re.search(r"```(?:json)?\s*(.*?)\s*```", json_str, re.DOTALL)
    if code_block_match:
        json_str = code_block_match.group(1).strip()

    # 验证 JSON 合法性
    try:
        data_obj = json.loads(json_str)
    except json.JSONDecodeError as e:
        print_error(f"大模型返回的 JSON 不合法: {e}")
        print(f"[CombatAgent] 原始内容片段（前 500 字符）:\n{json_str[:500]}")
        sys.exit(1)

    if not isinstance(data_obj, dict):
        print_error(f"大模型返回的 JSON 必须是对象类型，实际为: {type(data_obj).__name__}")
        sys.exit(1)

    # ========== 5. 按宪法格式封装并落盘 ==========
    result = {
        "source_agent": "combat_agent",
        "task_id": "task_001",
        "payload": data_obj,
    }

    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[CombatAgent] 战斗数值数据已保存至: {RESULT_FILE}")

    # ========== 6. 推动流水线 → pending_validation ==========
    if not os.path.exists(STATUS_FILE):
        print_error(f"任务状态文件不存在: {STATUS_FILE}")
        sys.exit(1)

    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        status_data = json.load(f)

    current_state = status_data.get("current_state", "")
    status_data["current_state"] = "pending_validation"
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)
    print(f"[CombatAgent] 任务状态已更新: {current_state} -> pending_validation")
    print("[CombatAgent] 战斗数值策划工作完成，流水线已推进至校验阶段。")


if __name__ == "__main__":
    main()
