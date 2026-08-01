"""
app/infrastructure/indicators/indicators/sma.py
------------------------------------------------------
SMA (Simple Moving Average): متوسط الإغلاق البسيط على period شمعة.

SMA[i] = mean(close[i-period+1 .. i])   لـ i >= period-1، وإلا None.
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.utils import closes, sma_series, to_optional_list
from app.infrastructure.market.models import Candle


class SMA(Indicator):
    name = "sma"

    def min_candles_required(self, **params: Any) -> int:
        return int(params.get("period", 20))

    def calculate(self, candles: list[Candle], **params: Any) -> list[float | None]:
        period = int(params.get("period", 20))
        required = self.min_candles_required(period=period)
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        result = to_optional_list(sma_series(closes(candles), period))
        logger.debug("SMA(period={}): آخر قيمة = {}", period, result[-1])
        return result
