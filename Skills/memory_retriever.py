"""
Memory Retriever (轻量级 RAG 检索模块)
职责：通过关键词匹配 Knowledge/ 下的红黑榜，注入项目记忆到 Agent Prompt。
纯 Python 原生实现，无外部数据库依赖。
"""

import os


def retrieve_memory(query_text: str, root_dir: str) -> str:
    """
    简易 RAG 检索：通过 query_text 中的关键词匹配知识库。
    返回拼接后的记忆注入文本，无匹配时返回空串。
    """
    best_dir = os.path.join(root_dir, "Knowledge", "best_practices")
    anti_dir = os.path.join(root_dir, "Knowledge", "anti_patterns")

    if not os.path.exists(best_dir) or not os.path.exists(anti_dir):
        return ""

    def _get_top_file_content(target_dir: str) -> str | None:
        files = [
            f for f in os.listdir(target_dir)
            if f.endswith(".md") and not f.startswith("_")
        ]
        if not files:
            return None

        best_file = None
        max_score = -1
        for f in files:
            score = sum(1 for char in f.replace(".md", "") if char in query_text)
            if score > max_score:
                max_score = score
                best_file = f

        if best_file:
            filepath = os.path.join(target_dir, best_file)
            with open(filepath, "r", encoding="utf-8") as f:
                return f"【源文件: {best_file}】\n{f.read().strip()}"
        return None

    best_content = _get_top_file_content(best_dir)
    anti_content = _get_top_file_content(anti_dir)

    if not best_content and not anti_content:
        return ""

    memory_injection = "\n\n" + "=" * 40 + "\n【🧠 项目核心记忆库挂载 (RAG)】\n"
    if best_content:
        memory_injection += f"\n🟢 【优秀范式借鉴】（请严格学习其逻辑骨架）：\n{best_content}\n"
    if anti_content:
        memory_injection += f"\n🔴 【历史血泪规避】（绝对不可重犯以下错误）：\n{anti_content}\n"
    memory_injection += "=" * 40 + "\n\n"

    return memory_injection
