"""
UX Agent (UX 交互架构师)
职责：读取系统策划详细案 → 过滤后台逻辑 → 输出 UI 交互蓝图与生图清单
严格遵循"表现层脱水中间件"角色，只出信息架构，不做视觉设计。
输出：ux_blueprint.md
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
DETAIL_FILE   = os.path.join(WORKSPACE_DIR, "system_design_detail.md")
BLUEPRINT_FILE = os.path.join(WORKSPACE_DIR, "ui_interaction_blueprint.md")
STATUS_FILE   = os.path.join(WORKSPACE_DIR, "task_status.json")
PROMPT_FILE   = os.path.join(ROOT_DIR, "Agents", "prompts", "ux_agent_prompt.md")
META_FILE     = os.path.join(WORKSPACE_DIR, "project_meta.json")

RED   = "\033[91m"
GRN   = "\033[92m"
RESET = "\033[0m"


def loud_fail(msg: str):
    print(f"{RED}========== [UX Agent] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}=========================================={RESET}")
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
    # ========== 1. 加载上游上下文 ==========
    detail_text = load_file(DETAIL_FILE)
    if not detail_text:
        loud_fail(f"系统策划详细案不存在: {DETAIL_FILE}")

    # 读取主策草案中的 system_name
    system_name = "未命名"
    if os.path.exists(META_FILE):
        try:
            with open(META_FILE, "r", encoding="utf-8") as f:
                meta = json.load(f)
            system_name = meta.get("system_name", "未命名")
        except Exception:
            pass

    print(f"[UX Agent] 已读取: {system_name} ({len(detail_text)} 字符)")

    # ========== 2. 加载角色设定 Prompt ==========
    system_prompt = load_file(PROMPT_FILE)
    if not system_prompt:
        print(f"{RED}[UX Agent] 警告: 未找到 Prompt 文件 {PROMPT_FILE}，使用内置回退{RESET}")
        system_prompt = "你是资深 UX 交互架构师，请根据系统策划案输出 UI 交互蓝图。"

    # ========== 3. 动态组装提示词（XML 标签隔离任务指令与原材料）==========
    user_prompt = f"""请为【{system_name}】提取 UI 交互蓝图。
以下是系统策划撰写的底层逻辑案全文，请严格按照你的角色设定，进行"表现层脱水"和"UX 自动补全"：

<System_Design_Document>
{detail_text}
</System_Design_Document>"""

    # ========== 4. 注入 RAG 知识上下文 ==========
    rag_context = load_knowledge_with_context(ROOT_DIR, task_domain="表现演出")
    if rag_context:
        user_prompt += f"\n\n{rag_context}"
        print(f"[UX Agent] 已注入 RAG 上下文 ({len(rag_context)} 字符)")
    else:
        print("[UX Agent] RAG 知识库为空（无匹配领域的案例）")

    # ========== 5. 执行脱水与生图提炼（低温度确保严谨性）==========
    print("[UX Agent] 正在呼叫大模型进行表现层脱水...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt, max_tokens=8192, temperature=0.3)
    except Exception:
        loud_fail("大模型调用失败")

    print(f"[UX Agent] 大模型返回完成 ({len(llm_response)} 字符)")

    # ========== 6. 蓝图落盘 ==========
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(BLUEPRINT_FILE, "w", encoding="utf-8") as f:
            f.write(llm_response.strip())
        print(f"{GRN}[UX Agent] UI 交互蓝图已保存: {BLUEPRINT_FILE}{RESET}")
    except Exception:
        loud_fail(f"写入失败: {BLUEPRINT_FILE}")

    # ========== 7. 推动流水线 ==========
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                status_data = json.load(f)
            status_data["current_state"] = "ui_done"
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
            print("[UX Agent] 任务状态已更新 -> ui_done")
    except Exception:
        pass

    print("[UX Agent] UI 交互蓝图设计完成。")


if __name__ == "__main__":
    main()
