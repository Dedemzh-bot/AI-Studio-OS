"""Deterministic QA guard used before the LLM consistency audit."""

import json
import os
from collections import Counter
from typing import Any


class QAAuditor:
    """Catch structural failures with code before asking an LLM to review semantics."""

    REQUIRED_FILES = {
        "system_design_detail.md": "system_planner",
        "system_schema.json": "schema_translator",
        "ui_interaction_blueprint.md": "ux_agent",
        "system_numerical_data.json": "numerical_planner",
        "system_numerical_docs.json": "numerical_planner",
        "tech_blueprint.md": "tech_architect",
    }
    JSON_FILES = {
        "system_schema.json",
        "system_numerical_data.json",
        "system_numerical_docs.json",
    }
    ID_KEYS = ("id", "ID", "item_id", "config_id", "skill_id", "system_id")

    def audit(self, data: dict, context: dict) -> tuple[bool, str]:
        """Compatibility API for callers that already have parsed data."""
        issues = self._validate_value(data, "$")
        return (not issues, "\n".join(issues) if issues else "确定性 QA 通过")

    def audit_workspace(self, workspace_dir: str) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        parsed: dict[str, Any] = {}

        for filename, agent in self.REQUIRED_FILES.items():
            path = os.path.join(workspace_dir, filename)
            if not os.path.isfile(path) or os.path.getsize(path) < 10:
                issues.append(self._issue(
                    agent, filename, "$", f"必需交付物缺失或为空: {filename}",
                    f"重新生成 {filename}",
                ))
                continue

            if filename in self.JSON_FILES:
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        parsed[filename] = json.load(f)
                except (OSError, json.JSONDecodeError) as exc:
                    issues.append(self._issue(
                        agent, filename, "$", f"JSON 无法解析: {exc}",
                        "重新输出合法、完整的 JSON",
                    ))

        schema = parsed.get("system_schema.json")
        if schema is not None and (not isinstance(schema, (dict, list)) or not schema):
            issues.append(self._issue(
                "schema_translator", "system_schema.json", "$",
                "系统 Schema 根节点必须是非空对象或数组", "输出非空的系统 Schema",
            ))

        numerical = parsed.get("system_numerical_data.json")
        if numerical is not None:
            if not isinstance(numerical, dict) or not numerical:
                issues.append(self._issue(
                    "numerical_planner", "system_numerical_data.json", "$",
                    "数值配表根节点必须是非空对象", "按模块重新生成非空数值配表",
                ))
            else:
                issues.extend(self._find_duplicate_ids(numerical))

        return issues

    def _find_duplicate_ids(self, data: Any) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []

        def walk(value: Any, path: str):
            if isinstance(value, dict):
                for key, child in value.items():
                    walk(child, f"{path}.{key}")
            elif isinstance(value, list):
                found: list[tuple[str, Any]] = []
                for index, child in enumerate(value):
                    if isinstance(child, dict):
                        for key in self.ID_KEYS:
                            if key in child and isinstance(child[key], (str, int)):
                                found.append((f"{path}[{index}].{key}", child[key]))
                                break
                    walk(child, f"{path}[{index}]")
                counts = Counter(value for _path, value in found)
                duplicates = {value for value, count in counts.items() if count > 1}
                issues.extend(
                    self._issue(
                        "numerical_planner", "system_numerical_data.json", item_path,
                        f"同一记录列表中检测到重复主键值: {item_value}", "为重复记录分配唯一主键",
                    )
                    for item_path, item_value in found if item_value in duplicates
                )

        walk(data, "$")
        return issues

    def _validate_value(self, value: Any, path: str) -> list[str]:
        errors: list[str] = []
        if isinstance(value, dict):
            for key, child in value.items():
                errors.extend(self._validate_value(child, f"{path}.{key}"))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                errors.extend(self._validate_value(child, f"{path}[{index}]"))
        elif isinstance(value, str) and not value.strip():
            errors.append(f"{path}: 字符串为空")
        return errors

    @staticmethod
    def _issue(agent: str, target: str, anchor: str, problem: str, suggestion: str) -> dict:
        return {
            "responsible_agent": agent,
            "target_file": target,
            "anchor": anchor,
            "problem_description": problem,
            "fix_suggestion": suggestion,
            "severity": "critical",
            "source": "deterministic_qa",
        }
