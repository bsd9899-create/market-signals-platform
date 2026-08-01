"""
app/infrastructure/news/exceptions.py
--------------------------------------------
استثناءات واضحة لطبقة الأخبار.
"""

from __future__ import annotations


class NewsProviderError(Exception):
    """الأصل المشترك لكل أخطاء مزوّدي الأخبار."""


class NewsUnavailableError(NewsProviderError):
    def __init__(self, reason: str | None = None) -> None:
        message = "الأخبار غير متاحة حالياً"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.reason = reason
