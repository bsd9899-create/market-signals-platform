"""
app/infrastructure/telegram/telegram_service.py
------------------------------------------------------
TelegramService: نقطة الاستخدام الوحيدة لإرسال أي رسالة - يستخدم
TelegramSender (افتراضياً LoggingTelegramSender - بلا اتصال حقيقي) +
المُنسِّقات (Formatters) المناسبة لكل نوع محتوى.
"""

from __future__ import annotations

from loguru import logger

from app.infrastructure.reports.models import DailyReportSummary
from app.infrastructure.signals.models import Signal
from app.infrastructure.telegram.alert_formatter import AlertFormatter, Severity
from app.infrastructure.telegram.daily_report_formatter import DailyReportFormatter
from app.infrastructure.telegram.sender import LoggingTelegramSender, TelegramSender
from app.infrastructure.telegram.signal_formatter import SignalFormatter


class TelegramService:
    def __init__(self, sender: TelegramSender | None = None) -> None:
        self._sender = sender or LoggingTelegramSender()
        self._signal_formatter = SignalFormatter()
        self._daily_report_formatter = DailyReportFormatter()
        self._alert_formatter = AlertFormatter()

    def send_message(self, chat_id: str, text: str) -> bool:
        result = self._sender.send(chat_id, text)
        logger.info("TelegramService.send_message: chat_id={} -> {}", chat_id, result)
        return result

    def send_signal_alert(self, chat_id: str, signal: Signal) -> bool:
        text = self._signal_formatter.format(signal)
        return self.send_message(chat_id, text)

    def send_daily_report(self, chat_id: str, summary: DailyReportSummary) -> bool:
        text = self._daily_report_formatter.format(summary)
        return self.send_message(chat_id, text)

    def send_alert(self, chat_id: str, title: str, body: str, severity: Severity = "info") -> bool:
        text = self._alert_formatter.format(title, body, severity)
        return self.send_message(chat_id, text)
