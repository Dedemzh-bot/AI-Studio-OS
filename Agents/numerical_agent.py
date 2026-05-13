"""
Numerical Agent (数值策划)
职责：产出数值 JSON，强制附带模拟曲线验证数据。
"""

class NumericalAgent:
    def __init__(self):
        self.workspace_path = ".agent_workspace"

    def generate(self, task_spec: dict) -> dict:
        """
        根据任务规格生成数值方案。
        必须包含 simulation_curve 字段用于验证。
        """
        raise NotImplementedError

    def simulate(self, data: dict) -> dict:
        """运行数值模拟，返回模拟结果曲线。"""
        raise NotImplementedError
