"""
app/infrastructure/news/services/news_service.py
------------------------------------------------------
NewsService: يتعامل حصراً مع NewsProvider (لا يعرف أي مزود فعلي)، ويضيف
فوقه NewsScorer لحساب درجة معنويات (Sentiment Score) مجمَّعة.
"""

from __future__ import annotations

from loguru import logger

from app.infrastructure.news.models import NewsItem
from app.infrastructure.news.providers.base import NewsProvider
from app.infrastructure.news.scoring import NewsScore, NewsScorer


class NewsService:
    def __init__(self, provider: NewsProvider, scorer: NewsScorer | None = None) -> None:
        self._provider = provider
        self._scorer = scorer or NewsScorer()

    def get_latest_news(self, symbol: str | None = None, limit: int = 10) -> list[NewsItem]:
        news = self._provider.get_latest_news(symbol, limit)
        logger.info("NewsService.get_latest_news: symbol={} -> {} خبراً عبر {}", symbol, len(news), type(self._provider).__name__)
        return news

    def get_news_score(self, symbol: str | None = None, limit: int = 10) -> NewsScore:
        news = self.get_latest_news(symbol, limit)
        score = self._scorer.score_items(news)
        logger.info("NewsService.get_news_score: symbol={} -> {}", symbol, score.average_score)
        return score

    def health_check(self) -> bool:
        result = self._provider.health_check()
        logger.info("NewsService.health_check: {} -> {}", type(self._provider).__name__, result)
        return result
