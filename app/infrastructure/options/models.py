"""
app/infrastructure/options/models.py
------------------------------------------
OptionContract وOptionChain: نماذج بيانات فقط (Dataclasses مُجمَّدة).

Greeks (gamma/theta/vega/rho): حقول Placeholder - قيم رقمية عادية بلا
أي حساب فعلي بعد (المزود الوهمي يملأها بقيم ثابتة معقولة)؛ حساب Greeks
حقيقي (Black-Scholes أو من مزود حقيقي) مسؤولية مرحلة قادمة.
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
    delta: float
    gamma: float = 0.0     # Placeholder - بلا حساب فعلي بعد
    theta: float = 0.0     # Placeholder - بلا حساب فعلي بعد
    vega: float = 0.0      # Placeholder - بلا حساب فعلي بعد
    rho: float = 0.0       # Placeholder - بلا حساب فعلي بعد


@dataclass(frozen=True)
class OptionChain:
    symbol: str
    expiration: str
    contracts: list[OptionContract]
