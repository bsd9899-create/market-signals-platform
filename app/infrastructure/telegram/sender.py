"""
app/infrastructure/telegram/sender.py
--------------------------------------------
TelegramSender: الواجهة المجرَّدة لإرسال رسالة فعلياً - نفس فلسفة
MarketDataProvider/NewsProvider/OptionsProvider تماماً (Open/Closed).

LoggingTelegramSender: التطبيق الوحيد المتاح الآن - **لا يتصل بأي
شبكة ولا يستخدم أي توكن حقيقي إطلاقاً** - فقط يسجّل الرسالة عبر Loguru
ويُرجع True (محاكاة إرسال ناجح). ربط بوت Telegram حقيقي لاحقاً = كتابة
TelegramSender جديد (مثال: RealTelegramSender يستخدم python-telegram-bot)
دون أي تعديل على TelegramService.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from loguru import logger


class TelegramSender(ABC):
    @abstractmethod
    def send(self, chat_id: str, text: str) -> bool: ...


class LoggingTelegramSender(TelegramSender):
    def send(self, chat_id: str, text: str) -> bool:
        logger.info("LoggingTelegramSender (بلا اتصال حقيقي) - chat_id={} | الرسالة:\n{}", chat_id, text)
        return True
