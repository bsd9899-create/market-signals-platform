"""
app/infrastructure/indicators/indicators/rsi.py
------------------------------------------------------
RSI (Relative Strength Index) - طريقة وايلدر (Wilder's Smoothing)
القياسية، period=14 افتراضياً:

delta[i] = close[i] - close[i-1]
gain[i] = max(delta[i], 0)  |  loss[i] = max(-delta[i], 0)
أول avg_gain/avg_loss = متوسط بسيط لأول period قيمة من gain/loss
بعدها: avg[i] = (avg[i-1]*(period-1) + value[i]) / period  (تنعيم وايلدر)
RS = avg_gain / avg_loss   |   RSI = 100 - 100/(1+RS)

يحتاج period+1 شمعة على الأقل (period فرق سعري = period+1 سعر إغلاق).
"""

from __future__ import annotations

from typing import Any

import numpy as np
from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.utils import closes, to_optional_list, wilder_smooth
from app.infrastructure.market.models import Candle


class RSI(Indicator):
    name = "rsi"

    def min_candles_required(self, **params: Any) -> int:
        return int(params.get("period", 14)) + 1

    def calculate(self, candles: list[Candle], **params: Any) -> list[float | None]:
        period = int(params.get("period", 14))
        required = self.min_candles_required(period=period)
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        close = closes(candles)
        delta = np.diff(close)  # طوله = len(close) - 1
        gain = np.where(delta > 0, delta, 0.0)
        loss = np.where(delta < 0, -delta, 0.0)

        avg_gain = wilder_smooth(gain, period)
        avg_loss = wilder_smooth(loss, period)

        with np.errstate(divide="ignore", invalid="ignore"):
            rs = np.where(avg_loss == 0, np.inf, avg_gain / avg_loss)
            rsi = 100 - (100 / (1 + rs))
        rsi = np.where(np.isnan(avg_gain), np.nan, rsi)

        # rsi محسوبة على delta (طولها len(close)-1) - نُحاذيها مع close
        # بإضافة NaN في البداية لتطابق طول قائمة الشموع الأصلية.
        aligned = np.insert(rsi, 0, np.nan)

        result = to_optional_list(aligned)
        logger.debug("RSI(period={}): آخر قيمة = {}", period, result[-1])
        return result
