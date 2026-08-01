"""
app/infrastructure/strategies/strategies/trend_following.py
--------------------------------------------------------------------
Trend Following: تطابق إذا كان الاتجاه (TrendDetection) صاعداً أو
هابطاً بوضوح (وليس محايداً). الثقة تتناسب مع نسبة الفارق بين EMA
السريع والبطيء (كلما ابتعدا عن بعضهما، كان الاتجاه أوضح).
"""

from __future__ import annotations

from app.infrastructure.indicators.service import IndicatorService
from app.infrastructure.market.models import Candle
from app.infrastructure.signals.models import SignalDirection
from app.infrastructure.strategies.base import Strategy
from app.infrastructure.strategies.exceptions import InsufficientCandlesError
from app.infrastructure.strategies.models import StrategyResult


class TrendFollowing(Strategy):
    name = "trend_following"

    def min_candles_required(self) -> int:
        return 50

    def evaluate(self, candles: list[Candle]) -> StrategyResult:
        required = self.min_candles_required()
        if len(candles) < required:
            raise InsufficientCandlesError(self.name, required, len(candles))

        trend = IndicatorService().calculate("trend_detection", candles)

        if trend.trend == "neutral" or trend.fast_ema is None or trend.slow_ema is None:
            return StrategyResult(
                strategy_name=self.name, matched=False, direction=SignalDirection.NEUTRAL,
                confidence=0.0, reason="لا يوجد اتجاه واضح (EMA السريع والبطيء متقاربان جداً).",
            )

        gap_percent = abs(trend.fast_ema - trend.slow_ema) / trend.slow_ema * 100
        confidence = min(100.0, gap_percent * 20)  # تدرّج بسيط: 5% فارق = ثقة كاملة تقريباً
        direction = SignalDirection.BUY if trend.trend == "bullish" else SignalDirection.SELL

        return StrategyResult(
            strategy_name=self.name, matched=True, direction=direction,
            confidence=round(confidence, 2),
            reason=f"اتجاه {trend.trend} واضح - فارق EMA={gap_percent:.2f}%.",
        )
