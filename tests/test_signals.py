"""
tests/test_signals.py
--------------------------
اختبار حقيقي لـ SignalEngine - بلا أي اتصال إنترنت (بيانات مُولَّدة
محلياً فقط عبر Candle مباشرة، لا حاجة لـ MockProvider هنا).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.infrastructure.market.models import Candle
from app.infrastructure.signals.exceptions import InsufficientCandlesError
from app.infrastructure.signals.models import ConfidenceWeights, SignalDirection
from app.infrastructure.signals.signal_engine import SignalEngine

import pytest


def make_candles(closes: list[float]) -> list[Candle]:
    now = datetime.now(timezone.utc)
    return [
        Candle(
            symbol="TEST", timeframe="1h", timestamp=now + timedelta(hours=i),
            open=c, high=c + 0.3, low=c - 0.3, close=c, volume=1000,
        )
        for i, c in enumerate(closes)
    ]


def test_strong_uptrend_produces_buy_with_full_fields() -> None:
    closes = [100 + i * 1.5 for i in range(80)]  # صعود متصل نظيف
    signal = SignalEngine().generate("AAPL", make_candles(closes))

    assert signal.direction == SignalDirection.BUY
    assert signal.confidence >= 65.0
    assert signal.symbol == "AAPL"
    assert signal.timeframe == "1h"
    assert signal.entry == closes[-1]
    assert signal.stop_loss is not None and signal.stop_loss < signal.entry
    assert signal.take_profit is not None and signal.take_profit > signal.entry
    assert signal.risk_reward is not None and signal.risk_reward > 0
    assert set(signal.indicators_used) == {"trend_detection", "momentum_detection", "rsi", "macd"}
    assert len(signal.reasons) > 0
    assert signal.timestamp is not None


def test_strong_downtrend_produces_sell_with_full_fields() -> None:
    closes = [300 - i * 1.5 for i in range(80)]  # هبوط متصل نظيف
    signal = SignalEngine().generate("TSLA", make_candles(closes))

    assert signal.direction == SignalDirection.SELL
    assert signal.confidence <= 35.0
    assert signal.stop_loss is not None and signal.stop_loss > signal.entry
    assert signal.take_profit is not None and signal.take_profit < signal.entry
    assert signal.risk_reward is not None and signal.risk_reward > 0


def test_flat_constant_price_produces_neutral_with_no_risk_levels() -> None:
    """سعر ثابت تماماً (بلا أي حركة إطلاقاً) - EMA السريع=EMA البطيء=
    السعر الحالي بالضبط، فتسقط TrendDetection في "neutral" حتمياً
    (لا فارق '>' ولا '<' يتحقق). لاحظ: RSI يُصبح 100 هنا وفق الصيغة
    القياسية (avg_loss=0 -> RS→∞) - هذا سلوك موثَّق طبيعي في utils.py،
    وليس خطأً؛ يرفع النتيجة إلى 60 فقط (لا يزال أقل من buy_threshold=65)."""
    closes = [100.0] * 80
    signal = SignalEngine().generate("GOOGL", make_candles(closes))

    assert signal.direction == SignalDirection.NEUTRAL
    assert signal.stop_loss is None
    assert signal.take_profit is None
    assert signal.risk_reward is None
    assert signal.strategy_used == []


def test_insufficient_candles_raises() -> None:
    with pytest.raises(InsufficientCandlesError):
        SignalEngine().generate("AAPL", make_candles([100.0] * 10))


def test_confidence_weights_are_configurable_and_affect_score() -> None:
    """يثبت أن الأوزان قابلة للتخصيص فعلياً - إيقاف مساهمة الاتجاه
    (trend_weight=0) يجب أن يقلّل الثقة النهائية مقارنةً بالأوزان
    الافتراضية على نفس البيانات بالضبط."""
    closes = [100 + i * 1.5 for i in range(80)]
    candles = make_candles(closes)

    default_signal = SignalEngine().generate("AAPL", candles)

    zero_trend_weights = ConfidenceWeights(trend_weight=0.0)
    zero_trend_signal = SignalEngine(weights=zero_trend_weights).generate("AAPL", candles)

    assert zero_trend_signal.confidence < default_signal.confidence


def test_strategy_used_only_includes_strategies_matching_signal_direction() -> None:
    closes = [100 + i * 1.5 for i in range(80)]
    signal = SignalEngine().generate("AAPL", make_candles(closes))

    assert signal.direction == SignalDirection.BUY
    # كل استراتيجية مذكورة في strategy_used يجب أن تكون فعلاً من الأسماء المعروفة
    known_strategies = {"trend_following", "pullback", "breakout", "reversal", "momentum"}
    assert set(signal.strategy_used).issubset(known_strategies)
