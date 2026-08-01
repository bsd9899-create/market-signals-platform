"""
app/infrastructure/telegram/position_event_formatter.py
------------------------------------------------------------------
PositionEventFormatter: يحوّل PositionEvent (من PositionMonitor) إلى نص
رسالة Telegram - TP1 HIT / TP2 HIT / STOP LOSS HIT.
"""

from __future__ import annotations

from app.infrastructure.telegram.telegram_formatter import TelegramFormatter
from app.infrastructure.tracking.models import PositionEvent

_TITLE_BY_KIND = {"TP1_HIT": "✅ TP1 HIT", "TP2_HIT": "🏆 TP2 HIT", "STOP_HIT": "❌ STOP LOSS HIT"}


class PositionEventFormatter:
    def format(self, event: PositionEvent) -> str:
        sections = [
            _TITLE_BY_KIND[event.kind],
            f"Symbol: {event.symbol} ({event.option_type})",
            f"Strike: {event.strike:.1f}",
            f"وقت الوصول: {event.occurred_at.strftime('%Y-%m-%d %H:%M UTC')}",
        ]
        if event.profit_loss_percent is not None:
            sign = "+" if event.profit_loss_percent >= 0 else ""
            sections.append(f"نسبة الربح: {sign}{event.profit_loss_percent:.2f}%")
        return TelegramFormatter().render(sections, include_disclaimer=False)
