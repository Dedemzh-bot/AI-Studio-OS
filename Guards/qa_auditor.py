"""
QA Auditor (防线二：双重否决 Double-Veto)
职责：对通过 Schema 校验的数据进行逻辑审查。
一旦发现逻辑瑕疵（如数值溢出、死循环条件、矛盾规则等），
必须强制挂起拦截，绝不让被拒的废案流入后续环节。
"""

class QAAuditor:
    def __init__(self):
        self.veto_threshold = 0.0  # 否决阈值

    def audit(self, data: dict, context: dict) -> tuple[bool, str]:
        """
        双重否决审计。
        返回 (pass, reason)。
        若 pass=False，reason 需写明拦截原因。
        """
        raise NotImplementedError

    def veto(self, reason: str) -> tuple[bool, str]:
        """执行否决，返回拦截信号和原因。"""
        return False, reason
