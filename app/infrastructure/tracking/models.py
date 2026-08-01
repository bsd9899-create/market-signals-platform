"""
app/infrastructure/tracking/models.py
--------------------------------------------
PositionEvent: نتيجة مراقبة مركز مفتوح واحد (بيانات فقط).

DailyCounters: عدّادات يومية بسيطة لأحداث لا تُشتَق من Trade Journal
وحده بسهولة (عدد BETTER ENTRY/RE-ENTRY المُرسَلة فعلياً) - تُصفَّر مع كل
يوم تداول جديد (راجع EventCounterTracker).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from app.infrastructure.tracking.statistics import TradeStatistics

PositionEventKind = Literal["TP1_HIT", "TP2_HIT", "STOP_HIT"]


@dataclass(frozen=True)
class PositionEvent:
    kind: PositionEventKind
    trade_id: int
    symbol: str
    option_type: str
    strike: float
    price: float
    occurred_at: datetime
    profit_loss_percent: float | None = None


@dataclass
class DailyCounters:
    trading_date: date
    signals_sent: int = 0
    call_count: int = 0
    put_count: int = 0
    better_entry_count: int = 0
    re_entry_count: int = 0


@dataclass(frozen=True)
class TradeReportData:
    """مدخل جاهز لـ TradeReportFormatter - يُبنى في app/main.py من
    EventCounterTracker + TradeJournal + TradeStatisticsCalculator معاً."""

    period_label: str  # "يومي" / "أسبوعي" / "شهري"
    period_value: str  # نص جاهز (تاريخ أو نطاق تاريخ)
    signals_sent: int
    total_trades: int
    call_count: int
    put_count: int
    tp1_count: int
    tp2_count: int
    stop_count: int
    better_entry_count: int
    re_entry_count: int
    statistics: "TradeStatistics"
