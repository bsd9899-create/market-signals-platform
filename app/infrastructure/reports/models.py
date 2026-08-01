"""
app/infrastructure/reports/models.py
------------------------------------------
نماذج بيانات محرك التقارير - كلها Dataclasses مُجمَّدة.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True)
class DailyStats:
    """مدخل خام واحد لكل يوم - يُبنى من مصدر خارجي (قاعدة بيانات لاحقاً،
    أو بيانات مُختبَرة الآن)."""

    report_date: date
    total_scans: int
    signals_sent: int
    wins: int
    losses: int


@dataclass(frozen=True)
class DailyReportSummary:
    report_date: date
    total_scans: int
    signals_sent: int
    wins: int
    losses: int
    win_rate: float


@dataclass(frozen=True)
class WeeklyReportSummary:
    week_start: date
    week_end: date
    total_scans: int
    signals_sent: int
    wins: int
    losses: int
    win_rate: float


@dataclass(frozen=True)
class MonthlyReportSummary:
    month_start: date
    month_end: date
    total_scans: int
    signals_sent: int
    wins: int
    losses: int
    win_rate: float


@dataclass(frozen=True)
class StrategyStatistics:
    strategy_name: str
    signal_count: int
    average_confidence: float


@dataclass(frozen=True)
class SignalStatistics:
    total: int
    buy_count: int
    sell_count: int
    neutral_count: int
    average_confidence: float
    strategy_statistics: list[StrategyStatistics] = field(default_factory=list)


@dataclass(frozen=True)
class PerformanceReportSummary:
    total_scans: int
    signals_sent: int
    wins: int
    losses: int
    win_rate: float
    average_risk_reward: float
    average_confidence: float
