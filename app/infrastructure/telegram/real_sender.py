"""
app/infrastructure/telegram/real_sender.py
--------------------------------------------------
RealTelegramSender: تطبيق حقيقي لـ TelegramSender (الواجهة المجرَّدة في
sender.py - **بلا أي تعديل عليها**) عبر Telegram Bot HTTP API مباشرة
باستخدام httpx - مكتبة HTTP خفيفة، وليس python-telegram-bot (لا حاجة
لتبعية SDK كاملة من أجل استدعاء sendMessage واحد بسيط).

بيانات الاعتماد (TELEGRAM_BOT_TOKEN) لا تُقرأ داخل الصف مباشرة -
RealTelegramSender.from_env(env) هي نقطة القراءة الوحيدة، حتى يبقى
الصف قابلاً للاختبار عبر معاملات صريحة.

send() **لا يحتوي على أي try/except** عمداً - أي خطأ اتصال/شبكة
(Timeout، DNS، انقطاع، إلخ) يُرفَع كما هو (Exception كاملة بسطرها
الأصلي وTraceback) إلى المُستدعي، بدل ابتلاعه أو تلخيصه، بناءً على طلب
صريح بعدم إخفاء أي تفصيل من الخطأ. آخر URL/Status Code/Response Body
مُتاحة دائماً عبر last_url/last_status_code/last_response_body.
"""

from __future__ import annotations

import httpx
from loguru import logger

from app.infrastructure.telegram.sender import TelegramSender

TELEGRAM_API_BASE = "https://api.telegram.org"


class RealTelegramSender(TelegramSender):
    def __init__(self, bot_token: str, timeout_seconds: float = 10.0) -> None:
        self._bot_token = bot_token
        self._client = httpx.Client(timeout=timeout_seconds)
        self.last_url: str | None = None
        self.last_status_code: int | None = None
        self.last_response_body: str | None = None

    @classmethod
    def from_env(cls, env: dict[str, str | None]) -> RealTelegramSender:
        bot_token = env.get("TELEGRAM_BOT_TOKEN") or ""
        if not bot_token:
            logger.warning("RealTelegramSender.from_env: TELEGRAM_BOT_TOKEN فارغ في .env - أي إرسال سيفشل.")
        return cls(bot_token=bot_token)

    def build_url(self) -> str:
        return f"{TELEGRAM_API_BASE}/bot{self._bot_token}/sendMessage"

    def send(self, chat_id: str, text: str) -> bool:
        self.last_url = self.build_url()
        logger.info("RealTelegramSender.send: URL={}", self.last_url)

        response = self._client.post(self.last_url, json={"chat_id": chat_id, "text": text})

        self.last_status_code = response.status_code
        self.last_response_body = response.text
        logger.info("RealTelegramSender.send: HTTP Status={}", response.status_code)
        logger.info("RealTelegramSender.send: Response Body={}", response.text)

        return response.status_code == 200

    def close(self) -> None:
        self._client.close()
