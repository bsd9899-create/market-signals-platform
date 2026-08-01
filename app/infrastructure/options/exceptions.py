"""
app/infrastructure/options/exceptions.py
-------------------------------------------------
استثناءات واضحة لطبقة الخيارات.
"""

from __future__ import annotations


class OptionsProviderError(Exception):
    """الأصل المشترك لكل أخطاء مزوّدي بيانات الخيارات."""


class OptionsUnavailableError(OptionsProviderError):
    def __init__(self, reason: str | None = None) -> None:
        message = "بيانات الخيارات غير متاحة حالياً"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.reason = reason
