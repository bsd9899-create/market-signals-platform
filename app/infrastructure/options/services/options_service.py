"""
app/infrastructure/options/services/options_service.py
-------------------------------------------------------------
OptionsService: يتعامل حصراً مع OptionsProvider (لا يعرف أي مزود فعلي).
"""

from __future__ import annotations

from loguru import logger

from app.infrastructure.options.models import OptionChain
from app.infrastructure.options.providers.base import OptionsProvider


class OptionsService:
    def __init__(self, provider: OptionsProvider) -> None:
        self._provider = provider

    def get_option_chain(self, symbol: str, expiration: str | None = None) -> OptionChain:
        chain = self._provider.get_option_chain(symbol, expiration)
        logger.info(
            "OptionsService.get_option_chain: {} {} -> {} عقداً عبر {}",
            symbol, chain.expiration, len(chain.contracts), type(self._provider).__name__,
        )
        return chain

    def get_expirations(self, symbol: str) -> list[str]:
        return self._provider.get_expirations(symbol)

    def health_check(self) -> bool:
        result = self._provider.health_check()
        logger.info("OptionsService.health_check: {} -> {}", type(self._provider).__name__, result)
        return result
