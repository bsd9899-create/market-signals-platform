"""
app/infrastructure/strategies/models.py
----------------------------------------------
StrategyResult: نتيجة تقييم استراتيجية واحدة على قائمة شموع.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.signals.models import SignalDirection


@dataclass(frozen=True)
class StrategyResult:
    strategy_name: str
    matched: bool
    direction: SignalDirection
    confidence: float
    reason: str
