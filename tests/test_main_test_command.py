"""
tests/test_main_test_command.py
--------------------------------------
اختبار حقيقي لوضع الاختبار عبر Telegram في app/main.py
(_build_test_status_text/_build_sample_test_signal/_handle_test_command) -
بلا أي اتصال شبكة حقيقي (telegram_service/market_service مُزيَّفان بسيطان،
نفس نمط test_main_decision_logic.py).
"""

from __future__ import annotations

from app.main import (
    _TEST_TRIGGER_TEXTS,
    _build_sample_test_signal,
    _build_test_status_text,
    _handle_test_command,
)
from app.infrastructure.config.loader import ConfigLoader
from app.infrastructure.signals.models import SignalDirection


class _FakeMarketService:
    def __init__(self, is_open: bool = True, raise_error: bool = False) -> None:
        self._is_open = is_open
        self._raise_error = raise_error

    def get_market_status(self):
        if self._raise_error:
            raise RuntimeError("market data down")
        from types import SimpleNamespace
        return SimpleNamespace(is_open=self._is_open)


class _FakeTelegramService:
    def __init__(self, succeed: bool = True) -> None:
        self.succeed = succeed
        self.sent_messages: list[tuple[str, str]] = []

    def send_message(self, chat_id: str, text: str) -> bool:
        self.sent_messages.append((chat_id, text))
        return self.succeed


class _FakeLogger:
    def __init__(self) -> None:
        self.info_calls: list[str] = []
        self.error_calls: list[str] = []
        self.exception_calls: list[str] = []
        self.warning_calls: list[str] = []

    def info(self, msg, *a, **k):
        self.info_calls.append(msg)

    def error(self, msg, *a, **k):
        self.error_calls.append(msg)

    def exception(self, msg, *a, **k):
        self.exception_calls.append(msg)

    def warning(self, msg, *a, **k):
        self.warning_calls.append(msg)


class _FakeProvider:
    """بلا عقد حقيقي - يحاكي عدم توفر بيانات خيارات (المسار التقديري)."""

    def get_best_option_contract(self, symbol, direction, entry):
        return None


class _BrokenProvider:
    def get_best_option_contract(self, symbol, direction, entry):
        raise RuntimeError("option chain down")


class _FakeNewsProvider:
    def get_latest_news(self, symbol, limit=5):
        return []

    def get_earnings_info(self, symbol):
        return None

    def get_sec_filings(self, symbol, limit=5):
        return []

    def get_analyst_actions(self, symbol, limit=3):
        return []


def _config() -> ConfigLoader:
    return ConfigLoader()


# ---------------------------------------------------------------------
# _build_test_status_text
# ---------------------------------------------------------------------


def test_build_test_status_text_includes_all_required_fields() -> None:
    text = _build_test_status_text(_config(), _FakeMarketService(is_open=True))
    assert "✅ البوت يعمل" in text
    assert "🕒 الوقت:" in text
    assert "📈 السوق: مفتوح" in text
    assert "🤖 الإصدار:" in text


def test_build_test_status_text_shows_closed_when_market_closed() -> None:
    text = _build_test_status_text(_config(), _FakeMarketService(is_open=False))
    assert "📈 السوق: مغلق" in text


def test_build_test_status_text_falls_back_to_closed_on_market_error() -> None:
    text = _build_test_status_text(_config(), _FakeMarketService(raise_error=True))
    assert "📈 السوق: مغلق" in text  # لا يفشل السطر بالكامل بسبب تعذّر حالة السوق


# ---------------------------------------------------------------------
# _build_sample_test_signal
# ---------------------------------------------------------------------


def test_build_sample_test_signal_is_realistic_buy_signal() -> None:
    signal = _build_sample_test_signal()
    assert signal.symbol == "AAPL"
    assert signal.direction == SignalDirection.BUY
    assert signal.confidence == 85.0
    assert signal.stop_loss is not None and signal.take_profit is not None
    assert len(signal.reasons) > 0


def test_sample_test_signal_formats_via_real_signal_formatter() -> None:
    from app.infrastructure.telegram.signal_formatter import SignalFormatter

    text = SignalFormatter().format(_build_sample_test_signal())
    assert "AAPL — CALL" in text
    assert "⭐ التقييم:" in text


# ---------------------------------------------------------------------
# _handle_test_command
# ---------------------------------------------------------------------


def test_handle_test_command_sends_two_messages_and_logs_success() -> None:
    telegram_service = _FakeTelegramService(succeed=True)
    logger = _FakeLogger()

    _handle_test_command(_config(), logger, telegram_service, _FakeMarketService(), _FakeProvider(), _FakeNewsProvider(), "999")

    assert len(telegram_service.sent_messages) == 2
    assert telegram_service.sent_messages[0][1].startswith("✅ البوت يعمل")
    assert "🧪 توصية تجريبية" in telegram_service.sent_messages[1][1]
    assert "AAPL — CALL" in telegram_service.sent_messages[1][1]
    assert any("executed successfully" in msg for msg in logger.info_calls)


def test_handle_test_command_logs_failure_when_send_fails() -> None:
    telegram_service = _FakeTelegramService(succeed=False)
    logger = _FakeLogger()

    _handle_test_command(_config(), logger, telegram_service, _FakeMarketService(), _FakeProvider(), _FakeNewsProvider(), "999")

    assert any("failed" in msg for msg in logger.error_calls)


def test_handle_test_command_logs_failure_on_exception() -> None:
    class _BrokenTelegramService:
        def send_message(self, chat_id, text):
            raise RuntimeError("boom")

    logger = _FakeLogger()
    _handle_test_command(_config(), logger, _BrokenTelegramService(), _FakeMarketService(), _FakeProvider(), _FakeNewsProvider(), "999")
    assert any("failed" in msg for msg in logger.exception_calls)


def test_handle_test_command_degrades_gracefully_when_enrichment_fails() -> None:
    """فشل مصدر البيانات (خيارات/أخبار) أثناء الإثراء الاختياري لا يجب أن
    يمنع إرسال رسالة الاختبار - يتراجع فقط لعرض تقديري بلا إثراء."""
    telegram_service = _FakeTelegramService(succeed=True)
    logger = _FakeLogger()

    _handle_test_command(_config(), logger, telegram_service, _FakeMarketService(), _BrokenProvider(), _FakeNewsProvider(), "999")

    assert len(telegram_service.sent_messages) == 2
    assert "AAPL — CALL" in telegram_service.sent_messages[1][1]
    assert any("executed successfully" in msg for msg in logger.info_calls)
    assert any(logger.warning_calls)


def test_handle_test_command_never_touches_database_or_tracker() -> None:
    """لا Journal، لا Scanner، لا NotificationTracker يُمرَّر لهذه الدالة
    أصلاً - إثبات بنيوي: التوقيع نفسه لا يقبلها إطلاقاً."""
    import inspect
    params = list(inspect.signature(_handle_test_command).parameters)
    for forbidden in ("journal", "tracker", "scanner", "position_monitor"):
        assert forbidden not in params


# ---------------------------------------------------------------------
# نصوص التفعيل
# ---------------------------------------------------------------------


def test_trigger_texts_match_exactly_arabic_and_english() -> None:
    assert "تجربة" in _TEST_TRIGGER_TEXTS
    assert "test" in _TEST_TRIGGER_TEXTS
    assert "hello" not in _TEST_TRIGGER_TEXTS
