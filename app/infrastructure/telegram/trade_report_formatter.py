"""
app/infrastructure/telegram/trade_report_formatter.py
------------------------------------------------------------------
TradeReportFormatter: يحوّل TradeReportData (يومي/أسبوعي/شهري) إلى نص
رسالة Telegram - سطر واحد لكل صفقة مغلقة (رمز، نوع، Strike، Expiration،
الدخول، الأهداف، النتيجة، النسبة، ✅/❌) ثم ملخص مختصر أسفل الرسالة
(بطلب صريح). Telegram هنا **بلا parse_mode** (نص خام فقط - راجع
RealTelegramSender) فلا معنى لجدول Markdown/HTML حقيقي؛ كل صفقة تُعرَض
كبطاقة قصيرة مفصولة بسطر فارغ بدل ذلك - أقرب تمثيل "مرتب" مُمكن في نص
عادي.

الأهداف المعروضة هنا (tp1/tp2) هي مستويات **السهم الأساسي** المحفوظة في
Trade Journal فعلياً (نفس ما استُخدِم لتحديد النتيجة) - وليست علاوة
الخيار T1/T2/T3 المعروضة في رسالة التوصية الأصلية (تلك عرض فقط، غير
محفوظة - راجع signal_formatter.py).

الإحصاءات (الفائز/الخاسر/الأفضل/الأسوأ...) تُحسَب هنا داخلياً عبر
TradeStatisticsCalculator من closed_trades مباشرة - بلا أي ازدواج حساب
مع TradeStatisticsCalculator نفسه (يبقى بلا أي تعديل، وله اختباراته
المستقلة في test_tracking.py).
"""

from __future__ import annotations

from app.infrastructure.telegram.message_builder import MessageBuilder
from app.infrastructure.tracking.models import TradeReportData
from app.infrastructure.tracking.statistics import TradeStatisticsCalculator

_TITLE_ICON = {"يومي": "📊", "أسبوعي": "📈", "شهري": "🗓️"}
_RESULT_LABEL = {"TP2_HIT": "TP2 🎯", "STOPPED": "وقف 🛑"}


class TradeReportFormatter:
    def format(self, data: TradeReportData) -> str:
        icon = _TITLE_ICON.get(data.period_label, "📊")
        builder = MessageBuilder().line(f"{icon} التقرير {data.period_label} — {data.period_value}").blank()

        if not data.closed_trades:
            builder.line("لا صفقات مغلقة خلال هذه الفترة.").blank()
        else:
            for trade in data.closed_trades:
                builder.line(self._trade_row(trade)).blank()

        stats = TradeStatisticsCalculator().calculate(data.closed_trades)
        net_profit = round(stats.total_profit - stats.total_loss, 2)
        sign = "+" if net_profit >= 0 else ""

        return (
            builder
            .key_value("إجمالي الفرص", stats.total_trades)
            .key_value("الناجحة", stats.wins)
            .key_value("الخاسرة", stats.losses)
            .key_value("نسبة النجاح", f"{stats.win_rate}%")
            .key_value("إجمالي الربح", f"{sign}{net_profit}%")
            .key_value("أفضل صفقة", f"{stats.best_trade_symbol} ({stats.best_trade_profit:+}%)" if stats.best_trade_symbol else "-")
            .key_value("أسوأ صفقة", f"{stats.worst_trade_symbol} ({stats.worst_trade_profit:+}%)" if stats.worst_trade_symbol else "-")
            .build()
        )

    @staticmethod
    def _trade_row(trade) -> str:
        mark = "✅" if trade.status == "TP2_HIT" else "❌"
        result = _RESULT_LABEL.get(trade.status, trade.status)
        pnl = trade.profit_loss_percent or 0.0
        sign = "+" if pnl >= 0 else ""
        return (
            f"{mark} {trade.symbol} {trade.option_type} | Strike {trade.strike:g} | Exp {trade.expiration}\n"
            f"دخول {trade.option_entry_low:.2f}-{trade.option_entry_high:.2f}$ → {result} ({sign}{pnl}%)"
        )
