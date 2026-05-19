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
KNOWLEDGE_DIR = os.path.join(WORKSPACE_DIR, "knowledge")
CONCEPT_FILE  = os.path.join(WORKSPACE_DIR, "concept_brief.md")
CODEX_FILE    = os.path.join(KNOWLEDGE_DIR, "project_codex.md")
VISION_FILE   = os.path.join(KNOWLEDGE_DIR, "project_vision.md")
STANDARDS_FILE = os.path.join(KNOWLEDGE_DIR, "design_standards.json")
CAPABILITIES_FILE = os.path.join(KNOWLEDGE_DIR, "team_capabilities.md")
DRAFT_OUTPUT  = os.path.join(WORKSPACE_DIR, "system_design_draft.md")
REGISTRY_FILE = os.path.join(WORKSPACE_DIR, "global_asset_registry.json")
FEEDBACK_FILE = os.path.join(WORKSPACE_DIR, "boss_feedback.txt")
STATUS_FILE   = os.path.join(WORKSPACE_DIR, "task_status.json")

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

    # ========== 2. 构建提示词（高级制作人脑补与提案准则） ==========
    system_prompt = f"""你是一位高级游戏制作人兼主策划。老板只负责下达宏观愿景，具体设计细节是你的本职工作。

你的核心准则：

【抓大放小，大权独揽】
你绝对不应该向老板询问具体数值（如每日几次）、具体交互表现（如怎么运镜、碰哪里）、具体的 UI 布局或微观的玩法设计。这些都是你的本职工作！当遇到未说明的细节时，你必须根据 project_vision.md 的基调自行脑补并设计一套完整的方案。

【绝对禁止重复提问】
在提问前，必须仔细检查 concept_brief.md 中的历史问答记录。绝对不允许提出与历史记录中语义高度重复的问题！

【精准追问漏洞】
如果老板上一轮的回答遗漏了你关注的某个具体参数，下一轮提问时，请直接针对该单一遗漏点进行极其具体的提问，不要带上已经确认过的内容。

【懂得自我脑补】
如果老板的回答中包含"其他没了"、"随便"、"你看着办"等字眼，或者老板已经回答了 2 轮以上，请立刻停止追问！你必须立刻调用你的专业素养和 project_vision.md（项目宪法），为缺失的参数脑补一个最符合项目调性的默认值，然后直接返回 {{"status": "draft_ready"}} 推进管线。

【提案代疑问】
你的第一要务是尽快生成 system_design_draft.md 草案。与其在终端里问老板"这个怎么做"，不如直接把你脑补的最优解写进草案里，交由老板在【黑板审批环节】去修改！

【一定触发的追问条件】
你只能在以下三种极端情况下必须返回 {{"status": "need_info", "question": "..."}} 发起追问：
1. 老板的需求与《项目宪法》发生严重的根本性冲突（例如要求加男角色）。
2. 老板的需求会彻底摧毁现有的核心商业化闭环（例如要求把核心抽卡代币设为无限免费）。
3. 需求指向极其模糊，导致你完全无法猜测其核心系统定位（例如老板只发了一个词"苹果"）。

项目宪法：
{vision}

设计规范模板：
{standards_text}

输出格式（重要！两者必须同时包含）：
- 第一步：先输出 {{"status": "draft_ready"}}
- 第二步：紧接着必须输出 ```markdown ... ``` 代码块，包含完整的设计草案！
  草稿必须严格按照 design_standards.json 的 6 个强制章节结构编写。
  禁止只输出 JSON 而不输出 markdown 草案！JSON 和 markdown 缺一不可！！

【最高指令】你必须且只能输出合法的 JSON 字符串！绝对禁止在 JSON 前后输出任何 markdown 文本、思考过程或解释语！"""

    user_prompt = f"以下是老板的概念简案：\n\n{concept}"

    if feedback:
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
    print(llm_response[:800])
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
