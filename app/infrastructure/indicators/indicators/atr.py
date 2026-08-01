"""
app/infrastructure/indicators/indicators/atr.py
------------------------------------------------------
ATR (Average True Range) - طريقة وايلدر، period=14 افتراضياً:

TR[i] = max(high[i]-low[i], |high[i]-close[i-1]|, |low[i]-close[i-1]|)
ATR = تنعيم وايلدر لـTR (نفس أسلوب RSI - راجع utils.wilder_smooth)
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.utils import closes, highs, lows, to_optional_list, true_range, wilder_smooth
from app.infrastructure.market.models import Candle


class ATR(Indicator):
    name = "atr"

    def min_candles_required(self, **params: Any) -> int:
        return int(params.get("period", 14))

    def calculate(self, candles: list[Candle], **params: Any) -> list[float | None]:
        period = int(params.get("period", 14))
        required = self.min_candles_required(period=period)
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        tr = true_range(highs(candles), lows(candles), closes(candles))
        atr = wilder_smooth(tr, period)

        result = to_optional_list(atr)
        logger.debug("ATR(period={}): آخر قيمة = {}", period, result[-1])
        return result
