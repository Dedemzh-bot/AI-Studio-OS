"""
Numerical Planner (数值策划 / 经济模型设计师)
职责：读取系统 Schema + 概念简案，设计数值成长表（升级曲线、货币消耗、属性收益等）。
产出：system_numerical_data.json
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
OUTPUT_FILE      = os.path.join(WORKSPACE_DIR, "system_numerical_data.json")
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
    # 1a. 读取概念简案
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

    # 1b. 读取系统 Schema
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

    # ========== 2. 构建数值策划人设提示词 ==========
    system_prompt = """你是一位精通 Excel 和经济模型的游戏数值策划。

请根据传入的系统模块结构，为其设计具体的数值成长表。

设计要求：
1. 每个模块的每个等级/节点都需要填充具体数值
2. 升级消耗曲线应遵循合理的数学模型（如指数增长 rate=1.5、斐波那契、二次曲线等）
3. 属性收益随等级递增，边际效益可逐步递减
4. 数值必须在合理区间内，不能出现天文数字
5. 如果涉及货币消耗，优先设计为整数

必须输出纯 JSON 数组格式。数组中每个元素代表一个模块的数值矩阵。
格式示例：
[
  {
    "module": "模块名称",
    "levels": [
      {"level": 1, "cost": 100, "effect_value": 10},
      {"level": 2, "cost": 150, "effect_value": 21},
      ...
    ]
  }
]

最高指令：
1. 禁止废话，禁止解释，禁止问候语
2. 只输出合法的纯 JSON 数组
3. 数值必须具体到每个等级，不能留空"""

    user_prompt = f"""以下是老板的概念简案：

---
{concept_text}
---

以下是系统架构师定义的核心数据模块（JSON）：

```json
{schema_json_str}
```

请为以上系统模块设计一套完整的数值成长矩阵。直接输出 JSON 数组。"""

    # ========== 3. 调用大模型 ==========
    print("[Numerical Planner] 正在呼叫大模型设计数值成长表...")
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
        numerical_data = json.loads(clean_json_str)
    except json.JSONDecodeError:
        loud_fail(f"大模型返回的不是合法 JSON！完整原始返回:\n{llm_response}")

    if not isinstance(numerical_data, list):
        loud_fail(f"数值数据必须是 JSON 数组，实际为: {type(numerical_data).__name__}")

    # ========== 5. 保存数值数据 ==========
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(numerical_data, f, ensure_ascii=False, indent=2)
        print(f"{GRN}[Numerical Planner] 数值成长表已保存: {OUTPUT_FILE}{RESET}")
        print(f"[Numerical Planner] 共 {len(numerical_data)} 个模块")

        # 摘要打印
        for mod in numerical_data:
            mod_name = mod.get("module", "未知模块")
            levels = len(mod.get("levels", mod.get("nodes", [])))
            print(f"[Numerical Planner]   {mod_name}: {levels} 个等级/节点")

    except Exception:
        loud_fail(f"写入数值数据失败: {OUTPUT_FILE}")

    # ========== 6. 推动流水线 → completed ==========
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
