"""
app/infrastructure/indicators/indicators
----------------------------------------------
14 مؤشراً مبنياً (Built-in) - كل واحد في ملفه المستقل. default_registry()
تُسجِّلها جميعاً في IndicatorRegistry جديد - هذه هي الدالة الوحيدة التي
"تعرف" بكل المؤشرات المبنية؛ إضافة مؤشر مبنيّ جديد يعني إضافته هنا
فقط، بينما إضافة مؤشر خارجي (من كود مستهلك آخر) لا تحتاج لمس هذا
الملف إطلاقاً - فقط `service.register(MyIndicator())` مباشرة.
"""

from __future__ import annotations

from app.infrastructure.indicators.indicators.adx import ADX
from app.infrastructure.indicators.indicators.atr import ATR
from app.infrastructure.indicators.indicators.bollinger_bands import BollingerBands
from app.infrastructure.indicators.indicators.ema import EMA
from app.infrastructure.indicators.indicators.macd import MACD
from app.infrastructure.indicators.indicators.momentum_detection import MomentumDetection
from app.infrastructure.indicators.indicators.rsi import RSI
from app.infrastructure.indicators.indicators.sma import SMA
from app.infrastructure.indicators.indicators.stochastic_rsi import StochasticRSI
from app.infrastructure.indicators.indicators.support_resistance import SupportResistance
from app.infrastructure.indicators.indicators.trend_detection import TrendDetection
from app.infrastructure.indicators.indicators.volume_average import VolumeAverage
from app.infrastructure.indicators.indicators.volume_spike import VolumeSpike
from app.infrastructure.indicators.indicators.vwap import VWAP
from app.infrastructure.indicators.registry import IndicatorRegistry

__all__ = [
    "ADX", "ATR", "BollingerBands", "EMA", "MACD", "MomentumDetection", "RSI", "SMA",
    "StochasticRSI", "SupportResistance", "TrendDetection", "VolumeAverage", "VolumeSpike", "VWAP",
    "default_registry",
]


def default_registry() -> IndicatorRegistry:
    """يُنشئ IndicatorRegistry جديداً مع تسجيل كل الـ14 مؤشراً المبنية."""
    registry = IndicatorRegistry()
    for indicator_cls in (
        SMA, EMA, RSI, MACD, VWAP, ATR, BollingerBands, ADX, StochasticRSI,
        VolumeAverage, VolumeSpike, SupportResistance, TrendDetection, MomentumDetection,
    ):
        registry.register(indicator_cls())
    return registry
