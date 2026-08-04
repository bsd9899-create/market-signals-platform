"""
tests/test_yahoo_provider_options.py
-------------------------------------------
اختبار حقيقي لـYahooFinanceProvider.get_best_option_contract() -> ScoredOption
(Option Score 0-100 مرجَّح: Liquidity/OpenInterest/Volume/Spread/IV) -
**بلا أي اتصال شبكة إطلاقاً**: yf.Ticker تُستبدَل بكائن وهمي (FakeTicker)
يُرجِع DataFrames جاهزة.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
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


def test_picks_highest_option_score_by_liquidity(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([
        _row(100.0, 1.0, 1.2, 1.1, volume=10, oi=5),    # سيولة ضعيفة
        _row(101.0, 1.0, 1.2, 1.1, volume=100, oi=50),  # الأعلى سيولة - يفوز
        _row(99.0, 1.0, 1.2, 1.1, volume=20, oi=10),
    ])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    result = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, reference_price=100.0)
    assert result is not None
    assert result.contract.strike == 101.0
    assert result.contract.volume == 100
    assert result.contract.open_interest == 50
    assert 0.0 <= result.score <= 100.0


def test_higher_open_interest_wins_when_liquidity_tied(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([
        _row(100.0, 1.0, 1.2, 1.1, volume=50, oi=50),   # مجموع=100
        _row(101.0, 1.0, 1.2, 1.1, volume=20, oi=80),   # مجموع=100 أيضاً - OI أعلى يفوز
    ])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    result = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, reference_price=100.0)
    assert result.contract.strike == 101.0
    assert result.contract.open_interest == 80


def test_narrower_spread_wins_when_liquidity_and_oi_tied(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([
        _row(100.0, 1.0, 1.5, 1.2, volume=50, oi=50),   # فارق واسع
        _row(101.0, 1.0, 1.1, 1.05, volume=50, oi=50),  # فارق ضيق - يفوز
    ])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    result = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, reference_price=100.0)
    assert result.contract.strike == 101.0


def test_filters_to_near_money_band_before_scoring(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([
        _row(100.0, 1.0, 1.1, 1.05, volume=5, oi=5),           # ضمن ±15% من 100
        _row(500.0, 1.0, 1.1, 1.05, volume=99999, oi=99999),   # بعيد جداً عن ATM رغم سيولته الهائلة
    ])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    result = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, reference_price=100.0)
    assert result.contract.strike == 100.0  # وليس 500 رغم سيولته الأعلى - لأنه بعيد عن ATM


def test_sell_direction_uses_puts_table(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([_row(100.0, 1.0, 1.1, 1.05, volume=10, oi=10)])
    puts = _calls_df([_row(100.0, 0.8, 0.9, 0.85, volume=20, oi=20)])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, puts)
    _patch_ticker(monkeypatch, ticker)

    result = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.SELL, reference_price=100.0)
    assert result.contract.option_type == "PUT"
    assert result.contract.bid == 0.8


def test_delta_and_greeks_never_fabricated(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([_row(100.0, 1.0, 1.1, 1.05, volume=10, oi=10)])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    result = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, reference_price=100.0)
    assert result.contract.delta is None
    assert result.contract.gamma is None
    assert result.contract.theta is None
    assert result.contract.vega is None
    assert result.contract.rho is None


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


def test_nan_bid_ask_falls_back_to_last_price_not_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """شائع في تغذية Yahoo المجانية خارج ساعات التسعير الحيّ حتى لعقود
    نشطة فعلياً: Bid/Ask يُعادان صفر/NaN بينما lastPrice حقيقي ومتوفر -
    يجب عرض lastPrice بدل صفر وهمي 0.00$ (وليس استبعاد العقد بالكامل،
    وإلا لن يُعرَض سعر حقيقي أبداً عملياً - راجع تحقق البيانات الحقيقية)."""
    calls = _calls_df([_row(100.0, math.nan, math.nan, 1.5, volume=10, oi=10)])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    result = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, 100.0)
    assert result is not None
    assert result.contract.bid == 1.5 and result.contract.ask == 1.5
    assert 0.0 <= result.score <= 100.0


def test_no_price_data_at_all_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    """لا Bid/Ask ولا lastPrice (كلها صفر/NaN) = لا بيانات سعر حقيقية
    إطلاقاً - يتراجع الاستدعاء إلى None (المسار التقديري المُوسَّم بوضوح
    في SignalFormatter بدلاً من عقد "حقيقي" وهمي بسعر 0.00$)."""
    calls = _calls_df([_row(100.0, math.nan, math.nan, 0.0, volume=10, oi=10)])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    result = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, 100.0)
    assert result is None


def test_real_bid_ask_contract_chosen_over_last_price_only_one_when_scores_favor_it(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([
        _row(100.0, math.nan, math.nan, 1.0, volume=5, oi=5),   # بلا Bid/Ask حيّ - سيولة منخفضة
        _row(101.0, 1.0, 1.02, 1.01, volume=50, oi=50),         # Bid/Ask حيّان + فارق ضيق + سيولة أعلى - يفوز
    ])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    result = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, 100.0)
    assert result is not None
    assert result.contract.strike == 101.0
    assert result.contract.bid == 1.0 and result.contract.ask == 1.02


def test_premium_above_3_dollars_excluded(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([
        _row(100.0, 4.0, 4.2, 4.1, volume=99999, oi=99999),  # سيولة عالية لكن العلاوة > 3$
        _row(101.0, 1.0, 1.1, 1.05, volume=10, oi=10),        # ضمن سقف 3$ - يجب اختياره
    ])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    result = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, 100.0)
    assert result is not None
    assert result.contract.strike == 101.0


def test_all_real_quotes_above_3_dollars_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = _calls_df([_row(100.0, 4.0, 4.2, 4.1, volume=10, oi=10)])
    ticker = _FakeTicker("AAPL", ("2026-08-07",), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    assert YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, 100.0) is None


def test_picks_expiration_after_today_skipping_0dte(monkeypatch: pytest.MonkeyPatch) -> None:
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    future_str = (datetime.now(timezone.utc) + pd.Timedelta(days=5)).strftime("%Y-%m-%d")
    calls = _calls_df([_row(100.0, 1.0, 1.1, 1.05, volume=10, oi=10)])
    ticker = _FakeTicker("AAPL", (today_str, future_str), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    result = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, 100.0)
    assert result is not None
    assert result.contract.expiration == future_str


def test_picks_first_expiration_when_none_are_future(monkeypatch: pytest.MonkeyPatch) -> None:
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    calls = _calls_df([_row(100.0, 1.0, 1.1, 1.05, volume=10, oi=10)])
    ticker = _FakeTicker("AAPL", (today_str,), calls, pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)

    result = YahooFinanceProvider().get_best_option_contract("AAPL", SignalDirection.BUY, 100.0)
    assert result is not None
    assert result.contract.expiration == today_str


# ---------------------------------------------------------------------
# _option_score - وحدات القياس البحتة
# ---------------------------------------------------------------------


def test_option_score_high_liquidity_narrow_spread_moderate_iv_scores_high() -> None:
    score = YahooFinanceProvider._option_score(
        volume=5000, open_interest=2000, bid=1.0, ask=1.02, implied_volatility=0.375,
    )
    assert score > 90.0


def test_option_score_illiquid_wide_spread_scores_low() -> None:
    score = YahooFinanceProvider._option_score(
        volume=0, open_interest=0, bid=0.05, ask=0.50, implied_volatility=0.0,
    )
    assert score < 20.0


def test_option_score_always_within_bounds() -> None:
    score = YahooFinanceProvider._option_score(
        volume=999999, open_interest=999999, bid=1.0, ask=1.0, implied_volatility=5.0,
    )
    assert 0.0 <= score <= 100.0
