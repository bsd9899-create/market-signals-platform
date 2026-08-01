"""
app/infrastructure/strategies/strategy_engine.py
--------------------------------------------------------
StrategyEngine: نقطة الاستدعاء الموحَّدة لكل الاستراتيجيات - لا "يعرف"
أي استراتيجية بعينها (Open/Closed)، تماماً كـIndicatorService.
"""

from __future__ import annotations

from loguru import logger

from app.infrastructure.market.models import Candle
from app.infrastructure.strategies.base import Strategy
from app.infrastructure.strategies.models import StrategyResult
from app.infrastructure.strategies.registry import StrategyRegistry
from app.infrastructure.strategies.strategies import default_registry


class StrategyEngine:
    def __init__(self, registry: StrategyRegistry | None = None) -> None:
        self._registry = registry if registry is not None else default_registry()
        logger.info("StrategyEngine: جاهز مع {} استراتيجية: {}", len(self._registry.names()), self._registry.names())

    def register(self, strategy: Strategy) -> None:
        self._registry.register(strategy)
        logger.info("StrategyEngine: تم تسجيل استراتيجية جديدة: {}", strategy.name)

    def evaluate(self, name: str, candles: list[Candle]) -> StrategyResult:
        strategy = self._registry.get(name)
        logger.info("StrategyEngine.evaluate: {} على {} شمعة", name, len(candles))
        result = strategy.evaluate(candles)
        logger.debug("StrategyEngine.evaluate: {} -> matched={}, direction={}", name, result.matched, result.direction.value)
        return result

    def evaluate_all(self, candles: list[Candle]) -> dict[str, StrategyResult]:
        """يقيّم كل الاستراتيجيات المسجَّلة، متجاهلاً أي استراتيجية بها
        بيانات غير كافية (لا يوقف البقية)."""
        from app.infrastructure.strategies.exceptions import InsufficientCandlesError

        results: dict[str, StrategyResult] = {}
        for name in self._registry.names():
            try:
                results[name] = self.evaluate(name, candles)
            except InsufficientCandlesError:
                logger.debug("StrategyEngine.evaluate_all: تخطي {} - بيانات غير كافية.", name)
        return results

    def available_strategies(self) -> list[str]:
        return self._registry.names()
