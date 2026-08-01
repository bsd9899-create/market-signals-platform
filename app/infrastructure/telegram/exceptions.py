"""
app/infrastructure/telegram/exceptions.py
--------------------------------------------------
استثناءات واضحة لطبقة Telegram.
"""

from __future__ import annotations


class TelegramError(Exception):
    """الأصل المشترك لكل أخطاء طبقة Telegram."""


class TelegramSendError(TelegramError):
    def __init__(self, chat_id: str, reason: str) -> None:
        super().__init__(f"فشل إرسال رسالة إلى chat_id={chat_id}: {reason}")
        self.chat_id = chat_id
        self.reason = reason
