"""
app/infrastructure/scanner/scheduler.py
--------------------------------------------
ScannerScheduler: يُشغِّل Scanner.scan_all() دورياً في Thread خلفي
(daemon) - start()/stop() لدورة الحياة، run_once() لتشغيل فحص واحد
فوراً ومباشرة (مفيد للاختبار الحتمي بلا انتظار زمني حقيقي).
"""

from __future__ import annotations

import threading

from loguru import logger

from app.infrastructure.scanner.models import ScanReport
from app.infrastructure.scanner.scanner import Scanner


class ScannerScheduler:
    def __init__(
        self, scanner: Scanner, symbols: list[str], timeframes: list[str] | None = None,
        interval_seconds: float = 300.0,
    ) -> None:
        self._scanner = scanner
        self._symbols = symbols
        self._timeframes = timeframes
        self._interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.run_count = 0
        self.last_report: ScanReport | None = None

    def run_once(self) -> ScanReport:
        self.last_report = self._scanner.scan_all(self._symbols, self._timeframes)
        self.run_count += 1
        return self.last_report

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                logger.exception("ScannerScheduler: فشل تنفيذ دورة فحص - سيُعاد المحاولة في الدورة القادمة.")
            self._stop_event.wait(self._interval_seconds)

    def start(self) -> None:
        if self.is_running:
            logger.debug("ScannerScheduler: يعمل بالفعل - تجاهل start() مكرر.")
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("ScannerScheduler: بدأ التشغيل (كل {} ثانية).", self._interval_seconds)

    def stop(self, timeout: float = 5.0) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=timeout)
        logger.info("ScannerScheduler: توقف.")

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
