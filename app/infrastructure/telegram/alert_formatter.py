"""
app/infrastructure/telegram/alert_formatter.py
-----------------------------------------------------
AlertFormatter: يُغلِّف أي نص رسالة بترويسة حسب مستوى الخطورة
(Severity) - info/warning/error/critical.
"""

from __future__ import annotations

from typing import Literal

from app.infrastructure.telegram.message_builder import MessageBuilder

Severity = Literal["info", "warning", "error", "critical"]

_SEVERITY_EMOJI: dict[Severity, str] = {
    "info": "ℹ️",
    "warning": "⚠️",
    "error": "🚨",
    "critical": "🆘",
}


class AlertFormatter:
    def format(self, title: str, body: str, severity: Severity = "info") -> str:
        return (
            MessageBuilder()
            .header(f"{_SEVERITY_EMOJI[severity]} {title}")
            .line(body)
            .build()
        )
