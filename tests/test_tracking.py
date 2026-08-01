"""
tests/test_tracking.py
---------------------------
اختبار حقيقي لطبقة Tracking (TradeJournal + PositionMonitor +
TradeStatisticsCalculator + EventCounterTracker + DailyCounterStore) -
قاعدة بيانات SQLite حقيقية مؤقتة (نفس نمط test_database.py)، وMockProvider
لبيانات السوق (بلا أي اتصال شبكة).

التشغيل: pytest tests/test_tracking.py -v
"""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.infrastructure.database.database import DatabaseManager
from app.infrastructure.market.providers import mock_provider as mock_provider_module
from app.infrastructure.market.providers.mock_provider import MockProvider
from app.infrastructure.market.services import MarketService
from app.infrastructure.tracking.counter_store import DailyCounterStore
from app.infrastructure.tracking.event_counters import EventCounterTracker
from app.infrastructure.tracking.models import DailyCounters
from app.infrastructure.tracking.position_monitor import PositionMonitor
from app.infrastructure.tracking.statistics import TradeStatisticsCalculator
from app.infrastructure.tracking.trade_journal import TradeJournal


@pytest.fixture()
def db_manager() -> Iterator[DatabaseManager]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        manager = DatabaseManager(f"sqlite:///{db_path.as_posix()}")
        manager.connect()
        manager.create_tables()
        yield manager
        manager.close()


@pytest.fixture()
def journal(db_manager: DatabaseManager) -> TradeJournal:
    return TradeJournal(db_manager)


def _open_sample_trade(journal: TradeJournal, *, direction: str = "buy", entry: float = 100.0) -> int:
    return journal.open_trade(
        symbol="AAPL", timeframe="5m", direction=direction, option_type="CALL" if direction == "buy" else "PUT",
        strike=105.0, expiration="2026-08-07", option_entry_low=0.9, option_entry_high=1.1,
        entry=entry, stop=entry - 1.0 if direction == "buy" else entry + 1.0,
        tp1=entry + 0.5 if direction == "buy" else entry - 0.5, tp2=entry + 1.0 if direction == "buy" else entry - 1.0,
        confidence=85.0, risk_reward=2.0, strategy="momentum,trend_following", reasons="RSI=65.0.",
    )


# ---------------------------------------------------------------------
# TradeJournal
# ---------------------------------------------------------------------


def test_open_trade_creates_open_status(journal: TradeJournal) -> None:
    trade_id = _open_sample_trade(journal)
    open_trades = journal.get_open_trades()
    assert len(open_trades) == 1
    assert open_trades[0].id == trade_id
    assert open_trades[0].status == "OPEN"
    assert open_trades[0].symbol == "AAPL"


def test_mark_tp1_hit_keeps_trade_open_but_updates_status(journal: TradeJournal) -> None:
    trade_id = _open_sample_trade(journal)
    journal.mark_tp1_hit(trade_id, 100.5, datetime.now(timezone.utc))

    open_trades = journal.get_open_trades()
    assert len(open_trades) == 1  # TP1_HIT لا يزال "مفتوحاً" (بانتظار TP2 أو Stop)
    assert open_trades[0].status == "TP1_HIT"
    assert open_trades[0].tp1_hit_price == 100.5


def test_mark_tp2_hit_closes_trade(journal: TradeJournal) -> None:
    trade_id = _open_sample_trade(journal)
    now = datetime.now(timezone.utc)
    journal.mark_tp2_hit(trade_id, 101.0, now, profit_loss_percent=1.0)

    assert journal.get_open_trades() == []
    closed = journal.get_closed_between(now - timedelta(minutes=1), now + timedelta(minutes=1))
    assert len(closed) == 1
    assert closed[0].status == "TP2_HIT"
    assert closed[0].profit_loss_percent == 1.0


def test_mark_stopped_closes_trade(journal: TradeJournal) -> None:
    trade_id = _open_sample_trade(journal)
    now = datetime.now(timezone.utc)
    journal.mark_stopped(trade_id, 99.0, now, profit_loss_percent=-1.0)

    assert journal.get_open_trades() == []
    closed = journal.get_closed_between(now - timedelta(minutes=1), now + timedelta(minutes=1))
    assert closed[0].status == "STOPPED"
    assert closed[0].profit_loss_percent == -1.0


