"""
app/infrastructure/options/providers/mock_provider.py
--------------------------------------------------------------
MockOptionsProvider: بيانات ثابتة بالكامل - بلا أي اتصال إنترنت أو API
خارجي إطلاقاً.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loguru import logger

from app.infrastructure.options.exceptions import OptionsUnavailableError
from app.infrastructure.options.models import OptionChain, OptionContract
from app.infrastructure.options.providers.base import OptionsProvider

_FIXED_EXPIRATIONS_DAYS_AHEAD = (7, 14, 30)
_FIXED_UNDERLYING_PRICE = 100.0


class MockOptionsProvider(OptionsProvider):
    def get_expirations(self, symbol: str) -> list[str]:
        today = datetime.now(timezone.utc)
        expirations = [(today + timedelta(days=d)).strftime("%Y-%m-%d") for d in _FIXED_EXPIRATIONS_DAYS_AHEAD]
        logger.debug("MockOptionsProvider.get_expirations: {} -> {}", symbol, expirations)
        return expirations

    def get_option_chain(self, symbol: str, expiration: str | None = None) -> OptionChain:
        expirations = self.get_expirations(symbol)
        target_expiration = expiration or expirations[0]
        if expiration is not None and expiration not in expirations:
            raise OptionsUnavailableError(f"لا توجد سلسلة عقود لـ{symbol} بتاريخ {expiration}")

        contracts = []
        for offset in (-5, -2, 0, 2, 5):
            strike = _FIXED_UNDERLYING_PRICE + offset
            for option_type in ("CALL", "PUT"):
                mid = max(0.05, 5.0 - abs(offset) * 0.5)
                contracts.append(
                    OptionContract(
                        symbol=symbol, option_type=option_type, strike=strike, expiration=target_expiration,
                        bid=round(mid - 0.05, 2), ask=round(mid + 0.05, 2), last=round(mid, 2),
                        volume=100, open_interest=500,
                        implied_volatility=0.30, delta=0.5 if option_type == "CALL" else -0.5,
                        gamma=0.02, theta=-0.03, vega=0.10, rho=0.01,  # Placeholder ثابت - بلا حساب فعلي
                    )
                )

        logger.debug("MockOptionsProvider.get_option_chain: {} {} -> {} عقداً", symbol, target_expiration, len(contracts))
        return OptionChain(symbol=symbol, expiration=target_expiration, contracts=contracts)

    def health_check(self) -> bool:
        return True
