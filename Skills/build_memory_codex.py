"""
Build Memory Codex (全局项目记忆生成器)
职责：扫描 project_db/ → 全量重建 project_codex.md + global_asset_registry.json
【v5】超强鲁棒性：Array/Dict双重解析 + 逐文件 try-except + 全量重建模式
"""

import json
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
PROJECT_DB_DIR = os.path.join(WORKSPACE_DIR, "project_db")
CODEX_FILE = os.path.join(WORKSPACE_DIR, "project_codex.md")
REGISTRY_FILE = os.path.join(WORKSPACE_DIR, "global_asset_registry.json")

ID_FIELD_SUFFIX = "_id"
ID_FIELD_EXACT = {"skill_id", "key"}

FK_BLOCK_PATTERNS = [
    "unlock_", "require_", "prerequisite_",
    "previous_", "next_", "parent_",
    "ref_", "foreign_", "target_",
    "dependent_", "condition_",
]

NAME_SNIFF_KEYWORDS = ["name", "title", "desc", "type", "label"]
SEMANTIC_KEY_PATTERNS = [
    "_id", "name", "title", "desc", "type", "label",
    "cost", "price", "level", "amount", "duration",
    "effect", "color", "material", "style", "anchor",
    "icon", "prompt", "rich_text",
]

RED = "\033[91m"
GRN = "\033[92m"
RESET = "\033[0m"


def is_fk_field(field_name: str) -> bool:
    for p in FK_BLOCK_PATTERNS:
        if p in field_name.lower():
            return True
    return False


def is_id_field(field_name: str) -> bool:
    if is_fk_field(field_name):
        return False
    fl = field_name.lower()
    if fl in ID_FIELD_EXACT:
        return True
    return len(field_name) > 3 and fl.endswith(ID_FIELD_SUFFIX)


def extract_id_value(value):
    if isinstance(value, str) and len(value.strip()) < 64:
        return value.strip()
    if isinstance(value, (int, float)):
        return int(value) if value == int(value) else value
    return None


def has_semantic_key(item: dict) -> bool:
    for key in item:
        for pat in SEMANTIC_KEY_PATTERNS:
            if pat in key.lower():
                return True
    return False


def sniff_sibling_name(parent: dict, skip_keys: set) -> str:
    for key, value in parent.items():
        if key in skip_keys or not isinstance(value, str):
            continue
        for kw in NAME_SNIFF_KEYWORDS:
            if kw in key.lower() and value.strip() and len(value.strip()) < 128:
                return value.strip()
    return ""


def _get_primary_id(record: dict):
    for key, val in record.items():
        if key.endswith("_id") and isinstance(val, (str, int)):
            return val
    for key in ("id", "_id"):
        if key in record and isinstance(record[key], (str, int)):
            return record[key]
    return None


# ============================================================
# 压缩 Codex 用
# ============================================================

def collect_ids(data, top_name: str = "root") -> dict:
    collector = {}
    _collect(data, top_name, collector, 0)
    return collector


def _collect(data, ns: str, collector: dict, depth: int):
    if depth >= 5 or data is None:
        return

    if isinstance(data, dict):
        current_ns = ns
        for k in ("module_name", "module"):
            if k in data and isinstance(data[k], str):
                current_ns = data[k]
                break

        for key, value in data.items():
            if is_id_field(key):
                ev = extract_id_value(value)
                if ev is not None:
                    bk = f"[{current_ns}] {key}"
                    collector.setdefault(bk, {"values": set(), "names": set()})
                    collector[bk]["values"].add(ev)
                    name = sniff_sibling_name(data, {key})
                    if name:
                        collector[bk]["names"].add(name)
            if key.lower() != "docs":
                cn = key if depth == 0 and not is_id_field(key) else current_ns
                _collect(value, cn, collector, depth + 1)

    elif isinstance(data, list):
        for item in data:
            _collect(item, ns, collector, depth + 1)


