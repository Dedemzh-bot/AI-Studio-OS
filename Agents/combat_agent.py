"""
Combat Agent (战斗策划)
职责：负责战斗机制设定。无权写引擎代码，只产出战斗设计文档/JSON。
"""

class CombatAgent:
    def __init__(self):
        self.workspace_path = ".agent_workspace"

    def design_mechanics(self, task_spec: dict) -> dict:
        """
        根据任务规格设计战斗机制。
        产出战斗规则 JSON，不涉及代码实现。
        """
        raise NotImplementedError

    def generate_skill_table(self, mechanics: dict) -> dict:
        """基于机制设计生成技能数据表。"""
        raise NotImplementedError
