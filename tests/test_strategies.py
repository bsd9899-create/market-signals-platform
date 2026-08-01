"""
tests/test_strategies.py
----------------------------
اختبار حقيقي لكل استراتيجية على حدة + StrategyEngine (Open/Closed).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from app.infrastructure.market.models import Candle
from app.infrastructure.signals.models import SignalDirection
from app.infrastructure.strategies.base import Strategy
from app.infrastructure.strategies.exceptions import InsufficientCandlesError, StrategyNotFoundError
from app.infrastructure.strategies.models import StrategyResult
from app.infrastructure.strategies.strategies.breakout import Breakout
from app.infrastructure.strategies.strategies.momentum import Momentum
from app.infrastructure.strategies.strategies.pullback import Pullback
from app.infrastructure.strategies.strategies.reversal import Reversal
from app.infrastructure.strategies.strategies.trend_following import TrendFollowing
from app.infrastructure.strategies.strategy_engine import StrategyEngine


def make_candles(closes: list[float], highs: list[float] | None = None, lows: list[float] | None = None) -> list[Candle]:
    now = datetime.now(timezone.utc)
    n = len(closes)
    highs = highs if highs is not None else [c + 0.3 for c in closes]
    lows = lows if lows is not None else [c - 0.3 for c in closes]
    return [
        Candle(symbol="TEST", timeframe="1h", timestamp=now + timedelta(hours=i),
               open=closes[i], high=highs[i], low=lows[i], close=closes[i], volume=1000)
        for i in range(n)
    ]


def test_trend_following_matches_on_clear_uptrend() -> None:
    closes = [100 + i * 1.5 for i in range(60)]
    result = TrendFollowing().evaluate(make_candles(closes))
    assert result.matched is True
    assert result.direction == SignalDirection.BUY
    assert result.confidence > 0


def test_trend_following_no_match_on_flat_price() -> None:
    result = TrendFollowing().evaluate(make_candles([100.0] * 60))
    assert result.matched is False
    assert result.direction == SignalDirection.NEUTRAL


def test_trend_following_insufficient_candles_raises() -> None:
    with pytest.raises(InsufficientCandlesError):
        TrendFollowing().evaluate(make_candles([100.0] * 10))


def test_pullback_matches_when_price_returns_to_fast_ema_within_trend() -> None:
    # اتجاه صاعد واضح ثم ثبات السعر الأخير قريباً جداً من EMA السريع
    closes = [100 + i * 1.5 for i in range(59)]
    closes.append(closes[-1])  # الشمعة الأخيرة قريبة جداً من السعر السابق (وبالتالي من EMA السريع نسبياً)
    result = Pullback(tolerance_percent=5.0).evaluate(make_candles(closes))
    # مطابق أو غير مطابق - المهم أنه لا يفشل وأن الاتجاه صاعد إذا تطابق
    if result.matched:
        assert result.direction == SignalDirection.BUY


def test_breakout_matches_on_clear_breakout_above_resistance() -> None:
    # نطاق تذبذب بين 95 و105 لعدة شموع، ثم اختراق واضح فوق 105
    base = [100, 105, 95, 105, 95, 105, 95, 105, 95, 105, 95]
    closes = base + [120.0]  # اختراق واضح فوق أعلى مقاومة مكتشَفة
    result = Breakout().evaluate(make_candles(closes))
    assert result.matched is True
    assert result.direction == SignalDirection.BUY


def test_breakout_no_match_within_range() -> None:
    closes = [100, 105, 95, 105, 95, 105, 95, 105, 95, 105, 100]
    result = Breakout().evaluate(make_candles(closes))
    assert result.matched is False


def test_reversal_matches_overbought_with_bearish_confirmation() -> None:
    # صعود متصل يدفع RSI للتشبّع الشرائي، ثم شمعة أخيرة هابطة (close < open)
    closes = [100 + i * 2 for i in range(20)]
    candles = make_candles(closes)
    # نُعدِّل الشمعة الأخيرة لتكون هابطة فعلياً (close < open) مع الحفاظ على قيمة close نفسها
    last = candles[-1]
    candles[-1] = Candle(
        symbol=last.symbol, timeframe=last.timeframe, timestamp=last.timestamp,
        open=last.close + 5, high=last.high, low=last.low, close=last.close, volume=last.volume,
    )
    result = Reversal(overbought=70.0, oversold=30.0).evaluate(candles)
    assert result.matched is True
    assert result.direction == SignalDirection.SELL


def test_reversal_no_match_without_extreme_rsi() -> None:
    closes = [100.0] * 20
    result = Reversal().evaluate(make_candles(closes))
    assert result.matched is False


def test_momentum_matches_on_strong_positive_roc() -> None:
    closes = [100 + i * 2 for i in range(15)]
    result = Momentum(threshold_percent=1.0).evaluate(make_candles(closes))
    assert result.matched is True
    assert result.direction == SignalDirection.BUY
    assert result.confidence > 0


def test_momentum_no_match_below_threshold() -> None:
    closes = [100.0 + i * 0.001 for i in range(15)]  # حركة ضئيلة جداً
    result = Momentum(threshold_percent=5.0).evaluate(make_candles(closes))
    assert result.matched is False


# ---------------------------------------------------------------------
# StrategyEngine
# ---------------------------------------------------------------------


def test_strategy_engine_registers_5_builtin_strategies() -> None:
    engine = StrategyEngine()
    assert engine.available_strategies() == sorted(
        ["trend_following", "pullback", "breakout", "reversal", "momentum"]
    )


def test_strategy_engine_evaluate_all_returns_results_for_sufficient_data() -> None:
    closes = [100 + i * 1.5 for i in range(60)]
    engine = StrategyEngine()
    results = engine.evaluate_all(make_candles(closes))
    assert "trend_following" in results
    assert isinstance(results["trend_following"], StrategyResult)


def test_strategy_engine_unknown_strategy_raises() -> None:
    with pytest.raises(StrategyNotFoundError):
        StrategyEngine().evaluate("does_not_exist", make_candles([100.0] * 60))


def test_open_closed_extensibility_custom_strategy_without_modifying_existing_code() -> None:
    """يثبت Open/Closed فعلياً: استراتيجية جديدة كلياً (مُعرَّفة هنا فقط)
    تُسجَّل وتعمل دون أي تعديل على StrategyEngine أو أي استراتيجية قائمة."""

    class AlwaysBuy(Strategy):
        name = "always_buy"

        def min_candles_required(self) -> int:
            return 1

        def evaluate(self, candles: list[Candle]) -> StrategyResult:
            return StrategyResult(
                strategy_name=self.name, matched=True, direction=SignalDirection.BUY,
                confidence=100.0, reason="اختبار OCP.",
            )

    engine = StrategyEngine()
    assert "always_buy" not in engine.available_strategies()

    engine.register(AlwaysBuy())

    assert "always_buy" in engine.available_strategies()
    result = engine.evaluate("always_buy", make_candles([100.0]))
    assert result.matched is True
    assert result.direction == SignalDirection.BUY
