"""
app/infrastructure/telegram/telegram_formatter.py
------------------------------------------------------------
TelegramFormatter: يجمّع أقسام رسالة (كل قسم نص جاهز، قد يكون متعدد
الأسطر) في رسالة Telegram نهائية واحدة عبر MessageBuilder - فاصل سميك
دائماً في النهاية، وتحذير الإخلاء الثابت **فقط عند include_disclaimer**
(افتراضياً True - يناسب رسائل الدخول الفعلية عبر SignalFormatter؛
False لرسائل أحداث لاحقة مثل TP1/TP2/STOP HIT حيث لا معنى لتحذير "ادخل
فقط إذا..." على صفقة أُغلِقت أصلاً).

**ممنوع أن تظهر هنا أو في أي قسم يُمرَّر إليه**: JSON خام، HTTP Status،
Response Body، أسماء كلاسات، أو Stack Trace - هذه رسالة للمستخدم النهائي
فقط، وليست سجل تصحيح (Debug Log).
"""

from __future__ import annotations

from app.infrastructure.telegram.message_builder import MessageBuilder

_DISCLAIMER_LINES = (
    "⚠️ بيانات الخيارات قد تتأخر 15 دقيقة.",
    "ادخل فقط إذا كان سعر العقد داخل نطاق الدخول.",
)


class TelegramFormatter:
    def render(self, sections: list[str], include_disclaimer: bool = True) -> str:
        blocks = [*sections, "\n".join(_DISCLAIMER_LINES)] if include_disclaimer else list(sections)

        builder = MessageBuilder()
        for index, block in enumerate(blocks):
            for line in block.split("\n"):
                builder.line(line)
            if index < len(blocks) - 1:
                builder.blank()

        builder.blank()
        builder.thick_separator()
        return builder.build()
