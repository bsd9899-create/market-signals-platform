"""
app/infrastructure/telegram/command_listener.py
------------------------------------------------------
TelegramCommandListener: يجلب رسائل Telegram الواردة فعلياً عبر
getUpdates (Long Polling حقيقي - Telegram Bot API الرسمي) - **بلا أي
منطق أوامر هنا** (تفسير النص/الرد يعيش في app/main.py حصراً) - فقط
يُرجِع الرسائل الجديدة كنص خام، ويُقدِّم offset تلقائياً بعد كل استدعاء
لتفادي إعادة معالجة نفس الرسالة مرتين.

يستخدم httpx (نفس مكتبة RealTelegramSender - بلا أي تبعية إضافية).
عند أي فشل (شبكة/HTTP غير 200 - مثال: 409 Conflict إذا كان هناك
Webhook مُفعَّل مسبقاً على نفس البوت) يُرجِع قائمة فارغة بعد انتظار قصير
(تفادي حلقة فشل متكرر بلا توقف) - بلا رفع استثناء.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import httpx
from loguru import logger

_TELEGRAM_API_BASE = "https://api.telegram.org"
_ERROR_BACKOFF_SECONDS = 3.0


@dataclass(frozen=True)
class IncomingMessage:
    chat_id: str
    text: str
    update_id: int


class TelegramCommandListener:
    def __init__(self, bot_token: str, poll_timeout_seconds: float = 25.0) -> None:
        self._bot_token = bot_token
        self._poll_timeout_seconds = poll_timeout_seconds
        self._client = httpx.Client(timeout=poll_timeout_seconds + 10.0)
        self._offset: int | None = None

    def poll(self) -> list[IncomingMessage]:
        """طلب Long Polling واحد (يحظر حتى poll_timeout_seconds أو حتى
        وصول تحديث جديد أيهما أقرب) - يُرجِع الرسائل النصية الجديدة فقط."""
        url = f"{_TELEGRAM_API_BASE}/bot{self._bot_token}/getUpdates"
        params: dict[str, object] = {"timeout": int(self._poll_timeout_seconds)}
        if self._offset is not None:
            params["offset"] = self._offset

        try:
            response = self._client.get(url, params=params)
        except httpx.HTTPError as exc:
            logger.warning("TelegramCommandListener.poll: خطأ شبكة: {}", exc)
            time.sleep(_ERROR_BACKOFF_SECONDS)
            return []

        if response.status_code != 200:
            logger.warning("TelegramCommandListener.poll: HTTP {} - {}", response.status_code, response.text)
            time.sleep(_ERROR_BACKOFF_SECONDS)
            return []

        updates = response.json().get("result", [])
        messages: list[IncomingMessage] = []
        for update in updates:
            update_id = update.get("update_id")
            if update_id is not None:
                self._offset = update_id + 1

            message = update.get("message") or {}
            text = message.get("text")
            chat = message.get("chat") or {}
            chat_id = chat.get("id")
            if text is not None and chat_id is not None and update_id is not None:
                messages.append(IncomingMessage(chat_id=str(chat_id), text=text, update_id=update_id))

        return messages

    def close(self) -> None:
        self._client.close()
