"""
app/infrastructure/strategies/strategies/pullback.py
------------------------------------------------------------
Pullback: تطابق إذا كان هناك اتجاه واضح (TrendDetection) والسعر
الحالي عاد قريباً جداً من EMA السريع (ارتداد مؤقت داخل الاتجاه العام)
- ضمن tolerance_percent (1.0% افتراضياً).
"""

from __future__ import annotations

from app.infrastructure.indicators.service import IndicatorService
from app.infrastructure.market.models import Candle
from app.infrastructure.signals.models import SignalDirection
from app.infrastructure.strategies.base import Strategy
from app.infrastructure.strategies.exceptions import InsufficientCandlesError
from app.infrastructure.strategies.models import StrategyResult


class Pullback(Strategy):
    name = "pullback"

    def __init__(self, tolerance_percent: float = 1.0) -> None:
        self._tolerance_percent = tolerance_percent

    def min_candles_required(self) -> int:
        return 50

    def evaluate(self, candles: list[Candle]) -> StrategyResult:
        required = self.min_candles_required()
        if len(candles) < required:
            raise InsufficientCandlesError(self.name, required, len(candles))

        trend = IndicatorService().calculate("trend_detection", candles)
        current_price = candles[-1].close

        if trend.trend == "neutral" or trend.fast_ema is None:
            return StrategyResult(
                strategy_name=self.name, matched=False, direction=SignalDirection.NEUTRAL,
                confidence=0.0, reason="لا يوجد اتجاه واضح لتحديد ارتداد ضمنه.",
            )

        distance_percent = abs(current_price - trend.fast_ema) / trend.fast_ema * 100
        if distance_percent > self._tolerance_percent:
            return StrategyResult(
                strategy_name=self.name, matched=False, direction=SignalDirection.NEUTRAL,
                confidence=0.0,
                reason=f"السعر بعيد عن EMA السريع ({distance_percent:.2f}% > {self._tolerance_percent}%).",
            )

        confidence = max(0.0, 100.0 - (distance_percent / self._tolerance_percent) * 100.0)
        direction = SignalDirection.BUY if trend.trend == "bullish" else SignalDirection.SELL

        return StrategyResult(
            strategy_name=self.name, matched=True, direction=direction,
            confidence=round(confidence, 2),
            reason=f"ارتداد ضمن اتجاه {trend.trend} - المسافة عن EMA السريع={distance_percent:.2f}%.",
        )
