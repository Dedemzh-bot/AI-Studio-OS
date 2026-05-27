"""
System Planner (系统策划执行者)
职责：读取主策草案 + PM 排期 + 原始简案 → 极其详尽地扩写 → system_design_detail.md
绝不越权替主策做方向决策，不替 PM 分派下游任务，只负责把玩法规则讲透。
"""

import json
import os
import sys
import traceback

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(FILE_DIR)
sys.path.insert(0, ROOT_DIR)

from Skills.llm_client import ask_llm

WORKSPACE_DIR   = os.path.join(ROOT_DIR, ".agent_workspace")
CONCEPT_FILE    = os.path.join(WORKSPACE_DIR, "concept_brief.md")
DRAFT_FILE      = os.path.join(WORKSPACE_DIR, "system_design_draft.md")
PLAN_FILE       = os.path.join(WORKSPACE_DIR, "task_plan.md")
CODEX_FILE      = os.path.join(WORKSPACE_DIR, "project_codex.md")
REGISTRY_FILE   = os.path.join(ROOT_DIR, "Knowledge", "global_asset_registry.json")
DETAIL_OUTPUT   = os.path.join(WORKSPACE_DIR, "system_design_detail.md")
FEEDBACK_FILE   = os.path.join(WORKSPACE_DIR, "boss_feedback.txt")
STATUS_FILE     = os.path.join(WORKSPACE_DIR, "task_status.json")
FIX_FILE        = os.path.join(WORKSPACE_DIR, ".fix_correction.json")
PROMPT_FILE     = os.path.join(ROOT_DIR, "Agents", "prompts", "system_planner_prompt.md")

RED   = "\033[91m"
GRN   = "\033[92m"
RESET = "\033[0m"


def loud_fail(msg: str):
    print(f"{RED}========== [System Planner] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}=============================================={RESET}")
    sys.exit(1)


def load_file(path: str) -> str:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return ""


def main():
    # ========== 1. 强制读取三个上下文文件 ==========
    concept = load_file(CONCEPT_FILE)
    draft = load_file(DRAFT_FILE)
    plan = load_file(PLAN_FILE)
    feedback = load_file(FEEDBACK_FILE)

    if not concept:
        loud_fail(f"概念简案为空: {CONCEPT_FILE}")
    if not draft:
        loud_fail(f"主策草案不存在: {DRAFT_FILE}")
    if not plan:
        print("[System Planner][警告] PM 排期表未找到，将以无排期模式运行。")

    print(f"[System Planner] 已读取: 简案({len(concept)}c) 草案({len(draft)}c) 排期({len(plan)}c)")

    # 全局记忆
    codex = load_file(CODEX_FILE)
    registry = load_file(REGISTRY_FILE)
    if len(registry) > 5000:
        registry = registry[:5000]

    # ========== 2. 从独立文件加载角色设定 Prompt ==========
    sys_prompt = load_file(PROMPT_FILE)
    if not sys_prompt:
        print(f"{RED}[System Planner] 警告: 未找到 Prompt 文件 {PROMPT_FILE}，使用内置回退{RESET}")
        sys_prompt = "你是系统策划，请根据主策草案输出详细设计。"
    system_prompt = sys_prompt

    # ========== 3. 构建用户提示词 ==========
    user_prompt = (
        f"【老板原始简案】:\n{concept}\n\n"
        f"【主策宏观草案（请在此框架内扩写，不要推翻大方向）】:\n{draft}"
    )
    if plan:
        user_prompt += f"\n\n【PM 排期表（参考任务依赖，不在文档中复述）】:\n{plan}"
    if feedback:
        user_prompt = f"【老板修改意见】: {feedback}\n\n{user_prompt}"
    if codex:
        user_prompt += f"\n\n【项目记忆】:\n{codex}"
    if registry:
        user_prompt += f"\n\n【资产登记表】:\n```json\n{registry}\n```"

    # ---- 定向修复模式 ----
    if os.path.exists(FIX_FILE):
        try:
            with open(FIX_FILE, "r", encoding="utf-8") as f:
                fix_data = json.load(f)
            if fix_data.get("correction_mode"):
                anchor = fix_data.get("anchor", "?")
                desc = fix_data.get("problem", "?")
                user_prompt += (
                    f"\n\n【最高指令：定向修复模式】"
                    f"审查官在你的文档中发现了错误。"
                    f"请只在锚点 [{anchor}] 处进行针对性修改以解决以下问题：{desc}。"
                    f"绝对保证文档的其他所有部分一字不差地保留！"
                    f"千万不要因为修复一个问题而重写或精简其他无关内容！"
                )
                print(f"[System Planner] 进入定向修复模式 — 锚点: {anchor}")
            os.remove(FIX_FILE)
        except Exception as e:
            print(f"[System Planner][警告] 读取修复指令失败: {e}")

    # ========== 4. 调用大模型 ==========
    # ---- RAG 记忆注入（直接从已加载的 Codex + Registry 构建） ----
    rag_context = ""
    if codex:
        rag_context += f"\n【项目记忆 Codex】:\n{codex}"
    if registry:
        rag_context += f"\n\n【已有资产登记表】:\n```json\n{registry}\n```"
    if rag_context:
        user_prompt += rag_context
        print(f"[System Planner] 已注入 RAG 记忆 ({len(rag_context)} 字符)")

    print("[System Planner] 正在呼叫大模型扩写详细设计...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt)
    except Exception:
        loud_fail("大模型调用失败")

    print("=" * 60)
    print("【大模型原始返回】:")
    try:
        print(llm_response[:800])
    except UnicodeEncodeError:
        print(llm_response[:800].encode("ascii", errors="replace").decode("ascii"))
    if len(llm_response) > 800:
        print(f"... (共 {len(llm_response)} 字符)")
    print("=" * 60)

    if not llm_response.strip():
        loud_fail("大模型返回了空内容")

    # ========== 5. 保存至独立文件，禁止覆盖主策草案 ==========
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(DETAIL_OUTPUT, "w", encoding="utf-8") as f:
            f.write(llm_response.strip())
        print(f"{GRN}[System Planner] 详细设计已保存: {DETAIL_OUTPUT} ({len(llm_response)} 字符){RESET}")
    except Exception:
        loud_fail(f"写入失败: {DETAIL_OUTPUT}")

    # ========== 6. 推进流水线 ==========
    try:
        if not os.path.exists(STATUS_FILE):
            loud_fail(f"状态文件不存在: {STATUS_FILE}")
        with open(STATUS_FILE, "r", encoding="utf-8") as f:
            status_data = json.load(f)
        current_state = status_data.get("current_state", "")
        status_data["current_state"] = "pending_system_approval"
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status_data, f, ensure_ascii=False, indent=2)
        print(f"[System Planner] 状态: {current_state} -> pending_system_approval")
        print("[System Planner] 详细设计完成，等待老板审批。")
    except Exception:
        loud_fail(f"更新状态失败: {STATUS_FILE}")


if __name__ == "__main__":
    main()
