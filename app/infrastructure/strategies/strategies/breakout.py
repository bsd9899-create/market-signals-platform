"""
app/infrastructure/strategies/strategies/breakout.py
------------------------------------------------------------
Breakout: تطابق إذا أغلق السعر الحالي فوق آخر مستوى مقاومة مكتشَف
(اختراق صعودي) أو تحت آخر مستوى دعم مكتشَف (اختراق هبوطي) - عبر مؤشر
Support & Resistance.
"""

from __future__ import annotations

from app.infrastructure.indicators.service import IndicatorService
from app.infrastructure.market.models import Candle
from app.infrastructure.signals.models import SignalDirection
from app.infrastructure.strategies.base import Strategy
from app.infrastructure.strategies.exceptions import InsufficientCandlesError
from app.infrastructure.strategies.models import StrategyResult


class Breakout(Strategy):
    name = "breakout"

    def min_candles_required(self) -> int:
        return 11  # window=5 الافتراضي لـ Support & Resistance -> 2*5+1

    def evaluate(self, candles: list[Candle]) -> StrategyResult:
        required = self.min_candles_required()
        if len(candles) < required:
            raise InsufficientCandlesError(self.name, required, len(candles))

        levels = IndicatorService().calculate("support_resistance", candles)
        current_price = candles[-1].close

        if levels.resistance_levels and current_price > max(levels.resistance_levels):
            resistance = max(levels.resistance_levels)
            gap_percent = (current_price - resistance) / resistance * 100
            return StrategyResult(
                strategy_name=self.name, matched=True, direction=SignalDirection.BUY,
                confidence=round(min(100.0, gap_percent * 50), 2),
                reason=f"اختراق صعودي فوق مقاومة {resistance:.2f} بنسبة {gap_percent:.2f}%.",
            )

        if levels.support_levels and current_price < min(levels.support_levels):
            support = min(levels.support_levels)
            gap_percent = (support - current_price) / support * 100
            return StrategyResult(
                strategy_name=self.name, matched=True, direction=SignalDirection.SELL,
                confidence=round(min(100.0, gap_percent * 50), 2),
                reason=f"اختراق هبوطي تحت دعم {support:.2f} بنسبة {gap_percent:.2f}%.",
            )

        return StrategyResult(
            strategy_name=self.name, matched=False, direction=SignalDirection.NEUTRAL,
            confidence=0.0, reason="السعر ضمن نطاق الدعم/المقاومة الحاليَين - لا اختراق.",
        )
