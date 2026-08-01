"""
tests/test_telegram.py
---------------------------
اختبار حقيقي لطبقة Telegram - **بلا أي اتصال شبكة إطلاقاً** (كل شيء
عبر LoggingTelegramSender الذي يسجّل فقط عبر Loguru).
"""

from __future__ import annotations

import inspect
import time
from dataclasses import replace
from datetime import date, datetime, timezone

from loguru import logger

from app.infrastructure.options.models import OptionContract
from app.infrastructure.reports.models import DailyReportSummary
from app.infrastructure.signals.models import Signal, SignalDirection
from app.infrastructure.telegram import notification_tracker as notification_tracker_module
from app.infrastructure.telegram import sender as sender_module
from app.infrastructure.telegram.alert_formatter import AlertFormatter
from app.infrastructure.telegram.daily_report_formatter import DailyReportFormatter
from app.infrastructure.telegram.message_builder import MessageBuilder
from app.infrastructure.telegram.notification_tracker import NotificationTracker
from app.infrastructure.telegram.sender import LoggingTelegramSender
from app.infrastructure.telegram.signal_formatter import SignalFormatter
from app.infrastructure.telegram.telegram_service import TelegramService


def _signal(direction: SignalDirection = SignalDirection.BUY) -> Signal:
    is_buy = direction == SignalDirection.BUY
    return Signal(
        symbol="AAPL", timeframe="1h", direction=direction, confidence=84.5,
        entry=101.0, stop_loss=100.5 if is_buy else 101.5, take_profit=102.0 if is_buy else 100.0,
        risk_reward=2.0, strategy_used=["trend_following"], indicators_used=["rsi", "macd"],
        reasons=[
            "اتجاه صاعد (EMA سريع=102.00 > EMA بطيء=100.00)." if is_buy else "اتجاه هابط (EMA سريع=100.00 < EMA بطيء=102.00).",
            "RSI=65.0." if is_buy else "RSI=35.0.",
        ],
        timestamp=datetime.now(timezone.utc),
    )


def test_message_builder_fluent_api() -> None:
    text = (
        MessageBuilder()
        .header("عنوان")
        .key_value("مفتاح", "قيمة")
        .line("سطر عادي")
        .separator()
        .build()
    )
    assert "عنوان" in text
    assert "مفتاح: قيمة" in text
    assert "سطر عادي" in text


def test_signal_formatter_buy_becomes_call() -> None:
    text = SignalFormatter().format(_signal(SignalDirection.BUY))
    assert "🚨 AAPL — CALL" in text
    assert "84.5%" in text
    assert "Bullish" in text
    assert "SELL" not in text and "BUY" not in text  # Signal.direction الخام لا يُطبَع كنص


def test_signal_formatter_sell_becomes_put() -> None:
    text = SignalFormatter().format(_signal(SignalDirection.SELL))
    assert "🚨 AAPL — PUT" in text
    assert "Bearish" in text


def test_signal_formatter_estimated_path_marks_values_as_estimated() -> None:
    text = SignalFormatter().format(_signal())
    assert "تقديرية" in text
    assert "Strike:" in text
    assert "Exp:" in text
    assert "💰 دخول:" in text
    assert "🛑 وقف:" in text
    assert "🎯 T1:" in text and "🎯 T2:" in text
    assert "🕒 المتوقع:" in text
    assert "⭐ الثقة:" in text
    assert "📌 سبب الإشارة:" in text
    assert "⚠️ بيانات الخيارات قد تتأخر 15 دقيقة." in text
    assert "━━━━━━━━━━━━━━" in text


def test_signal_formatter_real_option_contract_uses_real_values_not_estimated() -> None:
    contract = OptionContract(
        symbol="AAPL", option_type="CALL", strike=105.0, expiration="2026-08-07",
        bid=0.92, ask=1.12, last=1.02, volume=500, open_interest=1200, implied_volatility=0.35, delta=0.48,
    )
    text = SignalFormatter().format(_signal(SignalDirection.BUY), contract)
    assert "Strike: 105.0" in text
    assert "0.92$–1.12$" in text
    assert "Exp: 07/08" in text
    assert "تقديرية" not in text


def test_signal_formatter_never_leaks_debug_content() -> None:
    """ممنوع أن تحتوي الرسالة على JSON خام/HTTP Status/أسماء كلاسات/Stack
    Trace - هذه رسالة للمستخدم النهائي فقط."""
    text = SignalFormatter().format(_signal())
    for forbidden in ('{"', "HTTP Status", "Response Body", "Traceback", "SignalFormatter", "Exception"):
        assert forbidden not in text


