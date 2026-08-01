"""
app/infrastructure/strategies/exceptions.py
--------------------------------------------------
استثناءات واضحة لمحرك الاستراتيجيات.
"""

from __future__ import annotations


class StrategyError(Exception):
    """الأصل المشترك لكل أخطاء محرك الاستراتيجيات."""


class StrategyNotFoundError(StrategyError):
    def __init__(self, name: str) -> None:
        super().__init__(f"استراتيجية غير مسجَّلة: {name}")
        self.name = name


class InsufficientCandlesError(StrategyError):
    def __init__(self, strategy_name: str, required: int, given: int) -> None:
        super().__init__(
            f"بيانات غير كافية لاستراتيجية {strategy_name}: مطلوب {required} شمعة، المُعطى {given}."
        )
        self.strategy_name = strategy_name
        self.required = required
        self.given = given
