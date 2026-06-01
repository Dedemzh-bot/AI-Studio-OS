"""
Config Splitter (JSON 自动化拆表与合并)
职责：读取数值策划输出的 docs + data → 按模块拆分为独立的 Excel/ JSON 文件
支持跨系统追加合并（同主键覆盖更新，新主键追加）
"""

import json
import os
import sys

FILE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(FILE_DIR)
sys.path.insert(0, ROOT_DIR)

WORKSPACE_DIR = os.path.join(ROOT_DIR, ".agent_workspace")
DOCS_FILE = os.path.join(WORKSPACE_DIR, "system_numerical_docs.json")
DATA_FILE = os.path.join(WORKSPACE_DIR, "system_numerical_data.json")
EXCEL_DIR = os.path.join(ROOT_DIR, "Excel")


def load_json(path: str) -> dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def flatten_to_records(data) -> list[dict]:
    """将 continuous_formulas / discrete_milestones / 数组 / 扁平字典展平为记录列表"""
    if isinstance(data, list):
        return data
    if not isinstance(data, dict):
        return []

    records = []

    # continuous_formulas: 提取为 parameters 记录
    cf = data.get("continuous_formulas", {})
    if cf and isinstance(cf, dict):
        params = {}
        for key, val in cf.items():
            if isinstance(val, dict):
                for sub_k, sub_v in val.items():
                    params[f"{key}.{sub_k}"] = sub_v
            else:
                params[key] = val
        if params:
            records.append(params)

    # discrete_milestones: 每个里程碑是一条记录
    dm = data.get("discrete_milestones", {})
    if dm and isinstance(dm, dict):
        for level, milestone in dm.items():
            if isinstance(milestone, dict):
                entry = {"level": int(level) if level.isdigit() else level}
                entry.update(milestone)
                records.append(entry)

    # 扁平字典（非公式/里程碑结构）直接当单条记录
    has_struct = bool(cf) or bool(dm)
    if not has_struct and data:
        flat = {}
        for k, v in data.items():
            if isinstance(v, (str, int, float, bool, type(None))):
                flat[k] = v
        if flat:
            records.append(flat)

    return records


def get_primary_id(record: dict) -> str | None:
    """取记录的第一个字段作为主键"""
    if not record:
        return None
    first_val = list(record.values())[0]
    return str(first_val)


def merge_records(old_data: list, new_data: list) -> list:
    """合并：同主键覆盖更新，新主键追加"""
    if not new_data:
        return old_data

    old_index = {}
    for i, rec in enumerate(old_data):
        pid = get_primary_id(rec)
        if pid is not None:
            old_index[pid] = i

    for rec in new_data:
        pid = get_primary_id(rec)
        if pid is not None and pid in old_index:
            old_data[old_index[pid]] = rec
        else:
            old_data.append(rec)

    return old_data


def main():
    data = load_json(DATA_FILE)
    docs = load_json(DOCS_FILE)

    if not data:
        print("[ConfigSplitter] system_numerical_data.json 为空或不存在，跳过")
        return

    field_dict = docs.get("field_dictionary", {})
    os.makedirs(EXCEL_DIR, exist_ok=True)

    total_modules = 0
    total_merged = 0
    total_new = 0

    for module_name, module_data in data.items():
        if isinstance(module_data, list):
            records = module_data
        elif isinstance(module_data, dict):
            records = flatten_to_records(module_data)
        else:
            continue
        if not records:
            continue

        # 构建 _metadata
        module_fields = set()
        for rec in records:
            module_fields.update(rec.keys())
        metadata = {"module": module_name, "fields": {}}
        for f in sorted(module_fields):
            if f in field_dict:
                metadata["fields"][f] = field_dict[f]
            else:
                metadata["fields"][f] = f"【待补充】{f}"

        new_entry = {"_metadata": metadata, "data": records}

        out_path = os.path.join(EXCEL_DIR, f"{module_name}.json")
        if os.path.exists(out_path):
            existing = load_json(out_path)
            old_data = existing.get("data", []) if isinstance(existing, dict) else []
            merged = merge_records(old_data, records)
            existing["data"] = merged
            existing["_metadata"]["fields"].update(metadata["fields"])
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, ensure_ascii=False, indent=2)
            total_merged += len([r for r in records if get_primary_id(r) in {
                get_primary_id(o) for o in old_data}])
            total_new += len(records) - total_merged
            print(f"[ConfigSplitter] 合并: {module_name}.json ({total_merged} 覆盖, {total_new} 新增)")
        else:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(new_entry, f, ensure_ascii=False, indent=2)
            print(f"[ConfigSplitter] 新建: {module_name}.json ({len(records)} 条)")
            total_new += len(records)

        total_modules += 1

    print(f"[ConfigSplitter] 完成: {total_modules} 个模块, {total_new} 条记录 → {EXCEL_DIR}")


if __name__ == "__main__":
    main()
