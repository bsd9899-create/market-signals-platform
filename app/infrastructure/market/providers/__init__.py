"""
app/infrastructure/market/providers
---------------------------------------
MarketDataProvider (الواجهة المجرَّدة) وMockProvider (المزود الوهمي
الوحيد المتاح في هذه المرحلة - بلا أي اتصال إنترنت).
"""

from app.infrastructure.market.providers.base import MarketDataProvider
from app.infrastructure.market.providers.mock_provider import MockProvider

__all__ = ["MarketDataProvider", "MockProvider"]
