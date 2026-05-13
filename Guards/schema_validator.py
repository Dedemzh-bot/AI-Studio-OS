"""
Schema Validator (防线一：强校验)
职责：基于 active_schema.json 对 current_result.json 进行 JSON Schema 校验。
无情拦截任何不符合契约的数据，拒绝放行。
"""

import json
import os


TYPE_MAP = {
    "string": str,
    "number": (int, float),
    "integer": int,
    "boolean": bool,
    "array": list,
    "object": dict,
    "null": type(None),
}


def validate(data, schema, path: str = "$"):
    """
    严格递归校验 data 是否符合 schema 契约。
    校验顺序：类型 > 必填字段 > 多余字段 > 递归子属性

    不符合即刻 raise ValueError，错误信息精确到 JSONPath。
    """
    if not isinstance(schema, dict):
        raise ValueError(f"[{path}] Schema 本身必须是 dict 类型")

    # 跳过 meta 字段
    if "$schema" in schema:
        schema = {k: v for k, v in schema.items() if k != "$schema"}

    schema_type = schema.get("type")

    # --- 1. 类型校验 ---
    if schema_type:
        expected_types = TYPE_MAP.get(schema_type)
        if expected_types is None:
            raise ValueError(f"[{path}] Schema 中声明的 type '{schema_type}' 不支持")
        if isinstance(expected_types, tuple):
            if not isinstance(data, expected_types):
                raise ValueError(
                    f"[{path}] 类型错误: 期望 {schema_type}，实际为 {type(data).__name__}"
                )
        else:
            if type(data) is not expected_types:
                raise ValueError(
                    f"[{path}] 类型错误: 期望 {schema_type}，实际为 {type(data).__name__}"
                )

    # --- 2. 按类型深入校验 ---
    if schema_type == "object":
        _validate_object(data, schema, path)
    elif schema_type == "array":
        _validate_array(data, schema, path)
    elif schema_type == "string":
        _validate_string(data, schema, path)
    elif schema_type in ("number", "integer"):
        _validate_number(data, schema, path)

    return True


def _validate_object(data: dict, schema: dict, path: str):
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    additional = schema.get("additionalProperties", False)

    # 2a. 检查必填字段
    for field in required:
        if field not in data:
            raise ValueError(f"[{path}] 缺少必填字段: '{field}'")

    # 2b. 检查字段是否在 properties 中定义
    for key in data:
        if key not in properties:
            if not additional:
                raise ValueError(f"[{path}] 发现未声明字段: '{key}'(Schema 不允许额外属性)")

    # 2c. 递归校验每个已声明的属性
    for key, prop_schema in properties.items():
        if key in data:
            validate(data[key], prop_schema, f"{path}.{key}")


def _validate_array(data: list, schema: dict, path: str):
    items_schema = schema.get("items")
    if items_schema is None:
        return

    if isinstance(items_schema, dict):
        for i, item in enumerate(data):
            validate(item, items_schema, f"{path}[{i}]")
    elif isinstance(items_schema, list):
        for i, (item, item_sch) in enumerate(zip(data, items_schema)):
            validate(item, item_sch, f"{path}[{i}]")
        if len(data) > len(items_schema):
            for i in range(len(items_schema), len(data)):
                raise ValueError(
                    f"[{path}[{i}]] 数组超出 Schema items 定义长度({len(items_schema)})"
                )


def _validate_string(data: str, schema: dict, path: str):
    min_len = schema.get("minLength")
    max_len = schema.get("maxLength")
    pattern = schema.get("pattern")
    enum = schema.get("enum")

    if min_len is not None and len(data) < min_len:
        raise ValueError(f"[{path}] 字符串长度 {len(data)} 小于最小长度 {min_len}")
    if max_len is not None and len(data) > max_len:
        raise ValueError(f"[{path}] 字符串长度 {len(data)} 大于最大长度 {max_len}")
    if pattern is not None:
        import re
        if not re.match(pattern, data):
            raise ValueError(f"[{path}] 字符串 '{data}' 不匹配正则: {pattern}")
    if enum is not None and data not in enum:
        raise ValueError(f"[{path}] 值 '{data}' 不在枚举允许范围: {enum}")


def _validate_number(data: (int, float), schema: dict, path: str):
    minimum = schema.get("minimum")
    maximum = schema.get("maximum")
    exclusive_min = schema.get("exclusiveMinimum")
    exclusive_max = schema.get("exclusiveMaximum")
    enum = schema.get("enum")

    if minimum is not None and data < minimum:
        raise ValueError(f"[{path}] 数值 {data} 小于最小值 {minimum}")
    if maximum is not None and data > maximum:
        raise ValueError(f"[{path}] 数值 {data} 大于最大值 {maximum}")
    if exclusive_min is not None and data <= exclusive_min:
        raise ValueError(f"[{path}] 数值 {data} 未大于最小值(不含) {exclusive_min}")
    if exclusive_max is not None and data >= exclusive_max:
        raise ValueError(f"[{path}] 数值 {data} 未小于最大值(不含) {exclusive_max}")
    if enum is not None and data not in enum:
        raise ValueError(f"[{path}] 值 {data} 不在枚举允许范围: {enum}")


class SchemaValidator:
    def __init__(self):
        self.schema_path = ".agent_workspace/active_schema.json"

    def validate(self, data: dict, schema: dict | None = None) -> tuple[bool, list[str]]:
        """
        校验数据是否符合当前激活的 Schema。
        返回 (pass, errors)。
        """
        errors: list[str] = []
        try:
            if schema is None:
                schema = self.load_active_schema()
            validate(data, schema)
        except ValueError as e:
            errors.append(str(e))

        return len(errors) == 0, errors

    def load_active_schema(self) -> dict:
        """从 active_schema.json 加载当前生效的校验契约。"""
        with open(self.schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
