"""
app/infrastructure/news/providers/base.py
------------------------------------------------
NewsProvider: الواجهة المجرَّدة - أي مزود أخبار حقيقي مستقبلي (مثال:
Benzinga، NewsAPI) يطبّق هذه الواجهة دون أي تعديل على NewsService.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.infrastructure.news.models import NewsItem


class NewsProvider(ABC):
    @abstractmethod
    def get_latest_news(self, symbol: str | None = None, limit: int = 10) -> list[NewsItem]: ...

    @abstractmethod
    def health_check(self) -> bool: ...
