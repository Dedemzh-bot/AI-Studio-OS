"""
Tech Architect (主程 / 技术架构师)
职责：读取系统策划详细案 + 数值字典 → 输出程序开发蓝图 tech_blueprint.md
禁止写代码，只做系统拆分、接口定义和架构规划。
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
DETAIL_FILE      = os.path.join(WORKSPACE_DIR, "system_design_detail.md")
SCHEMA_FILE      = os.path.join(WORKSPACE_DIR, "system_schema.json")
DOCS_FILE        = os.path.join(WORKSPACE_DIR, "system_numerical_docs.json")
PROMPT_FILE      = os.path.join(ROOT_DIR, "Agents", "prompts", "tech_architect_prompt.md")
BLUEPRINT_OUTPUT = os.path.join(WORKSPACE_DIR, "tech_blueprint.md")
STATUS_FILE      = os.path.join(WORKSPACE_DIR, "task_status.json")
FIX_FILE         = os.path.join(WORKSPACE_DIR, ".fix_correction.json")

RED   = "\033[91m"
GRN   = "\033[92m"
RESET = "\033[0m"


def loud_fail(msg: str):
    print(f"{RED}========== [Tech Architect] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}==============================================={RESET}")
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
    # ========== 1. 读取三份上下文文件 ==========
    detail = load_file(DETAIL_FILE)
    docs = load_file(DOCS_FILE)

    if not detail:
        loud_fail(f"系统策划详细案不存在或为空: {DETAIL_FILE}")
    if not docs:
        print("[Tech Architect][警告] 数值字典未找到，将在无字典模式下运行。")

    print(f"[Tech Architect] 已读取: 详细案({len(detail)}c) 数值字典({len(docs)}c)")

    schema = load_file(SCHEMA_FILE)
    if schema:
        print(f"[Tech Architect] 已读取系统 Schema ({len(schema)}c)")

    # ========== 2. 从独立文件加载角色设定 Prompt ==========
    system_prompt = load_file(PROMPT_FILE)
    if not system_prompt:
        print(f"{RED}[Tech Architect] 警告: 未找到 Prompt 文件 {PROMPT_FILE}，使用回退{RESET}")
        system_prompt = "你是游戏主程序，请根据系统设计输出技术架构蓝图。"

    print(f"[Tech Architect] 已加载主程 Prompt ({len(system_prompt)} 字符)")

    # ---- 强制注入数值字典 ----
    if docs:
        system_prompt += (
            f"\n\n【绝对指令】：你必须且只能使用以下数值策划定义好的字段类型和默认值建表，"
            f"绝对不准自己创造新字段或修改默认值：\n\n{docs}"
        )
        print(f"[Tech Architect] 已将数值字典注入 System Prompt ({len(docs)} 字符)")

    # ========== 3. 构建用户提示词 ==========
    user_prompt = (
        f"【系统策划详细设计案】：\n\n{detail}\n\n"
        f"【数值策划数据字典】：\n\n{docs}"
    )
    if schema:
        user_prompt += f"\n\n【系统 Schema 骨架】：\n\n```json\n{schema}\n```"

    user_prompt += "\n\n请输出一份完整的技术架构蓝图（Markdown 格式），严格遵循五章结构。"

    # ---- 定向修复模式 ----
    in_fix_mode = False
    if os.path.exists(FIX_FILE):
        try:
            with open(FIX_FILE, "r", encoding="utf-8") as f:
                fix_data = json.load(f)
            if fix_data.get("correction_mode"):
                in_fix_mode = True
                anchor = fix_data.get("anchor", "?")
                desc = fix_data.get("problem", "?")
                user_prompt += (
                    f"\n\n【最高指令：定向修复模式】"
                    f"审查官在你的文档中发现了错误。"
                    f"请只在锚点 [{anchor}] 处进行针对性修改以解决以下问题：{desc}。"
                    f"绝对保证文档的其他所有部分一字不差地保留！"
                    f"千万不要因为修复一个问题而重写或精简其他无关内容！"
                )
                print(f"[Tech Architect] 进入定向修复模式 — 锚点: {anchor}")
            os.remove(FIX_FILE)
        except Exception as e:
            print(f"[Tech Architect][警告] 读取修复指令失败: {e}")

    # ========== 4. 注入 RAG 知识上下文 ==========
    rag_context = load_knowledge_with_context(ROOT_DIR, task_domain="技术架构")
    if rag_context:
        user_prompt += f"\n\n{rag_context}"
        print(f"[Tech Architect] 已注入 RAG 上下文 ({len(rag_context)} 字符)")
    else:
        print("[Tech Architect] RAG 知识库为空（无匹配领域的案例）")

    # ========== 5. 调用大模型 ==========
    print("[Tech Architect] 正在呼叫大模型生成技术架构蓝图...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt)
    except Exception:
        loud_fail("大模型调用失败")

    print("=" * 60)
    print("【大模型原始返回（前800字符）】:")
    try:
        print(llm_response[:800])
    except UnicodeEncodeError:
        print(llm_response[:800].encode("ascii", errors="replace").decode("ascii"))
    if len(llm_response) > 800:
        print(f"... (共 {len(llm_response)} 字符)")
    print("=" * 60)

    if not llm_response.strip():
        loud_fail("大模型返回了空内容")

    # ========== 5. 保存技术架构蓝图 ==========
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)
        with open(BLUEPRINT_OUTPUT, "w", encoding="utf-8") as f:
            f.write(llm_response.strip())
        print(f"{GRN}[Tech Architect] 技术架构蓝图已保存: {BLUEPRINT_OUTPUT} ({len(llm_response)} 字符){RESET}")
    except Exception:
        loud_fail(f"写入蓝图失败: {BLUEPRINT_OUTPUT}")

    # ========== 6. 推进流水线（定向修复模式跳过） ==========
    try:
        if in_fix_mode:
            print("[Tech Architect] 定向修复模式 — 不修改 task_status.json")
        elif not os.path.exists(STATUS_FILE):
            loud_fail(f"状态文件不存在: {STATUS_FILE}")
        else:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                status_data = json.load(f)
            current = status_data.get("current_state", "")
            status_data["current_state"] = "pending_tech_approval"
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
            print(f"[Tech Architect] 状态: {current} -> pending_tech_approval")
        print("[Tech Architect] 技术架构蓝图完成。")
    except Exception:
        loud_fail(f"更新状态失败: {STATUS_FILE}")


if __name__ == "__main__":
    main()
