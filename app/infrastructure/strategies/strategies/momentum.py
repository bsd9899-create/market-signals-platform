"""
app/infrastructure/strategies/strategies/momentum.py
------------------------------------------------------------
Momentum: تطابق إذا كان الزخم (MomentumDetection - معدل التغيّر
Rate-of-Change) واضح الاتجاه وتجاوزت قيمته المطلقة threshold_percent
(1.0% افتراضياً).
"""

from __future__ import annotations

from app.infrastructure.indicators.service import IndicatorService
from app.infrastructure.market.models import Candle
from app.infrastructure.signals.models import SignalDirection
from app.infrastructure.strategies.base import Strategy
from app.infrastructure.strategies.exceptions import InsufficientCandlesError
from app.infrastructure.strategies.models import StrategyResult


class Momentum(Strategy):
    name = "momentum"

    def __init__(self, threshold_percent: float = 1.0) -> None:
        self._threshold_percent = threshold_percent

    def min_candles_required(self) -> int:
        return 11  # MomentumDetection period=10 الافتراضي -> period+1

    def evaluate(self, candles: list[Candle]) -> StrategyResult:
        required = self.min_candles_required()
        if len(candles) < required:
            raise InsufficientCandlesError(self.name, required, len(candles))

        momentum = IndicatorService().calculate("momentum_detection", candles)
        roc = momentum.rate_of_change_percent

        if momentum.momentum == "neutral" or roc is None or abs(roc) < self._threshold_percent:
            return StrategyResult(
                strategy_name=self.name, matched=False, direction=SignalDirection.NEUTRAL,
                confidence=0.0, reason=f"زخم ضعيف (roc%={roc}) - أقل من العتبة {self._threshold_percent}%.",
            )

        direction = SignalDirection.BUY if momentum.momentum == "bullish" else SignalDirection.SELL
        confidence = min(100.0, abs(roc) * 10)

        return StrategyResult(
            strategy_name=self.name, matched=True, direction=direction,
            confidence=round(confidence, 2),
            reason=f"زخم {momentum.momentum} واضح (roc%={roc:.2f}).",
        )
