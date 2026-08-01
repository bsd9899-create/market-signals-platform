"""
tests/test_position_and_trade_reports.py
-----------------------------------------------
اختبار حقيقي لـPositionEventFormatter وTradeReportFormatter - بلا أي
اتصال شبكة، بيانات يدوية جاهزة فقط.
"""

from __future__ import annotations

from datetime import datetime, timezone

from app.infrastructure.telegram.position_event_formatter import PositionEventFormatter
from app.infrastructure.telegram.trade_report_formatter import TradeReportFormatter
from app.infrastructure.tracking.models import PositionEvent, TradeReportData
from app.infrastructure.tracking.statistics import TradeStatistics


def _event(kind: str, profit: float | None = 1.5) -> PositionEvent:
    return PositionEvent(
        kind=kind, trade_id=1, symbol="AAPL", option_type="CALL", strike=305.0,
        price=310.2, occurred_at=datetime(2026, 8, 1, 15, 30, tzinfo=timezone.utc), profit_loss_percent=profit,
    )


def test_tp1_hit_formatter_includes_required_fields() -> None:
    text = PositionEventFormatter().format(_event("TP1_HIT"))
    assert "✅ TP1 HIT" in text
    assert "AAPL" in text
    assert "305.0" in text
    assert "2026-08-01 15:30 UTC" in text
    assert "+1.50%" in text


def test_tp2_hit_formatter_title() -> None:
    text = PositionEventFormatter().format(_event("TP2_HIT", profit=3.2))
    assert "🏆 TP2 HIT" in text
    assert "+3.20%" in text


def test_stop_hit_formatter_shows_negative_sign() -> None:
    text = PositionEventFormatter().format(_event("STOP_HIT", profit=-1.1))
    assert "❌ STOP LOSS HIT" in text
    assert "-1.10%" in text


def test_position_event_formatter_never_includes_disclaimer_or_debug() -> None:
    text = PositionEventFormatter().format(_event("TP1_HIT"))
    assert "بيانات الخيارات قد تتأخر" not in text  # لا معنى لتحذير الدخول على صفقة مغلقة/جارية أصلاً
    for forbidden in ('{"', "HTTP Status", "Response Body", "Traceback", "Exception"):
        assert forbidden not in text


def _stats() -> TradeStatistics:
    return TradeStatistics(
        total_trades=5, wins=3, losses=2, win_rate=60.0, average_rr=2.0, average_profit=1.8, average_loss=0.9,
        profit_factor=3.0, total_profit=5.4, total_loss=1.8, best_trade_symbol="NVDA", best_trade_profit=3.1,
        worst_trade_symbol="TSLA", worst_trade_profit=-0.9, best_symbol="NVDA", best_strategy="momentum",
        best_timeframe="5m",
    )


def test_trade_report_formatter_includes_all_required_fields() -> None:
    data = TradeReportData(
        period_label="يومي", period_value="2026-08-01", signals_sent=8, total_trades=5, call_count=3,
        put_count=2, tp1_count=4, tp2_count=2, stop_count=2, better_entry_count=1, re_entry_count=1,
        statistics=_stats(),
    )
    text = TradeReportFormatter().format(data)

    for expected in (
        "📊 التقرير يومي — 2026-08-01", "عدد الإشارات: 8", "عدد الصفقات: 5", "عدد CALL: 3", "عدد PUT: 2",
        "عدد TP1: 4", "عدد TP2: 2", "عدد Stop Loss: 2", "عدد Better Entry: 1", "عدد Re-entry: 1",
        "عدد الصفقات الرابحة: 3", "عدد الصفقات الخاسرة: 2", "نسبة النجاح: 60.0%",
        "إجمالي الربح: 5.4%", "إجمالي الخسارة: 1.8%", "متوسط الربح: 1.8%", "متوسط الخسارة: 0.9%",
        "أفضل صفقة: NVDA (3.1%)", "أسوأ صفقة: TSLA (-0.9%)", "أفضل سهم: NVDA", "أفضل استراتيجية: momentum",
        "أفضل فريم: 5m", "Profit Factor: 3.0", "Average RR: 2.0",
    ):
        assert expected in text


def test_trade_report_formatter_weekly_and_monthly_icons_differ() -> None:
    stats = _stats()
    weekly = TradeReportFormatter().format(
        TradeReportData("أسبوعي", "w1", 1, 1, 1, 0, 1, 0, 0, 0, 0, stats)
    )
    monthly = TradeReportFormatter().format(
        TradeReportData("شهري", "m1", 1, 1, 1, 0, 1, 0, 0, 0, 0, stats)
    )
    assert "📈 التقرير أسبوعي" in weekly
    assert "🗓️ التقرير شهري" in monthly


def test_trade_report_formatter_handles_empty_statistics_gracefully() -> None:
    empty_stats = TradeStatistics(
        total_trades=0, wins=0, losses=0, win_rate=0.0, average_rr=0.0, average_profit=0.0, average_loss=0.0,
        profit_factor=0.0, total_profit=0.0, total_loss=0.0, best_trade_symbol=None, best_trade_profit=None,
        worst_trade_symbol=None, worst_trade_profit=None, best_symbol=None, best_strategy=None, best_timeframe=None,
    )
    data = TradeReportData("يومي", "2026-08-01", 0, 0, 0, 0, 0, 0, 0, 0, 0, empty_stats)
    text = TradeReportFormatter().format(data)
    assert "أفضل صفقة: -" in text
    assert "أفضل سهم: -" in text
