"""
app/infrastructure/news/scoring.py
------------------------------------
NewsScorer: يحوّل قائمة NewsItem إلى درجة رقمية واحدة (متوسط) -
positive=+1, negative=-1, neutral=0.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.news.models import NewsItem

_SENTIMENT_SCORES: dict[str, float] = {"positive": 1.0, "negative": -1.0, "neutral": 0.0}


@dataclass(frozen=True)
class NewsScore:
    symbol: str | None
    average_score: float
    item_count: int


class NewsScorer:
    def score_item(self, item: NewsItem) -> float:
        return _SENTIMENT_SCORES[item.sentiment]

    def score_items(self, items: list[NewsItem]) -> NewsScore:
        if not items:
            return NewsScore(symbol=None, average_score=0.0, item_count=0)
        scores = [self.score_item(item) for item in items]
        return NewsScore(
            symbol=items[0].symbol, average_score=round(sum(scores) / len(scores), 2), item_count=len(items),
        )
