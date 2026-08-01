"""
app/infrastructure/market/providers/base.py
--------------------------------------------------
MarketDataProvider: الواجهة المجرَّدة (Abstract Base Class) التي يجب
أن يطبّقها أي مزود بيانات سوق - حالي (MockProvider) أو مستقبلي (مثال:
Polygon حقيقياً). MarketService لا يتعامل إلا مع هذه الواجهة، أبداً مع
مزوّد فعلي مباشرة - هذا ما يسمح بتبديل المزود لاحقاً بدون تعديل أي كود
آخر (راجع services/market_service.py).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.infrastructure.market.models import Candle, MarketStatus, Quote


class MarketDataProvider(ABC):
    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        """يُرجع آخر عرض سعر (Quote) لرمز معيّن."""

    @abstractmethod
    def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> list[Candle]:
        """يُرجع حتى limit شمعة سعرية (الأحدث أولاً أو أخيراً - حسب
        المزود، لكن يجب أن يكون الترتيب ثابتاً ومُوثَّقاً في كل مزود)."""

    @abstractmethod
    def get_market_status(self) -> MarketStatus:
        """يُرجع حالة السوق اللحظية."""

    @abstractmethod
    def health_check(self) -> bool:
        """يتأكد أن المزود يعمل فعلياً (اتصال حي/بيانات وهمية جاهزة) -
        True إذا كان جاهزاً للاستخدام."""
