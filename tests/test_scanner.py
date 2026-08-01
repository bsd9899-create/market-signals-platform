"""
tests/test_scanner.py
--------------------------
اختبار حقيقي لـ Scanner وScannerScheduler - عبر MockProvider فقط (بلا
أي اتصال إنترنت). Scanner.scan_one يستدعي SignalEngine الحقيقي الذي
يحتاج 50 شمعة على الأقل - MockProvider.get_candles يُنتج البيانات
اللازمة محلياً.
"""

from __future__ import annotations

import time

from app.infrastructure.market.providers import MockProvider
from app.infrastructure.market.services import MarketService
from app.infrastructure.scanner.models import ScanProgress
from app.infrastructure.scanner.scanner import Scanner
from app.infrastructure.scanner.scheduler import ScannerScheduler


def _make_scanner(max_workers: int = 2) -> Scanner:
    return Scanner(MarketService(MockProvider()), max_workers=max_workers, candles_limit=100)


def test_scan_one_success_with_known_symbol() -> None:
    result = _make_scanner().scan_one("AAPL", "1h")
    assert result.error is None
    assert result.signal is not None
    assert result.symbol == "AAPL"
    assert result.timeframe == "1h"


def test_scan_one_handles_unknown_symbol_gracefully() -> None:
    """MockProvider يرفع SymbolNotFoundError لرمز غير معروف - Scanner
    يجب أن يلتقطه ويُرجع ScanResult.error بدل الانهيار."""
    result = _make_scanner().scan_one("UNKNOWN_XYZ", "1h")
    assert result.signal is None
    assert result.error is not None


def test_scan_symbol_covers_all_requested_timeframes() -> None:
    results = _make_scanner().scan_symbol("AAPL", ["5m", "1h", "1D"])
    assert len(results) == 3
    assert {r.timeframe for r in results} == {"5m", "1h", "1D"}


def test_scan_all_parallel_returns_correct_statistics() -> None:
    scanner = _make_scanner(max_workers=3)
    report = scanner.scan_all(["AAPL", "MSFT", "GOOGL"], timeframes=["5m", "1h"])

    assert report.statistics.total_symbols == 3
    assert report.statistics.total_timeframes == 2
    assert report.statistics.total_scans == 6
    assert report.statistics.successful_scans == 6
    assert report.statistics.failed_scans == 0
    assert report.statistics.duration_ms >= 0
    assert len(report.results) == 6


def test_scan_all_mixed_known_and_unknown_symbols_reports_failures_separately() -> None:
    scanner = _make_scanner()
    report = scanner.scan_all(["AAPL", "UNKNOWN_XYZ"], timeframes=["1h"])

    assert report.statistics.total_scans == 2
    assert report.statistics.successful_scans == 1
    assert report.statistics.failed_scans == 1


def test_scan_all_progress_callback_invoked_once_per_symbol() -> None:
    scanner = _make_scanner(max_workers=2)
    progress_updates: list[ScanProgress] = []

    scanner.scan_all(["AAPL", "MSFT"], timeframes=["1h"], progress_callback=progress_updates.append)

    assert len(progress_updates) == 2
    assert progress_updates[-1].completed_symbols == 2
    assert progress_updates[-1].total_symbols == 2


# ---------------------------------------------------------------------
# ScannerScheduler
# ---------------------------------------------------------------------


def test_scheduler_run_once_is_deterministic() -> None:
    scanner = _make_scanner()
    scheduler = ScannerScheduler(scanner, ["AAPL"], timeframes=["1h"], interval_seconds=999)

    report = scheduler.run_once()

    assert scheduler.run_count == 1
    assert scheduler.last_report is report
    assert report.statistics.total_scans == 1


def test_scheduler_start_stop_actually_runs_in_background_thread() -> None:
    """اختبار حقيقي لـ Threading الفعلي - فترة قصيرة جداً (0.05 ثانية)
    ثم انتظار حقيقي قصير للتأكد من تنفيذ أكثر من دورة واحدة فعلياً."""
    scanner = _make_scanner()
    scheduler = ScannerScheduler(scanner, ["AAPL"], timeframes=["1h"], interval_seconds=0.05)

    assert scheduler.is_running is False
    scheduler.start()
    assert scheduler.is_running is True

    time.sleep(0.3)  # يكفي لعدة دورات عند interval=0.05
    scheduler.stop(timeout=2.0)

    assert scheduler.is_running is False
    assert scheduler.run_count >= 2  # تأكيد أنها عملت أكثر من مرة فعلياً في الخلفية


def test_scheduler_start_is_idempotent() -> None:
    scanner = _make_scanner()
    scheduler = ScannerScheduler(scanner, ["AAPL"], timeframes=["1h"], interval_seconds=10)
    scheduler.start()
    first_thread = scheduler._thread  # noqa: SLF001 - فحص داخلي متعمَّد لإثبات عدم إنشاء Thread جديد
    scheduler.start()  # استدعاء ثانٍ - يجب ألا يُنشئ Thread جديداً
    assert scheduler._thread is first_thread  # noqa: SLF001
    scheduler.stop()