def test_signal_formatter_better_entry_banner() -> None:
    text = SignalFormatter().format(_signal(), better_entry=True)
    assert "🔄 Better Entry" in text


def test_signal_formatter_no_better_entry_banner_by_default() -> None:
    text = SignalFormatter().format(_signal())
    assert "🔄 Better Entry" not in text


def test_signal_formatter_news_note_never_blocks_and_can_override_confidence() -> None:
    text = SignalFormatter().format(_signal(), news_note="أخبار سلبية (2) تتعارض مع الاتجاه.", confidence_override=60.0)
    assert "📰 أخبار سلبية (2) تتعارض مع الاتجاه." in text
    assert "60.0%" in text
    assert "84.5%" not in text  # القيمة الأصلية لا تظهر عند وجود بديل للعرض فقط


def test_signal_formatter_without_news_note_omits_news_section() -> None:
    text = SignalFormatter().format(_signal())
    assert "📰" not in text


def test_signal_formatter_re_entry_banner_takes_priority_over_better_entry() -> None:
    text = SignalFormatter().format(_signal(), better_entry=True, re_entry=True)
    assert "🔁 Re-entry" in text
    assert "Better Entry" not in text


def test_signal_formatter_earnings_note_is_its_own_section() -> None:
    text = SignalFormatter().format(_signal(), earnings_note="Earnings خلال 24 ساعة.")
    assert "⚠️ Earnings خلال 24 ساعة." in text


def test_signal_formatter_compute_levels_matches_format_output() -> None:
    """compute_levels() (يستخدمه app/main.py لفتح صفقة في Trade Journal)
    يجب أن يُرجع بالضبط نفس الأرقام الظاهرة فعلياً في format()."""
    signal = _signal(SignalDirection.BUY)
    formatter = SignalFormatter()
    levels = formatter.compute_levels(signal)
    text = formatter.format(signal)

    assert f"{levels.strike:.1f}" in text
    assert f"{levels.entry_low:.2f}$–{levels.entry_high:.2f}$" in text
    assert f"{levels.t1:.2f}$" in text and f"{levels.t2:.2f}$" in text
    assert levels.option_type == "CALL"
    assert levels.is_estimated is True


def test_telegram_formatter_disclaimer_optional() -> None:
    from app.infrastructure.telegram.telegram_formatter import TelegramFormatter

    with_disclaimer = TelegramFormatter().render(["قسم واحد"], include_disclaimer=True)
    without_disclaimer = TelegramFormatter().render(["قسم واحد"], include_disclaimer=False)

    assert "بيانات الخيارات قد تتأخر" in with_disclaimer
    assert "بيانات الخيارات قد تتأخر" not in without_disclaimer
    assert "━━━━━━━━━━━━━━" in without_disclaimer  # الفاصل السميك يبقى دائماً


# ---------------------------------------------------------------------
# NotificationTracker
# ---------------------------------------------------------------------


def test_notification_tracker_first_signal_is_never_better_entry() -> None:
    tracker = NotificationTracker()
    assert tracker.is_better_entry("AAPL", _signal(SignalDirection.BUY)) is False


def test_notification_tracker_better_entry_for_buy_means_cheaper_price() -> None:
    tracker = NotificationTracker()
    first = _signal(SignalDirection.BUY)
    tracker.record_sent("AAPL", "text-1", first)

    cheaper = replace(first, entry=first.entry - 1.0)
    assert tracker.is_better_entry("AAPL", cheaper) is True

    pricier = replace(first, entry=first.entry + 1.0)
    assert tracker.is_better_entry("AAPL", pricier) is False


def test_notification_tracker_better_entry_for_sell_means_higher_price() -> None:
    tracker = NotificationTracker()
    first = _signal(SignalDirection.SELL)
    tracker.record_sent("NVDA", "text-1", first)

    higher = replace(first, entry=first.entry + 1.0)
    assert tracker.is_better_entry("NVDA", higher) is True

    lower = replace(first, entry=first.entry - 1.0)
    assert tracker.is_better_entry("NVDA", lower) is False


def test_notification_tracker_better_entry_false_after_direction_change() -> None:
    tracker = NotificationTracker()
    tracker.record_sent("AAPL", "text-1", _signal(SignalDirection.BUY))
    assert tracker.is_better_entry("AAPL", _signal(SignalDirection.SELL)) is False


