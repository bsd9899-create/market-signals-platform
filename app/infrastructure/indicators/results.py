"""
app/infrastructure/indicators/results.py
-----------------------------------------------
نتائج المؤشرات متعددة القيم (Dataclasses مُجمَّدة) - المؤشرات ذات
القيمة الواحدة (SMA، EMA، RSI، VWAP، ATR، Volume Average) تُرجع
list[float | None] مباشرة بلا حاجة لنموذج نتيجة خاص.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class MACDResult:
    macd_line: list[float | None]
    signal_line: list[float | None]
    histogram: list[float | None]


@dataclass(frozen=True)
class BollingerBandsResult:
    upper: list[float | None]
    middle: list[float | None]
    lower: list[float | None]


@dataclass(frozen=True)
class ADXResult:
    plus_di: list[float | None]
    minus_di: list[float | None]
    adx: list[float | None]


@dataclass(frozen=True)
class StochasticRSIResult:
    k: list[float | None]
    d: list[float | None]


@dataclass(frozen=True)
class VolumeSpikeResult:
    ratio: list[float | None]
    is_spike: list[bool]


@dataclass(frozen=True)
class SupportResistanceResult:
    support_levels: list[float]
    resistance_levels: list[float]


@dataclass(frozen=True)
class TrendDetectionResult:
    trend: Literal["bullish", "bearish", "neutral"]
    fast_ema: float | None
    slow_ema: float | None


@dataclass(frozen=True)
class MomentumDetectionResult:
    momentum: Literal["bullish", "bearish", "neutral"]
    rate_of_change_percent: float | None
