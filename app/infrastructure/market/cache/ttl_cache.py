"""
app/infrastructure/market/cache/ttl_cache.py
--------------------------------------------------
TTLCache: تخزين مؤقت بسيط في الذاكرة (In-Memory) مع صلاحية زمنية
(Time-To-Live) لكل عنصر. يستخدم time.monotonic() (وليس الوقت الفعلي
datetime.now()) حتى لا يتأثر بتغيّر ساعة النظام.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class _CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self, default_ttl_seconds: float = 60.0) -> None:
        self._default_ttl_seconds = default_ttl_seconds
        self._store: dict[str, _CacheEntry] = {}

    def set(self, key: str, value: Any, ttl_seconds: float | None = None) -> None:
        ttl = self._default_ttl_seconds if ttl_seconds is None else ttl_seconds
        self._store[key] = _CacheEntry(value=value, expires_at=time.monotonic() + ttl)

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() >= entry.expires_at:
            del self._store[key]  # منتهي الصلاحية - يُحذف عند أول قراءة له
            return None
        return entry.value

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)
