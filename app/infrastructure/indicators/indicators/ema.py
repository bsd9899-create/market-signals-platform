"""
app/infrastructure/indicators/indicators/ema.py
------------------------------------------------------
EMA (Exponential Moving Average): متوسط متحرك أسي - يدعم أي period
(وليس مقيَّداً بفترة واحدة ثابتة، بطلب صريح "جميع الفترات").

يُزرَع (Seed) بمتوسط بسيط لأول period قيمة، ثم:
EMA[i] = close[i] * k + EMA[i-1] * (1-k)   حيث k = 2 / (period + 1)
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.utils import closes, ema_series, to_optional_list
from app.infrastructure.market.models import Candle


class EMA(Indicator):
    name = "ema"

    def min_candles_required(self, **params: Any) -> int:
        return int(params.get("period", 20))

    def calculate(self, candles: list[Candle], **params: Any) -> list[float | None]:
        period = int(params.get("period", 20))
        required = self.min_candles_required(period=period)
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        result = to_optional_list(ema_series(closes(candles), period))
        logger.debug("EMA(period={}): آخر قيمة = {}", period, result[-1])
        return result