def compress_bucket(bucket: dict) -> str:
    values = bucket.get("values", set())
    names = bucket.get("names", set())
    if not values:
        return "-"
    all_num = all(isinstance(v, (int, float)) for v in values)
    if len(values) == 1:
        val = list(values)[0]
        return f"{val} (备注: {', '.join(sorted(names)[:3])})" if names else str(val)
    if all_num:
        nums = sorted(values)
        vs = str(nums[0]) if nums[0] == nums[-1] else f"{nums[0]} ~ {nums[-1]}"
        if names:
            ns = ", ".join(sorted(names)[:3])
            if len(names) > 3: ns += "..."
            return f"{vs} (包含: {ns})"
        return vs
    sv = sorted(str(v) for v in values)
    return ", ".join(sv) if len(sv) <= 3 else f"{', '.join(sv[:3])} ...等 {len(sv)} 个"


# ============================================================
# Registry 明细提取
# ============================================================

def extract_records_from_list(items: list) -> list[dict]:
    """从 JSON 数组中提取所有带语义字段的 object。"""
    records = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if has_semantic_key(item):
            # 确定模块名
            mod = item.get("module_name") or item.get("module") or "unknown"
            rec = {k: v for k, v in item.items()
                   if k not in ("module_name", "module", "docs")
                   and isinstance(v, (str, int, float, bool, list))}
            if rec:
                records.append({"module": mod, "record": rec})
    return records


def extract_records_from_dict(data: dict, top_name: str) -> list[dict]:
    """从 JSON 字典中提取所有带语义字段的离散记录。"""
    records = []

    def _extract(obj, current_mod: str):
        if obj is None:
            return
        if isinstance(obj, dict):
            for k in ("module_name", "module"):
                if k in obj and isinstance(obj[k], str):
                    current_mod = obj[k]
                    break

            has_id = any(is_id_field(k) for k in obj)
            if has_id and has_semantic_key(obj) and len(obj) >= 2:
                rec = {}
                for k, v in obj.items():
                    if k in ("module_name", "module", "docs"):
                        continue
                    if isinstance(v, (str, int, float, bool, list)):
                        rec[k] = v
                    elif isinstance(v, dict) and not any(isinstance(vv, (dict, list)) for vv in v.values()):
                        rec[k] = v
                if rec:
                    records.append({"module": current_mod, "record": rec})

            for key, val in obj.items():
                if key.lower() != "docs":
                    cm = key if not is_id_field(key) and not key.isdigit() else current_mod
                    _extract(val, cm)
        elif isinstance(obj, list):
            for item in obj:
                _extract(item, current_mod)

    _extract(data, top_name)
    return records


# ============================================================
# 主流程
# ============================================================

