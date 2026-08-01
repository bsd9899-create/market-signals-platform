"""
app/infrastructure/indicators/indicators/trend_detection.py
--------------------------------------------------------------------
Trend Detection - يُرجع حكماً واحداً (وليس سلسلة لكل شمعة) يعكس اتجاه
آخر شمعة في القائمة المُعطاة، بمقارنة EMA سريع (20) وEMA بطيء (50)
افتراضياً مع السعر الحالي (يُعيد استخدام EMA داخلياً):

bullish: fast_ema > slow_ema  و  السعر الحالي > fast_ema
bearish: fast_ema < slow_ema  و  السعر الحالي < fast_ema
neutral: خلاف ذلك
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.indicators.ema import EMA
from app.infrastructure.indicators.results import TrendDetectionResult
from app.infrastructure.market.models import Candle


class TrendDetection(Indicator):
    name = "trend_detection"

    def min_candles_required(self, **params: Any) -> int:
        return int(params.get("slow_period", 50))

    def calculate(self, candles: list[Candle], **params: Any) -> TrendDetectionResult:
        fast_period = int(params.get("fast_period", 20))
        slow_period = int(params.get("slow_period", 50))
        required = self.min_candles_required(slow_period=slow_period)
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        fast_ema = EMA().calculate(candles, period=fast_period)[-1]
        slow_ema = EMA().calculate(candles, period=slow_period)[-1]
        current_price = candles[-1].close

        if fast_ema is None or slow_ema is None:
            trend = "neutral"
        elif fast_ema > slow_ema and current_price > fast_ema:
            trend = "bullish"
        elif fast_ema < slow_ema and current_price < fast_ema:
            trend = "bearish"
        else:
            trend = "neutral"

        result = TrendDetectionResult(trend=trend, fast_ema=fast_ema, slow_ema=slow_ema)
        logger.debug(
            "TrendDetection(fast={}, slow={}): {} (fast_ema={}, slow_ema={})",
            fast_period, slow_period, trend, fast_ema, slow_ema,
        )
        return result
