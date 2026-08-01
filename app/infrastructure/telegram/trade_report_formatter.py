"""
app/infrastructure/telegram/trade_report_formatter.py
------------------------------------------------------------------
TradeReportFormatter: يحوّل TradeReportData (يومي/أسبوعي/شهري) إلى نص
رسالة Telegram - نفس أسلوب DailyReportFormatter الموجود (MessageBuilder
مباشرة، بلا فاصل/تحذير SignalFormatter) لكن بكل الحقول المطلوبة صراحة.
"""

from __future__ import annotations

from app.infrastructure.telegram.message_builder import MessageBuilder
from app.infrastructure.tracking.models import TradeReportData

_TITLE_ICON = {"يومي": "📊", "أسبوعي": "📈", "شهري": "🗓️"}


class TradeReportFormatter:
    def format(self, data: TradeReportData) -> str:
        stats = data.statistics
        icon = _TITLE_ICON.get(data.period_label, "📊")

        return (
            MessageBuilder()
            .line(f"{icon} التقرير {data.period_label} — {data.period_value}")
            .blank()
            .key_value("عدد الإشارات", data.signals_sent)
            .key_value("عدد الصفقات", data.total_trades)
            .key_value("عدد CALL", data.call_count)
            .key_value("عدد PUT", data.put_count)
            .key_value("عدد TP1", data.tp1_count)
            .key_value("عدد TP2", data.tp2_count)
            .key_value("عدد Stop Loss", data.stop_count)
            .key_value("عدد Better Entry", data.better_entry_count)
            .key_value("عدد Re-entry", data.re_entry_count)
            .blank()
            .key_value("عدد الصفقات الرابحة", stats.wins)
            .key_value("عدد الصفقات الخاسرة", stats.losses)
            .key_value("نسبة النجاح", f"{stats.win_rate}%")
            .blank()
            .key_value("إجمالي الربح", f"{stats.total_profit}%")
            .key_value("إجمالي الخسارة", f"{stats.total_loss}%")
            .key_value("متوسط الربح", f"{stats.average_profit}%")
            .key_value("متوسط الخسارة", f"{stats.average_loss}%")
            .blank()
            .key_value("أفضل صفقة", f"{stats.best_trade_symbol} ({stats.best_trade_profit}%)" if stats.best_trade_symbol else "-")
            .key_value("أسوأ صفقة", f"{stats.worst_trade_symbol} ({stats.worst_trade_profit}%)" if stats.worst_trade_symbol else "-")
            .key_value("أفضل سهم", stats.best_symbol or "-")
            .key_value("أفضل استراتيجية", stats.best_strategy or "-")
            .key_value("أفضل فريم", stats.best_timeframe or "-")
            .blank()
            .key_value("Profit Factor", stats.profit_factor)
            .key_value("Average RR", stats.average_rr)
            .build()
        )
