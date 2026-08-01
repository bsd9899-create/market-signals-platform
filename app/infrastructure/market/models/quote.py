"""
app/infrastructure/market/models/quote.py
-----------------------------------------------
Quote: عرض سعر لحظي (Bid/Ask/Last) - نموذج بيانات فقط (Dataclass).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Quote:
    symbol: str
    bid: float
    ask: float
    last: float
    spread: float
    timestamp: datetime
