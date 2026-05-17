"""
Numerical Planner (数值策划 / 经济模型设计师)
职责：读取系统 Schema + 概念简案 → 输出单 JSON（docs+data）→ 物理拆分落盘 → 推动流水线
单 JSON 设计：根对象含 docs 和 data 两个顶级 Key，代码端自动拆分保存
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
WORKSPACE_DIR    = os.path.join(ROOT_DIR, ".agent_workspace")
CONCEPT_FILE     = os.path.join(WORKSPACE_DIR, "concept_brief.md")
SCHEMA_SYS_FILE  = os.path.join(WORKSPACE_DIR, "system_schema.json")
DOCS_OUTPUT_FILE = os.path.join(WORKSPACE_DIR, "system_numerical_docs.json")
DATA_OUTPUT_FILE = os.path.join(WORKSPACE_DIR, "system_numerical_data.json")
RESULT_FILE      = os.path.join(WORKSPACE_DIR, "current_result.json")
STATUS_FILE      = os.path.join(WORKSPACE_DIR, "task_status.json")

RED   = "\033[91m"
GRN   = "\033[92m"
RESET = "\033[0m"


def loud_fail(msg: str):
    print(f"{RED}========== [Numerical Planner] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}=================================================={RESET}")
    sys.exit(1)


def main():
    # ========== 1. 读取双重上下文 ==========
    try:
        if not os.path.exists(CONCEPT_FILE):
            loud_fail(f"概念简案文件不存在: {CONCEPT_FILE}")

        with open(CONCEPT_FILE, "r", encoding="utf-8") as f:
            concept_text = f.read().strip()

        if not concept_text:
            loud_fail("概念简案内容为空")

        print(f"[Numerical Planner] 已读取概念简案 ({len(concept_text)} 字符)")

    except Exception:
        loud_fail(f"读取概念简案失败: {CONCEPT_FILE}")

    try:
        if not os.path.exists(SCHEMA_SYS_FILE):
            loud_fail(f"系统 Schema 文件不存在: {SCHEMA_SYS_FILE}")

        with open(SCHEMA_SYS_FILE, "r", encoding="utf-8") as f:
            schema_data = json.load(f)

        print(f"[Numerical Planner] 已读取系统 Schema ({len(json.dumps(schema_data))} 字符)")

    except json.JSONDecodeError:
        loud_fail(f"系统 Schema JSON 解析失败: {SCHEMA_SYS_FILE}")
    except Exception:
        loud_fail(f"读取系统 Schema 失败: {SCHEMA_SYS_FILE}")

    schema_json_str = json.dumps(schema_data, ensure_ascii=False, indent=2)

    # ========== 2. 构建 System Prompt（单 JSON：docs + data） ==========
    system_prompt = """你是一位主导工业级游戏数据流的顶级数值架构师。

## 你必须且只能输出【一个】完整的 JSON 对象

该对象必须包含 docs 和 data 两个顶级 Key。

## docs 区块规范（极其详尽的数据字典）

作为顶级数值架构师，你输出的 docs 区块必须是一份极其详尽的数据字典（Data Dictionary），必须能让任何人类程序员或 AI 代理一眼看懂。
docs 必须包含以下四个子模块，且必须用中文进行详细备注：

### 1. system_summary（字符串）
一句话概括该系统的核心经济循环或养成目的。示例：
"公会贡献度系统：用于控制玩家每日通过行为获取公会积分的上限与速率。"

### 2. field_dictionary（对象）★ 最重要的部分
穷举 data 表中出现的每一个核心字段。格式必须为：
"字段名": "【数据类型】详细的业务作用说明、取值范围、以及默认值（如果有）。"
示例：
{
  "daily_max_contribution_base": "【整型 Int】1级公会的每日最大贡献度基础值。不得低于0。",
  "growth_type": "【字符串 String】成长曲线类型。如 'linear' 表示线性递增，代码计算时使用 base + level * growth_coef。"
}

### 3. relations_and_enums（对象）
详细说明跨表外键调用关系，以及状态码枚举。示例：
{
  "prerequisite_node_id": "外键 → tech_node_config.node_id。标识解锁本节点的前置节点。",
  "contribution_type": "枚举值：1=金币捐献，2=钻石捐献，3=活跃任务"
}

### 4. implementation_notes（字符串）
给下游主程序或 UI 策划的执行建议。示例：
"建议程序在每日凌晨 4 点重置该积分的累计进度。公式建议：daily_max = base + guild_level * growth。"

## data 区块规范（绝对纯净）

data 块继续保持绝对的纯净，不包含任何中文解释字段。使用 continuous_formulas + discrete_milestones 模式。

## 完整 JSON 输出模板

