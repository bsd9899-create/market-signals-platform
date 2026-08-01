"""
tests/test_report_schedule.py
----------------------------------
اختبار حقيقي لدوال app/infrastructure/reports/schedule.py - بحتة بلا
حالة، تواريخ ثابتة يدوية (بلا Mock، بلا شبكة).
"""

from __future__ import annotations

from datetime import date

from app.infrastructure.reports.schedule import (
    is_friday,
    is_in_daily_report_window,
    is_last_trading_day_of_month,
)


def test_is_in_daily_report_window_true_after_close() -> None:
    assert is_in_daily_report_window(16) is True
    assert is_in_daily_report_window(19) is True


def test_is_in_daily_report_window_false_before_close_or_too_late() -> None:
    assert is_in_daily_report_window(15) is False
    assert is_in_daily_report_window(9) is False
    assert is_in_daily_report_window(20) is False
    assert is_in_daily_report_window(23) is False


def test_is_friday_true_only_on_friday() -> None:
    assert is_friday(date(2026, 8, 7)) is True  # جمعة فعلية
    assert is_friday(date(2026, 8, 6)) is False  # خميس


def test_is_last_trading_day_of_month_true_for_weekday_month_end() -> None:
    # أغسطس 2026 ينتهي يوم الاثنين 2026-08-31
    assert is_last_trading_day_of_month(date(2026, 8, 31)) is True
    assert is_last_trading_day_of_month(date(2026, 8, 28)) is False


def test_is_last_trading_day_of_month_skips_weekend_to_friday() -> None:
    # سبتمبر 2026 ينتهي يوم الأربعاء 2026-09-30 (يوم عمل) - نتحقق حالة
    # مختلفة: شهر ينتهي بعطلة أسبوعية. نوفمبر 2026 ينتهي الاثنين 30 -
    # لنستخدم شهراً ينتهي بيوم أحد فعلياً: مايو 2026 ينتهي الأحد 31.
    assert is_last_trading_day_of_month(date(2026, 5, 29)) is True  # الجمعة الأخيرة قبل عطلة نهاية الشهر
    assert is_last_trading_day_of_month(date(2026, 5, 31)) is False  # الأحد نفسه ليس يوم عمل
    assert is_last_trading_day_of_month(date(2026, 5, 28)) is False  # ليس الأخير
