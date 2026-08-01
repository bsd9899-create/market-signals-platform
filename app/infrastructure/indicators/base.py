"""
app/infrastructure/indicators/base.py
--------------------------------------------
Indicator: الواجهة المجرَّدة (Abstract Base Class) التي يطبّقها كل
مؤشر. هذا هو أساس مبدأ الفتح للتوسع/الإغلاق للتعديل (Open/Closed):
إضافة مؤشر جديد = صف جديد يطبّق هذه الواجهة + تسجيله في
IndicatorRegistry، دون تعديل أي مؤشر قائم أو IndicatorService نفسه.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from app.infrastructure.market.models import Candle


class Indicator(ABC):
    name: ClassVar[str]
    """اسم فريد يُستخدم كمفتاح في IndicatorRegistry (مثال: "sma", "rsi")."""

    @abstractmethod
    def min_candles_required(self, **params: Any) -> int:
        """أقل عدد شموع مطلوب لحساب هذا المؤشر بالمعاملات المُعطاة -
        يُستخدم لرفع InsufficientDataError برسالة واضحة بدل خطأ حسابي غامض."""

    @abstractmethod
    def calculate(self, candles: list[Candle], **params: Any) -> Any:
        """يحسب المؤشر فعلياً. الشكل المُرجَع يختلف حسب المؤشر - راجع
        docstring كل مؤشر (list[float | None] غالباً، أو نتيجة مركَّبة
        من app/infrastructure/indicators/results.py)."""
