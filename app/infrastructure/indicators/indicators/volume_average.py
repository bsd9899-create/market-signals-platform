"""
app/infrastructure/indicators/indicators/volume_average.py
------------------------------------------------------------------
Volume Average: متوسط بسيط لحجم التداول على period شمعة (نفس رياضيات
SMA لكن على العمود volume بدل close).
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.utils import sma_series, to_optional_list, volumes
from app.infrastructure.market.models import Candle


class VolumeAverage(Indicator):
    name = "volume_average"

    def min_candles_required(self, **params: Any) -> int:
        return int(params.get("period", 20))

    def calculate(self, candles: list[Candle], **params: Any) -> list[float | None]:
        period = int(params.get("period", 20))
        required = self.min_candles_required(period=period)
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        result = to_optional_list(sma_series(volumes(candles), period))
        logger.debug("VolumeAverage(period={}): آخر قيمة = {}", period, result[-1])
        return result
