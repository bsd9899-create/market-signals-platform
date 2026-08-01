"""
app/infrastructure/scanner/scanner.py
------------------------------------------
Scanner: يفحص عدة رموز عبر عدة أطر زمنية (5m/15m/1h/4h/1D افتراضياً)
بالتوازي (ThreadPoolExecutor - مناسب هنا لأن العمل غالباً I/O-bound:
جلب بيانات عبر MarketService). فشل رمز/إطار واحد لا يوقف بقية الفحص
(راجع ScanResult.error).

خط الأنابيب الكامل لكل تركيب (رمز، إطار زمني) يمرّ عبر SignalEngine،
الذي بدوره يمرّ داخلياً عبر: MarketService (جلب الشموع، قبل استدعاء
SignalEngine) -> IndicatorService -> StrategyEngine -> RiskManager -
Scanner نفسه لا "يعرف" أي تفصيل من هذه الطبقات، فقط يُنسِّق الاستدعاء.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger

from app.infrastructure.market.services import MarketService
from app.infrastructure.scanner.models import (
    DEFAULT_TIMEFRAMES,
    ScanProgress,
    ScanReport,
    ScanResult,
    ScanStatistics,
)
from app.infrastructure.signals.exceptions import SignalEngineError
from app.infrastructure.signals.models import SignalDirection
from app.infrastructure.signals.signal_engine import SignalEngine


class Scanner:
    def __init__(
        self, market_service: MarketService, signal_engine: SignalEngine | None = None,
        max_workers: int = 4, candles_limit: int = 100,
    ) -> None:
        self._market_service = market_service
        self._signal_engine = signal_engine or SignalEngine()
        self._max_workers = max_workers
        self._candles_limit = candles_limit

    def scan_one(self, symbol: str, timeframe: str) -> ScanResult:
        try:
            candles = self._market_service.get_candles(symbol, timeframe, limit=self._candles_limit)
            signal = self._signal_engine.generate(symbol, candles)
            logger.debug("Scanner.scan_one: {} {} -> {}", symbol, timeframe, signal.direction.value)
            return ScanResult(symbol=symbol, timeframe=timeframe, signal=signal, error=None)
        except (SignalEngineError, Exception) as exc:  # noqa: BLE001 - فشل رمز واحد لا يجب أن يوقف الفحص كله
            logger.warning("Scanner.scan_one: فشل {} {} -> {}", symbol, timeframe, exc)
            return ScanResult(symbol=symbol, timeframe=timeframe, signal=None, error=str(exc))

    def scan_symbol(self, symbol: str, timeframes: list[str] | None = None) -> list[ScanResult]:
        timeframes = timeframes if timeframes is not None else list(DEFAULT_TIMEFRAMES)
        return [self.scan_one(symbol, tf) for tf in timeframes]

    def scan_all(
        self, symbols: list[str], timeframes: list[str] | None = None,
        progress_callback: Callable[[ScanProgress], None] | None = None,
    ) -> ScanReport:
        """يفحص كل الرموز بالتوازي (رمز واحد لكل Thread) - كل رمز يفحص
        أطره الزمنية بالتسلسل داخل Thread الخاص به. progress_callback
        (إن وُجد) يُستدعى بعد اكتمال كل رمز على حدة."""
        timeframes = timeframes if timeframes is not None else list(DEFAULT_TIMEFRAMES)
        logger.info("Scanner.scan_all: {} رمز × {} إطار زمني (max_workers={})", len(symbols), len(timeframes), self._max_workers)

        start = time.monotonic()
        results: list[ScanResult] = []
        completed = 0

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            futures = {executor.submit(self.scan_symbol, symbol, timeframes): symbol for symbol in symbols}
            for future in as_completed(futures):
                results.extend(future.result())
                completed += 1
                if progress_callback is not None:
                    progress_callback(ScanProgress(completed_symbols=completed, total_symbols=len(symbols)))

        duration_ms = (time.monotonic() - start) * 1000

        successful = [r for r in results if r.error is None]
        failed = [r for r in results if r.error is not None]
        buy_count = sum(1 for r in successful if r.signal and r.signal.direction == SignalDirection.BUY)
        sell_count = sum(1 for r in successful if r.signal and r.signal.direction == SignalDirection.SELL)
        neutral_count = sum(1 for r in successful if r.signal and r.signal.direction == SignalDirection.NEUTRAL)

        statistics = ScanStatistics(
            total_symbols=len(symbols),
            total_timeframes=len(timeframes),
            total_scans=len(results),
            successful_scans=len(successful),
            failed_scans=len(failed),
            buy_signals=buy_count,
            sell_signals=sell_count,
            neutral_signals=neutral_count,
            duration_ms=round(duration_ms, 2),
        )
        logger.info(
            "Scanner.scan_all: اكتمل - {} فحص ({} نجح، {} فشل) خلال {:.1f}ms - BUY={}, SELL={}, NEUTRAL={}",
            statistics.total_scans, statistics.successful_scans, statistics.failed_scans,
            statistics.duration_ms, buy_count, sell_count, neutral_count,
        )
        return ScanReport(results=results, statistics=statistics)
