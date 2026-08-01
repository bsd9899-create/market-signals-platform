"""
app/infrastructure/indicators/indicators/vwap.py
------------------------------------------------------
VWAP (Volume-Weighted Average Price) - تراكمي عبر كامل قائمة الشموع
المُعطاة (لا يوجد مفهوم "بداية جلسة تداول" هنا - ذلك قرار طبقة أعلى
تقرر أي نطاق شموع تُمرَّر):

typical_price[i] = (high[i] + low[i] + close[i]) / 3
vwap[i] = cumsum(typical_price * volume)[i] / cumsum(volume)[i]
"""

from __future__ import annotations

from typing import Any

import numpy as np
from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.utils import closes, highs, lows, to_optional_list, volumes
from app.infrastructure.market.models import Candle


class VWAP(Indicator):
    name = "vwap"

    def min_candles_required(self, **params: Any) -> int:
        return 1

    def calculate(self, candles: list[Candle], **params: Any) -> list[float | None]:
        required = self.min_candles_required()
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        typical_price = (highs(candles) + lows(candles) + closes(candles)) / 3.0
        volume = volumes(candles)
        cumulative_pv = np.cumsum(typical_price * volume)
        cumulative_v = np.cumsum(volume)

        with np.errstate(divide="ignore", invalid="ignore"):
            vwap = np.where(cumulative_v > 0, cumulative_pv / cumulative_v, np.nan)

        result = to_optional_list(vwap)
        logger.debug("VWAP: آخر قيمة = {}", result[-1])
        return result
