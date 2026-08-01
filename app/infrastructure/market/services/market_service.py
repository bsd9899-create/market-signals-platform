"""
app/infrastructure/market/services/market_service.py
----------------------------------------------------------
MarketService: يتعامل حصراً مع واجهة MarketDataProvider (لا يعرف شيئاً
عن أي مزود فعلي) - يضيف فوقها فقط تخزيناً مؤقتاً (TTLCache) وتسجيلاً
(Loguru). تبديل المزود لاحقاً:

    provider = MockProvider()
    service = MarketService(provider)

    # لاحقاً، بلا أي تعديل آخر:
    provider = PolygonProvider(...)  # مثال مستقبلي فقط
    service = MarketService(provider)
"""

from __future__ import annotations

from loguru import logger

from app.infrastructure.market.cache import TTLCache
from app.infrastructure.market.models import Candle, MarketStatus, Quote
from app.infrastructure.market.providers.base import MarketDataProvider


class MarketService:
    def __init__(self, provider: MarketDataProvider, cache_ttl_seconds: float = 30.0) -> None:
        self._provider = provider
        self._cache = TTLCache(default_ttl_seconds=cache_ttl_seconds)

    def get_quote(self, symbol: str) -> Quote:
        cache_key = f"quote:{symbol}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug("MarketService.get_quote: {} من الذاكرة المؤقتة", symbol)
            return cached

        quote = self._provider.get_quote(symbol)
        self._cache.set(cache_key, quote)
        logger.info("MarketService.get_quote: {} عبر {}", symbol, type(self._provider).__name__)
        return quote

    def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> list[Candle]:
        cache_key = f"candles:{symbol}:{timeframe}:{limit}"
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug("MarketService.get_candles: {} {} من الذاكرة المؤقتة", symbol, timeframe)
            return cached

        candles = self._provider.get_candles(symbol, timeframe, limit)
        self._cache.set(cache_key, candles)
        logger.info(
            "MarketService.get_candles: {} {} ({} شمعة) عبر {}",
            symbol, timeframe, len(candles), type(self._provider).__name__,
        )
        return candles

    def get_market_status(self) -> MarketStatus:
        cache_key = "market_status"
        cached = self._cache.get(cache_key)
        if cached is not None:
            logger.debug("MarketService.get_market_status: من الذاكرة المؤقتة")
            return cached

        status = self._provider.get_market_status()
        self._cache.set(cache_key, status)
        logger.info("MarketService.get_market_status: is_open={}", status.is_open)
        return status

    def health_check(self) -> bool:
        result = self._provider.health_check()
        logger.info("MarketService.health_check: {} -> {}", type(self._provider).__name__, result)
        return result

    def clear_cache(self) -> None:
        self._cache.clear()
        logger.debug("MarketService: تم تفريغ الذاكرة المؤقتة بالكامل.")
