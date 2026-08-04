"""
tests/test_main_decision_logic.py
----------------------------------------
اختبار حقيقي لدوال القرار البحتة في app/main.py
(_decide_entry_kind/_is_recently_closed/_compute_stock_t1) - بلا أي
اتصال شبكة أو قاعدة بيانات حقيقية (journal مُزيَّف بسيط لـ_decide_entry_kind).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from app.main import _compute_stock_t1, _decide_entry_kind, _is_recently_closed
from app.infrastructure.signals.models import Signal, SignalDirection


class _FakeJournal:
    def __init__(self, open_trades: list) -> None:
        self._open_trades = open_trades

    def get_open_trades(self):
        return self._open_trades


def _open_trade(
    symbol: str, direction: str, entry: float, strike: float = 100.0, expiration: str = "05/08",
    confidence: float = 80.0, better_entry_sent: bool = False,
):
    return SimpleNamespace(
        symbol=symbol, direction=direction, entry=entry, strike=strike, expiration=expiration,
        confidence=confidence, better_entry_sent=better_entry_sent,
    )


def _signal(direction: SignalDirection, entry: float, stop: float | None, tp: float | None) -> Signal:
    return Signal(
        symbol="AAPL", timeframe="5m", direction=direction, confidence=85.0, entry=entry,
        stop_loss=stop, take_profit=tp, risk_reward=2.0, strategy_used=["momentum"],
        indicators_used=[], reasons=[], timestamp=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------
# _decide_entry_kind
# ---------------------------------------------------------------------


def test_decide_entry_kind_open_new_when_no_open_trade() -> None:
    journal = _FakeJournal([])
    assert _decide_entry_kind(journal, "AAPL", "buy", 100.0, 100.0, "05/08", 80.0) == "OPEN_NEW"


def test_decide_entry_kind_better_entry_for_cheaper_buy() -> None:
    journal = _FakeJournal([_open_trade("AAPL", "buy", 105.0)])
    assert _decide_entry_kind(journal, "AAPL", "buy", 100.0, 100.0, "05/08", 80.0) == "BETTER_ENTRY"


def test_decide_entry_kind_skip_when_nothing_improved() -> None:
    journal = _FakeJournal([_open_trade("AAPL", "buy", 100.0, strike=100.0, expiration="05/08", confidence=80.0)])
    assert _decide_entry_kind(journal, "AAPL", "buy", 101.0, 100.0, "05/08", 80.0) == "SKIP"
    assert _decide_entry_kind(journal, "AAPL", "buy", 100.0, 100.0, "05/08", 80.0) == "SKIP"  # لا شيء تغيّر


def test_decide_entry_kind_better_entry_for_higher_sell() -> None:
    journal = _FakeJournal([_open_trade("AAPL", "sell", 100.0)])
    assert _decide_entry_kind(journal, "AAPL", "sell", 105.0, 100.0, "05/08", 80.0) == "BETTER_ENTRY"


def test_decide_entry_kind_open_new_when_direction_flips() -> None:
    journal = _FakeJournal([_open_trade("AAPL", "buy", 100.0)])
    assert _decide_entry_kind(journal, "AAPL", "sell", 100.0, 100.0, "05/08", 80.0) == "OPEN_NEW"


def test_decide_entry_kind_ignores_other_symbols() -> None:
    journal = _FakeJournal([_open_trade("NVDA", "buy", 100.0)])
    assert _decide_entry_kind(journal, "AAPL", "buy", 100.0, 100.0, "05/08", 80.0) == "OPEN_NEW"


def test_decide_entry_kind_better_entry_when_strike_changed_only() -> None:
    journal = _FakeJournal([_open_trade("AAPL", "buy", 100.0, strike=100.0, expiration="05/08", confidence=80.0)])
    assert _decide_entry_kind(journal, "AAPL", "buy", 100.0, 105.0, "05/08", 80.0) == "BETTER_ENTRY"


def test_decide_entry_kind_better_entry_when_expiration_changed_only() -> None:
    journal = _FakeJournal([_open_trade("AAPL", "buy", 100.0, strike=100.0, expiration="05/08", confidence=80.0)])
    assert _decide_entry_kind(journal, "AAPL", "buy", 100.0, 100.0, "12/08", 80.0) == "BETTER_ENTRY"


def test_decide_entry_kind_better_entry_when_confidence_increased_only() -> None:
    journal = _FakeJournal([_open_trade("AAPL", "buy", 100.0, strike=100.0, expiration="05/08", confidence=80.0)])
    assert _decide_entry_kind(journal, "AAPL", "buy", 100.0, 100.0, "05/08", 85.0) == "BETTER_ENTRY"


def test_decide_entry_kind_skip_when_better_entry_already_sent_for_this_trade() -> None:
    """Better Entry واحدة فقط لكل صفقة مفتوحة (بطلب صريح) - حتى لو تحسّن
    الدخول أكثر، لا تُرسَل Better Entry ثانية لنفس الصفقة."""
    journal = _FakeJournal([_open_trade("AAPL", "buy", 105.0, better_entry_sent=True)])
    assert _decide_entry_kind(journal, "AAPL", "buy", 100.0, 100.0, "05/08", 80.0) == "SKIP"


def test_decide_entry_kind_better_entry_still_allowed_before_first_one_sent() -> None:
    journal = _FakeJournal([_open_trade("AAPL", "buy", 105.0, better_entry_sent=False)])
    assert _decide_entry_kind(journal, "AAPL", "buy", 100.0, 100.0, "05/08", 80.0) == "BETTER_ENTRY"


# ---------------------------------------------------------------------
# _is_recently_closed
# ---------------------------------------------------------------------


def test_is_recently_closed_true_within_window() -> None:
    now = datetime.now(timezone.utc)
    recently_closed = {"AAPL": now - timedelta(hours=1)}
    assert _is_recently_closed(recently_closed, "AAPL", now) is True


def test_is_recently_closed_false_and_prunes_after_window() -> None:
    now = datetime.now(timezone.utc)
    recently_closed = {"AAPL": now - timedelta(hours=25)}
    assert _is_recently_closed(recently_closed, "AAPL", now) is False
    assert "AAPL" not in recently_closed  # نُظِّفت تلقائياً بعد انتهاء النافذة


def test_is_recently_closed_false_when_never_closed() -> None:
    assert _is_recently_closed({}, "AAPL", datetime.now(timezone.utc)) is False


# ---------------------------------------------------------------------
# _compute_stock_t1
# ---------------------------------------------------------------------


def test_compute_stock_t1_buy_is_halfway_to_take_profit() -> None:
    signal = _signal(SignalDirection.BUY, entry=100.0, stop=98.0, tp=104.0)
    assert _compute_stock_t1(signal) == 102.0


def test_compute_stock_t1_sell_is_halfway_to_take_profit() -> None:
    signal = _signal(SignalDirection.SELL, entry=100.0, stop=102.0, tp=96.0)
    assert _compute_stock_t1(signal) == 98.0


def test_compute_stock_t1_none_when_risk_levels_missing() -> None:
    signal = _signal(SignalDirection.BUY, entry=100.0, stop=None, tp=None)
    assert _compute_stock_t1(signal) is None
