"""
app/infrastructure/strategies/strategies/reversal.py
------------------------------------------------------------
Reversal: تطابق عند تطرّف RSI (>=overbought أو <=oversold) مع شمعة
أخيرة تؤكد الانعكاس (شمعة هابطة عند تشبّع شرائي، أو صاعدة عند تشبّع
بيعي) - overbought=70, oversold=30 افتراضياً.
"""

from __future__ import annotations

from app.infrastructure.indicators.service import IndicatorService
from app.infrastructure.market.models import Candle
from app.infrastructure.signals.models import SignalDirection
from app.infrastructure.strategies.base import Strategy
from app.infrastructure.strategies.exceptions import InsufficientCandlesError
from app.infrastructure.strategies.models import StrategyResult


class Reversal(Strategy):
    name = "reversal"

    def __init__(self, overbought: float = 70.0, oversold: float = 30.0) -> None:
        self._overbought = overbought
        self._oversold = oversold

    def min_candles_required(self) -> int:
        return 15  # RSI(14) يحتاج period+1

    def evaluate(self, candles: list[Candle]) -> StrategyResult:
        required = self.min_candles_required()
        if len(candles) < required:
            raise InsufficientCandlesError(self.name, required, len(candles))

        rsi = IndicatorService().calculate("rsi", candles)[-1]
        last_candle = candles[-1]
        is_bearish_candle = last_candle.close < last_candle.open
        is_bullish_candle = last_candle.close > last_candle.open

        if rsi is not None and rsi >= self._overbought and is_bearish_candle:
            return StrategyResult(
                strategy_name=self.name, matched=True, direction=SignalDirection.SELL,
                confidence=round(min(100.0, (rsi - self._overbought) * 5 + 50), 2),
                reason=f"تشبّع شرائي (RSI={rsi:.1f} >= {self._overbought}) مع شمعة هابطة تأكيدية.",
            )

        if rsi is not None and rsi <= self._oversold and is_bullish_candle:
            return StrategyResult(
                strategy_name=self.name, matched=True, direction=SignalDirection.BUY,
                confidence=round(min(100.0, (self._oversold - rsi) * 5 + 50), 2),
                reason=f"تشبّع بيعي (RSI={rsi:.1f} <= {self._oversold}) مع شمعة صاعدة تأكيدية.",
            )

        return StrategyResult(
            strategy_name=self.name, matched=False, direction=SignalDirection.NEUTRAL,
            confidence=0.0, reason=f"لا تشبّع واضح حالياً (RSI={rsi}).",
        )
