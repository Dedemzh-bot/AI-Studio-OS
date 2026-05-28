"""
RAG Loader — 统一知识库读取拦截器
职责：加载项目根 Knowledge/ 目录下的所有红黑榜及知识文件，
      在拼接给下游 Agent 前统一注入「RAG 记忆阅读器协议」Meta-Prompt，
      支持 task_domain 领域过滤 + Top-K 时间排序截断。
"""

import os
import re
import json

RAG_META_PROMPT = """=======================================================
⚠️ 【全局强制指令：如何阅读以下历史档案】

下方是系统从知识库中为你检索到的历史红黑榜档案。请你严格遵守以下阅读法则：

1. **【优先级法则】**：你必须最高优先读取带有 `[读取优先级：Highest]` 的核心总结部分。带有 `[读取优先级：Low]` 的骨架仅作结构参考。
2. **【领域隔离法则 (Domain Isolation)】**：注意每条档案顶部的 `[适用领域]`。
   - 强相关：如果该领域与你当前的任务（如：你正在做数值，且标签是"数值架构"）相符，你必须将其中的铁律视为**绝对不可违背的最高准则**！
   - 弱相关：如果标签是其他领域（如"表现演出"），请忽略其中的具体参数限制，仅学习其行文排版的格式化思路，绝不要让它干扰你的本职逻辑！
3. **【黑榜免疫法则】**：看到"黑榜"和"错误脱水骨架"时，明确知道那是错误的垃圾案子，绝对不可照搬！
======================================================="""

TOP_K = 3  # 红/黑榜各最多加载 Top-K 份最新文件

VALID_DOMAINS = (
    "概念设计", "系统逻辑", "数值架构", "表现演出",
    "文本剧情", "界面UI", "工作流调度", "技术架构",
)


def _load_file(path: str) -> str:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return ""


def _extract_domain(filepath: str) -> str | None:
    """读取文件前 10 行，正则提取 [适用领域]：xxx，返回领域字符串。"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            head = "".join(f.readline() for _ in range(10))
        m = re.search(r"\[适用领域\][：:]\s*(.+?)(?:\n|$)", head)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return None


def _domain_matches(file_domain: str | None, task_domain: str | None) -> bool:
    """判断文件领域是否匹配任务领域（子串包含）。"""
    if task_domain is None:
        return True  # 不传 task_domain 时全量
    if file_domain is None:
        return False  # 文件没打标签，未知领域，不纳入
    return task_domain in file_domain or file_domain in task_domain


def _scan_and_filter(dir_path: str, task_domain: str | None) -> list[tuple[str, str]]:
    """扫描目录下所有 .md / .json，返回 (文件路径, 内容) 的候选列表。"""
    results = []
    if not os.path.isdir(dir_path):
        return results
    for fname in sorted(os.listdir(dir_path)):
        fpath = os.path.join(dir_path, fname)
        if not os.path.isfile(fpath):
            continue
        if not (fname.endswith(".md") or fname.endswith(".json")):
            continue
        domain = _extract_domain(fpath)
        if _domain_matches(domain, task_domain):
            content = _load_file(fpath)
            if content:
                results.append((fpath, content))
    return results


def _topk_by_mtime(candidates: list[tuple[str, str]], k: int) -> list[str]:
    """按文件修改时间降序排列，取前 k 份内容。"""
    sorted_candidates = sorted(candidates, key=lambda x: os.path.getmtime(x[0]), reverse=True)
    return [content for _, content in sorted_candidates[:k]]


def load_rag_context(knowledge_dir: str, task_domain: str | None = None) -> str:
    """
    加载完整 RAG 上下文，支持领域过滤 + Top-K 截断。
    Args:
        knowledge_dir: Knowledge/ 目录路径
        task_domain: 任务领域标签，None 时全量加载
    Returns:
        拼接后的字符串，可直接嵌入下游 Agent 的 prompt
    """
    parts = []
    knowledge_dir = os.path.abspath(knowledge_dir)

    # ========== 1. 加载全局文件 ==========
    global_paths = {
        "project_codex": os.path.join(knowledge_dir, "project_codex.md"),
        "project_vision": os.path.join(knowledge_dir, "project_vision.md"),
        "design_standards": os.path.join(knowledge_dir, "design_standards.json"),
        "team_capabilities": os.path.join(knowledge_dir, "team_capabilities.md"),
        "global_asset_registry": os.path.join(knowledge_dir, "global_asset_registry.json"),
    }

    for label, path in global_paths.items():
        content = _load_file(path)
        if content:
            if label == "design_standards":
                try:
                    obj = json.loads(content)
                    content = json.dumps(obj, ensure_ascii=False, indent=2)
                except json.JSONDecodeError:
                    pass
            parts.append(content)

    # ========== 2. 扫描红榜（优秀案例）==========
    best_dir = os.path.join(knowledge_dir, "best_practices")
    best_candidates = _scan_and_filter(best_dir, task_domain)
    best_topk = _topk_by_mtime(best_candidates, TOP_K)

    # ========== 3. 扫描黑榜（错误案例）==========
    anti_dir = os.path.join(knowledge_dir, "anti_patterns")
    anti_candidates = _scan_and_filter(anti_dir, task_domain)
    anti_topk = _topk_by_mtime(anti_candidates, TOP_K)

    # ========== 4. 组装：全局 → Meta-Prompt → Top3红 → Top3黑 ==========
    if best_topk or anti_topk:
        parts.append(RAG_META_PROMPT)
        parts.extend(best_topk)
        parts.extend(anti_topk)

    return "\n\n".join(parts)


def load_knowledge_with_context(root_dir: str, task_domain: str | None = None) -> str:
    """便捷函数：给定项目根目录，返回带 Meta-Prompt 包装的完整知识上下文。"""
    knowledge_dir = os.path.join(root_dir, "Knowledge")
    return load_rag_context(knowledge_dir, task_domain)
