"""
app/infrastructure/strategies/strategies
----------------------------------------------
5 استراتيجيات مبنية (Built-in) - كل واحدة في ملفها المستقل.
default_registry() تُسجِّلها جميعاً.
"""

from __future__ import annotations

from app.infrastructure.strategies.registry import StrategyRegistry
from app.infrastructure.strategies.strategies.breakout import Breakout
from app.infrastructure.strategies.strategies.momentum import Momentum
from app.infrastructure.strategies.strategies.pullback import Pullback
from app.infrastructure.strategies.strategies.reversal import Reversal
from app.infrastructure.strategies.strategies.trend_following import TrendFollowing

__all__ = ["Breakout", "Momentum", "Pullback", "Reversal", "TrendFollowing", "default_registry"]


def default_registry() -> StrategyRegistry:
    registry = StrategyRegistry()
    for strategy_cls in (TrendFollowing, Pullback, Breakout, Reversal, Momentum):
        registry.register(strategy_cls())
    return registry
