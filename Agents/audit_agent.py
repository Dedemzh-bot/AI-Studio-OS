"""
Audit Agent (QA 审查官)
职责：审查策划案、数值配表、程序蓝图之间的一致性与完整性。
输出：audit_feedback.json + audit_trace_log.md（增量追踪）
"""

import json
import os
import re
import sys
import traceback
from datetime import datetime

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(FILE_DIR)
sys.path.insert(0, ROOT_DIR)

from Skills.llm_client import ask_llm, safe_extract_json

WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
PROMPT_FILE   = os.path.join(FILE_DIR, "prompts", "audit_agent_prompt.md")
DRAFT_FILE    = os.path.join(WORKSPACE_DIR, "system_design_draft.md")
DOCS_FILE     = os.path.join(WORKSPACE_DIR, "system_numerical_docs.json")
DATA_FILE     = os.path.join(WORKSPACE_DIR, "system_numerical_data.json")
BLUEPRINT_FILE = os.path.join(WORKSPACE_DIR, "tech_blueprint.md")
OUTPUT_FILE   = os.path.join(WORKSPACE_DIR, "audit_feedback.json")
TRACE_FILE    = os.path.join(WORKSPACE_DIR, "audit_trace_log.md")
STATUS_FILE   = os.path.join(WORKSPACE_DIR, "task_status.json")

RED   = "\033[91m"
GRN   = "\033[92m"
RESET = "\033[0m"


def loud_fail(msg: str):
    print(f"{RED}========== [Audit Agent] 致命错误 =========={RESET}")
    print(f"{RED}{msg}{RESET}")
    traceback.print_exc()
    print(f"{RED}==========================================={RESET}")
    sys.exit(1)


def read_file_safe(filepath: str, label: str) -> str:
    if not os.path.exists(filepath):
        print(f"[Audit Agent] {label} 不存在，跳过: {filepath}")
        return ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read().strip()
        print(f"[Audit Agent] 已读取 {label} ({len(content)} 字符)")
        return content
    except Exception as e:
        print(f"[Audit Agent][警告] 读取 {label} 失败: {e}")
        return ""


def main():
    # ========== 1. 全景读取 ==========
    # 1a. 读取审查官提示词
    if not os.path.exists(PROMPT_FILE):
        loud_fail(f"审查官提示词文件不存在: {PROMPT_FILE}")
    with open(PROMPT_FILE, "r", encoding="utf-8") as f:
        prompt_text = f.read().strip()
    print(f"[Audit Agent] 已加载审查官人设提示词 ({len(prompt_text)} 字符)")

    # 1b. 读取被审查的三类文档
    draft_text = read_file_safe(DRAFT_FILE, "系统策划案")
    docs_text = read_file_safe(DOCS_FILE, "数值说明书")
    data_text = read_file_safe(DATA_FILE, "数值配表")
    blueprint_text = read_file_safe(BLUEPRINT_FILE, "程序蓝图")

    if not draft_text and not data_text:
        loud_fail("无可审查的文档")

    # ========== 2. 构建审查 user_prompt ==========
    system_prompt = prompt_text

    parts = []
    if draft_text:
        parts.append(f"## 系统策划案\n\n{draft_text}")
    if docs_text:
        parts.append(f"## 数值说明书\n\n{docs_text}")
    if data_text:
        parts.append(f"## 数值配表\n\n{data_text}")
    if blueprint_text:
        parts.append(f"## 程序蓝图\n\n{blueprint_text}")

    user_prompt = "请审查以下文档之间的一致性与完整性：\n\n" + "\n\n---\n\n".join(parts)

    # ========== 3. 呼叫大模型 ==========
    print("[Audit Agent] 正在呼叫大模型进行审查...")
    try:
        llm_response = ask_llm(system_prompt, user_prompt, max_tokens=8192)
    except Exception:
        loud_fail("大模型调用失败")

    print(f"[Audit Agent] 大模型返回完成 ({len(llm_response)} 字符)")

    # ========== 4. 安全剥壳 + 解析 ==========
    json_str, extract_err = safe_extract_json(llm_response, "AuditAgent")
    if extract_err:
        loud_fail(f"JSON 提取失败: {extract_err}")

    try:
        audit_data = json.loads(json_str)
    except json.JSONDecodeError as e:
        loud_fail(f"审查结果 JSON 不合法: {e}\n原始返回:\n{llm_response}")

    if not isinstance(audit_data, dict):
        loud_fail(f"审查结果必须是对象类型，实际为: {type(audit_data).__name__}")

    status = audit_data.get("status", "reject")
    issues = audit_data.get("issues", [])

    print(f"[Audit Agent] 审查完成 — 状态: {status}, 问题数: {len(issues)}")

    # ========== 5. 保存审查结果 ==========
    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, ensure_ascii=False, indent=2)
    print(f"[Audit Agent] 审查结果已保存: {OUTPUT_FILE}")

    # ========== 6. 增量日志记录（仅 reject 时） ==========
    if status == "reject" and issues:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_lines = [f"\n--- 审查时间: {timestamp} ---\n"]

        total_weight = 0
        for i, issue in enumerate(issues, 1):
            agent = issue.get("responsible_agent", "unknown")
            target = issue.get("target_file", "?")
            anchor = issue.get("anchor", "?")
            desc = issue.get("problem_description", "?")
            suggestion = issue.get("fix_suggestion", "?")

            total_weight += 1
            log_lines.append(f"### Issue {i}\n")
            log_lines.append(f"- 责任方: {agent}\n")
            log_lines.append(f"- 目标文件: {target}\n")
            log_lines.append(f"- 锚点: {anchor}\n")
            log_lines.append(f"- 问题描述: {desc}\n")
            log_lines.append(f"- 修改建议: {suggestion}\n")

        log_lines.append(f"**当前审查总计问题:** {total_weight} 个\n")

        try:
            with open(TRACE_FILE, "a", encoding="utf-8") as f:
                f.writelines(log_lines)
            print(f"[Audit Agent] 审查问题已追加至审计追踪日志: {TRACE_FILE}")
        except Exception as e:
            print(f"[Audit Agent][警告] 写入追踪日志失败: {e}")

        print(f"{RED}[Audit Agent] [审查驳回] 共 {total_weight} 个问题{RESET}")
    else:
        print(f"{GRN}[Audit Agent] [审查通过] 文档间一致性与完整性检查通过{RESET}")

    # ========== 7. 不修改 task_status，由 Router 读取 audit_feedback.json 后自行决策 ==========
    print("[Audit Agent] 审查结束，等待 Router 读取反馈。")


if __name__ == "__main__":
    main()
