"""
app/infrastructure/news/providers/mock_provider.py
--------------------------------------------------------
MockNewsProvider: بيانات ثابتة بالكامل - بلا أي اتصال إنترنت أو API
خارجي إطلاقاً. المشاعر (Sentiment) تُحسَب فعلياً عبر
KeywordSentimentAnalyzer (محلي بالكامل) - وليست مُعلَّبة يدوياً - لإثبات
أن Placeholder التحليل يعمل حقاً، وليس مجرد حقل ثابت.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loguru import logger

from app.infrastructure.news.models import NewsItem
from app.infrastructure.news.providers.base import NewsProvider
from app.infrastructure.news.sentiment import KeywordSentimentAnalyzer, SentimentAnalyzer

_FIXED_HEADLINE_TEMPLATES: tuple[str, ...] = (
    "{symbol} تعلن نتائج فصلية beat التوقعات وتحقق growth قوياً",
    "محللون يرفعون تقييم {symbol} (upgrade)",
    "{symbol} تواجه ضغطاً تنظيمياً جديداً (decline محتمل)",
    "miss في تقديرات إيرادات {symbol} هذا الفصل",
    "{symbol} تعقد مؤتمراً صحفياً روتينياً",
)


class MockNewsProvider(NewsProvider):
    def __init__(self, sentiment_analyzer: SentimentAnalyzer | None = None) -> None:
        self._sentiment_analyzer = sentiment_analyzer or KeywordSentimentAnalyzer()

    def get_latest_news(self, symbol: str | None = None, limit: int = 10) -> list[NewsItem]:
        target_symbol = symbol or "MARKET"
        now = datetime.now(timezone.utc)
        items = [
            NewsItem(
                symbol=symbol,
                headline=(headline := template.format(symbol=target_symbol)),
                source="MockNewsProvider",
                sentiment=self._sentiment_analyzer.analyze(headline),
                published_at=now - timedelta(hours=i),
            )
            for i, template in enumerate(_FIXED_HEADLINE_TEMPLATES)
        ][:limit]
        logger.debug("MockNewsProvider.get_latest_news: symbol={}, {} خبراً", symbol, len(items))
        return items

    def health_check(self) -> bool:
        return True
