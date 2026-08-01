"""
app/infrastructure/tracking/event_counters.py
------------------------------------------------------
EventCounterTracker: عدّادات يومية بسيطة (في الذاكرة فقط) لأحداث
التقرير اليومي التي لا تُشتَق بسهولة من Trade Journal وحده (عدد
CALL/PUT المُرسَلة، BETTER ENTRY، RE-ENTRY) - تُصفَّر تلقائياً عند بداية
يوم تداول جديد (مقارنة بالتاريخ الحالي عند كل استدعاء).
"""

from __future__ import annotations

from datetime import date

from app.infrastructure.tracking.models import DailyCounters


class EventCounterTracker:
    def __init__(self) -> None:
        self._counters: DailyCounters | None = None

    def _ensure_today(self, today: date) -> DailyCounters:
        if self._counters is None or self._counters.trading_date != today:
            self._counters = DailyCounters(trading_date=today)
        return self._counters

    def record_signal_sent(self, today: date, option_type: str, is_better_entry: bool, is_re_entry: bool) -> None:
        counters = self._ensure_today(today)
        counters.signals_sent += 1
        if option_type == "CALL":
            counters.call_count += 1
        elif option_type == "PUT":
            counters.put_count += 1
        if is_better_entry:
            counters.better_entry_count += 1
        if is_re_entry:
            counters.re_entry_count += 1

    def snapshot(self, today: date) -> DailyCounters:
        return self._ensure_today(today)

    def reset(self, today: date) -> None:
        self._counters = DailyCounters(trading_date=today)
