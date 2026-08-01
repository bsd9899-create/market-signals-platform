"""
tests/test_market.py
------------------------
اختبار حقيقي (pytest) لطبقة بيانات السوق بالكامل: النماذج (Quote/
Candle/MarketStatus)، TTLCache، MockProvider، وMarketService - **بلا
أي اتصال إنترنت إطلاقاً** (MockProvider وحده، بيانات ثابتة/محسوبة محلياً).

التشغيل: pytest tests/test_market.py -v   (من جذر المشروع)
"""

from __future__ import annotations

import time
from datetime import datetime, timezone

import pytest

from app.infrastructure.market.cache import TTLCache
from app.infrastructure.market.exceptions import MarketUnavailableError, SymbolNotFoundError
from app.infrastructure.market.models import Candle, MarketStatus, Quote
from app.infrastructure.market.providers import MockProvider
from app.infrastructure.market.services import MarketService

# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------


def test_quote_model_fields() -> None:
    now = datetime.now(timezone.utc)
    quote = Quote(symbol="AAPL", bid=99.95, ask=100.05, last=100.00, spread=0.10, timestamp=now)
    assert quote.symbol == "AAPL"
    assert quote.bid == 99.95
    assert quote.ask == 100.05
    assert quote.last == 100.00
    assert quote.spread == 0.10
    assert quote.timestamp == now


def test_candle_model_fields() -> None:
    now = datetime.now(timezone.utc)
    candle = Candle(
        symbol="AAPL", timeframe="1m", timestamp=now,
        open=100.0, high=101.0, low=99.5, close=100.5, volume=1000,
    )
    assert candle.symbol == "AAPL"
    assert candle.timeframe == "1m"
    assert candle.high >= candle.low
    assert candle.volume == 1000


def test_market_status_model_fields() -> None:
    status = MarketStatus(is_open=True, premarket=False, after_hours=False, next_open=None, next_close=None)
    assert status.is_open is True
    assert status.premarket is False
    assert status.next_open is None


def test_models_are_immutable() -> None:
    """Dataclasses مُجمَّدة (frozen=True) - أي محاولة تعديل بعد الإنشاء تفشل."""
    quote = Quote(symbol="AAPL", bid=1, ask=2, last=1.5, spread=1, timestamp=datetime.now(timezone.utc))
    with pytest.raises(Exception):  # dataclasses.FrozenInstanceError
        quote.bid = 999  # type: ignore[misc]


# ---------------------------------------------------------------------
# TTLCache
# ---------------------------------------------------------------------


def test_cache_set_and_get() -> None:
    cache = TTLCache(default_ttl_seconds=60)
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"


def test_cache_missing_key_returns_none() -> None:
    cache = TTLCache()
    assert cache.get("nonexistent") is None


