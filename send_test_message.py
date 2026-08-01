"""
send_test_message.py
-------------------------
سكربت تحقق بسيط: يرسل رسالة اختبار حقيقية إلى Telegram عبر
RealTelegramSender (app/infrastructure/telegram/real_sender.py).

TELEGRAM_BOT_TOKEN وTELEGRAM_CHAT_ID يُقرآن بالترتيب التالي لكل متغير
على حدة:
    1. متغيرات البيئة الفعلية (os.environ) - الأولوية دائماً هنا.
    2. إذا لم يوجد المتغير في os.environ، يُقرأ من .env (عبر
       ConfigLoader.env، بلا أي تعديل على ConfigLoader نفسه).

يطبع دائماً: Telegram URL، ثم HTTP Status Code وResponse Body إذا وصل
رد فعلي من Telegram، أو Exception كاملة (Traceback) إذا فشل الطلب على
مستوى الاتصال نفسه (Timeout/DNS/انقطاع). لا شيء يُخفى أو يُلخَّص.

التشغيل (من جذر المشروع):
    python send_test_message.py
"""

from __future__ import annotations

import os
import sys
import traceback

from app.infrastructure.config.loader import ConfigLoader
from app.infrastructure.telegram.real_sender import RealTelegramSender


MESSAGE = "🚀 Market Signals Platform\n\nTelegram integration successful."


def _resolve(key: str, env_file_values: dict[str, str | None]) -> str:
    """os.environ أولاً، ثم .env إذا لم يوجد المتغير في os.environ."""
    from_os_environ = os.environ.get(key)
    if from_os_environ:
        return from_os_environ
    return env_file_values.get(key) or ""


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="replace")

    config = ConfigLoader()
    bot_token = _resolve("TELEGRAM_BOT_TOKEN", config.env)
    chat_id = _resolve("TELEGRAM_CHAT_ID", config.env)

    if not bot_token or not chat_id:
        print(
            "خطأ: TELEGRAM_BOT_TOKEN و/أو TELEGRAM_CHAT_ID فارغان - "
            "لم يُعثَر عليهما لا في os.environ ولا في .env. املأهما ثم أعد المحاولة."
        )
        return 1

    sender = RealTelegramSender(bot_token=bot_token)
    print(f"Telegram URL: {sender.build_url()}")

    try:
        success = sender.send(chat_id, MESSAGE)
    except Exception:
        print("Exception:")
        traceback.print_exc()
        return 1
    finally:
        sender.close()

    print(f"HTTP Status Code: {sender.last_status_code}")
    print(f"Response Body: {sender.last_response_body}")

    if success:
        print("Message sent successfully.")
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
