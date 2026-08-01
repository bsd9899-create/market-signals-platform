"""
app/infrastructure/news/sentiment.py
------------------------------------------
SentimentAnalyzer: واجهة مجرَّدة لتحليل المشاعر (Placeholder) -
KeywordSentimentAnalyzer هو التطبيق الوحيد الآن: تصنيف محلي بسيط
بالكلمات المفتاحية، **بلا أي نموذج NLP حقيقي أو API خارجي**. ربط محلل
مشاعر حقيقي لاحقاً (نموذج NLP/API) = كتابة SentimentAnalyzer جديد فقط.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal

Sentiment = Literal["positive", "negative", "neutral"]

_POSITIVE_KEYWORDS = ("growth", "beat", "upgrade", "surge", "rally", "profit", "أفضل", "يرفع")
_NEGATIVE_KEYWORDS = ("miss", "downgrade", "lawsuit", "decline", "plunge", "loss", "ضغط", "تباطؤ")


class SentimentAnalyzer(ABC):
    @abstractmethod
    def analyze(self, text: str) -> Sentiment: ...


class KeywordSentimentAnalyzer(SentimentAnalyzer):
    def analyze(self, text: str) -> Sentiment:
        lowered = text.lower()
        is_positive = any(keyword in lowered for keyword in _POSITIVE_KEYWORDS)
        is_negative = any(keyword in lowered for keyword in _NEGATIVE_KEYWORDS)
        if is_positive and not is_negative:
            return "positive"
        if is_negative and not is_positive:
            return "negative"
        return "neutral"
