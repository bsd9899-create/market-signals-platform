"""
tests/test_position_and_trade_reports.py
-----------------------------------------------
اختبار حقيقي لـPositionEventFormatter وTradeReportFormatter - بلا أي
اتصال شبكة، بيانات يدوية جاهزة فقط.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from app.infrastructure.telegram.position_event_formatter import PositionEventFormatter
from app.infrastructure.telegram.trade_report_formatter import TradeReportFormatter
from app.infrastructure.tracking.models import PositionEvent, TradeReportData


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


def _trade(symbol: str, option_type: str, strike: float, status: str, pnl: float) -> SimpleNamespace:
    return SimpleNamespace(
        symbol=symbol, option_type=option_type, strike=strike, expiration="2026-08-07",
        option_entry_low=2.15, option_entry_high=2.35, status=status, profit_loss_percent=pnl,
        risk_reward=2.0, timeframe="5m", strategy="momentum",
    )


def test_trade_report_formatter_includes_all_required_fields() -> None:
    data = TradeReportData(
        period_label="يومي", period_value="2026-08-01",
        closed_trades=[
            _trade("NVDA", "CALL", 205.0, "TP2_HIT", 3.1),
            _trade("TSLA", "PUT", 290.0, "STOPPED", -0.9),
        ],
    )
    text = TradeReportFormatter().format(data)

    for expected in (
        "📊 التقرير يومي — 2026-08-01",
        "✅ NVDA CALL", "Strike 205", "TP2 🎯", "+3.1%",
        "❌ TSLA PUT", "Strike 290", "وقف 🛑", "-0.9%",
        "إجمالي الفرص: 2", "الناجحة: 1", "الخاسرة: 1", "نسبة النجاح: 50.0%",
        "إجمالي الربح: +2.2%", "أفضل صفقة: NVDA (+3.1%)", "أسوأ صفقة: TSLA (-0.9%)",
    ):
        assert expected in text


def test_trade_report_formatter_weekly_and_monthly_icons_differ() -> None:
    trades = [_trade("NVDA", "CALL", 205.0, "TP2_HIT", 3.1)]
    weekly = TradeReportFormatter().format(TradeReportData("أسبوعي", "w1", trades))
    monthly = TradeReportFormatter().format(TradeReportData("شهري", "m1", trades))
    assert "📈 التقرير أسبوعي" in weekly
    assert "🗓️ التقرير شهري" in monthly


def test_trade_report_formatter_handles_no_closed_trades_gracefully() -> None:
    data = TradeReportData("يومي", "2026-08-01", closed_trades=[])
    text = TradeReportFormatter().format(data)
    assert "لا صفقات مغلقة خلال هذه الفترة." in text
    assert "أفضل صفقة: -" in text
    assert "إجمالي الفرص: 0" in text
