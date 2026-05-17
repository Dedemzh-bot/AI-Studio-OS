"""
Numerical Agent (数值架构师)
职责：读取概念简案 + Schema → 输出单 JSON（docs+data）→ 物理拆分落盘 → 推动流水线
单 JSON 设计：根对象含 docs 和 data 两个顶级 Key，代码端自动拆分保存
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
DOCS_OUTPUT_FILE = os.path.join(WORKSPACE_DIR, "system_numerical_docs.json")
DATA_OUTPUT_FILE = os.path.join(WORKSPACE_DIR, "system_numerical_data.json")
RESULT_FILE = os.path.join(WORKSPACE_DIR, "current_result.json")
STATUS_FILE = os.path.join(WORKSPACE_DIR, "task_status.json")


def print_error(msg: str):
    """打印红色错误信息（ANSI 转义码）"""
    print(f"\033[91m[NumericalAgent][错误] {msg}\033[0m")


def main():
    # ========== 1. 读取双重上下文 ==========
    if not os.path.exists(CONCEPT_FILE):
        print_error(f"概念简案文件不存在: {CONCEPT_FILE}")
        sys.exit(1)

    with open(CONCEPT_FILE, "r", encoding="utf-8") as f:
        concept_text = f.read().strip()

    if not concept_text:
        print_error("概念简案内容为空，无法继续")
        sys.exit(1)

    print(f"[NumericalAgent] 已读取概念简案 ({len(concept_text)} 字符)")

    if not os.path.exists(SCHEMA_FILE):
        print_error(f"Schema 文件不存在: {SCHEMA_FILE}")
        sys.exit(1)

    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema_text = f.read().strip()

    print(f"[NumericalAgent] 已读取 JSON Schema ({len(schema_text)} 字符)")

    # ========== 2. 构建 System Prompt（单 JSON：docs + data） ==========
    system_prompt = """你是一位主导工业级游戏数据流的顶级数值架构师。

## 你必须且只能输出【一个】完整的 JSON 对象

该对象必须包含 docs 和 data 两个顶级 Key：

```json
{
  "docs": {
    "foreign_keys": {"描述": "跨表说明..."},
    "rules": {"描述": "业务规则..."}
  },
  "data": {
    "guild_contribution": {
      "continuous_formulas": {
        "daily_max_contribution": {"base": 500, "growth": 50, "type": "linear"}
      },
      "discrete_milestones": {}
    }
  }
}
```

## ⚠️【致命红线（FATAL ERROR）】

绝对禁止在 data 中使用 levels 数组枚举具体等级！必须使用公式与里程碑！

## 转换规范
读取上游 schema 中的 continuous_fields（连续成长字段）和 discrete_fields（离散解锁字段）：
1. continuous_fields → 转化为 continuous_formulas 中的公式和系数（base + growth + type）
2. discrete_fields → 转化为 discrete_milestones 中以特定等级为 Key 的字典记录
3. growth type 仅限: "linear", "exponential", "logarithmic"

## 铁律
1. 只输出一个 JSON 对象，含 docs 和 data 两个顶级 Key，缺一不可
2. docs 中放规则说明书（外键引用、业务规则、公式备注）
3. data 中放纯净数值配置（无注释、无说明、可直接反序列化为 Excel）
4. 【致命红线】：data 中禁止任何 [{"level":1}, {"level":2}...] 枚举数组！违者系统崩溃！
5. 连续成长用 continuous_formulas，离散触发用 discrete_milestones
6. 禁止任何日期/时间戳字段
7. 禁止在 JSON 之外输出任何解释性文字
8. 输出体积必须紧凑，确保不触发 LLM Token 上限"""

    user_prompt = f"""以下是老板的概念简案：

---
{concept_text}
---

以下是必须严格遵守的 JSON Schema 契约：

---
{schema_text}
---

请输出一个完整的 JSON 对象，包含 docs（说明书）和 data（数值配置）两个顶级 Key。
data 中必须用 continuous_formulas + discrete_milestones 模式，禁止 levels 枚举数组。
直接输出 JSON，不要加任何 Markdown 标记或解释。"""

    # ========== 3. 调用大模型 ==========
    print("[NumericalAgent] 正在调用大模型生成单 JSON（docs+data）...")
    try:
        response = ask_llm(system_prompt, user_prompt)
    except Exception as e:
        print_error(f"大模型调用失败: {e}")
        sys.exit(1)

    print(f"[NumericalAgent] 大模型返回完成 ({len(response)} 字符)")

    # ========== 4. 提取唯一 JSON ==========
    json_str = response.strip()

    # 如果被 ```json ... ``` 包裹，提取内容
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", json_str, re.DOTALL)
    if code_block_match:
        json_str = code_block_match.group(1).strip()

    # 严格解析为 Python 字典
    try:
        parsed_json = json.loads(json_str)
    except json.JSONDecodeError as e:
        print_error(f"JSON 解析失败: {e}")
        print(f"[NumericalAgent] 原始内容片段（前 500 字符）:\n{json_str[:500]}")
        sys.exit(1)

    if not isinstance(parsed_json, dict):
        print_error(f"根 JSON 必须是对象类型，实际为: {type(parsed_json).__name__}")
        sys.exit(1)

    # ========== 5. 精准提取 docs 和 data ==========
    docs_content = parsed_json.get("docs", {})
    data_content = parsed_json.get("data", {})

    if not docs_content and "docs" not in parsed_json:
        print_error('根 JSON 缺失顶级 Key: "docs"，且默认值为空')
        sys.exit(1)
    if not data_content and "data" not in parsed_json:
        print_error('根 JSON 缺失顶级 Key: "data"，且默认值为空')
        sys.exit(1)

    if not isinstance(data_content, dict):
        print_error(f'data 必须是对象类型，实际为: {type(data_content).__name__}')
        sys.exit(1)

    print("[NumericalAgent] 单 JSON 解析成功：docs + data 均已就绪")

    # ========== 6. 物理拆分落盘 ==========
    os.makedirs(WORKSPACE_DIR, exist_ok=True)

    with open(DOCS_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(docs_content, f, ensure_ascii=False, indent=2)
    print(f"[NumericalAgent] 说明书已保存至: {DOCS_OUTPUT_FILE}")

    with open(DATA_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data_content, f, ensure_ascii=False, indent=2)
    print(f"[NumericalAgent] 纯净数值数据已保存至: {DATA_OUTPUT_FILE}")

    # ========== 7. 按宪法格式封装并落盘 current_result.json ==========
    result = {
        "source_agent": "numerical_agent",
        "task_id": "task_001",
        "payload": {
            "docs": docs_content,
            "data": data_content,
        },
    }
    with open(RESULT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"[NumericalAgent] 封装结果已保存至: {RESULT_FILE}")

    # ========== 8. 推动流水线 ==========
    if not os.path.exists(STATUS_FILE):
        print_error(f"任务状态文件不存在: {STATUS_FILE}")
        sys.exit(1)

    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        status_data = json.load(f)

    current_state = status_data.get("current_state", "")
    status_data["current_state"] = "pending_validation"
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)
    print(f"[NumericalAgent] 任务状态已更新: {current_state} -> pending_validation")
    print("[NumericalAgent] 数值架构师工作完成，流水线已推进至校验阶段。")


if __name__ == "__main__":
    main()
