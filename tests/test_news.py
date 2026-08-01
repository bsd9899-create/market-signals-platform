"""
tests/test_news.py
-----------------------
اختبار حقيقي لطبقة الأخبار - MockNewsProvider فقط (بلا أي API خارجي).
"""

from __future__ import annotations

import inspect

from app.infrastructure.news.providers import mock_provider as mock_provider_module
from app.infrastructure.news.providers.mock_provider import MockNewsProvider
from app.infrastructure.news.scoring import NewsScorer
from app.infrastructure.news.sentiment import KeywordSentimentAnalyzer
from app.infrastructure.news.services.news_service import NewsService


def test_mock_news_provider_returns_items_with_valid_sentiment() -> None:
    provider = MockNewsProvider()
    items = provider.get_latest_news("AAPL", limit=3)
    assert len(items) == 3
    assert all(item.symbol == "AAPL" for item in items)
    assert all(item.sentiment in ("positive", "negative", "neutral") for item in items)


def test_mock_news_provider_health_check() -> None:
    assert MockNewsProvider().health_check() is True


def test_mock_news_provider_no_network_dependency() -> None:
    source = inspect.getsource(mock_provider_module)
    for forbidden in ("requests", "httpx", "urllib", "socket", "aiohttp"):
        assert forbidden not in source


def test_keyword_sentiment_analyzer_positive() -> None:
    analyzer = KeywordSentimentAnalyzer()
    assert analyzer.analyze("Company reports strong growth and beats estimates") == "positive"


def test_keyword_sentiment_analyzer_negative() -> None:
    analyzer = KeywordSentimentAnalyzer()
    assert analyzer.analyze("Company faces lawsuit after earnings miss") == "negative"


def test_keyword_sentiment_analyzer_neutral() -> None:
    analyzer = KeywordSentimentAnalyzer()
    assert analyzer.analyze("Company holds routine press conference") == "neutral"


def test_news_scorer_average_score_hand_verified() -> None:
    """positive=+1, negative=-1, neutral=0 - نتحقق من مثال ثابت:
    [positive, positive, negative, negative, neutral] -> متوسط = 0.0."""
    from datetime import datetime, timezone

    from app.infrastructure.news.models import NewsItem

    items = [
        NewsItem(symbol="AAPL", headline="a", source="s", sentiment="positive", published_at=datetime.now(timezone.utc)),
        NewsItem(symbol="AAPL", headline="b", source="s", sentiment="positive", published_at=datetime.now(timezone.utc)),
        NewsItem(symbol="AAPL", headline="c", source="s", sentiment="negative", published_at=datetime.now(timezone.utc)),
        NewsItem(symbol="AAPL", headline="d", source="s", sentiment="negative", published_at=datetime.now(timezone.utc)),
        NewsItem(symbol="AAPL", headline="e", source="s", sentiment="neutral", published_at=datetime.now(timezone.utc)),
    ]
    score = NewsScorer().score_items(items)
    assert score.average_score == 0.0
    assert score.item_count == 5
    assert score.symbol == "AAPL"


def test_news_scorer_empty_list() -> None:
    score = NewsScorer().score_items([])
    assert score.average_score == 0.0
    assert score.item_count == 0


def test_news_service_get_latest_news_delegates_to_provider() -> None:
    service = NewsService(MockNewsProvider())
    news = service.get_latest_news("AAPL", limit=2)
    assert len(news) == 2


def test_news_service_get_news_score() -> None:
    service = NewsService(MockNewsProvider())
    score = service.get_news_score("AAPL")
    assert score.item_count > 0
    assert -1.0 <= score.average_score <= 1.0


def test_news_service_health_check() -> None:
    assert NewsService(MockNewsProvider()).health_check() is True
