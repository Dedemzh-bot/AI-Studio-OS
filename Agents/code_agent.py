"""
Code Agent (程序执行)
职责：机械化翻译 JSON 为 Godot GDScript。不进行创意设计，只做纯翻译。
"""

class CodeAgent:
    def __init__(self):
        self.workspace_path = ".agent_workspace"

    def translate(self, spec: dict) -> str:
        """
        将设计 JSON 翻译为 GDScript 代码。
        输入必须已经通过 schema 校验。
        """
        raise NotImplementedError

    def generate_scene(self, spec: dict, template: str = "") -> str:
        """基于规格生成 Godot 场景文件内容。"""
        raise NotImplementedError
