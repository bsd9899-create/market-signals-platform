"""
app/infrastructure/market/models/market_status.py
---------------------------------------------------------
MarketStatus: حالة السوق اللحظية - نموذج بيانات فقط (Dataclass).
next_open/next_close قد تكونان None إذا لم يوفّرها المزود.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarketStatus:
    is_open: bool
    premarket: bool
    after_hours: bool
    next_open: datetime | None
    next_close: datetime | None
