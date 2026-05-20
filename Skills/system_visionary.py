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

【宏观定调器法则（提问铁律）】
在起草之前，你必须判断老板简案中的"核心玩法机制"是否清晰（比如：它到底是个数值养成系统？还是个操作类小游戏？还是个抽卡系统？）。

1. 【强制宏观嗅探】：如果老板只给了一个名字（如"私人宿舍"），导致你面临两条以上的宏观路径选择，你必须返回 need_info 至少发起一次定调提问。

2. 【提问的艺术：给选项，定大局】：你的提问必须是宏观层面的（如："老板，宿舍系统的主轴是像猛男捡树枝那样的【装扮养成】，还是主打触摸交互的【动作小游戏】？"）。绝对禁止询问诸如"每天限制几次"、"价格多少"等微观数值细节（这些由你后续自行脑补）。

3. 【单次锁定】：只要老板回答了你关于"宏观大方向"的问题，你必须立刻停止提问，用专业能力脑补所有剩下的微观细节，直接输出纯净、笃定的草案。

【一定触发的追问条件】
你只能在以下三种极端情况下必须返回 {{"status": "need_info", "question": "..."}} 发起追问：
1. 老板的需求与《项目宪法》发生严重的根本性冲突（例如要求加男角色）。
2. 老板的需求会彻底摧毁现有的核心商业化闭环（例如要求把核心抽卡代币设为无限免费）。
3. 需求指向极其模糊，导致你面临两条以上互斥的宏观路径（如"私人宿舍"既可能是养成系统也可能是动作小游戏），此时必须发起宏观定调提问。

项目宪法：
{vision}

设计规范模板：
{standards_text}

【排版红线 — 绝对结构化】
作为资深系统策划，你的文档必须是结构化的，不是小说。以下铁律优先级最高：

1.【封杀文字墙】绝对禁止输出超过 3 句话的连续自然语言段落！所有玩法机制、规则判定，必须使用 Markdown 的「多级列表」或「表格」来呈现。

2.【状态机撰写规范】在描述交互逻辑（如小游戏点击、成功/失败）时，必须采用以下 Condition-Action-Feedback 模板：

```
### 玩法动作规则
- **[触发动作]**：玩家进行单次点击/滑动。
  - **[判定条件]**：点击位置是否在目标判定区内。
  - **✅ [单次成功反馈]**：
    - **表现层**：播放特效A，角色触发语音B（娇羞音）。
    - **数值层**：好感度/进度条 +10。
  - **❌ [单次失败反馈]**：
    - **表现层**：镜头抖动，角色触发语音C（抗拒）。
    - **数值层**：失误次数 +1。
```

3.【边界条件与结算】在描述"胜利/失败"结算时，必须清晰列出：
   **[结算条件] → [表现层播片] → [数值产出] → [状态重置/退出流转]**
   每一项使用独立的二级/三级列表项，不得混写成段落。

4.【表格优先】凡是涉及"星级vs奖励"、"等级vs消耗"等多维对比数据，必须使用 Markdown 表格，禁止用文字描述代替。

输出格式（重要！两者必须同时包含）：
- 第一步：先输出 {{"status": "draft_ready"}}
- 第二步：紧接着必须输出 ```markdown ... ``` 代码块，包含完整的设计草案！
  草案必须严格按照 design_standards.json 的 6 个强制章节结构编写，
  且全文必须遵循【排版红线】的结构化要求（列表+表格+CAF模板，禁止文字墙）。
  禁止只输出 JSON 而不输出 markdown 草案！JSON 和 markdown 缺一不可！！

【最高指令】你必须且只能输出合法的 JSON 字符串！绝对禁止在 JSON 前后输出任何 markdown 文本、思考过程或解释语！"""

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