def test_get_sent_between_and_tp1_hits_between(journal: TradeJournal) -> None:
    now = datetime.now(timezone.utc)
    trade_id = _open_sample_trade(journal)
    journal.mark_tp1_hit(trade_id, 100.5, now)

    sent = journal.get_sent_between(now - timedelta(minutes=1), now + timedelta(minutes=1))
    assert len(sent) == 1
    tp1_hits = journal.get_tp1_hits_between(now - timedelta(minutes=1), now + timedelta(minutes=1))
    assert len(tp1_hits) == 1


# ---------------------------------------------------------------------
# PositionMonitor - MockProvider بسعر ثابت قابل للتعديل يدوياً بين الاستدعاءات
# ---------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _restore_mock_price() -> Iterator[None]:
    original = mock_provider_module._FIXED_PRICE
    yield
    mock_provider_module._FIXED_PRICE = original


def test_position_monitor_detects_tp1_then_tp2(journal: TradeJournal) -> None:
    trade_id = _open_sample_trade(journal, direction="buy", entry=100.0)  # tp1=100.5, tp2=101.0, stop=99.0
    market_service = MarketService(MockProvider(), cache_ttl_seconds=0)
    monitor = PositionMonitor(market_service, journal)

    mock_provider_module._FIXED_PRICE = 100.0
    assert monitor.check_open_positions() == []

    mock_provider_module._FIXED_PRICE = 100.6
    events = monitor.check_open_positions()
    assert len(events) == 1 and events[0].kind == "TP1_HIT"

    mock_provider_module._FIXED_PRICE = 101.5
    events = monitor.check_open_positions()
    assert len(events) == 1 and events[0].kind == "TP2_HIT"
    assert journal.get_open_trades() == []


def test_position_monitor_detects_stop_hit(journal: TradeJournal) -> None:
    _open_sample_trade(journal, direction="buy", entry=100.0)  # stop=99.0
    market_service = MarketService(MockProvider(), cache_ttl_seconds=0)
    monitor = PositionMonitor(market_service, journal)

    mock_provider_module._FIXED_PRICE = 98.5
    events = monitor.check_open_positions()
    assert len(events) == 1 and events[0].kind == "STOP_HIT"
    assert events[0].profit_loss_percent < 0
    assert journal.get_open_trades() == []


def test_position_monitor_sell_direction_uses_inverted_comparisons(journal: TradeJournal) -> None:
    _open_sample_trade(journal, direction="sell", entry=100.0)  # tp1=99.5, tp2=99.0, stop=101.0
    market_service = MarketService(MockProvider(), cache_ttl_seconds=0)
    monitor = PositionMonitor(market_service, journal)

    mock_provider_module._FIXED_PRICE = 99.4
    events = monitor.check_open_positions()
    assert len(events) == 1 and events[0].kind == "TP1_HIT"


def test_position_monitor_ignores_unknown_symbol_gracefully(journal: TradeJournal) -> None:
    journal.open_trade(
        symbol="UNKNOWN_XYZ", timeframe="5m", direction="buy", option_type="CALL", strike=1.0,
        expiration="2026-08-07", option_entry_low=0.1, option_entry_high=0.2, entry=1.0, stop=0.5,
        tp1=1.5, tp2=2.0, confidence=80.0, risk_reward=2.0, strategy="momentum", reasons="",
    )
    market_service = MarketService(MockProvider(), cache_ttl_seconds=0)
    monitor = PositionMonitor(market_service, journal)
    events = monitor.check_open_positions()  # SymbolNotFoundError من MockProvider - لا يجب أن يُسقِط المراقبة كلها
    assert events == []
    assert len(journal.get_open_trades()) == 1  # الصفقة تبقى مفتوحة (لم تُغلَق خطأً بسبب فشل الجلب)


# ---------------------------------------------------------------------
# TradeStatisticsCalculator
# ---------------------------------------------------------------------


def test_statistics_empty_list_returns_zeroed_stats() -> None:
    stats = TradeStatisticsCalculator().calculate([])
    assert stats.total_trades == 0
    assert stats.win_rate == 0.0
    assert stats.profit_factor == 0.0


