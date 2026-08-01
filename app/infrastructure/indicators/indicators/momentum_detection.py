"""
app/infrastructure/indicators/indicators/momentum_detection.py
--------------------------------------------------------------------------
Momentum Detection - يُرجع حكماً واحداً لآخر شمعة، بمعدل التغيّر
(Rate of Change) للسعر عبر period شمعة (10 افتراضياً):

roc% = (close[-1] - close[-1-period]) / close[-1-period] * 100
bullish: roc% > 0   |   bearish: roc% < 0   |   neutral: roc% == 0
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.results import MomentumDetectionResult
from app.infrastructure.indicators.utils import closes
from app.infrastructure.market.models import Candle


class MomentumDetection(Indicator):
    name = "momentum_detection"

    def min_candles_required(self, **params: Any) -> int:
        return int(params.get("period", 10)) + 1

    def calculate(self, candles: list[Candle], **params: Any) -> MomentumDetectionResult:
        period = int(params.get("period", 10))
        required = self.min_candles_required(period=period)
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        close = closes(candles)
        reference_price = close[-1 - period]
        roc_percent = (close[-1] - reference_price) / reference_price * 100

        if roc_percent > 0:
            momentum = "bullish"
        elif roc_percent < 0:
            momentum = "bearish"
        else:
            momentum = "neutral"

        result = MomentumDetectionResult(momentum=momentum, rate_of_change_percent=float(roc_percent))
        logger.debug("MomentumDetection(period={}): {} (roc%={})", period, momentum, roc_percent)
        return result
