"""
Visionary & System Designer (Skill A)
职责：读取用户简案 + 知识库 → 强制追问闭环 / 起草系统设计草案
输出：JSON {"status":"need_info","question":"..."} 或 {"status":"draft_ready"}
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
KNOWLEDGE_DIR = os.path.join(ROOT_DIR, "Knowledge")
CODEX_FILE    = os.path.join(KNOWLEDGE_DIR, "project_codex.md")
VISION_FILE   = os.path.join(KNOWLEDGE_DIR, "project_vision.md")
STANDARDS_FILE = os.path.join(KNOWLEDGE_DIR, "design_standards.json")
CAPABILITIES_FILE = os.path.join(KNOWLEDGE_DIR, "team_capabilities.md")
REGISTRY_FILE = os.path.join(KNOWLEDGE_DIR, "global_asset_registry.json")
FEEDBACK_FILE = os.path.join(WORKSPACE_DIR, "boss_feedback.txt")
STATUS_FILE   = os.path.join(WORKSPACE_DIR, "task_status.json")
PROMPT_FILE   = os.path.join(ROOT_DIR, "Agents", "prompts", "lead_planner_prompt.md")

RED   = "\033[91m"
GRN   = "\033[92m"
YEL   = "\033[93m"
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
    # ========== 1. 加载所有知识源 ==========
    concept = load_file(CONCEPT_FILE)
    if not concept:
        print(f"{RED}概念简案为空，无法继续{RESET}")
        sys.exit(1)

    vision = load_file(VISION_FILE)
    codex = load_file(CODEX_FILE)
    capabilities = load_file(CAPABILITIES_FILE)
    registry = load_file(REGISTRY_FILE)

    standards_text = load_file(STANDARDS_FILE)
    if standards_text:
        try:
            standards_obj = json.loads(standards_text)
            standards_text = json.dumps(standards_obj, ensure_ascii=False, indent=2)
        except json.JSONDecodeError:
            pass

    feedback = load_file(FEEDBACK_FILE)

    print(f"[Visionary] 已加载: 概念简案({len(concept)}c) 愿景({len(vision)}c) 规范({len(standards_text)}c) Codex({len(codex)}c)")

    # ========== 2. 从独立文件加载角色设定 Prompt ==========
    lead_prompt = load_file(PROMPT_FILE)
    if not lead_prompt:
        print(f"{RED}[Visionary] 警告: 未找到主策 Prompt 文件 {PROMPT_FILE}，使用内置回退{RESET}")
        lead_prompt = "你是游戏主策划，输出宏观草案。"

    # 注入项目宪法和设计规范
    if vision:
        lead_prompt += f"\n\n【项目宪法】:\n{vision}"
    if standards_text:
        lead_prompt += f"\n\n【输出格式规范】:\n{standards_text}"

    system_prompt = lead_prompt

    user_prompt = f"以下是老板的概念简案：\n\n{concept}"

    if feedback:
        # 读取现有草案，让 Visionary 基于其上做局部修改
        existing_draft = load_file(DRAFT_OUTPUT)
        if existing_draft:
            user_prompt = (
                f"【老板修改意见】: {feedback}\n\n"
                f"【上一版设计草案（请在此基础做局部修改，不要全盘重写）】:\n{existing_draft}\n\n"
                f"{user_prompt}"
            )
        else:
            user_prompt = f"【老板对上一轮的反驳/补充】: {feedback}\n\n{user_prompt}"

    if codex:
        user_prompt += f"\n\n【项目记忆 Codex】:\n{codex}"

    if registry and len(registry) > 100:
        user_prompt += f"\n\n【已有资产登记表（截取5000字）】:\n{registry[:5000]}"

    if capabilities:
        user_prompt += f"\n\n【下游团队能力】:\n{capabilities}"

    # ========== 3. 调用大模型 ==========
    print("[Visionary] 正在呼叫大模型进行需求审核与起草...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt)
    except Exception:
        traceback.print_exc()
        sys.exit(1)

    print("=" * 60)
    print("【大模型原始返回】:")
    try:
        print(llm_response[:800])
    except UnicodeEncodeError:
        print(llm_response[:800].encode("ascii", errors="replace").decode("ascii"))
    if len(llm_response) > 800:
        print(f"... (共 {len(llm_response)} 字符)")
    print("=" * 60)

    # ========== 4. 解析状态 ==========
    # 尝试提取 JSON 状态
    json_match = re.search(r'\{"status"\s*:\s*"(need_info|draft_ready)"\s*(?:,\s*"question"\s*:\s*"(.*?)")?\s*\}', llm_response, re.DOTALL)
    if not json_match:
        json_match = re.search(r'\{\s*"status"\s*:\s*"(need_info|draft_ready)"[^}]*\}', llm_response)

    if json_match:
        status_json_str = json_match.group(0)
        try:
            status_json = json.loads(status_json_str)
        except json.JSONDecodeError:
            status_json = {"status": "need_info", "question": "（解析状态失败，请老板检查输出）"}

        status = status_json.get("status", "need_info")
        question = status_json.get("question", "")

        if status == "need_info":
            print(f"\n{YEL}[主策追问] {question}{RESET}")
            # 输出纯 JSON 给 Router 解析
            print(json.dumps({"status": "need_info", "question": question}, ensure_ascii=False))
            sys.exit(0)

        elif status == "draft_ready":
            print(f"\n{GRN}[主策确认] 需求已达 100% 标准，正在起草设计草案...{RESET}")
            # 提取 Markdown 草案（多道回退策略）
            draft = ""
            # 策略1: markdown 代码块
            md_match = re.search(r"```(?:markdown)?\s*([\s\S]*?)```", llm_response, re.DOTALL)
            if md_match:
                draft = md_match.group(1).strip()
            # 策略2: JSON 之后所有文本（跳过可能的空白）
            if not draft or len(draft) < 100:
                post_json = llm_response[json_match.end():].strip()
                if len(post_json) > 100 and ('#' in post_json or '*' in post_json or '-' in post_json):
                    draft = post_json
            # 策略3: 整个回应去掉 JSON 部分
            if not draft or len(draft) < 100:
                draft = re.sub(r'\{[^{}]*"status"[^{}]*\}', '', llm_response).strip()

            if not draft or len(draft) < 100:
                # 回退：用二次调用请求 LLM 单独输出草案
                print("[Visionary] 草案未随 JSON 返回，发起二次调用提取...")
                draft_prompt = "请根据之前的分析，输出完整的设计草案。纯 Markdown 格式，不要 JSON。"
                try:
                    draft_response = ask_llm(system_prompt, user_prompt + "\n\n" + draft_prompt)
                    md_match2 = re.search(r"```(?:markdown)?\s*([\s\S]*?)```", draft_response, re.DOTALL)
                    if md_match2:
                        draft = md_match2.group(1).strip()
                    elif len(draft_response) > 100 and '#' in draft_response:
                        draft = draft_response.strip()
                except Exception:
                    pass

            if not draft or len(draft) < 100:
                print(f"{RED}未能提取有效设计草案{RESET}")
                sys.exit(1)

            os.makedirs(WORKSPACE_DIR, exist_ok=True)
            with open(DRAFT_OUTPUT, "w", encoding="utf-8") as f:
                f.write(draft)
            print(f"{GRN}[Visionary] 设计草案已保存: {DRAFT_OUTPUT} ({len(draft)} 字符){RESET}")

            # 推进状态
            try:
                if os.path.exists(STATUS_FILE):
                    with open(STATUS_FILE, "r", encoding="utf-8") as f:
                        sd = json.load(f)
                    sd["current_state"] = "pending_design_approval"
                    with open(STATUS_FILE, "w", encoding="utf-8") as f:
                        json.dump(sd, f, ensure_ascii=False, indent=2)
            except Exception:
                pass

            print(json.dumps({"status": "draft_ready"}, ensure_ascii=False))
            sys.exit(0)
    else:
        print(f"{RED}无法解析大模型状态输出{RESET}")
        print(json.dumps({"status": "need_info", "question": "无法解析您的输出，请简化格式重试"}, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    main()
