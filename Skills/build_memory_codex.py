"""
Build Memory Codex (全局项目记忆生成器)
职责：扫描 .agent_workspace/ 下的业务数据表 → 提取核心摘要 → 生成 project_codex.md
【已修复】数据聚合 + 范围压缩 + 外键屏蔽，彻底防止 Token 爆炸
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
CODEX_FILE = os.path.join(WORKSPACE_DIR, "project_codex.md")

# ============================================================
# 1. 严格黑名单：AI 框架内部运行文件，禁止扫描
# ============================================================
BLACKLIST = {
    "current_result.json",
    "active_schema.json",
    "blueprint.json",
    "task_route.json",
    "task_status.json",
    "audit_feedback.json",
}

DOCS_SUFFIX = "_docs"

# ============================================================
# 2. 精准 ID 字段规则
# ============================================================
ID_FIELD_SUFFIX = "_id"
ID_FIELD_EXACT = {"skill_id", "key"}

# 外键/条件词根：这些字段本质上是指向其他表的，不是本表自身 ID
FK_BLOCK_PATTERNS = [
    "unlock_", "require_", "prerequisite_",
    "previous_", "next_", "parent_",
    "ref_", "foreign_", "target_",
    "dependent_", "condition_",
]

RED = "\033[91m"
GRN = "\033[92m"
RESET = "\033[0m"


def is_docs_file(filename: str) -> bool:
    name_lower = filename.lower()
    return DOCS_SUFFIX in name_lower or name_lower.endswith(f"{DOCS_SUFFIX}.json")


def is_blacklisted(filename: str) -> bool:
    return filename in BLACKLIST


def is_fk_field(field_name: str) -> bool:
    """判断字段是否为外键/条件字段，应跳过。"""
    field_lower = field_name.lower()
    for pattern in FK_BLOCK_PATTERNS:
        if pattern in field_lower:
            return True
    return False


def is_id_field(field_name: str) -> bool:
    """判断字段是否为精准 ID 字段，且非外键。"""
    if is_fk_field(field_name):
        return False
    field_lower = field_name.lower()
    if field_lower in ID_FIELD_EXACT:
        return True
    if len(field_name) > 3 and field_lower.endswith(ID_FIELD_SUFFIX):
        return True
    return False


def extract_id_value(value):
    """返回可聚合的值：字符串或数值，跳过中文长句。"""
    if isinstance(value, str):
        stripped = value.strip()
        if len(stripped) < 64 and not any('\u4e00' <= c <= '\u9fff' for c in stripped):
            return stripped
    elif isinstance(value, (int, float)):
        return int(value) if value == int(value) else value
    return None


def collect_ids(data, max_depth=5, current_depth=0):
    """
    遍历数据表，按 [namespace] field_name 分组收集所有值。
    返回 dict: { "[ns] field": set_of_values }
    """
    collector = {}
    _collect_recursive(data, "root", collector, max_depth, current_depth)
    return collector


def _collect_recursive(data, namespace: str, collector: dict, max_depth, depth):
    if depth >= max_depth or data is None:
        return

    if isinstance(data, dict):
        # 检查 module_name / module 作为命名空间
        current_ns = namespace
        for ns_key in ("module_name", "module"):
            if ns_key in data and isinstance(data[ns_key], str):
                current_ns = data[ns_key]
                break

        for key, value in data.items():
            if is_id_field(key):
                extracted = extract_id_value(value)
                if extracted is not None:
                    bucket_key = f"[{current_ns}] {key}"
                    if bucket_key not in collector:
                        collector[bucket_key] = set()
                    collector[bucket_key].add(extracted)

            # 递归深入
            if key.lower() != "docs":
                child_ns = key if depth == 0 and not is_id_field(key) else current_ns
                _collect_recursive(value, child_ns, collector, max_depth, depth + 1)

    elif isinstance(data, list):
        for item in data:
            _collect_recursive(item, namespace, collector, max_depth, depth + 1)


def compress_values(bucket: set) -> str:
    """
    压缩一组值：
    - 全数值 → min ~ max
    - 字符串 → 去重后最多展示前 3 个 + 计数
    """
    values = sorted(bucket, key=str)

    # 判断是否全部为数值
    all_numeric = all(isinstance(v, (int, float)) for v in bucket)
    if all_numeric and len(bucket) >= 2:
        nums = [v for v in bucket]
        min_val = min(nums)
        max_val = max(nums)
        if min_val == max_val:
            return str(min_val)
        return f"{min_val} ~ {max_val}"
    elif all_numeric and len(bucket) == 1:
        return str(list(bucket)[0])

    # 字符串处理
    str_values = sorted([str(v) for v in bucket])
    if len(str_values) <= 3:
        return ", ".join(str_values)
    else:
        head = ", ".join(str_values[:3])
        return f"{head} ...等 {len(str_values)} 个"


def extract_module_names(obj):
    modules = set()
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, dict):
                name = item.get("module_name") or item.get("module")
                if name and isinstance(name, str):
                    modules.add(name)
    elif isinstance(obj, dict):
        name = obj.get("module_name") or obj.get("module")
        if name and isinstance(name, str):
            modules.add(name)
    return modules


def extract_top_keys(obj):
    if isinstance(obj, dict):
        return list(obj.keys())
    return []


def main():
    print("[Codex] 正在扫描 .agent_workspace/ 下的业务数据表...")

    all_modules = set()
    all_compressed_ids = []  # [(label, compressed_str)]
    file_sketches = []

    try:
        all_files = [
            f for f in os.listdir(WORKSPACE_DIR)
            if f.endswith(".json") and os.path.isfile(os.path.join(WORKSPACE_DIR, f))
        ]
    except FileNotFoundError:
        all_files = []

    skipped_blacklist = 0
    skipped_docs = 0

    for filename in sorted(all_files):
        filepath = os.path.join(WORKSPACE_DIR, filename)

        if is_blacklisted(filename):
            print(f"[Codex]   [框架文件] {filename} — 跳过")
            skipped_blacklist += 1
            continue

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"[Codex]   [跳过] {filename} — 无法解析: {e}")
            continue

        top_keys = extract_top_keys(data)
        modules = extract_module_names(data)
        all_modules.update(modules)

        # ID 收集 + 压缩
        compressed = {}
        if is_docs_file(filename):
            print(f"[Codex]   [说明书] {filename} — 跳过 ID 提取，仅记录模块")
            skipped_docs += 1
        else:
            collector = collect_ids(data)
            for bucket_key, value_set in collector.items():
                if value_set:
                    compressed[bucket_key] = compress_values(value_set)
                    all_compressed_ids.append((bucket_key, compressed[bucket_key]))

        size_kb = os.path.getsize(filepath) / 1024
        sketch = f"- **{filename}** ({size_kb:.1f} KB)"
        if top_keys:
            sketch += f" | 顶级 Key: `{', '.join(top_keys[:10])}`"
        if modules:
            sketch += f" | 模块: {', '.join(sorted(modules)[:10])}"
        if compressed:
            compressed_items = [f"{k}: {v}" for k, v in list(compressed.items())[:10]]
            sketch += f" | ID: {', '.join(compressed_items)}"
        file_sketches.append(sketch)

        id_label = "跳过(说明书)" if is_docs_file(filename) else f"{len(compressed)} 组(已压缩)"
        print(f"[Codex]   [OK] {filename} ({size_kb:.1f} KB, {len(top_keys)} keys, {len(modules)} modules, {id_label})")

    if skipped_blacklist:
        print(f"[Codex]   [过滤] 共跳过 {skipped_blacklist} 个框架运行文件")
    if skipped_docs:
        print(f"[Codex]   [过滤] 共跳过 {skipped_docs} 个说明书文件")

    # ========== 生成 Markdown ==========
    lines = []
    lines.append("# 项目记忆 Codex")
    lines.append("")
    lines.append("> 自动生成于 `build_memory_codex.py`，为所有 Agent 提供全局上下文。")
    lines.append("> 仅扫描业务数据表，已过滤框架运行文件 & 外键字段。")
    lines.append("> ID 已做范围压缩（min~max）/ 截断去重，防止 Token 爆炸。")
    lines.append("")

    lines.append("## 系统概览")
    if all_modules:
        lines.append(f"- 已有系统模块: {', '.join(sorted(all_modules))}")
    else:
        lines.append("- 已有系统模块: （未检测到模块名定义）")
    lines.append("")

    lines.append("## 已占用的业务 ID（范围压缩 / 去重截断）")
    if all_compressed_ids:
        # 按标签排序
        seen = set()
        unique_items = []
        for label, val in all_compressed_ids:
            if (label, val) not in seen:
                seen.add((label, val))
                unique_items.append((label, val))
        unique_items.sort(key=lambda x: str(x[0]))
        lines.append(f"- 共 {len(unique_items)} 组标识符")
        for label, val in unique_items:
            lines.append(f"  - `{label}: {val}`")
    else:
        lines.append("- （未检测到已占用 ID）")
    lines.append("")

    lines.append("## 业务数据表清单")
    if file_sketches:
        for sketch in file_sketches:
            lines.append(sketch)
    else:
        lines.append("- （未扫描到任何业务数据表）")
    lines.append("")

    codex_text = "\n".join(lines)

    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    with open(CODEX_FILE, "w", encoding="utf-8") as f:
        f.write(codex_text)

    print(f"{GRN}[Codex] project_codex.md 已生成: {CODEX_FILE}{RESET}")
    print(f"[Codex]   模块数: {len(all_modules)}, 压缩后 ID 组数: {len(all_compressed_ids)}, 业务文件数: {len(file_sketches)}")


if __name__ == "__main__":
    main()
