"""
app/infrastructure/market/cache
------------------------------------
TTLCache: تخزين مؤقت بسيط في الذاكرة يستخدمه MarketService لتقليل عدد
الاستدعاءات المتكررة لمزود البيانات.
"""

from app.infrastructure.market.cache.ttl_cache import TTLCache

__all__ = ["TTLCache"]
