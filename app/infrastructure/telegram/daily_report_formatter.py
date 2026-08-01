"""
app/infrastructure/telegram/daily_report_formatter.py
------------------------------------------------------------
DailyReportFormatter: يحوّل DailyReportSummary إلى نص رسالة Telegram.
"""

from __future__ import annotations

from app.infrastructure.reports.models import DailyReportSummary
from app.infrastructure.telegram.message_builder import MessageBuilder


class DailyReportFormatter:
    def format(self, summary: DailyReportSummary) -> str:
        return (
            MessageBuilder()
            .header(f"📊 التقرير اليومي — {summary.report_date}")
            .key_value("إجمالي الفحوصات", summary.total_scans)
            .key_value("الإشارات المُرسَلة", summary.signals_sent)
            .key_value("الفوز (Wins)", summary.wins)
            .key_value("الخسارة (Losses)", summary.losses)
            .key_value("نسبة الفوز (Win Rate)", f"{summary.win_rate}%")
            .build()
        )