def test_notification_tracker_target_was_hit_when_entry_passes_stored_take_profit() -> None:
    tracker = NotificationTracker()
    first = _signal(SignalDirection.BUY)  # take_profit=102.0, entry=101.0
    tracker.record_sent("AAPL", "text-1", first)

    reentry_past_target = replace(first, entry=103.0)
    assert tracker.target_was_hit("AAPL", reentry_past_target) is True

    still_below_target = replace(first, entry=101.5)
    assert tracker.target_was_hit("AAPL", still_below_target) is False


def test_notification_tracker_blocks_only_exact_duplicate_within_window(monkeypatch) -> None:
    monkeypatch.setattr(notification_tracker_module, "DUPLICATE_WINDOW_SECONDS", 0.05)
    tracker = notification_tracker_module.NotificationTracker()

    assert tracker.should_send("AAPL", "نفس النص") is True
    tracker.record_sent("AAPL", "نفس النص")

    assert tracker.should_send("AAPL", "نفس النص") is False  # نفس النص خلال النافذة
    assert tracker.should_send("AAPL", "نص مختلف تماماً") is True  # نص مختلف - يُسمَح فوراً بلا انتظار

    time.sleep(0.1)
    assert tracker.should_send("AAPL", "نفس النص") is True  # انتهت نافذة الـ5 دقائق (المُصغَّرة هنا للاختبار)


def test_notification_tracker_no_opportunity_message_also_deduplicated() -> None:
    tracker = NotificationTracker()
    text = "🔍 تم فحص السوق بالكامل.\nلم يتم العثور على فرصة تستحق الدخول حاليًا."
    assert tracker.should_send("__NO_OPPORTUNITY__", text) is True
    tracker.record_sent("__NO_OPPORTUNITY__", text)
    assert tracker.should_send("__NO_OPPORTUNITY__", text) is False


def test_daily_report_formatter_includes_key_fields() -> None:
    summary = DailyReportSummary(
        report_date=date(2026, 8, 1), total_scans=10, signals_sent=4, wins=3, losses=1, win_rate=75.0,
    )
    text = DailyReportFormatter().format(summary)
    assert "2026-08-01" in text
    assert "75.0" in text
    assert "10" in text


def test_alert_formatter_includes_severity_and_body() -> None:
    text = AlertFormatter().format("تحذير مخاطرة", "تجاوزت الحد اليومي.", severity="warning")
    assert "تحذير مخاطرة" in text
    assert "تجاوزت الحد اليومي." in text
    assert "⚠️" in text


def test_logging_telegram_sender_returns_true_and_logs_no_network() -> None:
    captured: list[str] = []
    sink_id = logger.add(lambda message: captured.append(message.record["message"]), level="INFO")
    try:
        result = LoggingTelegramSender().send("12345", "رسالة اختبار")
    finally:
        logger.remove(sink_id)

    assert result is True
    assert any("12345" in msg for msg in captured)


def test_logging_telegram_sender_no_network_dependency() -> None:
    """يتحقق من غياب أي *استيراد* فعلي لمكتبة شبكة/بوت حقيقية - وليس مجرد
    غياب الكلمة كنص (sender.py يذكر "python-telegram-bot" في التوثيق
    كمثال لمرحلة قادمة، وهذا مقصود ومطلوب، وليس استيراداً فعلياً)."""
    source = inspect.getsource(sender_module)
    forbidden_imports = ("import requests", "import httpx", "import urllib", "import socket", "import aiohttp", "import telegram")
    for forbidden in forbidden_imports:
        assert forbidden not in source


def test_telegram_service_send_message() -> None:
    service = TelegramService()
    assert service.send_message("12345", "نص") is True


def test_telegram_service_send_signal_alert() -> None:
    service = TelegramService()
    assert service.send_signal_alert("12345", _signal()) is True


def test_telegram_service_send_daily_report() -> None:
    service = TelegramService()
    summary = DailyReportSummary(
        report_date=date(2026, 8, 1), total_scans=10, signals_sent=4, wins=3, losses=1, win_rate=75.0,
    )
    assert service.send_daily_report("12345", summary) is True


def test_telegram_service_send_alert() -> None:
    service = TelegramService()
    assert service.send_alert("12345", "عنوان", "نص", severity="error") is True


def test_telegram_service_uses_logging_sender_by_default() -> None:
    service = TelegramService()
    assert isinstance(service._sender, LoggingTelegramSender)  # noqa: SLF001 - تأكيد بنيوي متعمَّد
