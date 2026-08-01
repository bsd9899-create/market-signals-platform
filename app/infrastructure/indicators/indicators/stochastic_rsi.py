"""
app/infrastructure/indicators/indicators/stochastic_rsi.py
------------------------------------------------------------------
Stochastic RSI - "ستوكاستيك" مطبَّق على RSI بدل السعر مباشرة.
rsi_period=14, stoch_period=14, k_period=3, d_period=3 افتراضياً:

rsi = RSI(close, rsi_period)
stoch_rsi[i] = (rsi[i] - min(rsi نافذة stoch_period)) / (max - min)
              (0.0 إذا كان max == min لتفادي القسمة على صفر)
%K = SMA(stoch_rsi, k_period) * 100
%D = SMA(%K, d_period)

يُعاد استخدام RSI (indicators/rsi.py) داخلياً - تركيب (Composition) بدل
تكرار حساب RSI من جديد.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.indicators.rsi import RSI
from app.infrastructure.indicators.results import StochasticRSIResult
from app.infrastructure.indicators.utils import sma_series, to_optional_list
from app.infrastructure.market.models import Candle


class StochasticRSI(Indicator):
    name = "stochastic_rsi"

    def min_candles_required(self, **params: Any) -> int:
        rsi_period = int(params.get("rsi_period", 14))
        stoch_period = int(params.get("stoch_period", 14))
        k_period = int(params.get("k_period", 3))
        d_period = int(params.get("d_period", 3))
        return rsi_period + stoch_period + k_period + d_period - 2

    def calculate(self, candles: list[Candle], **params: Any) -> StochasticRSIResult:
        rsi_period = int(params.get("rsi_period", 14))
        stoch_period = int(params.get("stoch_period", 14))
        k_period = int(params.get("k_period", 3))
        d_period = int(params.get("d_period", 3))
        required = self.min_candles_required(
            rsi_period=rsi_period, stoch_period=stoch_period, k_period=k_period, d_period=d_period,
        )
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        n = len(candles)
        rsi_full = RSI().calculate(candles, period=rsi_period)
        offset1 = rsi_period  # أول فهرس فيه RSI صالحة (راجع rsi.py)
        rsi_valid = np.array(rsi_full[offset1:], dtype=float)

        # المرحلة 1: Stochastic RSI الخام على rsi_valid (خالية من NaN)
        stoch_rel = np.full(len(rsi_valid), np.nan)
        for j in range(stoch_period - 1, len(rsi_valid)):
            window = rsi_valid[j - stoch_period + 1 : j + 1]
            lo, hi = window.min(), window.max()
            stoch_rel[j] = 0.0 if hi == lo else (rsi_valid[j] - lo) / (hi - lo)

        # المرحلة 2: %K = SMA(stoch_rel صالحة فقط) - قُصَّت لتفادي انتشار NaN عبر cumsum
        stoch_valid_only = stoch_rel[stoch_period - 1 :]
        k_on_valid = sma_series(stoch_valid_only, k_period)
        k_rel = np.full(len(rsi_valid), np.nan)
        k_rel[stoch_period - 1 :] = k_on_valid

        # المرحلة 3: %D = SMA(%K صالحة فقط)
        d_valid_start = stoch_period - 1 + k_period - 1
        d_on_valid = sma_series(k_rel[d_valid_start:], d_period)
        d_rel = np.full(len(rsi_valid), np.nan)
        d_rel[d_valid_start:] = d_on_valid

        k_full = np.full(n, np.nan)
        d_full = np.full(n, np.nan)
        k_full[offset1:] = k_rel * 100
        d_full[offset1:] = d_rel * 100

        result = StochasticRSIResult(k=to_optional_list(k_full), d=to_optional_list(d_full))
        logger.debug(
            "StochasticRSI(rsi={}, stoch={}, k={}, d={}): آخر %K={}, %D={}",
            rsi_period, stoch_period, k_period, d_period, result.k[-1], result.d[-1],
        )
        return result
