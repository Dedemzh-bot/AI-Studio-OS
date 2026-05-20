"""
Lead Planner (主策划 Agent)
职责：读取概念简案 -> 生成 JSON Schema + 验收表 -> 推动流水线至验证阶段
"""

import os
import json
import re
import sys
import glob

# 将项目根目录加入 sys.path，确保能导入 Skills 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Skills.llm_client import ask_llm, safe_extract_json

# ---- 路径配置（全部使用绝对路径） ----
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
CONCEPT_FILE = os.path.join(WORKSPACE_DIR, "concept_brief.md")
SCHEMA_FILE = os.path.join(WORKSPACE_DIR, "active_schema.json")
REVIEW_FILE = os.path.join(WORKSPACE_DIR, "review_board.md")
STATUS_FILE = os.path.join(WORKSPACE_DIR, "task_status.json")
CODEX_FILE = os.path.join(WORKSPACE_DIR, "project_codex.md")
KNOWLEDGE_DIR = os.path.join(ROOT_DIR, "Knowledge")


def print_error(msg: str):
    """打印红色错误信息（ANSI 转义码）"""
    print(f"\033[91m[LeadPlanner][错误] {msg}\033[0m")


def main():
    # ========== 1. 读取概念简案 ==========
    if not os.path.exists(CONCEPT_FILE):
        print_error(f"概念简案文件不存在: {CONCEPT_FILE}")
        sys.exit(1)

    with open(CONCEPT_FILE, "r", encoding="utf-8") as f:
        concept_text = f.read().strip()

    if not concept_text:
        print_error("概念简案内容为空，无法继续")
        sys.exit(1)

    print(f"[LeadPlanner] 已读取概念简案 ({len(concept_text)} 字符)")

    # ========== 1.5. 加载知识库（RAG 上下文注入） ==========
    knowledge_context = ""
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)  # 目录不存在则自动创建
    md_files = glob.glob(os.path.join(KNOWLEDGE_DIR, "*.md"))
    if md_files:
        print(f"[LeadPlanner] 发现 {len(md_files)} 个知识库文件，正在加载...")
        for md_file in sorted(md_files):
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    knowledge_context += f"\n--- 知识库条目: {os.path.basename(md_file)} ---\n{content}\n"
                print(f"[LeadPlanner]   [OK] {os.path.basename(md_file)} ({len(content)} 字符)")
            except Exception as e:
                print_error(f"读取知识库文件失败: {md_file} - {e}")
    else:
        print("[LeadPlanner] 知识库目录为空，跳过上下文注入")

    # ========== 2. 构建 System Prompt ==========
    system_prompt = """你是一个顶级的游戏主策划兼系统架构师。你需要把人类的概念简案转化为严谨的数据结构。

你必须输出两部分内容：

第一部分是一段严谨的 JSON Schema，要求：
- 定义所有必要字段的类型、约束和说明
- 必须设置 "additionalProperties": false，禁止额外字段
- 必须包含因果追踪与触发来源追踪标签，以防范漏洞（如地图边缘爆炸导致无限刷怪）
- 【数据结构铁律】：绝对禁止在 Schema 中允许或使用"动态的、不可预知的字符串"作为 JSON 的 Key（例如不要设计 "tech_node_attack": {...} 这样的结构）。对于列表型数据，必须严格定义为 Array（数组）格式，并将唯一标识符作为内部的字段（如 "node_id": "tech_node_attack"）。
- Schema 必须符合 JSON Schema 规范（draft-07 或更高）

第二部分是用大白话解释这个 Schema 的 Markdown 验收表，列出所有字段的含义、取值范围、必填项、以及设计上的防漏洞措施。

请用以下标记严格分隔两部分，标记必须单独成行：
---JSON_START---
（JSON Schema 内容，必须是合法 JSON，不含注释）
---JSON_END---
---MARKDOWN_START---
（Markdown 验收表内容）
---MARKDOWN_END---

注意：JSON 部分必须是合法的 JSON，不要包含注释，不要有多余的文字。"""

    # ---- RAG 注入：全局知识库 ----
    if knowledge_context:
        knowledge_clause = (
            "\n\n"
            "【全局知识库限制】：在生成 Schema 和理解需求时，"
            "你必须绝对遵循以下公司级设计规范：\n"
            f"{knowledge_context}"
        )
        system_prompt += knowledge_clause
        print("[LeadPlanner] 已注入知识库上下文到 System Prompt")

    # ========== 2.5. 加载全局项目记忆（Codex） ==========
    codex_content = ""
    if os.path.exists(CODEX_FILE):
        try:
            with open(CODEX_FILE, "r", encoding="utf-8") as f:
                codex_content = f.read().strip()
            if codex_content:
                print(f"[LeadPlanner] 已加载项目记忆 Codex ({len(codex_content)} 字符)")
        except Exception:
            print("[LeadPlanner][警告] 项目记忆 Codex 读取失败，跳过")

    # 将 Codex 注入 user_prompt
    if codex_content:
        concept_text = (
            f"【全局项目记忆】：当前游戏项目已包含以下系统和已被占用的 ID 规范：\n"
            f"{codex_content}\n\n"
            f"请在设计时严格参考以上已有设定，确保新设计能与旧系统联动，并且绝对不要使用已被占用的 ID！\n\n"
            f"---\n\n"
            f"{concept_text}"
        )

    # ========== 3. 调用大模型 ==========
    print("[LeadPlanner] 正在调用大模型生成 Schema 与验收表...")
    try:
        response = ask_llm(system_prompt, concept_text)
    except Exception as e:
        print_error(f"大模型调用失败: {e}")
        sys.exit(1)

    print(f"[LeadPlanner] 大模型返回完成 ({len(response)} 字符)")

    # ========== 4. 解析回答：提取 JSON Schema ==========
    json_match = re.search(
        r"---JSON_START---\s*(.*?)\s*---JSON_END---",
        response,
        re.DOTALL,
    )
    if not json_match:
        print_error("未能从大模型回答中提取到 JSON Schema 部分，请检查 ---JSON_START---/---JSON_END--- 标记")
        sys.exit(1)

    json_str = json_match.group(1).strip()
    # 去嵌套的 ```json ``` 标记
    inner_code = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", json_str, re.DOTALL)
    if inner_code:
        json_str = inner_code.group(1).strip()
    # 兜底：万能剥壳
    if not json_str:
        json_str, _ = safe_extract_json(response, "LeadPlanner")
        if not json_str:
            print_error("JSON Schema 提取完全失败")
            sys.exit(1)

    # 验证 JSON 合法性
    try:
        schema_obj = json.loads(json_str)
    except json.JSONDecodeError as e:
        print_error(f"提取的 JSON Schema 不合法: {e}")
        print(f"[LeadPlanner] 原始内容片段（前 500 字符）:\n{json_str[:500]}")
        sys.exit(1)

    # ========== 5. 保存 JSON Schema ==========
    with open(SCHEMA_FILE, "w", encoding="utf-8") as f:
        json.dump(schema_obj, f, ensure_ascii=False, indent=2)
    print(f"[LeadPlanner] JSON Schema 已保存至: {SCHEMA_FILE}")

    # ========== 6. 解析回答：提取 Markdown 验收表 ==========
    md_match = re.search(
        r"---MARKDOWN_START---\s*(.*?)\s*---MARKDOWN_END---",
        response,
        re.DOTALL,
    )
    if md_match:
        md_content = md_match.group(1).strip()
    else:
        # 备用逻辑：尝试使用 JSON_END 之后的所有内容
        json_end_pos = response.rfind("---JSON_END---")
        if json_end_pos != -1:
            md_content = response[json_end_pos + len("---JSON_END---"):].strip()
            # 去掉可能残留的 MARKDOWN 标记
            md_content = re.sub(r"---MARKDOWN_(?:START|END)---", "", md_content).strip()
        else:
            md_content = f"# 验收表\n\n> 无法从大模型回答中解析出验收表，请手动检查原始回答。\n\n---\n\n{response}"
        print("[LeadPlanner][警告] 未找到 ---MARKDOWN_START--- 标记，已使用备用解析")

    # ========== 7. 保存验收表 ==========
    with open(REVIEW_FILE, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"[LeadPlanner] 验收表已保存至: {REVIEW_FILE}")

    # ========== 8. 推动流水线：状态 pending_design -> pending_execution ==========
    if not os.path.exists(STATUS_FILE):
        print_error(f"任务状态文件不存在: {STATUS_FILE}")
        sys.exit(1)

    with open(STATUS_FILE, "r", encoding="utf-8") as f:
        status_data = json.load(f)

    current_state = status_data.get("current_state", "")
    if current_state != "pending_design":
        print(
            f"[LeadPlanner][警告] 当前状态为 '{current_state}'，"
            f"非预期的 'pending_design'，仍将推进至 pending_execution"
        )

    status_data["current_state"] = "pending_execution"
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status_data, f, ensure_ascii=False, indent=2)
    print(f"[LeadPlanner] 任务状态已更新: {current_state} -> pending_execution")
    print("[LeadPlanner] 主策划工作完成，流水线已推进至 Combat Agent。")


if __name__ == "__main__":
    main()
