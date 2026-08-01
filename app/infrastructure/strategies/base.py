"""
app/infrastructure/strategies/base.py
--------------------------------------------
Strategy: الواجهة المجرَّدة التي يطبّقها كل استراتيجية - نفس أسلوب
Indicator (Open/Closed): استراتيجية جديدة = صف جديد يطبّق هذه الواجهة +
تسجيلها في StrategyRegistry، دون تعديل أي استراتيجية قائمة.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from app.infrastructure.market.models import Candle
from app.infrastructure.strategies.models import StrategyResult


class Strategy(ABC):
    name: ClassVar[str]

    @abstractmethod
    def min_candles_required(self) -> int: ...

    @abstractmethod
    def evaluate(self, candles: list[Candle]) -> StrategyResult: ...
