"""
tests/test_reports.py
--------------------------
اختبار حقيقي لـ ReportEngine - قيم يدوية محسوبة بدقة.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from app.infrastructure.reports.exceptions import EmptyReportDataError
from app.infrastructure.reports.models import DailyStats
from app.infrastructure.reports.report_engine import ReportEngine
from app.infrastructure.signals.models import Signal, SignalDirection


def _signal(direction: SignalDirection, confidence: float, strategies: list[str] | None = None) -> Signal:
    return Signal(
        symbol="AAPL", timeframe="1h", direction=direction, confidence=confidence,
        entry=100.0, stop_loss=95.0 if direction != SignalDirection.NEUTRAL else None,
        take_profit=110.0 if direction != SignalDirection.NEUTRAL else None,
        risk_reward=2.0 if direction != SignalDirection.NEUTRAL else None,
        strategy_used=strategies or [], indicators_used=["rsi"], reasons=[],
        timestamp=datetime.now(timezone.utc),
    )


def test_win_rate_hand_verified() -> None:
    engine = ReportEngine()
    assert engine.win_rate(wins=3, losses=1) == 75.0
    assert engine.win_rate(wins=0, losses=0) == 0.0
    assert engine.win_rate(wins=0, losses=5) == 0.0
    assert engine.win_rate(wins=5, losses=0) == 100.0


def test_average_risk_reward_hand_verified() -> None:
    engine = ReportEngine()
    assert engine.average_risk_reward([1.5, 2.0, 2.5]) == 2.0
    assert engine.average_risk_reward([]) == 0.0


def test_daily_report_hand_verified() -> None:
    engine = ReportEngine()
    stats = DailyStats(report_date=date(2026, 8, 1), total_scans=10, signals_sent=4, wins=3, losses=1)
    summary = engine.daily_report(stats)
    assert summary.win_rate == 75.0
    assert summary.total_scans == 10
    assert summary.signals_sent == 4


def test_weekly_report_aggregates_correctly() -> None:
    engine = ReportEngine()
    days = [
        DailyStats(report_date=date(2026, 8, 1), total_scans=5, signals_sent=2, wins=1, losses=1),
        DailyStats(report_date=date(2026, 8, 2), total_scans=5, signals_sent=2, wins=2, losses=0),
    ]
    summary = engine.weekly_report(days)
    assert summary.week_start == date(2026, 8, 1)
    assert summary.week_end == date(2026, 8, 2)
    assert summary.total_scans == 10
    assert summary.signals_sent == 4
    assert summary.wins == 3
    assert summary.losses == 1
    assert summary.win_rate == 75.0


def test_weekly_report_empty_raises() -> None:
    with pytest.raises(EmptyReportDataError):
        ReportEngine().weekly_report([])


def test_monthly_report_aggregates_correctly() -> None:
    engine = ReportEngine()
    days = [
        DailyStats(report_date=date(2026, 8, d), total_scans=1, signals_sent=1, wins=1, losses=0)
        for d in range(1, 6)
    ]
    summary = engine.monthly_report(days)
    assert summary.total_scans == 5
    assert summary.wins == 5
    assert summary.win_rate == 100.0


def test_monthly_report_empty_raises() -> None:
    with pytest.raises(EmptyReportDataError):
        ReportEngine().monthly_report([])


def test_signal_statistics_counts_and_strategy_stats() -> None:
    engine = ReportEngine()
    signals = [
        _signal(SignalDirection.BUY, 80.0, strategies=["trend_following"]),
        _signal(SignalDirection.BUY, 70.0, strategies=["trend_following", "momentum"]),
        _signal(SignalDirection.SELL, 60.0, strategies=["reversal"]),
        _signal(SignalDirection.NEUTRAL, 50.0),
    ]
    stats = engine.signal_statistics(signals)

    assert stats.total == 4
    assert stats.buy_count == 2
    assert stats.sell_count == 1
    assert stats.neutral_count == 1
    assert stats.average_confidence == round((80 + 70 + 60 + 50) / 4, 2)

    strategy_by_name = {s.strategy_name: s for s in stats.strategy_statistics}
    assert strategy_by_name["trend_following"].signal_count == 2
    assert strategy_by_name["trend_following"].average_confidence == 75.0  # (80+70)/2
    assert strategy_by_name["momentum"].signal_count == 1
    assert strategy_by_name["reversal"].signal_count == 1


def test_signal_statistics_empty_list() -> None:
    stats = ReportEngine().signal_statistics([])
    assert stats.total == 0
    assert stats.average_confidence == 0.0


def test_performance_report_hand_verified() -> None:
    engine = ReportEngine()
    days = [
        DailyStats(report_date=date(2026, 8, 1), total_scans=5, signals_sent=2, wins=1, losses=1),
        DailyStats(report_date=date(2026, 8, 2), total_scans=5, signals_sent=2, wins=2, losses=0),
    ]
    ratios = [1.5, 2.0, 2.5]
    signals = [_signal(SignalDirection.BUY, 80.0), _signal(SignalDirection.BUY, 60.0)]

    summary = engine.performance_report(days, ratios, signals)

    assert summary.total_scans == 10
    assert summary.wins == 3
    assert summary.losses == 1
    assert summary.win_rate == 75.0
    assert summary.average_risk_reward == 2.0
    assert summary.average_confidence == 70.0


def test_performance_report_empty_raises() -> None:
    with pytest.raises(EmptyReportDataError):
        ReportEngine().performance_report([], [])
