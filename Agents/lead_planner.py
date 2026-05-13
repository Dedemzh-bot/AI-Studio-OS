"""
OS Lead Planner (主策划)
职责：产出 Schema（active_schema.json）和 Blueprint（blueprint.json）
负责拆解用户需求为子任务，定义各子任务间的依赖关系。
"""

class LeadPlanner:
    def __init__(self):
        self.workspace_path = ".agent_workspace"

    def plan(self, user_request: str) -> dict:
        """
        根据用户需求生成任务蓝图。
        返回 blueprint 字典，写入 blueprint.json。
        """
        raise NotImplementedError

    def define_schema(self, blueprint: dict) -> dict:
        """
        根据蓝图生成当前激活的 JSON Schema 契约。
        返回 schema 字典，写入 active_schema.json。
        """
        raise NotImplementedError
