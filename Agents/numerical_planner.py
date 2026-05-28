"""
Numerical Planner (数值策划 / 经济模型设计师)
职责：读取系统 Schema + 概念简案 → 输出单 JSON（docs+data）→ 物理拆分落盘 → 推动流水线
单 JSON 设计：根对象含 docs 和 data 两个顶级 Key，代码端自动拆分保存
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

from Skills.llm_client import ask_llm, safe_extract_json
from Skills.rag_loader import load_knowledge_with_context

# ---- 所有读写目标均拼装为绝对路径 ----
WORKSPACE_DIR = os.path.join(os.environ.get("AI_STUDIO_DATA_DIR", ROOT_DIR), ".agent_workspace")
DETAIL_FILE      = os.path.join(WORKSPACE_DIR, "system_design_detail.md")
SCHEMA_SYS_FILE  = os.path.join(WORKSPACE_DIR, "system_schema.json")
DOCS_OUTPUT_FILE = os.path.join(WORKSPACE_DIR, "system_numerical_docs.json")
DATA_OUTPUT_FILE = os.path.join(WORKSPACE_DIR, "system_numerical_data.json")
RESULT_FILE      = os.path.join(WORKSPACE_DIR, "current_result.json")
STATUS_FILE      = os.path.join(WORKSPACE_DIR, "task_status.json")
FIX_FILE         = os.path.join(WORKSPACE_DIR, ".fix_correction.json")
PROMPT_FILE      = os.path.join(ROOT_DIR, "Agents", "prompts", "numerical_planner_prompt.md")

RED   = "\033[91m"
GRN   = "\033[92m"
RESET = "\033[0m"


def loud_fail(msg: str):
    print(f"{RED}========== [Numerical Planner] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}=================================================={RESET}")
    sys.exit(1)


def json_truncation_fail(msg: str):
    """JSON 截断/损坏特化退出 — 退出码 2，供 main_router 识别并自动重试。"""
    print(f"{RED}========== [Numerical Planner] JSON 截断或格式损坏 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    print(f"{RED}============================================================{RESET}")
    sys.exit(2)


def main():
    # ========== 1. 读取系统策划详细设计 ==========
    try:
        if not os.path.exists(DETAIL_FILE):
            loud_fail(f"系统策划详细设计不存在: {DETAIL_FILE}")

        with open(DETAIL_FILE, "r", encoding="utf-8") as f:
            detail_text = f.read().strip()

        if not detail_text:
            loud_fail("系统策划详细设计为空")

        print(f"[Numerical Planner] 已读取详细设计 ({len(detail_text)} 字符)")

    except Exception:
        loud_fail(f"读取详细设计失败: {DETAIL_FILE}")

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

    # ========== 2. 从独立文件加载角色设定 Prompt ==========
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
        print(f"[Numerical Planner] 已加载数值策划 Prompt ({len(system_prompt)} 字符)")
    except Exception:
        print(f"{RED}[Numerical Planner] 警告: 未找到 Prompt 文件 {PROMPT_FILE}，使用内置回退{RESET}")
        system_prompt = "你是数值策划，请根据系统设计输出数值配置。使用 docs+data 双 Key JSON 格式。"

    user_prompt = (
        f"以下是系统策划的详细设计案：\n\n---\n{detail_text}\n---\n\n"
        f"以下是系统 Schema：\n\n```json\n{schema_json_str}\n```\n\n"
        "请输出完整的 JSON 对象（含 docs 和 data 两个顶级 Key）。"
    )

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
                print(f"[Numerical Planner] 进入定向修复模式 — 锚点: {anchor}")
            os.remove(FIX_FILE)
        except Exception as e:
            print(f"[Numerical Planner][警告] 读取修复指令失败: {e}")

    # ========== 3. 注入 RAG 知识上下文 ==========
    rag_context = load_knowledge_with_context(ROOT_DIR, task_domain="数值架构")
    if rag_context:
        user_prompt += f"\n\n{rag_context}"
        print(f"[Numerical Planner] 已注入 RAG 上下文 ({len(rag_context)} 字符)")

    # ========== 4. 调用大模型 ==========
    print("[Numerical Planner] 正在呼叫大模型设计数值配置...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt, max_tokens=8192)
    except Exception:
        loud_fail("大模型调用失败（网络超时 / API Key 无效 / 服务不可用）")

    print(f"[Numerical Planner] 大模型返回完成 ({len(llm_response)} 字符)")

    # ========== 4. 万能剥壳 + 防崩溃解析 ==========
    json_str, extract_err = safe_extract_json(llm_response, "NumericalPlanner")
    if extract_err:
        json_truncation_fail(extract_err)

    try:
        parsed = json.loads(json_str)
    except json.JSONDecodeError as e:
        json_truncation_fail(
            f"大模型生成的 JSON 被截断或格式损坏！\n"
            f"错误位置: 第 {e.lineno} 行, 第 {e.colno} 列\n"
            f"错误详情: {e.msg}\n"
            f"--- 尾部 300 字符 ---\n{json_str[-300:]}\n"
            f"--- 完整原始返回 ---\n{llm_response}"
        )

    if not isinstance(parsed, dict):
        loud_fail(f"根 JSON 必须是对象类型，实际为: {type(parsed).__name__}")

    # ========== 5. 精准提取 docs 和 data ==========
    docs_content = parsed.get("docs", {})
    data_content = parsed.get("data", {})

    if not docs_content and "docs" not in parsed:
        loud_fail('根 JSON 缺失顶级 Key: "docs"')
    if not data_content and "data" not in parsed:
        loud_fail('根 JSON 缺失顶级 Key: "data"')

    if not isinstance(data_content, dict):
        loud_fail(f'data 必须是对象类型，实际为: {type(data_content).__name__}')

    print(f"{GRN}[Numerical Planner] 单 JSON 解析成功：docs + data 均已就绪{RESET}")

    # ========== 6. 物理拆分落盘 ==========
    try:
        os.makedirs(WORKSPACE_DIR, exist_ok=True)

        with open(DOCS_OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(docs_content, f, ensure_ascii=False, indent=2)
        print(f"{GRN}[Numerical Planner] 说明书已保存: {DOCS_OUTPUT_FILE}{RESET}")

        with open(DATA_OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(data_content, f, ensure_ascii=False, indent=2)
        print(f"{GRN}[Numerical Planner] 纯净数值数据已保存: {DATA_OUTPUT_FILE}{RESET}")

    except Exception:
        loud_fail(f"写入产出文件失败")

    # ========== 7. 按宪法格式封装并落盘 current_result.json ==========
    try:
        result = {
            "source_agent": "numerical_planner",
            "task_id": "task_001",
            "payload": {
                "docs": docs_content,
                "data": data_content,
            },
        }
        with open(RESULT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"[Numerical Planner] 封装结果已保存: {RESULT_FILE}")
    except Exception:
        loud_fail(f"写入封装结果失败: {RESULT_FILE}")

    # ========== 8. 推动流水线（定向修复模式跳过） ==========
    try:
        if in_fix_mode:
            print("[Numerical Planner] 定向修复模式 — 不修改 task_status.json")
        elif not os.path.exists(STATUS_FILE):
            loud_fail(f"任务状态文件不存在: {STATUS_FILE}")
        else:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                status_data = json.load(f)
            current_state = status_data.get("current_state", "")
            status_data["current_state"] = "completed"
            with open(STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(status_data, f, ensure_ascii=False, indent=2)
            print(f"[Numerical Planner] 任务状态已更新: {current_state} -> completed")
        print("[Numerical Planner] 数值策划工作完成。")
    except Exception:
        loud_fail(f"更新任务状态失败: {STATUS_FILE}")


if __name__ == "__main__":
    main()
