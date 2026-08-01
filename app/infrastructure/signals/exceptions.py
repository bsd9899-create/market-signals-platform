"""
app/infrastructure/signals/exceptions.py
---------------------------------------------
استثناءات واضحة لمحرك الإشارات.
"""

from __future__ import annotations


class SignalEngineError(Exception):
    """الأصل المشترك لكل أخطاء محرك الإشارات."""


class InsufficientCandlesError(SignalEngineError):
    def __init__(self, required: int, given: int) -> None:
        super().__init__(f"بيانات غير كافية لتوليد إشارة: مطلوب {required} شمعة على الأقل، المُعطى {given}.")
        self.required = required
        self.given = given
