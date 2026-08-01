"""
app/infrastructure/scanner/models.py
------------------------------------------
ScanResult: نتيجة فحص رمز واحد على إطار زمني واحد. error يُملأ (وsignal
يبقى None) إذا فشل هذا التركيب تحديداً - بقية الفحص يكمل عادةً.

ScanProgress: يُمرَّر إلى progress_callback أثناء scan_all() (رمز واحد
مكتمل = تحديث واحد - كل رمز يفحص كل أطره الزمنية داخلياً قبل التحديث).

ScanStatistics + ScanReport: ملخص إحصائي شامل بعد اكتمال scan_all().
"""

from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.signals.models import Signal

DEFAULT_TIMEFRAMES: tuple[str, ...] = ("5m", "15m", "1h", "4h", "1D")


@dataclass(frozen=True)
class ScanResult:
    symbol: str
    timeframe: str
    signal: Signal | None
    error: str | None


@dataclass(frozen=True)
class ScanProgress:
    completed_symbols: int
    total_symbols: int


@dataclass(frozen=True)
class ScanStatistics:
    total_symbols: int
    total_timeframes: int
    total_scans: int
    successful_scans: int
    failed_scans: int
    buy_signals: int
    sell_signals: int
    neutral_signals: int
    duration_ms: float


@dataclass(frozen=True)
class ScanReport:
    results: list[ScanResult]
    statistics: ScanStatistics
