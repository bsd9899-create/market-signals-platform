"""
app/infrastructure/market/providers/mock_provider.py
----------------------------------------------------------
MockProvider: مزود بيانات وهمي بالكامل - بيانات ثابتة/محسوبة محلياً
فقط، **بلا أي اتصال إنترنت أو API خارجي إطلاقاً**. الغرض الوحيد: اختبار
MarketService وكامل النظام دون الاعتماد على أي مزود حقيقي.

رموز معروفة ثابتة فقط (_KNOWN_SYMBOLS) - أي رمز آخر يرفع
SymbolNotFoundError، لإثبات أن معالجة الأخطاء تعمل فعلياً دون الحاجة
لأي شبكة.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loguru import logger

from app.infrastructure.market.exceptions import MarketUnavailableError, SymbolNotFoundError
from app.infrastructure.market.models import Candle, MarketStatus, Quote
from app.infrastructure.market.providers.base import MarketDataProvider

_KNOWN_SYMBOLS = ("AAPL", "MSFT", "GOOGL", "NVDA", "TSLA")
_FIXED_PRICE = 100.00


class MockProvider(MarketDataProvider):
    """simulate_unavailable=True يجعل كل الاستدعاءات ترفع
    MarketUnavailableError - مفيد لاختبار تعامل MarketService مع فشل
    المزود، دون الحاجة لأي انقطاع شبكة حقيقي."""

    def __init__(self, simulate_unavailable: bool = False) -> None:
        self.simulate_unavailable = simulate_unavailable
        self.call_counts: dict[str, int] = {
            "get_quote": 0, "get_candles": 0, "get_market_status": 0, "health_check": 0,
        }

    def _check_available(self) -> None:
        if self.simulate_unavailable:
            logger.error("MockProvider: محاكاة عدم توفر مزود البيانات.")
            raise MarketUnavailableError("محاكاة عدم توفر (simulate_unavailable=True)")

    def get_quote(self, symbol: str) -> Quote:
        self.call_counts["get_quote"] += 1
        self._check_available()
        if symbol not in _KNOWN_SYMBOLS:
            logger.warning("MockProvider.get_quote: رمز غير معروف: {}", symbol)
            raise SymbolNotFoundError(symbol)

        logger.debug("MockProvider.get_quote: {}", symbol)
        return Quote(
            symbol=symbol,
            bid=_FIXED_PRICE - 0.05,
            ask=_FIXED_PRICE + 0.05,
            last=_FIXED_PRICE,
            spread=0.10,
            timestamp=datetime.now(timezone.utc),
        )

    def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> list[Candle]:
        self.call_counts["get_candles"] += 1
        self._check_available()
        if symbol not in _KNOWN_SYMBOLS:
            logger.warning("MockProvider.get_candles: رمز غير معروف: {}", symbol)
            raise SymbolNotFoundError(symbol)

        logger.debug("MockProvider.get_candles: {} {} (limit={})", symbol, timeframe, limit)
        now = datetime.now(timezone.utc)
        candles = []
        for i in range(limit):
            base = _FIXED_PRICE + i * 0.01  # نمط ثابت متزايد بسيط - قابل للتكرار في كل استدعاء
            candles.append(
                Candle(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=now - timedelta(minutes=(limit - i)),
                    open=base,
                    high=base + 0.05,
                    low=base - 0.05,
                    close=base + 0.02,
                    volume=1000 + i,
                )
            )
        return candles

    def get_market_status(self) -> MarketStatus:
        self.call_counts["get_market_status"] += 1
        self._check_available()
        logger.debug("MockProvider.get_market_status")
        return MarketStatus(
            is_open=True, premarket=False, after_hours=False, next_open=None, next_close=None,
        )

    def health_check(self) -> bool:
        self.call_counts["health_check"] += 1
        if self.simulate_unavailable:
            logger.error("MockProvider.health_check: فشل (محاكاة عدم توفر).")
            return False
        logger.debug("MockProvider.health_check: OK")
        return True
