"""
app/infrastructure/indicators/exceptions.py
--------------------------------------------------
استثناءات واضحة لمحرك المؤشرات.
"""

from __future__ import annotations


class IndicatorError(Exception):
    """الأصل المشترك لكل أخطاء محرك المؤشرات."""


class IndicatorNotFoundError(IndicatorError):
    """اسم مؤشر غير مسجَّل في IndicatorRegistry."""

    def __init__(self, name: str) -> None:
        super().__init__(f"مؤشر غير مسجَّل: {name}")
        self.name = name


class InsufficientDataError(IndicatorError):
    """عدد الشموع المُعطى أقل من الحد الأدنى المطلوب لحساب المؤشر."""

    def __init__(self, indicator_name: str, required: int, given: int) -> None:
        super().__init__(
            f"بيانات غير كافية لحساب {indicator_name}: مطلوب {required} شمعة على الأقل، المُعطى {given}."
        )
        self.indicator_name = indicator_name
        self.required = required
        self.given = given
