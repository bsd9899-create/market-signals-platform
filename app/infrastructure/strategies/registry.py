"""
app/infrastructure/strategies/registry.py
------------------------------------------------
StrategyRegistry: سجل بسيط اسم -> Strategy - نفس فلسفة
IndicatorRegistry بالضبط.
"""

from __future__ import annotations

from loguru import logger

from app.infrastructure.strategies.base import Strategy
from app.infrastructure.strategies.exceptions import StrategyNotFoundError


class StrategyRegistry:
    def __init__(self) -> None:
        self._strategies: dict[str, Strategy] = {}

    def register(self, strategy: Strategy) -> None:
        self._strategies[strategy.name] = strategy
        logger.debug("StrategyRegistry: سُجِّلت استراتيجية جديدة: {}", strategy.name)

    def get(self, name: str) -> Strategy:
        try:
            return self._strategies[name]
        except KeyError:
            raise StrategyNotFoundError(name) from None

    def names(self) -> list[str]:
        return sorted(self._strategies.keys())
