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
⚠️ 【全局强制指令：RAG 记忆库正确使用法则】

下方是系统为你检索到的历史红黑榜档案。你【绝对禁止】将这些档案视为"排版模板"或"填空题"！你必须按照以下认知逻辑使用它们：

1. **【最高指令：学神不学形】**：
   你必须将 100% 的注意力集中在带有 `[读取优先级：Highest]` 的【核心经验总结】或【核心问题总结】上。将其作为你此次设计的"避坑指南"和"底层逻辑检查清单"。

2. **【骨架隔离法则 (防格式滥用)】**：
   带有 `[读取优先级：Low]` 的脱水骨架，仅仅是为了向你展示"过去成功/失败的具体样子"，【绝对不是】让你抄袭它的文档层级、排版格式或标题结构！
   - 严禁死板套用骨架中的结构（如：不要因为看到别人用了五段式，就把"系统概述"也写成五段式）。
   - 严禁强行对齐骨架中的名词（如：不要因为过去的案子有"热点"，就在当前无关的案子里硬编一个"热点"）。

3. **【动态结构生成 (独立思考)】**：
   你当前输出的文档结构、标题层级和排版方式，必须【完全基于当前分配给你的具体需求和系统特征】来动态设计！
   - 例：如果是剧情系统，结构应该是"分支、节点、演出"；如果是社交系统，结构应该是"关系网、数据流、权限"。
   - 结合当前需求进行独立思考，用 RAG 的最高优先级经验来审查自己的逻辑是否闭环，而不是用 RAG 的骨架来束缚自己的排版。
========================================================""" 

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


def _topk_by_mtime(candidates: list[tuple[str, str]], k: int) -> list[tuple[str, str]]:
    """按文件修改时间降序排列，取前 k 份 (文件路径, 内容)。"""
    sorted_candidates = sorted(candidates, key=lambda x: os.path.getmtime(x[0]), reverse=True)
    return sorted_candidates[:k]


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
    best_contents = [content for _, content in best_topk]
    total_best = len(os.listdir(best_dir)) if os.path.isdir(best_dir) else 0

    # ========== 3. 扫描黑榜（错误案例）==========
    anti_dir = os.path.join(knowledge_dir, "anti_patterns")
    anti_candidates = _scan_and_filter(anti_dir, task_domain)
    anti_topk = _topk_by_mtime(anti_candidates, TOP_K)
    anti_contents = [content for _, content in anti_topk]
    total_anti = len(os.listdir(anti_dir)) if os.path.isdir(anti_dir) else 0

    # ========== 4. 打印 RAG 筛选日志 ==========
    domain_label = task_domain or "全量"
    print(f"[RAG] task_domain={domain_label} | best_practices: {len(best_candidates)}/{total_best} 匹配 | anti_patterns: {len(anti_candidates)}/{total_anti} 匹配")
    if best_topk:
        print(f"[RAG] 优秀案例 Top{TOP_K}:")
        for fp, _ in best_topk:
            print(f"  - {os.path.basename(fp)}")
    if anti_topk:
        print(f"[RAG] 错误案例 Top{TOP_K}:")
        for fp, _ in anti_topk:
            print(f"  - {os.path.basename(fp)}")
    total_loaded = len(best_topk) + len(anti_topk)
    total_chars = sum(len(c) for _, c in best_topk) + sum(len(c) for _, c in anti_topk)
    print(f"[RAG] 最终加载 {total_loaded} 个文件, {total_chars} 字符")

    # ========== 5. 组装：全局 → Meta-Prompt → Top3红 → Top3黑 ==========
    if best_contents or anti_contents:
        parts.append(RAG_META_PROMPT)
        parts.extend(best_contents)
        parts.extend(anti_contents)

    result = "\n\n".join(parts)
    print(f"[RAG] 总上下文（含全局文件+Meta): {len(result)} 字符")
    return result


def load_knowledge_with_context(root_dir: str, task_domain: str | None = None) -> str:
    """便捷函数：给定项目根目录，返回带 Meta-Prompt 包装的完整知识上下文。"""
    knowledge_dir = os.path.join(root_dir, "Knowledge")
    return load_rag_context(knowledge_dir, task_domain)
