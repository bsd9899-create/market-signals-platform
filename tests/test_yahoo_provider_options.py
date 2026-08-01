"""
tests/test_yahoo_provider_options.py
-------------------------------------------
اختبار حقيقي لمنطق ترتيب العقود في
YahooFinanceProvider.get_best_option_contract() - **بلا أي اتصال شبكة
إطلاقاً**: yf.Ticker تُستبدَل بكائن وهمي (FakeTicker) يُرجِع
DataFrames جاهزة، لإثبات أن الترتيب (سيولة -> OpenInterest -> Volume ->
أضيق Bid/Ask) يعمل فعلياً - وليس تخميناً.
"""

from __future__ import annotations

from types import SimpleNamespace

import pandas as pd
import pytest

from app.infrastructure.market.providers import yahoo_provider as yahoo_provider_module
from app.infrastructure.market.providers.yahoo_provider import YahooFinanceProvider
from app.infrastructure.signals.models import SignalDirection


def _calls_df(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows)


class _FakeTicker:
    def __init__(self, symbol: str, expirations: tuple[str, ...], calls: pd.DataFrame, puts: pd.DataFrame) -> None:
        self.symbol = symbol
        self.options = expirations
        self._calls = calls
        self._puts = puts

    def option_chain(self, expiration: str):
        return SimpleNamespace(calls=self._calls, puts=self._puts)


def _patch_ticker(monkeypatch: pytest.MonkeyPatch, ticker: _FakeTicker) -> None:
    monkeypatch.setattr(yahoo_provider_module.yf, "Ticker", lambda symbol: ticker)


def _row(strike, bid, ask, last, volume, oi, iv=0.3):
    return {"strike": strike, "bid": bid, "ask": ask, "lastPrice": last, "volume": volume, "openInterest": oi, "impliedVolatility": iv}


def test_picks_highest_liquidity_first(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([
        _row(100.0, 1.0, 1.2, 1.1, volume=10, oi=5),    # liquidity=15
        _row(101.0, 1.0, 1.2, 1.1, volume=100, oi=50),  # liquidity=150 - الأفضل
        _row(99.0, 1.0, 1.2, 1.1, volume=20, oi=10),    # liquidity=30
    ])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    contract = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, reference_price=100.0)
    assert contract is not None
    assert contract.strike == 101.0
    assert contract.volume == 100
    assert contract.open_interest == 50


def test_tie_on_liquidity_breaks_by_open_interest_then_volume(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([
        _row(100.0, 1.0, 1.2, 1.1, volume=50, oi=50),   # liquidity=100, oi=50
        _row(101.0, 1.0, 1.2, 1.1, volume=20, oi=80),   # liquidity=100, oi=80 - الأعلى OI يفوز عند تعادل السيولة
    ])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    contract = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, reference_price=100.0)
    assert contract.strike == 101.0
    assert contract.open_interest == 80


def test_tie_on_liquidity_and_oi_breaks_by_narrowest_spread(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([
        _row(100.0, 1.0, 1.5, 1.2, volume=50, oi=50),   # spread=0.5
        _row(101.0, 1.0, 1.1, 1.05, volume=50, oi=50),  # spread=0.1 - الأضيق يفوز
    ])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    contract = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, reference_price=100.0)
    assert contract.strike == 101.0


def test_filters_to_near_money_band_before_ranking(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([
        _row(100.0, 1.0, 1.1, 1.05, volume=5, oi=5),      # ضمن ±15% من 100 - داخل النطاق
        _row(500.0, 1.0, 1.1, 1.05, volume=99999, oi=99999),  # بعيد جداً عن ATM رغم سيولته الهائلة
    ])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    contract = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, reference_price=100.0)
    assert contract.strike == 100.0  # وليس 500 رغم سيولته الأعلى - لأنه بعيد عن ATM


def test_sell_direction_uses_puts_table(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([_row(100.0, 1.0, 1.1, 1.05, volume=10, oi=10)])
    puts = _calls_df([_row(100.0, 0.8, 0.9, 0.85, volume=20, oi=20)])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, puts)
    _patch_ticker(monkeypatch, ticker)

    contract = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.SELL, reference_price=100.0)
    assert contract.option_type == "PUT"
    assert contract.bid == 0.8


def test_no_expirations_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    ticker = _FakeTicker("UNKNOWN", (), pd.DataFrame(), pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)
    assert YahooFinanceProvider().get_best_option_contract("UNKNOWN", SignalDirection.BUY, 100.0) is None


def test_empty_chain_table_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    ticker = _FakeTicker("AAPL", ("2026-08-07",), pd.DataFrame(), pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)
    assert YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, 100.0) is None


def test_expirations_fetch_failure_returns_none_not_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    class _BrokenTicker:
        @property
        def options(self):
            raise RuntimeError("network down")

    monkeypatch.setattr(yahoo_provider_module.yf, "Ticker", lambda symbol: _BrokenTicker())
    assert YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, 100.0) is None


def test_nan_bid_ask_treated_as_zero_not_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    import math
    calls = _calls_df([_row(100.0, math.nan, math.nan, 1.0, volume=10, oi=10)])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    contract = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, 100.0)
    assert contract is not None
    assert contract.bid == 0.0
    assert contract.ask == 0.0