def test_statistics_computes_win_rate_and_profit_factor(journal: TradeJournal) -> None:
    now = datetime.now(timezone.utc)
    win_id = _open_sample_trade(journal, entry=100.0)
    journal.mark_tp2_hit(win_id, 102.0, now, profit_loss_percent=2.0)
    loss_id = _open_sample_trade(journal, entry=100.0)
    journal.mark_stopped(loss_id, 99.0, now, profit_loss_percent=-1.0)

    closed = journal.get_closed_between(now - timedelta(minutes=1), now + timedelta(minutes=1))
    stats = TradeStatisticsCalculator().calculate(closed)

    assert stats.total_trades == 2
    assert stats.wins == 1
    assert stats.losses == 1
    assert stats.win_rate == 50.0
    assert stats.total_profit == 2.0
    assert stats.total_loss == 1.0
    assert stats.profit_factor == 2.0
    assert stats.best_symbol == "AAPL"
    assert stats.best_strategy == "momentum"


def test_statistics_profit_factor_with_no_losses() -> None:
    from app.infrastructure.database.models import Trade

    trade = Trade(
        symbol="NVDA", timeframe="5m", direction="buy", option_type="CALL", strike=200.0, expiration="2026-08-07",
        option_entry_low=1.0, option_entry_high=1.2, entry=200.0, stop=195.0, tp1=202.0, tp2=204.0,
        exit_price=204.0, profit_loss_percent=2.0, confidence=90.0, risk_reward=2.0, strategy="breakout",
        reasons="", status="TP2_HIT", entry_time=datetime.now(timezone.utc),
    )
    stats = TradeStatisticsCalculator().calculate([trade])
    assert stats.total_loss == 0.0
    assert stats.profit_factor == 2.0  # لا خسائر - Profit Factor = إجمالي الربح مباشرة (موثَّق في statistics.py)


# ---------------------------------------------------------------------
# EventCounterTracker + DailyCounterStore
# ---------------------------------------------------------------------


def test_event_counter_tracker_accumulates_same_day() -> None:
    tracker = EventCounterTracker()
    today = date(2026, 8, 1)
    tracker.record_signal_sent(today, "CALL", is_better_entry=False, is_re_entry=False)
    tracker.record_signal_sent(today, "PUT", is_better_entry=True, is_re_entry=False)
    tracker.record_signal_sent(today, "CALL", is_better_entry=False, is_re_entry=True)

    snapshot = tracker.snapshot(today)
    assert snapshot.signals_sent == 3
    assert snapshot.call_count == 2
    assert snapshot.put_count == 1
    assert snapshot.better_entry_count == 1
    assert snapshot.re_entry_count == 1


def test_event_counter_tracker_resets_on_new_day() -> None:
    tracker = EventCounterTracker()
    day1 = date(2026, 8, 1)
    day2 = date(2026, 8, 2)
    tracker.record_signal_sent(day1, "CALL", False, False)
    assert tracker.snapshot(day1).signals_sent == 1

    tracker.record_signal_sent(day2, "PUT", False, False)
    snapshot_day2 = tracker.snapshot(day2)
    assert snapshot_day2.signals_sent == 1  # صُفِّر عند تغيّر اليوم - لم يتراكم مع day1
    assert snapshot_day2.put_count == 1


def test_daily_counter_store_round_trip(db_manager: DatabaseManager) -> None:
    store = DailyCounterStore(db_manager)
    today = date(2026, 8, 1)
    counters = DailyCounters(
        trading_date=today, signals_sent=5, call_count=3, put_count=2, better_entry_count=1, re_entry_count=1,
    )
    store.save(counters)

    loaded = store.load(today)
    assert loaded is not None
    assert loaded.signals_sent == 5
    assert loaded.call_count == 3
    assert loaded.better_entry_count == 1


def test_daily_counter_store_load_missing_date_returns_none(db_manager: DatabaseManager) -> None:
    store = DailyCounterStore(db_manager)
    assert store.load(date(2020, 1, 1)) is None


def test_daily_counter_store_load_range(db_manager: DatabaseManager) -> None:
    store = DailyCounterStore(db_manager)
    day1, day2, day3 = date(2026, 8, 3), date(2026, 8, 4), date(2026, 8, 5)
    store.save(DailyCounters(trading_date=day1, signals_sent=1))
    store.save(DailyCounters(trading_date=day3, signals_sent=3))  # day2 غير محفوظ عمداً

    results = store.load_range(day1, day3)
    assert len(results) == 2
    assert {r.trading_date for r in results} == {day1, day3}
