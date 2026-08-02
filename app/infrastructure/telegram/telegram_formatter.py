"""
app/infrastructure/telegram/telegram_formatter.py
------------------------------------------------------------
TelegramFormatter: يجمّع أقسام رسالة (كل قسم نص جاهز، قد يكون متعدد
الأسطر) في رسالة Telegram نهائية واحدة عبر MessageBuilder.

- include_disclaimer (افتراضياً True): يضيف تحذير سطر واحد "ادخل فقط
  إذا..." - False لرسائل أحداث لاحقة (TP1/TP2/STOP HIT) حيث لا معنى له
  على صفقة أُغلِقت أصلاً.
- include_separator (افتراضياً True): يضيف فاصلاً سميكاً في النهاية -
  False لرسائل يُراد أن تبقى مختصرة بلا "زخارف" (مثل بطاقة الإشارة -
  راجع SignalFormatter).

**ممنوع أن تظهر هنا أو في أي قسم يُمرَّر إليه**: JSON خام، HTTP Status،
Response Body، أسماء كلاسات، أو Stack Trace - هذه رسالة للمستخدم النهائي
فقط، وليست سجل تصحيح (Debug Log).
"""

from __future__ import annotations

from app.infrastructure.telegram.message_builder import MessageBuilder

_DISCLAIMER_TEXT = "⚠️ ادخل فقط إذا كان السعر داخل نطاق الدخول."


class TelegramFormatter:
    def render(self, sections: list[str], include_disclaimer: bool = True, include_separator: bool = True) -> str:
        blocks = [*sections, _DISCLAIMER_TEXT] if include_disclaimer else list(sections)

        builder = MessageBuilder()
        for index, block in enumerate(blocks):
            for line in block.split("\n"):
                builder.line(line)
            if index < len(blocks) - 1:
                builder.blank()

        if include_separator:
            builder.blank()
            builder.thick_separator()
        return builder.build()
