"""
app/infrastructure/market/exceptions.py
--------------------------------------------
استثناءات واضحة لطبقة بيانات السوق - أي Provider مستقبلي (Polygon،
Alpaca، إلخ) يجب أن يرفع هذه الاستثناءات نفسها بدل استثناءات مكتبته
الخاصة، حتى يبقى MarketService مستقلاً عن تفاصيل أي مزود.
"""

from __future__ import annotations


class MarketProviderError(Exception):
    """الأصل المشترك لكل أخطاء مزوّدي بيانات السوق."""


class SymbolNotFoundError(MarketProviderError):
    """الرمز (Symbol) غير معروف/غير مدعوم من المزود الحالي."""

    def __init__(self, symbol: str) -> None:
        super().__init__(f"الرمز غير موجود: {symbol}")
        self.symbol = symbol


class MarketUnavailableError(MarketProviderError):
    """تعذّر الوصول لمزوّد بيانات السوق (انقطاع/عطل مؤقت)."""

    def __init__(self, reason: str | None = None) -> None:
        message = "بيانات السوق غير متاحة حالياً"
        if reason:
            message += f": {reason}"
        super().__init__(message)
        self.reason = reason
