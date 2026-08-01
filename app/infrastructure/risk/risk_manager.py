"""
app/infrastructure/risk/risk_manager.py
--------------------------------------------
RiskManager: حسابات مخاطرة بحتة (رياضيات فقط) - لا تنفيذ صفقات، ولا
اتصال خارجي. يتعامل مع SignalDirection (BUY/SELL) لتحديد اتجاه الوقف/
الهدف تلقائياً.
"""

from __future__ import annotations

from loguru import logger

from app.infrastructure.indicators.service import IndicatorService
from app.infrastructure.market.models import Candle
from app.infrastructure.risk.exceptions import InvalidRiskParametersError, RiskLimitExceededError
from app.infrastructure.risk.models import PositionSizeResult, RiskSettings
from app.infrastructure.signals.models import SignalDirection


class RiskManager:
    def __init__(self, settings: RiskSettings | None = None) -> None:
        self._settings = settings or RiskSettings()

    def position_size(
        self, account_balance: float, entry_price: float, stop_loss_price: float, risk_percent: float | None = None,
    ) -> PositionSizeResult:
        risk_percent = risk_percent if risk_percent is not None else self._settings.default_risk_percent
        per_unit_risk = abs(entry_price - stop_loss_price)
        if per_unit_risk == 0:
            raise InvalidRiskParametersError("سعر الدخول ووقف الخسارة متطابقان - لا يمكن حساب حجم المركز.")

        risk_amount = account_balance * risk_percent / 100
        units = risk_amount / per_unit_risk

        result = PositionSizeResult(units=units, risk_amount=risk_amount, per_unit_risk=per_unit_risk)
        logger.info(
            "RiskManager.position_size: balance={}, risk%={} -> units={:.4f} (risk_amount={:.2f})",
            account_balance, risk_percent, result.units, result.risk_amount,
        )
        return result

    def stop_loss(self, entry_price: float, direction: SignalDirection, distance: float) -> float:
        if distance <= 0:
            raise InvalidRiskParametersError("مسافة وقف الخسارة يجب أن تكون أكبر من صفر.")
        if direction == SignalDirection.BUY:
            return entry_price - distance
        if direction == SignalDirection.SELL:
            return entry_price + distance
        raise InvalidRiskParametersError("لا يمكن حساب وقف خسارة لاتجاه NEUTRAL.")

    def atr_stop_loss(
        self, candles: list[Candle], direction: SignalDirection, period: int = 14, multiplier: float | None = None,
    ) -> float:
        multiplier = multiplier if multiplier is not None else self._settings.atr_multiplier
        atr_values = IndicatorService().calculate("atr", candles, period=period)
        atr = atr_values[-1]
        if atr is None:
            raise InvalidRiskParametersError("لا يمكن حساب ATR - بيانات غير كافية.")

        entry_price = candles[-1].close
        distance = atr * multiplier
        stop = self.stop_loss(entry_price, direction, distance)
        logger.info("RiskManager.atr_stop_loss: ATR={:.4f} x{} -> distance={:.4f}, stop={:.4f}", atr, multiplier, distance, stop)
        return stop

    def take_profit(
        self, entry_price: float, stop_loss_price: float, direction: SignalDirection, risk_reward_ratio: float | None = None,
    ) -> float:
        risk_reward_ratio = risk_reward_ratio if risk_reward_ratio is not None else self._settings.default_risk_reward_ratio
        risk = abs(entry_price - stop_loss_price)
        reward = risk * risk_reward_ratio

        if direction == SignalDirection.BUY:
            return entry_price + reward
        if direction == SignalDirection.SELL:
            return entry_price - reward
        raise InvalidRiskParametersError("لا يمكن حساب جني أرباح لاتجاه NEUTRAL.")

    def risk_reward_ratio(self, entry_price: float, stop_loss_price: float, take_profit_price: float) -> float:
        risk = abs(entry_price - stop_loss_price)
        reward = abs(take_profit_price - entry_price)
        if risk == 0:
            raise InvalidRiskParametersError("المخاطرة = صفر - لا يمكن حساب نسبة العائد/المخاطرة.")
        return reward / risk

    def check_max_daily_risk(self, risk_used_today_percent: float, new_trade_risk_percent: float) -> bool:
        allowed = (risk_used_today_percent + new_trade_risk_percent) <= self._settings.max_daily_risk_percent
        if not allowed:
            logger.warning(
                "RiskManager: تجاوز حد المخاطرة اليومي ({}% + {}% > {}%).",
                risk_used_today_percent, new_trade_risk_percent, self._settings.max_daily_risk_percent,
            )
        return allowed

    def check_max_open_positions(self, current_open_positions: int) -> bool:
        allowed = current_open_positions < self._settings.max_open_positions
        if not allowed:
            logger.warning(
                "RiskManager: تجاوز الحد الأقصى للمراكز المفتوحة ({} >= {}).",
                current_open_positions, self._settings.max_open_positions,
            )
        return allowed

    def assert_max_daily_risk(self, risk_used_today_percent: float, new_trade_risk_percent: float) -> None:
        if not self.check_max_daily_risk(risk_used_today_percent, new_trade_risk_percent):
            raise RiskLimitExceededError(
                f"تجاوز حد المخاطرة اليومي: {risk_used_today_percent}% + {new_trade_risk_percent}% "
                f"> {self._settings.max_daily_risk_percent}%"
            )

    def assert_max_open_positions(self, current_open_positions: int) -> None:
        if not self.check_max_open_positions(current_open_positions):
            raise RiskLimitExceededError(
                f"تجاوز الحد الأقصى للمراكز المفتوحة: {current_open_positions} >= {self._settings.max_open_positions}"
            )
