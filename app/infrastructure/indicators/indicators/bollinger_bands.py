"""
app/infrastructure/indicators/indicators/bollinger_bands.py
--------------------------------------------------------------------
Bollinger Bands - period=20, num_std=2 افتراضياً:

middle[i] = SMA(close, period)[i]
std[i] = الانحراف المعياري السكاني (Population, ddof=0) لـ close[i-period+1..i]
upper = middle + num_std * std   |   lower = middle - num_std * std
"""

from __future__ import annotations

from typing import Any

import numpy as np
from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.results import BollingerBandsResult
from app.infrastructure.indicators.utils import closes, sma_series, to_optional_list
from app.infrastructure.market.models import Candle


class BollingerBands(Indicator):
    name = "bollinger_bands"

    def min_candles_required(self, **params: Any) -> int:
        return int(params.get("period", 20))

    def calculate(self, candles: list[Candle], **params: Any) -> BollingerBandsResult:
        period = int(params.get("period", 20))
        num_std = float(params.get("num_std", 2.0))
        required = self.min_candles_required(period=period)
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        close = closes(candles)
        middle = sma_series(close, period)

        n = len(close)
        std = np.full(n, np.nan)
        for i in range(period - 1, n):
            std[i] = np.std(close[i - period + 1 : i + 1], ddof=0)

        upper = middle + num_std * std
        lower = middle - num_std * std

        result = BollingerBandsResult(
            upper=to_optional_list(upper),
            middle=to_optional_list(middle),
            lower=to_optional_list(lower),
        )
        logger.debug(
            "BollingerBands(period={}, num_std={}): آخر upper={}, middle={}, lower={}",
            period, num_std, result.upper[-1], result.middle[-1], result.lower[-1],
        )
        return result
