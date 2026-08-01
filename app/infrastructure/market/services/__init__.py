"""
app/infrastructure/market/services
---------------------------------------
MarketService: نقطة الاستخدام الوحيدة لبيانات السوق من بقية المشروع -
يغلّف أي MarketDataProvider بتخزين مؤقت وتسجيل.
"""

from app.infrastructure.market.services.market_service import MarketService

__all__ = ["MarketService"]
