"""
app/infrastructure/indicators/indicators/macd.py
------------------------------------------------------
MACD (Moving Average Convergence Divergence) - fast=12, slow=26,
signal=9 افتراضياً:

macd_line[i] = EMA_fast[i] - EMA_slow[i]
signal_line = EMA(macd_line صالحة فقط, period=signal)
histogram = macd_line - signal_line
"""

from __future__ import annotations

from typing import Any

import numpy as np
from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.results import MACDResult
from app.infrastructure.indicators.utils import closes, ema_series, to_optional_list
from app.infrastructure.market.models import Candle


class MACD(Indicator):
    name = "macd"

    def min_candles_required(self, **params: Any) -> int:
        slow = int(params.get("slow_period", 26))
        signal = int(params.get("signal_period", 9))
        return slow + signal - 1

    def calculate(self, candles: list[Candle], **params: Any) -> MACDResult:
        fast_period = int(params.get("fast_period", 12))
        slow_period = int(params.get("slow_period", 26))
        signal_period = int(params.get("signal_period", 9))
        required = self.min_candles_required(slow_period=slow_period, signal_period=signal_period)
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        close = closes(candles)
        ema_fast = ema_series(close, fast_period)
        ema_slow = ema_series(close, slow_period)
        macd_line = ema_fast - ema_slow  # NaN تنتشر تلقائياً حيث أي طرف NaN

        first_valid = slow_period - 1
        signal_line = np.full(len(close), np.nan)
        signal_line[first_valid:] = ema_series(macd_line[first_valid:], signal_period)

        histogram = macd_line - signal_line

        result = MACDResult(
            macd_line=to_optional_list(macd_line),
            signal_line=to_optional_list(signal_line),
            histogram=to_optional_list(histogram),
        )
        logger.debug(
            "MACD(fast={}, slow={}, signal={}): آخر macd={}, signal={}, hist={}",
            fast_period, slow_period, signal_period,
            result.macd_line[-1], result.signal_line[-1], result.histogram[-1],
        )
        return result
