"""
app/infrastructure/indicators/utils.py
--------------------------------------------
دوال مساعدة مشتركة (رياضيات أساسية فقط) تستخدمها عدة مؤشرات - وليست
مؤشرات بحد ذاتها. كل دالة هنا تعمل على مصفوفات numpy مستخرجة من
Candle، وتُرجع NaN (وليس None) في الفهارس التي لا تملك بيانات كافية -
IndicatorResult في كل مؤشر يحوّل NaN إلى None عند الإرجاع النهائي
للمستخدم (راجع _to_optional_list أدناه).
"""

from __future__ import annotations

import numpy as np

from app.infrastructure.market.models import Candle


def closes(candles: list[Candle]) -> np.ndarray:
    return np.array([c.close for c in candles], dtype=float)


def highs(candles: list[Candle]) -> np.ndarray:
    return np.array([c.high for c in candles], dtype=float)


def lows(candles: list[Candle]) -> np.ndarray:
    return np.array([c.low for c in candles], dtype=float)


def volumes(candles: list[Candle]) -> np.ndarray:
    return np.array([c.volume for c in candles], dtype=float)


def to_optional_list(values: np.ndarray) -> list[float | None]:
    """يحوّل مصفوفة numpy (قد تحتوي NaN) إلى list[float | None] عادية -
    شكل الإرجاع النهائي الموحَّد لكل المؤشرات (بدل NaN غير المفهومة
    للمستخدم النهائي)."""
    return [None if np.isnan(v) else float(v) for v in values]


def sma_series(values: np.ndarray, period: int) -> np.ndarray:
    """المتوسط المتحرك البسيط - NaN للفهارس الأولى التي لا تملك period
    قيمة سابقة كافية."""
    n = len(values)
    result = np.full(n, np.nan)
    if period <= 0 or n < period:
        return result
    cumsum = np.cumsum(np.insert(values, 0, 0.0))
    result[period - 1 :] = (cumsum[period:] - cumsum[:-period]) / period
    return result


def ema_series(values: np.ndarray, period: int) -> np.ndarray:
    """المتوسط المتحرك الأسي: يُزرَع (Seed) بـSMA لأول period قيمة، ثم
    مُعادلة EMA القياسية بعدها - k = 2 / (period + 1)."""
    n = len(values)
    result = np.full(n, np.nan)
    if period <= 0 or n < period:
        return result

    k = 2.0 / (period + 1)
    result[period - 1] = np.mean(values[:period])
    for i in range(period, n):
        result[i] = values[i] * k + result[i - 1] * (1 - k)
    return result


def wilder_smooth(values: np.ndarray, period: int) -> np.ndarray:
    """تنعيم وايلدر (Wilder's Smoothing) - المستخدَم في RSI/ATR/ADX
    الأصليين: أول قيمة = متوسط بسيط لأول period قيمة، ثم
    smoothed[i] = (smoothed[i-1] * (period-1) + values[i]) / period."""
    n = len(values)
    result = np.full(n, np.nan)
    if period <= 0 or n < period:
        return result

    result[period - 1] = np.mean(values[:period])
    for i in range(period, n):
        result[i] = (result[i - 1] * (period - 1) + values[i]) / period
    return result


def true_range(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
    """المدى الحقيقي (True Range) - يحتاج الإغلاق السابق، لذا الفهرس 0
    يستخدم high[0]-low[0] فقط (لا يوجد إغلاق سابق)."""
    n = len(high)
    tr = np.empty(n)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        tr[i] = max(
            high[i] - low[i],
            abs(high[i] - close[i - 1]),
            abs(low[i] - close[i - 1]),
        )
    return tr
