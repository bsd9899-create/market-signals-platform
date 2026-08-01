"""
tests/test_database.py
--------------------------
اختبار حقيقي (pytest) لطبقة قاعدة البيانات بالكامل: قاعدة بيانات
مؤقتة (SQLite على القرص، تُحذف بعد الاختبار) → إنشاء الجداول → إدخال
بيانات → تعديلها → حذفها → التأكد أن كل العمليات تعمل فعلياً - عبر
DatabaseManager وRepository الحقيقيَّين، بلا أي Mock.

التشغيل: pytest tests/test_database.py -v   (من جذر المشروع)
"""

from __future__ import annotations

import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

from app.infrastructure.database.database import DatabaseManager
from app.infrastructure.database.exceptions import DatabaseConnectionError, DatabaseNotConnectedError
from app.infrastructure.database.models import BotState, DailyReport, ScanLog, Signal
from app.infrastructure.database.repositories import (
    BotStateRepository,
    DailyReportRepository,
    ScanLogRepository,
    SignalRepository,
)
from app.infrastructure.database.repository import Repository


@pytest.fixture()
def db_manager() -> Iterator[DatabaseManager]:
    """قاعدة بيانات SQLite مؤقتة حقيقية على القرص (وليست :memory: -
    لتطابق سلوك الإنتاج فعلياً بما فيه فتح/إغلاق ملف حقيقي)، تُحذف بعد
    كل اختبار بغض النظر عن نجاحه أو فشله."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        manager = DatabaseManager(f"sqlite:///{db_path.as_posix()}")
        manager.connect()
        manager.create_tables()
        yield manager
        manager.close()


def test_connection_succeeds(db_manager: DatabaseManager) -> None:
    assert db_manager.test_connection() is True


def test_tables_created(db_manager: DatabaseManager) -> None:
    from app.infrastructure.database.base import Base

    table_names = set(Base.metadata.tables.keys())
    assert table_names == {"bot_state", "signals", "scan_logs", "daily_reports", "trades"}


def test_database_not_connected_raises() -> None:
    manager = DatabaseManager("sqlite:///unused.db")
    with pytest.raises(DatabaseNotConnectedError):
        manager.test_connection()
    with pytest.raises(DatabaseNotConnectedError):
        manager.create_tables()
    with pytest.raises(DatabaseNotConnectedError):
        with manager.session():
            pass


def test_connection_error_on_unreachable_path() -> None:
    manager = DatabaseManager("sqlite:////nonexistent_root_dir_xyz/impossible/app.db")
    manager.connect()
    with pytest.raises(DatabaseConnectionError):
        manager.test_connection()


def test_full_crud_bot_state(db_manager: DatabaseManager) -> None:
    with db_manager.session() as session:
        repo = Repository(session, BotState)

        # CREATE
        created = repo.create(key="last_run", value="2026-07-30")
        assert created.id is not None
        assert created.created_at is not None
        assert created.updated_at is not None
        created_id = created.id

    # قراءة في Session جديدة تماماً - يثبت أن البيانات فعلاً محفوظة على
    # القرص (Commit حقيقي) وليست فقط في ذاكرة الـSession السابقة.
    with db_manager.session() as session:
        repo = Repository(session, BotState)

        # READ
        fetched = repo.get_by_id(created_id)
        assert fetched is not None
        assert fetched.key == "last_run"
        assert fetched.value == "2026-07-30"
        assert repo.exists(created_id) is True
        assert repo.count() == 1

        # UPDATE
        updated = repo.update(created_id, value="2026-07-31")
        assert updated is not None
        assert updated.value == "2026-07-31"

    with db_manager.session() as session:
        repo = Repository(session, BotState)
        refetched = repo.get_by_id(created_id)
        assert refetched.value == "2026-07-31"  # التعديل فعلاً انحفظ (Commit)

        # DELETE
        deleted = repo.delete(created_id)
        assert deleted is True

    with db_manager.session() as session:
        repo = Repository(session, BotState)
        assert repo.exists(created_id) is False
        assert repo.count() == 0
        assert repo.get_by_id(created_id) is None


def test_update_and_delete_nonexistent_return_falsy(db_manager: DatabaseManager) -> None:
    with db_manager.session() as session:
        repo = Repository(session, BotState)
        assert repo.update(999_999, value="x") is None
        assert repo.delete(999_999) is False
        assert repo.exists(999_999) is False


def test_get_all_and_count_multiple_records(db_manager: DatabaseManager) -> None:
    with db_manager.session() as session:
        repo = Repository(session, Signal)
        repo.create(symbol="AAPL", direction="CALL", status="sent", confidence=91.5)
        repo.create(symbol="NVDA", direction="PUT", status="sent", confidence=85.0)
        repo.create(symbol="TSLA", direction="CALL", status="pending", confidence=70.0)

    with db_manager.session() as session:
        repo = Repository(session, Signal)
        all_signals = repo.get_all()
        assert len(all_signals) == 3
        assert repo.count() == 3
        symbols = {s.symbol for s in all_signals}
        assert symbols == {"AAPL", "NVDA", "TSLA"}


def test_crud_across_all_four_models(db_manager: DatabaseManager) -> None:
    """يثبت أن Repository العام يعمل فعلياً مع كل نموذج من الأربعة، لا
    مع BotState وحدها."""
    from datetime import date, datetime, timezone

    with db_manager.session() as session:
        bot_state_repo = Repository(session, BotState)
        signal_repo = Repository(session, Signal)
        scan_log_repo = Repository(session, ScanLog)
        daily_report_repo = Repository(session, DailyReport)

        bot_state_repo.create(key="mode", value="auto")
        signal_repo.create(symbol="GOOGL", direction="CALL", status="sent", confidence=80.0)
        scan_log_repo.create(
            started_at=datetime.now(timezone.utc), symbols_scanned=4, signals_found=1, duration_ms=1200,
        )
        daily_report_repo.create(
            report_date=date.today(), total_scans=1, signals_sent=1, wins=0, losses=0, win_rate=0.0,
        )

    with db_manager.session() as session:
        assert Repository(session, BotState).count() == 1
        assert Repository(session, Signal).count() == 1
        assert Repository(session, ScanLog).count() == 1
        assert Repository(session, DailyReport).count() == 1


def test_rollback_on_exception_leaves_no_partial_data(db_manager: DatabaseManager) -> None:
    """يثبت أن session_scope يتراجع (Rollback) فعلياً عند حدوث استثناء -
    لا تبقى بيانات جزئية محفوظة."""
    with pytest.raises(ValueError):
        with db_manager.session() as session:
            repo = Repository(session, BotState)
            repo.create(key="should_not_persist", value="x")
            raise ValueError("خطأ متعمَّد لاختبار Rollback")

    with db_manager.session() as session:
        repo = Repository(session, BotState)
        assert repo.count() == 0  # لم يُحفَظ شيء بسبب Rollback


def test_scan_log_has_no_created_updated_at(db_manager: DatabaseManager) -> None:
    """ScanLog يرث من Base مباشرة (وليس BaseModel) - يجب ألا يملك
    created_at/updated_at إطلاقاً، فقط id + حقوله الخاصة."""
    columns = {c.name for c in ScanLog.__table__.columns}
    assert columns == {"id", "started_at", "finished_at", "symbols_scanned", "signals_found", "duration_ms"}
    assert "created_at" not in columns
    assert "updated_at" not in columns


def test_specialized_repositories_full_crud(db_manager: DatabaseManager) -> None:
    """يثبت أن الأربعة Repositories المتخصصة تعمل فعلياً (ترث Repository
    العام بدون أي منطق إضافي) - CRUD كامل عبر كل واحد منها."""
    from datetime import date, datetime, timezone

    with db_manager.session() as session:
        bot_state_repo = BotStateRepository(session)
        signal_repo = SignalRepository(session)
        scan_log_repo = ScanLogRepository(session)
        daily_report_repo = DailyReportRepository(session)

        bot_state = bot_state_repo.create(key="phase", value="2")
        signal = signal_repo.create(symbol="MSFT", direction="CALL", status="sent", confidence=88.0)
        scan_log = scan_log_repo.create(
            started_at=datetime.now(timezone.utc), symbols_scanned=2, signals_found=1, duration_ms=500,
        )
        daily_report = daily_report_repo.create(
            report_date=date.today(), total_scans=2, signals_sent=1, wins=1, losses=0, win_rate=100.0,
        )
        ids = (bot_state.id, signal.id, scan_log.id, daily_report.id)

    with db_manager.session() as session:
        bot_state_repo = BotStateRepository(session)
        signal_repo = SignalRepository(session)
        scan_log_repo = ScanLogRepository(session)
        daily_report_repo = DailyReportRepository(session)

        assert bot_state_repo.get_by_id(ids[0]).key == "phase"
        assert signal_repo.get_by_id(ids[1]).symbol == "MSFT"
        assert scan_log_repo.get_by_id(ids[2]).symbols_scanned == 2
        assert daily_report_repo.get_by_id(ids[3]).win_rate == 100.0

        assert signal_repo.update(ids[1], status="closed").status == "closed"
        assert scan_log_repo.delete(ids[2]) is True
        assert scan_log_repo.exists(ids[2]) is False

        assert bot_state_repo.count() == 1
        assert signal_repo.count() == 1
        assert scan_log_repo.count() == 0
        assert daily_report_repo.count() == 1
