"""
app/infrastructure/options/liquidity.py
--------------------------------------------
تصنيف سيولة عقد خيارات (Placeholder بسيط بعتبات ثابتة) - بلا أي منطق
تداول فعلي، فقط تصنيف وصفي حسب Volume/Open Interest.
"""

from __future__ import annotations

from enum import Enum

from app.infrastructure.options.models import OptionContract


class LiquidityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


def classify_liquidity(
    contract: OptionContract, high_volume: int = 500, high_open_interest: int = 1000,
    low_volume: int = 50, low_open_interest: int = 100,
) -> LiquidityLevel:
    if contract.volume >= high_volume and contract.open_interest >= high_open_interest:
        return LiquidityLevel.HIGH
    if contract.volume <= low_volume or contract.open_interest <= low_open_interest:
        return LiquidityLevel.LOW
    return LiquidityLevel.MEDIUM
