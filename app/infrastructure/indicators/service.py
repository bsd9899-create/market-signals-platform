"""
app/infrastructure/indicators/service.py
-------------------------------------------
IndicatorService: نقطة الاستدعاء الموحَّدة لكل المؤشرات. لا "يعرف" أي
مؤشر بعينه - يتعامل فقط مع IndicatorRegistry، مما يحقق مبدأ الفتح
للتوسع/الإغلاق للتعديل (Open/Closed) فعلياً: إضافة مؤشر جديد لاحقاً
(حتى من كود خارج هذا المشروع) لا تتطلب أي تعديل على IndicatorService.

الاستخدام:
    service = IndicatorService()  # يُسجِّل الـ14 مؤشراً المبنية تلقائياً
    sma_values = service.calculate("sma", candles, period=20)

    # إضافة مؤشر جديد بدون تعديل أي كود قائم:
    service.register(MyCustomIndicator())
    result = service.calculate("my_custom", candles)
"""

from __future__ import annotations

from typing import Any

from loguru import logger

from app.infrastructure.indicators.base import Indicator
from app.infrastructure.indicators.indicators import default_registry
from app.infrastructure.indicators.registry import IndicatorRegistry
from app.infrastructure.market.models import Candle


class IndicatorService:
    def __init__(self, registry: IndicatorRegistry | None = None) -> None:
        self._registry = registry if registry is not None else default_registry()
        logger.info("IndicatorService: جاهز مع {} مؤشراً مسجَّلاً: {}", len(self._registry.names()), self._registry.names())

    def register(self, indicator: Indicator) -> None:
        """يسجّل مؤشراً جديداً (مبنياً أو خارجياً) - Open/Closed: لا يلمس
        أي كود قائم."""
        self._registry.register(indicator)
        logger.info("IndicatorService: تم تسجيل مؤشر جديد: {}", indicator.name)

    def calculate(self, name: str, candles: list[Candle], **params: Any) -> Any:
        indicator = self._registry.get(name)
        logger.info("IndicatorService.calculate: {} على {} شمعة (params={})", name, len(candles), params)
        result = indicator.calculate(candles, **params)
        logger.debug("IndicatorService.calculate: {} اكتمل بنجاح.", name)
        return result

    def available_indicators(self) -> list[str]:
        return self._registry.names()
