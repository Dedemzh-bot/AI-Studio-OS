"""
Build Memory Codex (全局项目记忆生成器)
职责：扫描 .agent_workspace/ 下的业务数据表 → 提取核心摘要 → 生成 project_codex.md + global_asset_registry.json
【已修复】严格前缀匹配 + 主键/外键区分，彻底消除跨前缀幻觉和外键污染
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
KNOWLEDGE_DIR = os.path.join(WORKSPACE_DIR, "knowledge")
CODEX_FILE = os.path.join(KNOWLEDGE_DIR, "project_codex.md")
REGISTRY_FILE = os.path.join(WORKSPACE_DIR, "global_asset_registry.json")

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
    "global_asset_registry.json",
    "project_codex.md",
}

DOCS_SUFFIX = "_docs"

# ============================================================
# 2. 精准 ID 字段规则
# ============================================================
ID_FIELD_SUFFIX = "_id"
ID_FIELD_EXACT = {"skill_id", "key"}

# 外键/条件词根：这些字段不是本表主键
FK_BLOCK_PATTERNS = [
    "unlock_", "require_", "prerequisite_",
    "previous_", "next_", "parent_",
    "ref_", "foreign_", "target_",
    "dependent_", "condition_",
]

# 备注名字段后缀（严格前缀匹配用）
NAME_SUFFIXES = ["_name", "_title", "_label"]

RED = "\033[91m"
GRN = "\033[92m"
RESET = "\033[0m"


def is_docs_file(filename: str) -> bool:
    name_lower = filename.lower()
    return DOCS_SUFFIX in name_lower or name_lower.endswith(f"{DOCS_SUFFIX}.json")


def is_blacklisted(filename: str) -> bool:
    return filename in BLACKLIST


def is_fk_field(field_name: str) -> bool:
    field_lower = field_name.lower()
    for pattern in FK_BLOCK_PATTERNS:
        if pattern in field_lower:
            return True
    return False


def get_id_prefix(field_name: str) -> str:
    """从 ID 字段名提取前缀。如 zone_id → zone, item_id → item。"""
    field_lower = field_name.lower()
    for suffix in ["_id", "_key", "_code"]:
        if field_lower.endswith(suffix):
            return field_name[: -len(suffix)]
    return field_name


def find_display_name(sibling_dict: dict, id_field: str) -> str | None:
    """
    严格前缀匹配查找同级字典中的备注名。
    如 id_field = "zone_id" → 只找 zone_name / zone_title。
    绝对禁止跨前缀抓取（如 fish_name）。
    """
    prefix = get_id_prefix(id_field).lower()
    # 精确匹配 prefix + _name / _title / _label
    for suffix in NAME_SUFFIXES:
        candidate = prefix + suffix
        if candidate in sibling_dict:
            val = sibling_dict[candidate]
            if isinstance(val, str) and val.strip():
                return val.strip()
    # 仅当 ID 字段为 "id" 这种通用名时，才匹配 name / title
    if prefix in ("", "id"):
        for exact in ("name", "title"):
            if exact in sibling_dict:
                val = sibling_dict[exact]
                if isinstance(val, str) and val.strip():
                    return val.strip()
    return None


def is_foreign_key(field_name: str, module_namespace: str) -> bool:
    """判断 ID 字段是否为外键（前缀与当前模块名不匹配）。"""
    if is_fk_field(field_name):
        return True
    prefix = get_id_prefix(field_name).lower()
    ns_lower = module_namespace.lower()
    # 如果前缀在模块命名空间中找不到重合，判定为外键
    # 例如模块 guild_shop_items 中的 currency_id → currency 不在模块名中 → 外键
    if prefix and prefix not in ns_lower and ns_lower not in prefix:
        # 额外豁免：通用主键 id
        if prefix not in ("", "id"):
            return True
    return False


def is_id_field(field_name: str) -> bool:
    if is_fk_field(field_name):
        return False
    field_lower = field_name.lower()
    if field_lower in ID_FIELD_EXACT:
        return True
    if len(field_name) > 3 and field_lower.endswith(ID_FIELD_SUFFIX):
        return True
    return False


def extract_id_value(value):
    if isinstance(value, str):
        stripped = value.strip()
        if len(stripped) < 64 and not any('\u4e00' <= c <= '\u9fff' for c in stripped):
            return stripped
    elif isinstance(value, (int, float)):
        return int(value) if value == int(value) else value
    return None


def collect_primary_ids(data, module_namespace: str, max_depth=5, current_depth=0):
    """
    遍历数据表，只收集主键 ID（跳过外键）。
    返回: { bucket_key: set_of_values } 其中 bucket_key = "[ns] field"
    """
    collector = {}
    _collect_recursive(data, module_namespace, module_namespace, collector, max_depth, current_depth)
    return collector


def _collect_recursive(data, root_ns: str, current_ns: str, collector: dict, max_depth, depth):
    if depth >= max_depth or data is None:
        return

    if isinstance(data, dict):
        # module_name / module 覆盖命名空间
        for ns_key in ("module_name", "module"):
            if ns_key in data and isinstance(data[ns_key], str):
                current_ns = data[ns_key]
                break

        for key, value in data.items():
            if is_id_field(key):
                # 外键跳过
                if is_foreign_key(key, current_ns):
                    continue
                extracted = extract_id_value(value)
                if extracted is not None:
                    bucket_key = f"[{current_ns}] {key}"
                    collector.setdefault(bucket_key, set()).add(extracted)

            if key.lower() != "docs":
                child_ns = key if depth == 0 and not is_id_field(key) else current_ns
                _collect_recursive(value, root_ns, child_ns, collector, max_depth, depth + 1)

    elif isinstance(data, list):
        for item in data:
            _collect_recursive(item, root_ns, current_ns, collector, max_depth, depth + 1)


def collect_id_registry(data, module_namespace: str, max_depth=5, current_depth=0):
    """
    收集带备注名的 ID 注册表（带前缀匹配）。
    返回: list of { "id": ..., "field": ..., "display_name": ...|null, "module": ... }
    """
    registry = []
    _collect_registry_recursive(data, module_namespace, module_namespace, registry, max_depth, current_depth)
    return registry


def _collect_registry_recursive(data, root_ns: str, current_ns: str, registry: list, max_depth, depth):
    if depth >= max_depth or data is None:
        return

    if isinstance(data, dict):
        for ns_key in ("module_name", "module"):
            if ns_key in data and isinstance(data[ns_key], str):
                current_ns = data[ns_key]
                break

        for key, value in data.items():
            if is_id_field(key):
                extracted = extract_id_value(value)
                if extracted is not None and not is_foreign_key(key, current_ns):
                    display = find_display_name(data, key)
                    registry.append({
                        "module": current_ns,
                        "field": key,
                        "value": str(extracted),
                        "display_name": display,
                    })

            if key.lower() != "docs":
                child_ns = key if depth == 0 and not is_id_field(key) else current_ns
                _collect_registry_recursive(value, root_ns, child_ns, registry, max_depth, depth + 1)

    elif isinstance(data, list):
        for item in data:
            _collect_registry_recursive(item, root_ns, current_ns, registry, max_depth, depth + 1)


def compress_values(bucket: set) -> str:
    values = sorted(bucket, key=str)
    all_numeric = all(isinstance(v, (int, float)) for v in bucket)
    if all_numeric and len(bucket) >= 2:
        nums = list(bucket)
        min_val, max_val = min(nums), max(nums)
        return f"{min_val}" if min_val == max_val else f"{min_val} ~ {max_val}"
    elif all_numeric and len(bucket) == 1:
        return str(list(bucket)[0])
    str_values = sorted([str(v) for v in bucket])
    if len(str_values) <= 3:
        return ", ".join(str_values)
    return f"{', '.join(str_values[:3])} ...等 {len(str_values)} 个"


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
    all_compressed_ids = []
    file_sketches = []
    all_registry = []

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

        compressed = {}
        fk_skipped = 0
        if is_docs_file(filename):
            skipped_docs += 1
            print(f"[Codex]   [说明书] {filename} — 跳过")
        else:
            # 主键收集（外键已过滤）
            collector = collect_primary_ids(data, filename.replace(".json", ""))
            for bucket_key, value_set in collector.items():
                if value_set:
                    compressed[bucket_key] = compress_values(value_set)
                    all_compressed_ids.append((bucket_key, compressed[bucket_key]))

            # ID 注册表（带备注名）
            registry = collect_id_registry(data, filename.replace(".json", ""))
            all_registry.extend(registry)

        size_kb = os.path.getsize(filepath) / 1024
        sketch = f"- **{filename}** ({size_kb:.1f} KB)"
        if top_keys:
            sketch += f" | 顶级 Key: `{', '.join(top_keys[:10])}`"
        if modules:
            sketch += f" | 模块: {', '.join(sorted(modules)[:10])}"
        if compressed:
            items = [f"{k}: {v}" for k, v in list(compressed.items())[:10]]
            sketch += f" | 主键: {', '.join(items)}"
        file_sketches.append(sketch)

        label = "跳过(说明书)" if is_docs_file(filename) else f"{len(compressed)} 主键组"
        fk_note = f", 过滤 {fk_skipped} 外键" if fk_skipped else ""
        print(f"[Codex]   [OK] {filename} ({size_kb:.1f} KB, {len(top_keys)} keys, {len(modules)} modules, {label}{fk_note})")

    if skipped_blacklist:
        print(f"[Codex]   [过滤] 跳过 {skipped_blacklist} 个框架文件")
    if skipped_docs:
        print(f"[Codex]   [过滤] 跳过 {skipped_docs} 个说明书文件")

    # ========== 生成 project_codex.md ==========
    lines = []
    lines.append("# 项目记忆 Codex")
    lines.append("")
    lines.append("> 仅扫描业务数据表，已过滤框架文件、外键字段。")
    lines.append("> ID 已做范围压缩 / 去重截断，防止 Token 爆炸。")
    lines.append("> 主键/外键已严格区分：只记录本模块主键 ID。")
    lines.append("")

    lines.append("## 系统概览")
    if all_modules:
        lines.append(f"- 已有系统模块: {', '.join(sorted(all_modules))}")
    else:
        lines.append("- （未检测到）")
    lines.append("")

    lines.append("## 已占用的主键 ID（范围压缩 / 去重截断）")
    if all_compressed_ids:
        seen = set()
        unique = []
        for label, val in all_compressed_ids:
            if (label, val) not in seen:
                seen.add((label, val))
                unique.append((label, val))
        unique.sort(key=lambda x: str(x[0]))
        lines.append(f"- 共 {len(unique)} 组")
        for label, val in unique:
            lines.append(f"  - `{label}: {val}`")
    else:
        lines.append("- （未检测到）")
    lines.append("")

    lines.append("## 业务数据表清单")
    for sketch in file_sketches:
        lines.append(sketch)
    lines.append("")

    codex_text = "\n".join(lines)

    # ========== 生成 global_asset_registry.json ==========
    registry_dedup = {}
    for entry in all_registry:
        key = f"{entry['module']}|{entry['field']}|{entry['value']}"
        if key not in registry_dedup:
            registry_dedup[key] = {
                "module": entry["module"],
                "field": entry["field"],
                "id": entry["value"],
                "display_name": entry["display_name"],
            }
    registry_list = sorted(registry_dedup.values(), key=lambda x: (x["module"], x["field"], x["id"]))

    # ========== 保存 ==========
    os.makedirs(WORKSPACE_DIR, exist_ok=True)

    with open(CODEX_FILE, "w", encoding="utf-8") as f:
        f.write(codex_text)

    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "description": "全局资产注册表 — 记录所有业务数据表中的主键 ID 及其备注名",
            "entries": registry_list,
        }, f, ensure_ascii=False, indent=2)

    print(f"{GRN}[Codex] project_codex.md → {CODEX_FILE}{RESET}")
    print(f"{GRN}[Codex] global_asset_registry.json → {REGISTRY_FILE}{RESET}")
    print(f"[Codex]   模块: {len(all_modules)}, 主键组: {len(unique)}, 注册条目: {len(registry_list)}, 业务文件: {len(file_sketches)}")


if __name__ == "__main__":
    main()
