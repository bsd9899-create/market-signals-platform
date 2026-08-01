"""
app/infrastructure/reports/schedule.py
------------------------------------------
دوال بحتة (بلا حالة، بلا I/O) لتحديد متى يجب إرسال تقرير يومي/أسبوعي/
شهري - تُستهلَك من app/main.py الذي يحتفظ بحالة "آخر تاريخ أُرسِل فيه كل
تقرير" (نقطة التركيب فقط، لا منطق قرار هناك).
"""

from __future__ import annotations

from datetime import date, timedelta

_MARKET_CLOSE_HOUR_ET = 16  # ساعة إغلاق التداول العادي (4:00 مساءً بتوقيت شرق أمريكا)
_REPORT_WINDOW_END_HOUR_ET = 20  # حد أعلى أمان - لا تحاول الإرسال بعد هذه الساعة (تفادي أي إطلاق ليلي غريب)


def is_in_daily_report_window(now_et_hour: int) -> bool:
    """True بين إغلاق السوق العادي وحد أعلى أمان - نافذة إرسال تقرير اليوم."""
    return _MARKET_CLOSE_HOUR_ET <= now_et_hour < _REPORT_WINDOW_END_HOUR_ET


def is_friday(today: date) -> bool:
    return today.weekday() == 4


def is_last_trading_day_of_month(today: date) -> bool:
    """آخر يوم عمل (اثنين-جمعة) في الشهر - بلا تقويم عطلات رسمية (قيد
    موثَّق ومقصود - لا تبعية تقويم تداول إضافية في هذه المرحلة).
    امتد today نفسه يوم عمل أولاً - وإلا False فوراً (نهاية أسبوع لا
    تُعتبر أبداً "آخر يوم تداول" حتى لو كانت آخر يوم تقويمي في الشهر)."""
    if today.weekday() >= 5:
        return False
    probe = today + timedelta(days=1)
    while probe.month == today.month:
        if probe.weekday() < 5:
            return False
        probe += timedelta(days=1)
    return True
