"""
app/infrastructure/news/models.py
------------------------------------
NewsItem: نموذج بيانات فقط (Dataclass مُجمَّدة).

EarningsInfo/AnalystAction/SecFiling: نماذج إضافية (Dataclasses مُجمَّدة)
لدعم YahooNewsProvider - Earnings القادمة، ترقيات/تخفيضات المحللين،
وإيداعات SEC - كلها بيانات فقط، بلا أي منطق قرار هنا.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal


@dataclass(frozen=True)
class NewsItem:
    symbol: str | None
    headline: str
    source: str
    sentiment: Literal["positive", "negative", "neutral"]
    published_at: datetime


@dataclass(frozen=True)
class EarningsInfo:
    symbol: str
    earnings_date: date
    hours_until: float


@dataclass(frozen=True)
class AnalystAction:
    symbol: str
    firm: str
    to_grade: str
    from_grade: str
    action: str
    graded_at: datetime


@dataclass(frozen=True)
class SecFiling:
    symbol: str
    form: str
    filing_date: date
    description: str
