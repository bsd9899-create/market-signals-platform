"""
app/infrastructure/market/models/candle.py
------------------------------------------------
Candle: شمعة سعرية واحدة (OHLCV) - نموذج بيانات فقط (Dataclass)، بلا
أي منطق تحليل. Dataclass (وليس Pydantic) للاتساق مع بقية المشروع
(config/settings_models.py يستخدم نفس الأسلوب) وتفادي تبعية إضافية
غير مستخدَمة في أي مكان آخر.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
