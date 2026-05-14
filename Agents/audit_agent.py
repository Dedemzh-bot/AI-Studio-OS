"""
Audit Agent (逻辑审查官 / 数值平衡主编)
职责：读取已通过语法安检的技能数据，审查数值平衡性，输出通过/驳回判定。
输出：audit_feedback.json
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

# ---- 所有读写目标均拼装为绝对路径 ----
WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
RESULT_FILE   = os.path.join(WORKSPACE_DIR, "current_result.json")
OUTPUT_FILE   = os.path.join(WORKSPACE_DIR, "audit_feedback.json")
STATUS_FILE   = os.path.join(WORKSPACE_DIR, "task_status.json")
KNOWLEDGE_DIR = os.path.join(ROOT_DIR, "Knowledge")

RED   = "\033[91m"
GRN   = "\033[92m"
RESET = "\033[0m"


def loud_fail(msg: str):
    """大声打印红色错误 + 完整 Traceback，然后 sys.exit(1) 通知 Router"""
    print(f"{RED}========== [Audit Agent] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}==========================================={RESET}")
    sys.exit(1)


def load_knowledge() -> str:
    """加载 Knowledge/*.md 中的全局设计规范，作为审查依据"""
    import glob
    context = ""
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)
    md_files = glob.glob(os.path.join(KNOWLEDGE_DIR, "*.md"))
    if md_files:
        for md_file in sorted(md_files):
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    context += f"\n--- {os.path.basename(md_file)} ---\n{content}\n"
            except Exception:
                pass
    return context


def main():
    # ========== 1. 读取已通过语法安检的数据 ==========
    try:
        if not os.path.exists(RESULT_FILE):
            loud_fail(f"待审查数据文件不存在: {RESULT_FILE}")

        with open(RESULT_FILE, "r", encoding="utf-8") as f:
            pristine_data = json.load(f)

        print(f"[Audit Agent] 已读取待审查数据")
        print(f"[Audit Agent] 文件路径: {RESULT_FILE}")
        print(f"[Audit Agent] 来源 Agent: {pristine_data.get('source_agent', 'unknown')}")

    except json.JSONDecodeError:
        loud_fail(f"待审查数据 JSON 解析失败: {RESULT_FILE}")
    except Exception:
        loud_fail(f"读取待审查数据失败: {RESULT_FILE}")

    payload = pristine_data.get("payload")
    if payload is None:
        loud_fail("待审查数据中缺少 payload 字段，无法审查")

    payload_json_str = json.dumps(payload, ensure_ascii=False, indent=2)

    # ========== 1.5 加载知识库作为审查依据 ==========
    knowledge_context = load_knowledge()
    if knowledge_context:
        print(f"[Audit Agent] 已加载知识库设计规范作为审查依据")

    # ========== 2. 构建数值平衡主编人设提示词 ==========
    system_prompt = """你是一位极其严苛的游戏数值平衡主编。请审查传入的技能数据。

审查要点：
1. 数值比例：伤害与冷却时间、消耗之间的关系是否合理
2. 极端数值：是否有破坏游戏平衡的超高或超低数值
3. 叠加机制：Buff/DeBuff 的叠加上限与增伤比例是否过度
4. 范围与持续时间：是否可能造成不可控的连锁反应
5. 如加载了知识库规范，必须以其为绝对审查标准

你必须输出纯 JSON 格式，包含以下字段：
- is_pass: 布尔值 true（通过）或 false（不通过）
- critique: 字符串，如果不通过给出具体的修改建议；如果通过写"合理，准许通过"

最高指令：
1. 禁止废话，禁止解释，禁止问候语
2. 只输出合法的纯 JSON，不要加 Markdown 标记"""

    # RAG 注入
    if knowledge_context:
        system_prompt += f"\n\n【全局设计规范（以此为绝对审查标准）】:\n{knowledge_context}"

    user_prompt = f"""以下是待审查的游戏技能数据（JSON 格式）：

```json
{payload_json_str}
```

请审查以上数据的数值平衡性，输出审查结果 JSON。"""

    # ========== 3. 调用大模型 ==========
    print("[Audit Agent] 正在呼叫大模型审查数值平衡性...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt)
    except Exception:
        loud_fail("大模型调用失败（网络超时 / API Key 无效 / 服务不可用）")

    print("=" * 60)
    print("【大模型原始返回】:")
    print(llm_response)
    print("=" * 60)
    print(f"[Audit Agent] 大模型返回完成 ({len(llm_response)} 字符)")

    # ========== 4. 正则精准提取 JSON ==========
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", llm_response, re.DOTALL)

    if json_match:
        clean_json_str = json_match.group(1).strip()
        print(f"[Audit Agent] 正则成功提取 JSON ({len(clean_json_str)} 字符)")
    else:
        clean_json_str = llm_response.strip()
        print("[Audit Agent] 未找到代码块标记，使用原始返回值")

    # 验证 JSON 合法性
    try:
        audit_data = json.loads(clean_json_str)
    except json.JSONDecodeError:
        loud_fail(f"大模型返回的不是合法 JSON！完整原始返回:\n{llm_response}")

    # ========== 5. 保存审查结果 ==========
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(audit_data, f, ensure_ascii=False, indent=2)
        print(f"[Audit Agent] 审查结果已保存至: {OUTPUT_FILE}")

        is_pass = audit_data.get("is_pass", False)
        critique = audit_data.get("critique", "(缺失)")

        if is_pass:
            print(f"{GRN}[Audit Agent] [审查通过] {critique}{RESET}")
        else:
            print(f"{RED}[Audit Agent] [审查驳回] {critique}{RESET}")

    except Exception:
        loud_fail(f"写入审查结果失败: {OUTPUT_FILE}")

    # ========== 6. 推动流水线 ==========
    try:
        if not os.path.exists(STATUS_FILE):
            loud_fail(f"任务状态文件不存在: {STATUS_FILE}")

        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status_data = json.load(f)

        current_state = status_data.get("current_state", "")
        status_data["current_state"] = "audited"

        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)

        print(f"[Audit Agent] 任务状态已更新: {current_state} -> audited")
        print("[Audit Agent] 数值审查工作完成。")

    except Exception:
        loud_fail(f"更新任务状态失败: {STATUS_FILE}")


if __name__ == "__main__":
    main()
