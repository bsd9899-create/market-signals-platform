"""
tests/test_risk.py
-----------------------
اختبار حقيقي لـ RiskManager - قيم يدوية محسوبة بدقة لكل عملية حسابية.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.infrastructure.market.models import Candle
from app.infrastructure.risk.exceptions import InvalidRiskParametersError, RiskLimitExceededError
from app.infrastructure.risk.models import RiskSettings
from app.infrastructure.risk.risk_manager import RiskManager
from app.infrastructure.signals.models import SignalDirection


def make_candles(closes: list[float], highs=None, lows=None) -> list[Candle]:
    now = datetime.now(timezone.utc)
    n = len(closes)
    highs = highs if highs is not None else [c + 0.5 for c in closes]
    lows = lows if lows is not None else [c - 0.5 for c in closes]
    return [
        Candle(symbol="TEST", timeframe="1h", timestamp=now + timedelta(hours=i),
               open=closes[i], high=highs[i], low=lows[i], close=closes[i], volume=1000)
        for i in range(n)
    ]


def test_position_size_hand_verified() -> None:
    """balance=10000, risk%=1 -> risk_amount=100؛ entry=100, stop=95 ->
    per_unit_risk=5؛ units=100/5=20."""
    rm = RiskManager(RiskSettings(default_risk_percent=1.0))
    result = rm.position_size(account_balance=10000, entry_price=100, stop_loss_price=95)
    assert result.risk_amount == 100.0
    assert result.per_unit_risk == 5
    assert result.units == 20.0


def test_position_size_custom_risk_percent_override() -> None:
    rm = RiskManager(RiskSettings(default_risk_percent=1.0))
    result = rm.position_size(account_balance=10000, entry_price=100, stop_loss_price=90, risk_percent=2.0)
    assert result.risk_amount == 200.0  # 2% من 10000
    assert result.units == 20.0  # 200/10


def test_position_size_zero_distance_raises() -> None:
    rm = RiskManager()
    with pytest.raises(InvalidRiskParametersError):
        rm.position_size(account_balance=10000, entry_price=100, stop_loss_price=100)


def test_stop_loss_buy_and_sell_directions() -> None:
    rm = RiskManager()
    assert rm.stop_loss(100, SignalDirection.BUY, distance=5) == 95
    assert rm.stop_loss(100, SignalDirection.SELL, distance=5) == 105


def test_stop_loss_neutral_direction_raises() -> None:
    rm = RiskManager()
    with pytest.raises(InvalidRiskParametersError):
        rm.stop_loss(100, SignalDirection.NEUTRAL, distance=5)


def test_stop_loss_non_positive_distance_raises() -> None:
    rm = RiskManager()
    with pytest.raises(InvalidRiskParametersError):
        rm.stop_loss(100, SignalDirection.BUY, distance=0)


def test_take_profit_hand_verified() -> None:
    """entry=100, stop=95 -> risk=5؛ rr=2 -> reward=10؛ BUY -> tp=110."""
    rm = RiskManager()
    tp = rm.take_profit(entry_price=100, stop_loss_price=95, direction=SignalDirection.BUY, risk_reward_ratio=2.0)
    assert tp == 110.0

    tp_sell = rm.take_profit(entry_price=100, stop_loss_price=105, direction=SignalDirection.SELL, risk_reward_ratio=2.0)
    assert tp_sell == 90.0


def test_take_profit_uses_default_ratio_from_settings() -> None:
    rm = RiskManager(RiskSettings(default_risk_reward_ratio=3.0))
    tp = rm.take_profit(entry_price=100, stop_loss_price=95, direction=SignalDirection.BUY)
    assert tp == 115.0  # risk=5 * 3 = 15 -> 100+15


def test_risk_reward_ratio_hand_verified() -> None:
    rm = RiskManager()
    ratio = rm.risk_reward_ratio(entry_price=100, stop_loss_price=95, take_profit_price=110)
    assert ratio == 2.0  # risk=5, reward=10


def test_risk_reward_ratio_zero_risk_raises() -> None:
    rm = RiskManager()
    with pytest.raises(InvalidRiskParametersError):
        rm.risk_reward_ratio(entry_price=100, stop_loss_price=100, take_profit_price=110)


def test_atr_stop_loss_uses_real_atr_value() -> None:
    """يتحقّق أن atr_stop_loss يستخدم ATR الحقيقي فعلياً (وليس رقماً
    ثابتاً) - نبني شموعاً بحركة سعرية حقيقية، نحسب ATR بأنفسنا يدوياً
    عبر IndicatorService مباشرة، ثم نتأكد أن stop_loss يطابق
    entry - ATR*multiplier بالضبط (BUY)."""
    import math

    from app.infrastructure.indicators.service import IndicatorService

    closes = [100 + i * 0.3 for i in range(20)]
    highs = [c + 1.0 for c in closes]
    lows = [c - 1.0 for c in closes]
    candles = make_candles(closes, highs=highs, lows=lows)

    expected_atr = IndicatorService().calculate("atr", candles, period=14)[-1]
    assert expected_atr is not None and expected_atr > 0  # تأكيد أن الحركة السعرية أنتجت ATR حقيقياً غير صفري

    rm = RiskManager()
    stop = rm.atr_stop_loss(candles, SignalDirection.BUY, period=14, multiplier=1.5)
    expected_stop = candles[-1].close - expected_atr * 1.5
    assert math.isclose(stop, expected_stop, rel_tol=1e-9)


def test_atr_stop_loss_raises_when_atr_is_zero() -> None:
    """سعر ثابت تماماً -> True Range = 0 دائماً -> ATR = 0 -> مسافة وقف
    = صفر - stop_loss() يرفض هذا بحق (وقف عند نفس سعر الدخول لا معنى
    له) بدل إرجاع قيمة مضلِّلة."""
    candles = make_candles([100.0] * 20, highs=[100.0] * 20, lows=[100.0] * 20)
    rm = RiskManager()
    with pytest.raises(InvalidRiskParametersError):
        rm.atr_stop_loss(candles, SignalDirection.BUY, period=14, multiplier=1.5)


def test_check_max_daily_risk_true_and_false() -> None:
    rm = RiskManager(RiskSettings(max_daily_risk_percent=5.0))
    assert rm.check_max_daily_risk(risk_used_today_percent=3.0, new_trade_risk_percent=1.0) is True
    assert rm.check_max_daily_risk(risk_used_today_percent=4.5, new_trade_risk_percent=1.0) is False


def test_check_max_open_positions_true_and_false() -> None:
    rm = RiskManager(RiskSettings(max_open_positions=3))
    assert rm.check_max_open_positions(current_open_positions=2) is True
    assert rm.check_max_open_positions(current_open_positions=3) is False


def test_assert_max_daily_risk_raises_on_exceed() -> None:
    rm = RiskManager(RiskSettings(max_daily_risk_percent=5.0))
    with pytest.raises(RiskLimitExceededError):
        rm.assert_max_daily_risk(risk_used_today_percent=5.0, new_trade_risk_percent=1.0)


def test_assert_max_open_positions_raises_on_exceed() -> None:
    rm = RiskManager(RiskSettings(max_open_positions=1))
    with pytest.raises(RiskLimitExceededError):
        rm.assert_max_open_positions(current_open_positions=1)
