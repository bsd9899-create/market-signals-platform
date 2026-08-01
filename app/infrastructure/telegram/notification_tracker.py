"""
app/infrastructure/telegram/notification_tracker.py
------------------------------------------------------------
NotificationTracker: يقرر هل تُرسَل رسالة إشعار جديدة لكل رمز أم لا -
منطق تكرار/تميّز/منع تكرار حرفي فقط، بلا أي علاقة بـ Scanner أو
SignalEngine (يستهلك Signal جاهزاً فقط - بلا أي حساب مؤشرات/استراتيجيات
هنا إطلاقاً).

القاعدة الوحيدة للمنع فعلياً: **لا تُرسَل نفس نص الرسالة حرفياً لنفس
المفتاح خلال 5 دقائق** - أي تغيّر حقيقي في المحتوى (سعر دخول أفضل،
Strike/Expiration مختلف، ثقة أعلى، اتجاه مختلف، هدف سابق تحقق ثم دخول
جديد) يُنتِج نصاً مختلفاً تلقائياً، فيُسمَح بإرساله فوراً دون أي انتظار
- لا يوجد أي منع آخر لتكرار الإشارة نفسها.
"""

from __future__ import annotations

import time

from app.infrastructure.signals.models import Signal, SignalDirection

DUPLICATE_WINDOW_SECONDS = 300.0  # 5 دقائق


class NotificationTracker:
    def __init__(self) -> None:
        self._last_text: dict[str, str] = {}
        self._last_sent_at: dict[str, float] = {}
        self._last_state: dict[str, dict[str, object]] = {}

    def is_better_entry(self, symbol: str, signal: Signal) -> bool:
        """True فقط إذا أُرسِلت إشارة سابقة لنفس الرمز/الاتجاه، وسعر
        الدخول الحالي أفضل فعلياً (أرخص لـCALL/BUY، أعلى لـPUT/SELL)."""
        state = self._last_state.get(symbol)
        if state is None or state["direction"] != signal.direction:
            return False
        if signal.direction == SignalDirection.BUY:
            return signal.entry < state["entry"]
        if signal.direction == SignalDirection.SELL:
            return signal.entry > state["entry"]
        return False

    def target_was_hit(self, symbol: str, signal: Signal) -> bool:
        """True إذا تجاوز سعر الدخول الحالي الهدف (Take Profit) المُخزَّن
        من آخر إشارة أُرسِلت لنفس الرمز/الاتجاه - أي تحقق الهدف فعلياً ثم
        ظهرت فرصة دخول جديدة (معلوماتي فقط - لا يمنع الإرسال أصلاً، لأن
        سعر الدخول الجديد يجعل النص مختلفاً تلقائياً)."""
        state = self._last_state.get(symbol)
        if state is None or state["direction"] != signal.direction or state.get("take_profit") is None:
            return False
        if signal.direction == SignalDirection.BUY:
            return signal.entry >= state["take_profit"]
        return signal.entry <= state["take_profit"]

    def should_send(self, key: str, message_text: str) -> bool:
        last_text = self._last_text.get(key)
        last_at = self._last_sent_at.get(key)
        if last_text == message_text and last_at is not None and (time.monotonic() - last_at) < DUPLICATE_WINDOW_SECONDS:
            return False
        return True

    def record_sent(self, key: str, message_text: str, signal: Signal | None = None) -> None:
        self._last_text[key] = message_text
        self._last_sent_at[key] = time.monotonic()
        if signal is not None:
            self._last_state[key] = {
                "entry": signal.entry, "direction": signal.direction, "take_profit": signal.take_profit,
                "confidence": signal.confidence,
            }
