"""
app/infrastructure/options/models.py
------------------------------------------
OptionContract وOptionChain: نماذج بيانات فقط (Dataclasses مُجمَّدة).

Greeks (delta/gamma/theta/vega/rho): **لا تُخترَع أبداً** - None إذا لم
يوفّرها المزود فعلياً (Yahoo Finance لا يوفّر أياً منها فعلياً - راجع
YahooFinanceProvider.get_best_option_contract). MockOptionsProvider
(بيانات تجريبية بالكامل، بلا اتصال حقيقي) هو الوحيد الذي يملأ قيماً
ثابتة معقولة، لأنه أصلاً وهمي بالكامل وليس ادّعاءً ببيانات حقيقية.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class OptionContract:
    symbol: str
    option_type: Literal["CALL", "PUT"]
    strike: float
    expiration: str
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float | None = None    # None إذا لم يوفّره المزود فعلياً (Yahoo لا يوفّره)
    gamma: float | None = None    # None إذا لم يوفّره المزود فعلياً
    theta: float | None = None    # None إذا لم يوفّره المزود فعلياً
    vega: float | None = None     # None إذا لم يوفّره المزود فعلياً
    rho: float | None = None      # None إذا لم يوفّره المزود فعلياً


@dataclass(frozen=True)
class OptionChain:
    symbol: str
    expiration: str
    contracts: list[OptionContract]