def test_cache_clear() -> None:
    cache = TTLCache()
    cache.set("a", 1)
    cache.set("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None
    assert len(cache) == 0


def test_cache_expiration() -> None:
    """يثبت انتهاء الصلاحية فعلياً - TTL قصير جداً (0.05 ثانية) + انتظار حقيقي قصير."""
    cache = TTLCache(default_ttl_seconds=0.05)
    cache.set("short_lived", "value")
    assert cache.get("short_lived") == "value"  # لم تنتهِ الصلاحية بعد
    time.sleep(0.1)
    assert cache.get("short_lived") is None  # انتهت الصلاحية فعلياً


def test_cache_per_key_ttl_overrides_default() -> None:
    cache = TTLCache(default_ttl_seconds=60)
    cache.set("quick", "value", ttl_seconds=0.05)
    time.sleep(0.1)
    assert cache.get("quick") is None


# ---------------------------------------------------------------------
# MockProvider
# ---------------------------------------------------------------------


def test_mock_provider_get_quote_known_symbol() -> None:
    provider = MockProvider()
    quote = provider.get_quote("AAPL")
    assert isinstance(quote, Quote)
    assert quote.symbol == "AAPL"
    assert quote.ask > quote.bid


def test_mock_provider_get_quote_unknown_symbol_raises() -> None:
    provider = MockProvider()
    with pytest.raises(SymbolNotFoundError):
        provider.get_quote("UNKNOWN_XYZ")


def test_mock_provider_get_candles() -> None:
    provider = MockProvider()
    candles = provider.get_candles("AAPL", "1m", limit=10)
    assert len(candles) == 10
    assert all(isinstance(c, Candle) for c in candles)
    assert all(c.symbol == "AAPL" and c.timeframe == "1m" for c in candles)


def test_mock_provider_get_candles_unknown_symbol_raises() -> None:
    provider = MockProvider()
    with pytest.raises(SymbolNotFoundError):
        provider.get_candles("UNKNOWN_XYZ", "1m")


def test_mock_provider_get_market_status() -> None:
    provider = MockProvider()
    status = provider.get_market_status()
    assert isinstance(status, MarketStatus)


def test_mock_provider_health_check() -> None:
    provider = MockProvider()
    assert provider.health_check() is True


def test_mock_provider_simulate_unavailable() -> None:
    provider = MockProvider(simulate_unavailable=True)
    assert provider.health_check() is False
    with pytest.raises(MarketUnavailableError):
        provider.get_quote("AAPL")
    with pytest.raises(MarketUnavailableError):
        provider.get_candles("AAPL", "1m")
    with pytest.raises(MarketUnavailableError):
        provider.get_market_status()


def test_mock_provider_no_network_dependency() -> None:
    """تأكيد بنيوي: MockProvider لا يستورد أي مكتبة HTTP/شبكة."""
    import inspect

    from app.infrastructure.market.providers import mock_provider

    source = inspect.getsource(mock_provider)
    for forbidden in ("requests", "httpx", "urllib", "socket", "aiohttp"):
        assert forbidden not in source


# ---------------------------------------------------------------------
# MarketService (Dependency Injection على MarketDataProvider فقط)
# ---------------------------------------------------------------------


def test_market_service_get_quote_delegates_to_provider() -> None:
    provider = MockProvider()
    service = MarketService(provider)
    quote = service.get_quote("AAPL")
    assert quote.symbol == "AAPL"
    assert provider.call_counts["get_quote"] == 1


def test_market_service_caches_quote() -> None:
    """يثبت أن الاستدعاء الثاني لنفس الرمز يأتي من الذاكرة المؤقتة -
    لا يزيد عداد استدعاءات المزود."""
    provider = MockProvider()
    service = MarketService(provider, cache_ttl_seconds=60)

    service.get_quote("AAPL")
    service.get_quote("AAPL")
    service.get_quote("AAPL")

    assert provider.call_counts["get_quote"] == 1  # وليس 3


def test_market_service_cache_expires_and_calls_provider_again() -> None:
    provider = MockProvider()
    service = MarketService(provider, cache_ttl_seconds=0.05)

    service.get_quote("AAPL")
    time.sleep(0.1)
    service.get_quote("AAPL")

    assert provider.call_counts["get_quote"] == 2


def test_market_service_get_candles_delegates_and_caches() -> None:
    provider = MockProvider()
    service = MarketService(provider, cache_ttl_seconds=60)

    candles1 = service.get_candles("AAPL", "1m", limit=5)
    candles2 = service.get_candles("AAPL", "1m", limit=5)

    assert len(candles1) == 5
    assert candles1 == candles2
    assert provider.call_counts["get_candles"] == 1


def test_market_service_get_market_status_delegates_and_caches() -> None:
    provider = MockProvider()
    service = MarketService(provider, cache_ttl_seconds=60)

    service.get_market_status()
    service.get_market_status()

    assert provider.call_counts["get_market_status"] == 1


def test_market_service_health_check_delegates() -> None:
    provider = MockProvider()
    service = MarketService(provider)
    assert service.health_check() is True
    assert provider.call_counts["health_check"] == 1


def test_market_service_health_check_reflects_provider_failure() -> None:
    provider = MockProvider(simulate_unavailable=True)
    service = MarketService(provider)
    assert service.health_check() is False


def test_market_service_clear_cache() -> None:
    provider = MockProvider()
    service = MarketService(provider, cache_ttl_seconds=60)

    service.get_quote("AAPL")
    service.clear_cache()
    service.get_quote("AAPL")

    assert provider.call_counts["get_quote"] == 2  # أُعيد الاستدعاء بعد التفريغ


def test_market_service_swap_provider_no_other_code_changes() -> None:
    """يثبت متطلب Dependency Injection حرفياً: تبديل المزود بدون أي
    تعديل على MarketService أو طريقة استخدامه."""
    provider = MockProvider()
    service = MarketService(provider)
    assert service.get_quote("AAPL").symbol == "AAPL"

    another_provider = MockProvider()  # لاحقاً: أي MarketDataProvider آخر
    another_service = MarketService(another_provider)
    assert another_service.get_quote("MSFT").symbol == "MSFT"
