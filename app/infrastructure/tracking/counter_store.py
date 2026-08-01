"""
app/infrastructure/tracking/counter_store.py
------------------------------------------------
DailyCounterStore: يحفظ/يستعيد DailyCounters ليوم تداول واحد عبر
BotState (مخزن key/value عام موجود بالفعل، بلا أي تعديل على بنيته) -
يُستخدَم فقط عند انتقال EventCounterTracker ليوم جديد (لحفظ ملخص اليوم
المنتهي قبل تصفيره)، والتقارير الأسبوعية/الشهرية (لجمع أيام سابقة لم
تعد في الذاكرة).
"""

from __future__ import annotations

import json
from datetime import date, timedelta

from loguru import logger

from app.infrastructure.database.database import DatabaseManager
from app.infrastructure.database.repositories.bot_state_repository import BotStateRepository
from app.infrastructure.tracking.models import DailyCounters

_KEY_PREFIX = "daily_counters:"


class DailyCounterStore:
    def __init__(self, db_manager: DatabaseManager) -> None:
        self._db = db_manager

    def save(self, counters: DailyCounters) -> None:
        key = f"{_KEY_PREFIX}{counters.trading_date.isoformat()}"
        payload = json.dumps({
            "signals_sent": counters.signals_sent, "call_count": counters.call_count,
            "put_count": counters.put_count, "better_entry_count": counters.better_entry_count,
            "re_entry_count": counters.re_entry_count,
        })
        with self._db.session() as session:
            BotStateRepository(session).set_value(key, payload)
        logger.debug("DailyCounterStore.save: {}", key)

    def load(self, trading_date: date) -> DailyCounters | None:
        key = f"{_KEY_PREFIX}{trading_date.isoformat()}"
        with self._db.session() as session:
            state = BotStateRepository(session).get_by_key(key)
        if state is None or not state.value:
            return None
        data = json.loads(state.value)
        return DailyCounters(trading_date=trading_date, **data)

    def load_range(self, start: date, end: date) -> list[DailyCounters]:
        results: list[DailyCounters] = []
        current = start
        while current <= end:
            loaded = self.load(current)
            if loaded is not None:
                results.append(loaded)
            current += timedelta(days=1)
        return results