{
  "docs": {
    "system_summary": "公会贡献度系统：用于控制玩家每日通过行为获取公会积分的上限与速率。",
    "field_dictionary": {
      "daily_max_contribution_base": "【整型 Int】1级公会的每日最大贡献度基础值。不得低于0。",
      "growth_type": "【字符串 String】成长曲线类型。如 'linear' 表示线性递增。"
    },
    "relations_and_enums": {
      "contribution_type": "枚举值：1=金币捐献，2=钻石捐献，3=活跃任务"
    },
    "implementation_notes": "建议程序在每日凌晨 4 点重置该积分的累计进度。"
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

## ⚠️【致命红线（FATAL ERROR）】

绝对禁止在 data 中使用 levels 数组枚举具体等级！必须使用公式与里程碑！

## 转换规范
1. continuous_fields → 转化为 continuous_formulas 中的公式和系数（base + growth + type）
2. discrete_fields → 转化为 discrete_milestones 中以特定等级为 Key 的字典记录
3. growth type 仅限: "linear", "exponential", "logarithmic"

## 铁律
1. 只输出一个 JSON 对象，含 docs 和 data 两个顶级 Key，缺一不可
2. docs 必须包含 system_summary / field_dictionary / relations_and_enums / implementation_notes 四个子模块，缺一不可
3. field_dictionary 必须穷举 data 中出现的每一个字段，格式为 "字段名": "【类型】业务说明"
4. data 中放纯净数值配置（无注释、无说明、可直接反序列化为 Excel）
5. 【致命红线】：data 中禁止任何 [{"level":1}, {"level":2}...] 枚举数组！违者系统崩溃！
6. 连续成长用 continuous_formulas，离散触发用 discrete_milestones
7. 禁止任何日期/时间戳字段
8. 禁止在 JSON 之外输出任何解释性文字"""

    user_prompt = f"""以下是老板的概念简案：

---
{concept_text}
---

以下是系统架构师定义的核心数据模块（JSON）：

```json
{schema_json_str}
```

请输出一个完整的 JSON 对象，包含 docs（说明书）和 data（数值配置）两个顶级 Key。
docs 必须包含 system_summary / field_dictionary / relations_and_enums / implementation_notes 四个子模块。
data 中必须用 continuous_formulas + discrete_milestones 模式，禁止 levels 枚举数组。
直接输出 JSON，不要加任何 Markdown 标记或解释。"""

    # ========== 3. 调用大模型 ==========
    print("[Numerical Planner] 正在呼叫大模型设计数值配置...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt)
    except Exception:
        loud_fail("大模型调用失败（网络超时 / API Key 无效 / 服务不可用）")

    print("=" * 60)
    print("【大模型原始返回】:")
    print(llm_response)
    print("=" * 60)
    print(f"[Numerical Planner] 大模型返回完成 ({len(llm_response)} 字符)")

    # ========== 4. 正则精准提取 JSON ==========
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", llm_response, re.DOTALL)

    if json_match:
        clean_json_str = json_match.group(1).strip()
        print(f"[Numerical Planner] 正则成功提取 JSON ({len(clean_json_str)} 字符)")
    else:
        clean_json_str = llm_response.strip()
        print("[Numerical Planner] 未找到代码块标记，使用原始返回值")

    try:
        parsed = json.loads(clean_json_str)
    except json.JSONDecodeError:
        loud_fail(f"JSON 解析失败！完整原始返回:\n{llm_response}")

    if not isinstance(parsed, dict):
        loud_fail(f"根 JSON 必须是对象类型，实际为: {type(parsed).__name__}")

    # ========== 5. 精准提取 docs 和 data ==========
    docs_content = parsed.get("docs", {})
    data_content = parsed.get("data", {})

    if not docs_content and "docs" not in parsed:
        loud_fail('根 JSON 缺失顶级 Key: "docs"')
    if not data_content and "data" not in parsed:
        loud_fail('根 JSON 缺失顶级 Key: "data"')

    if not isinstance(data_content, dict):
        loud_fail(f'data 必须是对象类型，实际为: {type(data_content).__name__}')

    print(f"{GRN}[Numerical Planner] 单 JSON 解析成功：docs + data 均已就绪{RESET}")

    # ========== 6. 物理拆分落盘 ==========
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)

        with open(DOCS_OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(docs_content, f, ensure_ascii=False, indent=2)
        print(f"{GRN}[Numerical Planner] 说明书已保存: {DOCS_OUTPUT_FILE}{RESET}")

        with open(DATA_OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data_content, f, ensure_ascii=False, indent=2)
        print(f"{GRN}[Numerical Planner] 纯净数值数据已保存: {DATA_OUTPUT_FILE}{RESET}")

    except Exception:
        loud_fail(f"写入产出文件失败")

    # ========== 7. 按宪法格式封装并落盘 current_result.json ==========
    try:
        result = {
            "source_agent": "numerical_planner",
            "task_id": "task_001",
            "payload": {
                "docs": docs_content,
                "data": data_content,
            },
        }
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[Numerical Planner] 封装结果已保存: {RESULT_FILE}")
    except Exception:
        loud_fail(f"写入封装结果失败: {RESULT_FILE}")

    # ========== 8. 推动流水线 → completed ==========
    try:
        if not os.path.exists(STATUS_FILE):
            loud_fail(f"任务状态文件不存在: {STATUS_FILE}")

        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status_data = json.load(f)

        current_state = status_data.get("current_state", "")
        status_data["current_state"] = "completed"

        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)

        print(f"[Numerical Planner] 任务状态已更新: {current_state} -> completed")
        print("[Numerical Planner] 数值策划工作完成，流水线终点。")

    except Exception:
        loud_fail(f"更新任务状态失败: {STATUS_FILE}")


if __name__ == "__main__":
    main()