def main():
    os.makedirs(PROJECT_DB_DIR, exist_ok=True)

    print(f"[Codex] 正在全量扫描 {PROJECT_DB_DIR}/ ...")

    try:
        all_files = sorted([
            f for f in os.listdir(PROJECT_DB_DIR)
            if f.endswith(".json") and os.path.isfile(os.path.join(PROJECT_DB_DIR, f))
        ])
    except FileNotFoundError:
        all_files = []

    all_modules = set()
    all_compressed_ids = []
    all_asset_records = []
    error_count = 0

    for filename in all_files:
        filepath = os.path.join(PROJECT_DB_DIR, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"{RED}[Codex]   [SKIP] {filename} - 无法解析: {e}{RESET}")
            error_count += 1
            continue

        base_name = filename.rsplit(".", 1)[0]

        try:
            # ---- 类型判断 ----
            if isinstance(data, list):
                # 数组结构：直接遍历每个 object
                print(f"[Codex]   [List] {filename} ({len(data)} items)")
                # Codex: 收集 ID
                collector = collect_ids(data, base_name)
                for bk, bucket in collector.items():
                    if bucket.get("values"):
                        cs = compress_bucket(bucket)
                        all_compressed_ids.append((bk, cs))
                # Registry: 提取记录
                recs = extract_records_from_list(data)
                all_asset_records.extend(recs)
                for r in recs:
                    all_modules.add(r["module"])

            elif isinstance(data, dict):
                # 字典结构：使用原递归逻辑
                top_keys = list(data.keys())
                modules_found = set()
                for tk in top_keys:
                    if isinstance(tk, str) and not tk.isdigit():
                        modules_found.add(tk)
                all_modules.update(modules_found)

                print(f"[Codex]   [Dict] {filename} ({len(top_keys)} keys, {len(modules_found)} modules)")
                # Codex: 收集 ID
                collector = collect_ids(data, base_name)
                for bk, bucket in collector.items():
                    if bucket.get("values"):
                        cs = compress_bucket(bucket)
                        all_compressed_ids.append((bk, cs))
                # Registry: 提取记录
                recs = extract_records_from_dict(data, base_name)
                all_asset_records.extend(recs)
                for r in recs:
                    all_modules.add(r["module"])

            else:
                print(f"[Codex]   [SKIP] {filename} - 不支持的数据类型: {type(data).__name__}")
                continue

        except Exception as e:
            print(f"{RED}[Codex]   [ERROR] {filename} 解析异常: {e}{RESET}")
            traceback.print_exc()
            error_count += 1
            continue

    # ========== 生成 project_codex.md (全量重建) ==========
    lines = [
        "# 项目记忆 Codex",
        "",
        "> 自动生成于 `build_memory_codex.py`，为所有 Agent 提供全局上下文。",
        "> 全量扫描 `project_db/`，范围压缩 + 名称嗅探语义备注。",
        "",
        "## 系统概览",
    ]
    if all_modules:
        lines.append(f"- 已有系统模块: {', '.join(sorted(all_modules))}")
    else:
        lines.append("- 已有系统模块: （未检测到）")
    lines.append("")

    lines.append("## 已占用的业务 ID（范围压缩 / 语义备注）")
    if all_compressed_ids:
        seen = set()
        uniq = []
        for label, val in all_compressed_ids:
            if (label, val) not in seen:
                seen.add((label, val))
                uniq.append((label, val))
        uniq.sort(key=lambda x: str(x[0]))
        lines.append(f"- 共 {len(uniq)} 组标识符")
        for label, val in uniq:
            lines.append(f"  - `{label}: {val}`")
    else:
        lines.append("- （未检测到）")
    lines.append("")

    with open(CODEX_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # ========== 生成 global_asset_registry.json (全量重建) ==========
    registry = {"modules": {}}
    for item in all_asset_records:
        mod = item["module"]
        rec = item["record"]
        if mod not in registry["modules"]:
            registry["modules"][mod] = []
        # 去重
        rh = json.dumps(rec, sort_keys=True, ensure_ascii=False)
        existing_hashes = {json.dumps(r, sort_keys=True, ensure_ascii=False) for r in registry["modules"][mod]}
        if rh not in existing_hashes:
            registry["modules"][mod].append(rec)

    # 按 ID 排序
    for mod in registry["modules"]:
        registry["modules"][mod] = sorted(
            registry["modules"][mod],
            key=lambda r: str(r.get("id", r.get(list(r.keys())[0] if r else "", "")))
        )

    with open(REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)

    total_records = sum(len(v) for v in registry["modules"].values())

    print(f"\n{GRN}[Codex] 全量重建完成:{RESET}")
    print(f"  project_codex.md → {CODEX_FILE}")
    print(f"  global_asset_registry.json → {REGISTRY_FILE}")
    print(f"  模块数: {len(registry['modules'])}, 压缩 ID 组: {len(all_compressed_ids)}, 明细记录: {total_records}")
    if error_count:
        print(f"{RED}  跳过错误文件: {error_count}{RESET}")


if __name__ == "__main__":
    main()
