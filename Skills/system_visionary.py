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

    # ========== 2. 构建提示词（强制追问闭环） ==========
    system_prompt = f"""你是一位高级游戏制作人兼主策划。

你的任务分为两个阶段：

【阶段一：强制审核】
请凭借你的专业敏锐度，审查当前的概念简案。你必须找出：
1. 边缘情况：极端状态、边界条件是否被忽略
2. 与旧系统的冲突：参考项目记忆 Codex 和全局资产登记表
3. 缺失的商业化维度：缺少付费点/经济循环闭环
4. 不符合项目愿景的设计：参考 project_vision.md

项目愿景：
{vision}

设计规范模板：
{standards_text}

如果发现以上任何缺失、冲突或不清晰之处，你必须输出：
{{"status": "need_info", "question": "你的具体追问（简洁、精准，不超过80字）"}}

【阶段二：起草设计草案】
只有当需求已经达到 100% 无懈可击的标准时（所有信息齐备，逻辑闭环，符合愿景和规范），你才输出：
{{"status": "draft_ready"}}

然后紧接着用 ```markdown ... ``` 代码块输出完整的系统设计草案。
草案必须严格遵循 design_standards.json 的骨架。

最高指令：
1. 绝对禁止盲目脑补缺失的关键参数
2. 一次最多提 1 个最关键的问题
3. 输出纯文本，不要用任何 Markdown 包裹外侧"""

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
            # 提取 Markdown 草案
            md_match = re.search(r"```(?:markdown)?\s*([\s\S]*?)```", llm_response, re.DOTALL)
            if md_match:
                draft = md_match.group(1).strip()
            else:
                # 尝试提取 JSON 之后的所有文本
                draft = llm_response[json_match.end():].strip()
                if len(draft) < 50:
                    draft = llm_response.strip()

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
