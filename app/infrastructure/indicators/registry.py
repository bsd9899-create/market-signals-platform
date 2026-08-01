"""
app/infrastructure/indicators/registry.py
------------------------------------------------
IndicatorRegistry: سجل بسيط اسم -> Indicator. IndicatorService يتعامل
معه فقط - لا يعرف شيئاً عن أي مؤشر بعينه، مما يحقق Open/Closed فعلياً:
إضافة مؤشر جديد لاحقاً = `registry.register(NewIndicator())` من أي
مكان، دون تعديل IndicatorRegistry أو IndicatorService.
"""

from __future__ import annotations

from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.exceptions import IndicatorNotFoundError


class IndicatorRegistry:
    def __init__(self) -> None:
        self._indicators: dict[str, Indicator] = {}

    def register(self, indicator: Indicator) -> None:
        self._indicators[indicator.name] = indicator
        logger.debug("IndicatorRegistry: سُجِّل مؤشر جديد: {}", indicator.name)

    def get(self, name: str) -> Indicator:
        try:
            return self._indicators[name]
        except KeyError:
            raise IndicatorNotFoundError(name) from None

    def names(self) -> list[str]:
        return sorted(self._indicators.keys())
