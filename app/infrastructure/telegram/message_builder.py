"""
app/infrastructure/telegram/message_builder.py
-----------------------------------------------------
MessageBuilder: أداة بناء رسائل نصية متعددة الأسطر بأسلوب مُتسلسل
(Fluent API) - تُستخدَم من كل المُنسِّقات (SignalFormatter،
DailyReportFormatter، AlertFormatter) بدل تجميع نصوص يدوياً في كل مكان.
"""

from __future__ import annotations


class MessageBuilder:
    def __init__(self) -> None:
        self._lines: list[str] = []

    def header(self, text: str) -> MessageBuilder:
        self._lines.append(f"*{text}*")
        return self

    def line(self, text: str = "") -> MessageBuilder:
        self._lines.append(text)
        return self

    def key_value(self, key: str, value: object) -> MessageBuilder:
        self._lines.append(f"{key}: {value}")
        return self

    def separator(self) -> MessageBuilder:
        self._lines.append("―――――――――――――――")
        return self

    def blank(self) -> MessageBuilder:
        """سطر فارغ - للتباعد بين الأقسام (يُستخدَم من TelegramFormatter)."""
        self._lines.append("")
        return self

    def thick_separator(self) -> MessageBuilder:
        """فاصل سميك مميَّز عن separator() العادي - لا يستبدله حتى لا
        يتأثر شكل AlertFormatter/DailyReportFormatter الحاليين."""
        self._lines.append("━━━━━━━━━━━━━━")
        return self

    def build(self) -> str:
        return "\n".join(self._lines)
