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
from Skills.rag_loader import load_knowledge_with_context

WORKSPACE_DIR = os.path.join(os.environ.get("AI_STUDIO_DATA_DIR", ROOT_DIR), ".agent_workspace")
KNOWLEDGE_DIR = os.path.join(os.environ.get("AI_STUDIO_DATA_DIR", ROOT_DIR), "Knowledge")
CONCEPT_FILE  = os.path.join(WORKSPACE_DIR, "concept_brief.md")
CODEX_FILE    = os.path.join(KNOWLEDGE_DIR, "project_codex.md")
VISION_FILE   = os.path.join(KNOWLEDGE_DIR, "project_vision.md")
STANDARDS_FILE = os.path.join(KNOWLEDGE_DIR, "design_standards.json")
CAPABILITIES_FILE = os.path.join(KNOWLEDGE_DIR, "team_capabilities.md")
REGISTRY_FILE = os.path.join(KNOWLEDGE_DIR, "global_asset_registry.json")
FEEDBACK_FILE = os.path.join(WORKSPACE_DIR, "boss_feedback.txt")
STATUS_FILE   = os.path.join(WORKSPACE_DIR, "task_status.json")
DRAFT_OUTPUT  = os.path.join(WORKSPACE_DIR, "system_design_draft.md")
META_FILE     = os.path.join(WORKSPACE_DIR, "project_meta.json")
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


def _extract_meta_field(draft: str, field: str) -> str:
    """从设计草案的标题行或 0_System_Meta 区域提取字段值。"""
    # 1. 匹配一级标题: # {system_name} - 宏观设计草案
    title_match = re.search(r'^#\s*(.+?)\s*-\s*宏观设计草案', draft, re.MULTILINE)
    if title_match:
        return title_match.group(1).strip()

    # 2. 匹配 meta 字段: **system_name**: XXX
    for pattern in [
        rf'\*\*{field}\*\*\s*[:：]\s*(.+?)(?:\n|$)',
        rf'{field}\s*[:：]\s*(.+?)(?:\n|$)',
    ]:
        m = re.search(pattern, draft, re.IGNORECASE | re.MULTILINE)
        if m:
            val = m.group(1).strip().strip('"').strip("'")
            if val and len(val) < 64:
                return val
    return ""


def main():
    # ========== 1. 加载所有知识源 ==========
    concept = load_file(CONCEPT_FILE)
    if not concept:
        print(f"{RED}概念简案为空，无法继续{RESET}")
        sys.exit(1)

    feedback = load_file(FEEDBACK_FILE)
    rag_context = load_knowledge_with_context(ROOT_DIR, task_domain="概念设计")
    vision = load_file(VISION_FILE)

    print(f"[Visionary] 已加载: 概念简案({len(concept)}c) RAG上下文({len(rag_context)}c)")

    # ========== 2. 从独立文件加载角色设定 Prompt ==========
    lead_prompt = load_file(PROMPT_FILE)
    if not lead_prompt:
        print(f"{RED}[Visionary] 警告: 未找到主策 Prompt 文件 {PROMPT_FILE}，使用内置回退{RESET}")
        lead_prompt = "你是游戏主策划，输出宏观草案。"

    # 注入项目宪法
    if vision:
        lead_prompt += f"\n\n【项目宪法】:\n{vision}"

    system_prompt = lead_prompt

    user_prompt = f"以下是老板的概念简案：\n\n{concept}"

    if feedback:
        existing_draft = load_file(DRAFT_OUTPUT)
        if existing_draft:
            user_prompt = (
                f"【老板修改意见】: {feedback}\n\n"
                f"【上一版设计草案（请在此基础做局部修改，不要全盘重写）】:\n{existing_draft}\n\n"
                f"{user_prompt}"
            )
        else:
            user_prompt = f"【老板对上一轮的反驳/补充】: {feedback}\n\n{user_prompt}"

    # 注入统一 RAG 知识上下文（含 Meta-Prompt + 红黑榜 + Codex + 规范等）
    if rag_context:
        user_prompt += f"\n\n{rag_context}"

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
    # 策略1: 直接完整解析
    status_json = None
    cleaned = llm_response.strip()
    for candidate in [cleaned, cleaned + '"', cleaned + '"}', cleaned + '"}}', cleaned + '"}']:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and parsed.get("status") in ("need_info", "draft_ready"):
                status_json = parsed
                break
        except json.JSONDecodeError:
            pass

    # 策略2: 正则提取（兼容内部含 Unicode 引号）
    if status_json is None:
        json_match = re.search(r'\{"status"\s*:\s*"(need_info|draft_ready)"\s*(?:,\s*"question"\s*:\s*"(.*?)")?\s*\}', llm_response, re.DOTALL)
        if not json_match:
            json_match = re.search(r'\{\s*"status"\s*:\s*"(need_info|draft_ready)"[^}]*\}', llm_response)
        if json_match:
            try:
                status_json = json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

    # 策略3: 扫描行（兼容 stdout 混杂多行）
    if status_json is None:
        for line in llm_response.split("\n"):
            line = line.strip()
            if line.startswith("{"):
                try:
                    parsed = json.loads(line)
                    if isinstance(parsed, dict) and parsed.get("status") in ("need_info", "draft_ready"):
                        status_json = parsed
                        break
                except json.JSONDecodeError:
                    pass

    if status_json:
        status = status_json.get("status", "need_info")
        question = status_json.get("question", "")

        if status == "need_info":
            print(f"\n{YEL}[主策追问] {question}{RESET}")
            # 写状态到 task_status.json，让 Router 通过读文件感知
            try:
                if os.path.exists(STATUS_FILE):
                    with open(STATUS_FILE, "r", encoding="utf-8") as f:
                        sd = json.load(f)
                    sd["current_state"] = "clarifying_requirements"
                    with open(STATUS_FILE, "w", encoding="utf-8") as f:
                        json.dump(sd, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
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
                json_end = llm_response.rfind("}")
                if json_end > 0:
                    post_json = llm_response[json_end+1:].strip()
                else:
                    post_json = ""
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

            # 提取 0_System_Meta 元数据，落盘 project_meta.json
            meta_name = _extract_meta_field(draft, "system_name") or "未命名系统"
            meta_tag = _extract_meta_field(draft, "primary_tag") or "通用"
            project_meta = {
                "system_name": meta_name,
                "primary_tag": meta_tag,
                "version": "v1",
            }
            try:
                os.makedirs(WORKSPACE_DIR, exist_ok=True)
                with open(META_FILE, "w", encoding="utf-8") as f:
                    json.dump(project_meta, f, ensure_ascii=False, indent=2)
                print(f"{GRN}[Visionary] 元数据已保存: {META_FILE} ({meta_name}/{meta_tag}){RESET}")
            except Exception:
                pass

            # ---- 清空审计日志，为新系统立项 ----
            trace_file = os.path.join(WORKSPACE_DIR, "audit_trace_log.md")
            try:
                os.makedirs(WORKSPACE_DIR, exist_ok=True)
                with open(trace_file, "w", encoding="utf-8") as f:
                    f.write(f"# {meta_name} - 审查修改日志\n\n")
                print(f"[Visionary] 审计日志已重置: {trace_file}")
            except Exception:
                pass

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

    print(f"{RED}无法解析大模型状态输出{RESET}")
    print(json.dumps({"status": "need_info", "question": "无法解析您的输出，请简化格式重试"}, ensure_ascii=False))
    sys.exit(1)


if __name__ == "__main__":
    main()
