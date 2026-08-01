"""
tests/test_indicators.py
-----------------------------
اختبار حقيقي وشامل (pytest) لمحرك المؤشرات كاملاً - بلا أي اتصال
إنترنت (بيانات ثابتة/مُولَّدة محلياً فقط).

منهج التحقق من صحة الحسابات:
1. قيم بسيطة محسوبة يدوياً (أرقام صحيحة يسهل تدقيقها بالحاسبة).
2. تطبيقات مرجعية مستقلة (ref_*) مكتوبة بأسلوب بسيط ومباشر تماماً
   (حلقات Python عادية، بلا numpy وبلا إعادة استخدام أي كود إنتاجي)
   تُقارَن مقابل المؤشرات الفعلية - إذا اتفق تطبيقان مستقلان تماماً على
   نفس النتيجة عبر مئات النقاط، فهذا دليل أقوى من مثال يدوي واحد فقط.
3. سيناريوهات مبنية عمداً بنتيجة واضحة/لا لبس فيها (مثال: سعر ثابت
   تماماً -> الانحراف المعياري = صفر؛ ارتفاع تدريجي متصل -> RSI=100).
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import IndicatorNotFoundError, InsufficientDataError
from app.infrastructure.indicators.service import IndicatorService
from app.infrastructure.market.models import Candle

# ---------------------------------------------------------------------
# أدوات بناء بيانات الاختبار
# ---------------------------------------------------------------------


def make_candles(
    closes: list[float],
    highs: list[float] | None = None,
    lows: list[float] | None = None,
    volumes: list[float] | None = None,
) -> list[Candle]:
    now = datetime.now(timezone.utc)
    n = len(closes)
    highs = highs if highs is not None else [c + 0.0 for c in closes]
    lows = lows if lows is not None else [c - 0.0 for c in closes]
    volumes = volumes if volumes is not None else [1000] * n
    return [
        Candle(
            symbol="TEST", timeframe="1m", timestamp=now + timedelta(minutes=i),
            open=closes[i], high=highs[i], low=lows[i], close=closes[i], volume=volumes[i],
        )
        for i in range(n)
    ]


def assert_series_close(actual: list[float | None], expected: list[float | None], tol: float = 1e-6) -> None:
    assert len(actual) == len(expected)
    for i, (a, e) in enumerate(zip(actual, expected)):
        if e is None:
            assert a is None, f"index {i}: expected None, got {a}"
        else:
            assert a is not None, f"index {i}: expected {e}, got None"
            assert math.isclose(a, e, rel_tol=tol, abs_tol=tol), f"index {i}: expected {e}, got {a}"


# ---------------------------------------------------------------------
# تطبيقات مرجعية مستقلة (حلقات Python بسيطة، بلا numpy) - "القيم المعروفة"
# ---------------------------------------------------------------------


def ref_sma(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    for i in range(period - 1, len(values)):
        result[i] = sum(values[i - period + 1 : i + 1]) / period
    return result


def ref_ema(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if len(values) < period:
        return result
    k = 2 / (period + 1)
    prev = sum(values[:period]) / period
    result[period - 1] = prev
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1 - k)
        result[i] = prev
    return result


def ref_rsi(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if len(values) < period + 1:
        return result
    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]

    def rsi_from(avg_gain: float, avg_loss: float) -> float:
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - 100 / (1 + rs)

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    result[period] = rsi_from(avg_gain, avg_loss)
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        result[i + 1] = rsi_from(avg_gain, avg_loss)
    return result


def ref_true_range(highs: list[float], lows: list[float], closes: list[float]) -> list[float]:
    tr = [highs[0] - lows[0]]
    for i in range(1, len(highs)):
        tr.append(max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1])))
    return tr


def ref_wilder_smooth(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = [None] * len(values)
    if len(values) < period:
        return result
    prev = sum(values[:period]) / period
    result[period - 1] = prev
    for i in range(period, len(values)):
        prev = (prev * (period - 1) + values[i]) / period
        result[i] = prev
    return result


def ref_atr(highs: list[float], lows: list[float], closes: list[float], period: int) -> list[float | None]:
    return ref_wilder_smooth(ref_true_range(highs, lows, closes), period)


def ref_bollinger(values: list[float], period: int, num_std: float) -> tuple[list, list, list]:
    n = len(values)
    middle = ref_sma(values, period)
    upper: list[float | None] = [None] * n
    lower: list[float | None] = [None] * n
    for i in range(period - 1, n):
        window = values[i - period + 1 : i + 1]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = math.sqrt(variance)
        upper[i] = middle[i] + num_std * std
        lower[i] = middle[i] - num_std * std
    return upper, middle, lower


# ---------------------------------------------------------------------
# SMA
# ---------------------------------------------------------------------


def test_sma_hand_verified_known_values() -> None:
    """closes=[10,20,30,40,50], period=3 -> يدوياً: mean(10,20,30)=20، mean(20,30,40)=30، mean(30,40,50)=40."""
    candles = make_candles([10, 20, 30, 40, 50])
    result = IndicatorService().calculate("sma", candles, period=3)
    assert result == [None, None, 20.0, 30.0, 40.0]


def test_sma_matches_independent_reference() -> None:
    closes = [round(50 + 10 * math.sin(i / 3) + i * 0.2, 4) for i in range(80)]
    candles = make_candles(closes)
    actual = IndicatorService().calculate("sma", candles, period=10)
    expected = ref_sma(closes, 10)
    assert_series_close(actual, expected)


def test_sma_insufficient_data_raises() -> None:
    candles = make_candles([1, 2, 3])
    with pytest.raises(InsufficientDataError):
        IndicatorService().calculate("sma", candles, period=5)


# ---------------------------------------------------------------------
# EMA
# ---------------------------------------------------------------------


def test_ema_hand_verified_known_values() -> None:
    """closes=[10,20,30,40,50,60,70], period=3 (k=0.5):
    seed=mean(10,20,30)=20؛ ثم 40*0.5+20*0.5=30؛ 50*0.5+30*0.5=40؛
    60*0.5+40*0.5=50؛ 70*0.5+50*0.5=60."""
    candles = make_candles([10, 20, 30, 40, 50, 60, 70])
    result = IndicatorService().calculate("ema", candles, period=3)
    assert result == [None, None, 20.0, 30.0, 40.0, 50.0, 60.0]


def test_ema_matches_independent_reference() -> None:
    closes = [round(100 + 5 * math.cos(i / 4) + i * 0.1, 4) for i in range(80)]
    candles = make_candles(closes)
    actual = IndicatorService().calculate("ema", candles, period=20)
    expected = ref_ema(closes, 20)
    assert_series_close(actual, expected)


# ---------------------------------------------------------------------
# RSI
# ---------------------------------------------------------------------


def test_rsi_matches_independent_reference_wilder_example() -> None:
    """مجموعة إغلاقات كلاسيكية بأسلوب المثال المرجعي لحساب RSI(14) بطريقة وايلدر."""
    closes = [
        44.34, 44.09, 44.15, 43.61, 44.33, 44.83, 45.10, 45.42, 45.84,
        46.08, 45.89, 46.03, 45.61, 46.28, 46.28,
    ]
    candles = make_candles(closes)
    actual = IndicatorService().calculate("rsi", candles, period=14)
    expected = ref_rsi(closes, 14)
    assert_series_close(actual, expected)
    assert actual[-1] is not None
    assert 0 <= actual[-1] <= 100


def test_rsi_all_gains_approaches_100() -> None:
    """ارتفاع متصل بلا أي خسارة واحدة -> avg_loss=0 -> RSI=100 بالضبط."""
    closes = [100 + i for i in range(20)]  # +1 كل شمعة، بلا أي هبوط إطلاقاً
    candles = make_candles(closes)
    result = IndicatorService().calculate("rsi", candles, period=14)
    assert result[-1] == 100.0


def test_rsi_matches_reference_on_random_walk() -> None:
    closes = [round(100 + sum(math.sin(j) for j in range(i + 1)) * 0.3, 4) for i in range(60)]
    candles = make_candles(closes)
    actual = IndicatorService().calculate("rsi", candles, period=14)
    expected = ref_rsi(closes, 14)
    assert_series_close(actual, expected)


# ---------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------


def test_macd_matches_independent_reference() -> None:
    closes = [round(100 + 8 * math.sin(i / 5) + i * 0.15, 4) for i in range(100)]
    candles = make_candles(closes)
    result = IndicatorService().calculate("macd", candles, fast_period=12, slow_period=26, signal_period=9)

    ema_fast = ref_ema(closes, 12)
    ema_slow = ref_ema(closes, 26)
    expected_macd_line = [
        None if (f is None or s is None) else f - s for f, s in zip(ema_fast, ema_slow)
    ]
    assert_series_close(result.macd_line, expected_macd_line)

    first_valid = 26 - 1
    macd_valid = [v for v in expected_macd_line[first_valid:]]
    expected_signal_valid = ref_ema(macd_valid, 9)
    expected_signal_line = [None] * first_valid + expected_signal_valid
    assert_series_close(result.signal_line, expected_signal_line)

    expected_histogram = [
        None if (m is None or s is None) else m - s
        for m, s in zip(expected_macd_line, expected_signal_line)
    ]
    assert_series_close(result.histogram, expected_histogram)


# ---------------------------------------------------------------------
# VWAP
# ---------------------------------------------------------------------


def test_vwap_hand_verified_known_values() -> None:
    """شمعتان فقط - يدوياً:
    typical1 = (10+8+9)/3 = 9؛ pv1 = 9*100 = 900؛ vwap1 = 900/100 = 9.0
    typical2 = (12+10+11)/3 = 11؛ pv2=11*200=2200؛ vwap2=(900+2200)/(100+200)=3100/300=10.333..."""
    candles = make_candles(
        closes=[9, 11], highs=[10, 12], lows=[8, 10], volumes=[100, 200],
    )
    result = IndicatorService().calculate("vwap", candles)
    assert math.isclose(result[0], 9.0, rel_tol=1e-9)
    assert math.isclose(result[1], 3100 / 300, rel_tol=1e-9)


# ---------------------------------------------------------------------
# ATR
# ---------------------------------------------------------------------


def test_atr_zero_when_no_price_movement() -> None:
    """high == low == close دائماً -> True Range = 0 دائماً -> ATR = 0."""
    candles = make_candles(closes=[100.0] * 20, highs=[100.0] * 20, lows=[100.0] * 20)
    result = IndicatorService().calculate("atr", candles, period=14)
    assert result[-1] == 0.0


def test_atr_matches_independent_reference() -> None:
    closes = [round(100 + 3 * math.sin(i / 4), 4) for i in range(50)]
    highs = [c + 0.5 for c in closes]
    lows = [c - 0.5 for c in closes]
    candles = make_candles(closes, highs=highs, lows=lows)
    actual = IndicatorService().calculate("atr", candles, period=14)
    expected = ref_atr(highs, lows, closes, 14)
    assert_series_close(actual, expected)


# ---------------------------------------------------------------------
# Bollinger Bands
# ---------------------------------------------------------------------


def test_bollinger_bands_zero_width_on_constant_price() -> None:
    """سعر ثابت تماماً -> الانحراف المعياري = صفر -> upper == middle == lower."""
    candles = make_candles([50.0] * 25)
    result = IndicatorService().calculate("bollinger_bands", candles, period=20)
    assert result.upper[-1] == result.middle[-1] == result.lower[-1] == 50.0


def test_bollinger_bands_matches_independent_reference() -> None:
    closes = [round(100 + 6 * math.sin(i / 3), 4) for i in range(60)]
    candles = make_candles(closes)
    result = IndicatorService().calculate("bollinger_bands", candles, period=20, num_std=2.0)
    expected_upper, expected_middle, expected_lower = ref_bollinger(closes, 20, 2.0)
    assert_series_close(result.upper, expected_upper)
    assert_series_close(result.middle, expected_middle)
    assert_series_close(result.lower, expected_lower)


# ---------------------------------------------------------------------
# ADX
# ---------------------------------------------------------------------


def test_adx_bounds_and_runs_without_error() -> None:
    closes = [round(100 + 10 * math.sin(i / 6) + i * 0.1, 4) for i in range(80)]
    highs = [c + 0.6 for c in closes]
    lows = [c - 0.6 for c in closes]
    candles = make_candles(closes, highs=highs, lows=lows)
    result = IndicatorService().calculate("adx", candles, period=14)
    assert result.adx[-1] is not None
    assert 0 <= result.adx[-1] <= 100
    assert 0 <= result.plus_di[-1] <= 100
    assert 0 <= result.minus_di[-1] <= 100


def test_adx_strong_uptrend_shows_dominant_plus_di() -> None:
    """اتجاه صاعد نظيف تماماً (كل شمعة أعلى من السابقة) -> +DI يجب أن
    يتفوّق بوضوح على -DI."""
    closes = [100 + i * 1.0 for i in range(60)]
    highs = [c + 0.3 for c in closes]
    lows = [c - 0.3 for c in closes]
    candles = make_candles(closes, highs=highs, lows=lows)
    result = IndicatorService().calculate("adx", candles, period=14)
    assert result.plus_di[-1] > result.minus_di[-1]


# ---------------------------------------------------------------------
# Stochastic RSI
# ---------------------------------------------------------------------


def test_stochastic_rsi_bounds_and_runs_without_error() -> None:
    closes = [round(100 + 8 * math.sin(i / 5) + i * 0.05, 4) for i in range(100)]
    candles = make_candles(closes)
    result = IndicatorService().calculate("stochastic_rsi", candles)
    assert result.k[-1] is not None
    assert result.d[-1] is not None
    assert 0 <= result.k[-1] <= 100
    assert 0 <= result.d[-1] <= 100


# ---------------------------------------------------------------------
# Volume Average / Volume Spike
# ---------------------------------------------------------------------


def test_volume_average_hand_verified_known_values() -> None:
    candles = make_candles(closes=[1] * 5, volumes=[100, 200, 300, 400, 500])
    result = IndicatorService().calculate("volume_average", candles, period=3)
    assert result == [None, None, 200.0, 300.0, 400.0]


def test_volume_spike_detects_obvious_spike() -> None:
    """20 شمعة بحجم ثابت 1000، ثم شمعة أخيرة بحجم 10x - يجب اكتشافها كـSpike."""
    volumes = [1000] * 20 + [10_000]
    candles = make_candles(closes=[100.0] * 21, volumes=volumes)
    result = IndicatorService().calculate("volume_spike", candles, period=20, threshold=2.0)
    assert result.is_spike[-1] is True
    assert result.ratio[-1] > 2.0


def test_volume_spike_no_spike_on_steady_volume() -> None:
    candles = make_candles(closes=[100.0] * 25, volumes=[1000] * 25)
    result = IndicatorService().calculate("volume_spike", candles, period=20, threshold=2.0)
    assert result.is_spike[-1] is False


# ---------------------------------------------------------------------
# Support & Resistance
# ---------------------------------------------------------------------


def test_support_resistance_detects_obvious_v_shape() -> None:
    """شكل V واضح: ينخفض حتى القاع في المنتصف ثم يرتفع - القاع يجب أن
    يُكتشف كدعم."""
    lows = [110, 105, 100, 95, 90, 85, 80, 85, 90, 95, 100, 105, 110]
    highs = [l + 5 for l in lows]
    closes = [l + 2 for l in lows]
    candles = make_candles(closes, highs=highs, lows=lows)
    result = IndicatorService().calculate("support_resistance", candles, window=5)
    assert 80 in result.support_levels


# ---------------------------------------------------------------------
# Trend Detection
# ---------------------------------------------------------------------


def test_trend_detection_clear_uptrend_is_bullish() -> None:
    closes = [100 + i * 1.5 for i in range(60)]
    candles = make_candles(closes)
    result = IndicatorService().calculate("trend_detection", candles, fast_period=10, slow_period=30)
    assert result.trend == "bullish"


def test_trend_detection_clear_downtrend_is_bearish() -> None:
    closes = [200 - i * 1.5 for i in range(60)]
    candles = make_candles(closes)
    result = IndicatorService().calculate("trend_detection", candles, fast_period=10, slow_period=30)
    assert result.trend == "bearish"


# ---------------------------------------------------------------------
# Momentum Detection
# ---------------------------------------------------------------------


def test_momentum_detection_positive_roc_is_bullish() -> None:
    closes = [100 + i for i in range(15)]  # يرتفع باستمرار
    candles = make_candles(closes)
    result = IndicatorService().calculate("momentum_detection", candles, period=10)
    assert result.momentum == "bullish"
    assert result.rate_of_change_percent > 0


def test_momentum_detection_negative_roc_is_bearish() -> None:
    closes = [100 - i for i in range(15)]  # ينخفض باستمرار
    candles = make_candles(closes)
    result = IndicatorService().calculate("momentum_detection", candles, period=10)
    assert result.momentum == "bearish"
    assert result.rate_of_change_percent < 0


# ---------------------------------------------------------------------
# IndicatorService - Registry, Errors, OCP Extensibility, Logging
# ---------------------------------------------------------------------


def test_service_registers_all_14_builtin_indicators() -> None:
    service = IndicatorService()
    names = service.available_indicators()
    assert names == sorted([
        "sma", "ema", "rsi", "macd", "vwap", "atr", "bollinger_bands", "adx",
        "stochastic_rsi", "volume_average", "volume_spike", "support_resistance",
        "trend_detection", "momentum_detection",
    ])
    assert len(names) == 14


def test_service_unknown_indicator_raises_clear_error() -> None:
    service = IndicatorService()
    with pytest.raises(IndicatorNotFoundError):
        service.calculate("does_not_exist", make_candles([1, 2, 3]))


def test_open_closed_extensibility_custom_indicator_without_modifying_existing_code() -> None:
    """يثبت Open/Closed فعلياً: مؤشر جديد بالكامل (مُعرَّف هنا فقط، في
    ملف الاختبار) يُسجَّل ويعمل دون أي تعديل على IndicatorService أو
    أي مؤشر مبنيّ قائم."""

    class AlwaysFortyTwo(Indicator):
        name = "always_forty_two"

        def min_candles_required(self, **params: Any) -> int:
            return 1

        def calculate(self, candles, **params: Any) -> list[float]:
            return [42.0 for _ in candles]

    service = IndicatorService()
    assert "always_forty_two" not in service.available_indicators()

    service.register(AlwaysFortyTwo())

    assert "always_forty_two" in service.available_indicators()
    result = service.calculate("always_forty_two", make_candles([1, 2, 3]))
    assert result == [42.0, 42.0, 42.0]


def test_logging_actually_emitted_for_calculate() -> None:
    """يثبت أن IndicatorService.calculate يُسجِّل فعلياً عبر Loguru -
    وليس مجرد ادّعاء - بإضافة Sink مؤقت يلتقط الرسائل الفعلية."""
    from loguru import logger

    captured: list[str] = []
    sink_id = logger.add(lambda message: captured.append(message.record["message"]), level="INFO")
    try:
        service = IndicatorService()
        service.calculate("sma", make_candles([1, 2, 3, 4, 5]), period=3)
    finally:
        logger.remove(sink_id)

    assert any("sma" in msg for msg in captured)


def test_each_indicator_raises_insufficient_data_with_too_few_candles() -> None:
    """كل مؤشر (بمعامله الافتراضي) يرفع InsufficientDataError برسالة
    واضحة عند إعطائه شمعة واحدة فقط (باستثناء VWAP الذي لا يحتاج حداً
    أدنى فعلياً)."""
    service = IndicatorService()
    one_candle = make_candles([100.0])
    for name in service.available_indicators():
        if name == "vwap":
            continue
        with pytest.raises(InsufficientDataError):
            service.calculate(name, one_candle)
