"""
app/infrastructure/telegram
--------------------------------
Telegram Layer - **بلا توكن حقيقي وبلا أي اتصال شبكة فعلي**. TelegramSender
(ABC) هو نقطة الإرسال الوحيدة - LoggingTelegramSender (الافتراضي هنا)
يسجّل الرسالة عبر Loguru فقط ويُرجع True، بنفس فلسفة MockProvider في
market/. ربط مُرسِل Telegram حقيقي (python-telegram-bot + توكن فعلي)
لاحقاً يعني كتابة TelegramSender جديد فقط، دون أي تعديل على
TelegramService أو المُنسِّقات (Formatters).
"""
