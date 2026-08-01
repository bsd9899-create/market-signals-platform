"""
app/infrastructure/indicators/indicators/volume_spike.py
------------------------------------------------------------
Volume Spike: يكتشف حجم تداول أعلى بشكل ملحوظ من متوسطه - period=20،
threshold=2.0 (أي ضِعف المتوسط) افتراضياً. يُعيد استخدام VolumeAverage
داخلياً (تركيب).

ratio[i] = volume[i] / volume_average[i]
is_spike[i] = ratio[i] >= threshold  (False إذا كانت ratio غير معرَّفة)
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.indicators.volume_average import VolumeAverage
from app.infrastructure.indicators.results import VolumeSpikeResult
from app.infrastructure.indicators.utils import volumes
from app.infrastructure.market.models import Candle


class VolumeSpike(Indicator):
    name = "volume_spike"

    def min_candles_required(self, **params: Any) -> int:
        return int(params.get("period", 20))

    def calculate(self, candles: list[Candle], **params: Any) -> VolumeSpikeResult:
        period = int(params.get("period", 20))
        threshold = float(params.get("threshold", 2.0))
        required = self.min_candles_required(period=period)
        if len(candles) < required:
            raise InsufficientDataError(self.name, required, len(candles))

        volume = volumes(candles)
        avg = VolumeAverage().calculate(candles, period=period)

        ratio: list[float | None] = []
        is_spike: list[bool] = []
        for vol, avg_value in zip(volume, avg):
            if avg_value is None or avg_value == 0:
                ratio.append(None)
                is_spike.append(False)
            else:
                r = float(vol / avg_value)
                ratio.append(r)
                is_spike.append(r >= threshold)

        result = VolumeSpikeResult(ratio=ratio, is_spike=is_spike)
        logger.debug(
            "VolumeSpike(period={}, threshold={}): آخر ratio={}, is_spike={}",
            period, threshold, result.ratio[-1], result.is_spike[-1],
        )
        return result
