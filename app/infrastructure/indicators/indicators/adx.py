"""
app/infrastructure/indicators/indicators/adx.py
------------------------------------------------------
ADX (Average Directional Index) - طريقة وايلدر الأصلية، period=14
افتراضياً:

+DM[i] = high[i]-high[i-1]  إذا كانت > (low[i-1]-low[i]) و > 0، وإلا 0
-DM[i] = low[i-1]-low[i]    إذا كانت > (high[i]-high[i-1]) و > 0، وإلا 0
TR كما في atr.py
+DI = 100 * تنعيم_وايلدر(+DM) / تنعيم_وايلدر(TR)
-DI = 100 * تنعيم_وايلدر(-DM) / تنعيم_وايلدر(TR)
DX  = 100 * |+DI - -DI| / (+DI + -DI)
ADX = تنعيم وايلدر لـDX نفسها (تنعيم من الدرجة الثانية)
"""

from __future__ import annotations

from typing import Any

import numpy as np
from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.results import ADXResult
from app.infrastructure.indicators.utils import highs, lows, closes, to_optional_list, true_range, wilder_smooth
from app.infrastructure.market.models import Candle


class ADX(Indicator):
    name = "adx"

    def min_candles_required(self, **params: Any) -> int:
        period = int(params.get("period", 14))
        return 2 * period - 1

    def calculate(self, candles: list[Candle], **params: Any) -> ADXResult:
        period = int(params.get("period", 14))
        required = self.min_candles_required(period=period)
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        high = highs(candles)
        low = lows(candles)
        close = closes(candles)
        n = len(high)

        plus_dm = np.zeros(n)
        minus_dm = np.zeros(n)
        for i in range(1, n):
            up_move = high[i] - high[i - 1]
            down_move = low[i - 1] - low[i]
            plus_dm[i] = up_move if (up_move > down_move and up_move > 0) else 0.0
            minus_dm[i] = down_move if (down_move > up_move and down_move > 0) else 0.0

        tr = true_range(high, low, close)

        smoothed_tr = wilder_smooth(tr, period)
        smoothed_plus_dm = wilder_smooth(plus_dm, period)
        smoothed_minus_dm = wilder_smooth(minus_dm, period)

        with np.errstate(divide="ignore", invalid="ignore"):
            plus_di = 100 * smoothed_plus_dm / smoothed_tr
            minus_di = 100 * smoothed_minus_dm / smoothed_tr
            dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di)

        first_valid = period - 1
        adx = np.full(n, np.nan)
        adx[first_valid:] = wilder_smooth(dx[first_valid:], period)

        result = ADXResult(
            plus_di=to_optional_list(plus_di),
            minus_di=to_optional_list(minus_di),
            adx=to_optional_list(adx),
        )
        logger.debug(
            "ADX(period={}): آخر +DI={}, -DI={}, ADX={}",
            period, result.plus_di[-1], result.minus_di[-1], result.adx[-1],
        )
        return result
