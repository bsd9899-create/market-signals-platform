"""
app/infrastructure/options/providers/base.py
-----------------------------------------------------
OptionsProvider: الواجهة المجرَّدة - أي مزود خيارات حقيقي مستقبلي
(مثال: Polygon، Tradier) يطبّق هذه الواجهة دون أي تعديل على
OptionsService.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.infrastructure.options.models import OptionChain


class OptionsProvider(ABC):
    @abstractmethod
    def get_option_chain(self, symbol: str, expiration: str | None = None) -> OptionChain: ...

    @abstractmethod
    def get_expirations(self, symbol: str) -> list[str]: ...

    @abstractmethod
    def health_check(self) -> bool: ...
