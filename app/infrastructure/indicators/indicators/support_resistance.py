"""
app/infrastructure/indicators/indicators/support_resistance.py
--------------------------------------------------------------------------
Support & Resistance - كشف القيعان/القمم المحلية (Fractal بسيط):
window=5 افتراضياً. الشمعة i تُعتبر دعماً إذا كان low[i] هو الأدنى ضمن
[i-window, i+window]، ومقاومة إذا كان high[i] هو الأعلى ضمن نفس النافذة.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.results import SupportResistanceResult
from app.infrastructure.indicators.utils import highs, lows
from app.infrastructure.market.models import Candle


class SupportResistance(Indicator):
    name = "support_resistance"

    def min_candles_required(self, **params: Any) -> int:
        window = int(params.get("window", 5))
        return 2 * window + 1

    def calculate(self, candles: list[Candle], **params: Any) -> SupportResistanceResult:
        window = int(params.get("window", 5))
        required = self.min_candles_required(window=window)
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        high = highs(candles)
        low = lows(candles)
        n = len(candles)

        support_levels: list[float] = []
        resistance_levels: list[float] = []
        for i in range(window, n - window):
            window_low = low[i - window : i + window + 1]
            window_high = high[i - window : i + window + 1]
            if low[i] == window_low.min():
                support_levels.append(float(low[i]))
            if high[i] == window_high.max():
                resistance_levels.append(float(high[i]))

        result = SupportResistanceResult(support_levels=support_levels, resistance_levels=resistance_levels)
        logger.debug(
            "SupportResistance(window={}): {} دعم، {} مقاومة",
            window, len(support_levels), len(resistance_levels),
        )
        return result
