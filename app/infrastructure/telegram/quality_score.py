"""
app/infrastructure/telegram/quality_score.py
------------------------------------------------
FinalScoreCalculator: يجمع كل عناصر جودة الإشارة في نتيجة نهائية واحدة
(Final Quality Score) - هي ما يُقارَن فعلياً بعتبة 70% في app/main.py
لتحديد الإرسال من عدمه (Signal.confidence الأصلي **لا يتغيّر إطلاقاً**).

technical_score = Signal.confidence كما هو - يُمثِّل Technical Analysis +
Strategy Agreement + Trend Strength مجتمعة فعلياً (SignalEngine يحسبها
من TrendDetection/MomentumDetection/MACD/RSI + مكافأة كل استراتيجية
متوافقة - بلا أي إعادة حساب هنا، وبلا أي تعديل على SignalEngine نفسه).

news_adjustment/earnings_adjustment/liquidity_adjustment: فروق محدودة
(موجبة أو سالبة) تُضاف فوق technical_score - موثَّقة بوضوح أدناه.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.news.models import EarningsInfo
from app.infrastructure.news.scoring import NewsScore
from app.infrastructure.options.models import OptionContract
from app.infrastructure.signals.models import SignalDirection

_NEWS_OPPOSED_WEIGHT = 8.0
_NEWS_ALIGNED_WEIGHT = 4.0
_EARNINGS_MAX_PENALTY = 10.0
_EARNINGS_WINDOW_HOURS = 48.0
_LIQUIDITY_HIGH_THRESHOLD = 5000
_LIQUIDITY_MEDIUM_THRESHOLD = 1000
_LIQUIDITY_LOW_THRESHOLD = 100
_LIQUIDITY_HIGH_BONUS = 5.0
_LIQUIDITY_MEDIUM_BONUS = 2.0
_LIQUIDITY_LOW_PENALTY = -6.0


@dataclass(frozen=True)
class QualityScoreBreakdown:
    technical_score: float
    news_adjustment: float
    earnings_adjustment: float
    liquidity_adjustment: float
    final_score: float


class FinalScoreCalculator:
    def calculate(
        self, technical_confidence: float, direction: SignalDirection, news_score: NewsScore,
        earnings_info: EarningsInfo | None, option_contract: OptionContract | None, is_estimated_contract: bool,
    ) -> QualityScoreBreakdown:
        news_adjustment = self._news_adjustment(news_score, direction)
        earnings_adjustment = self._earnings_adjustment(earnings_info)
        liquidity_adjustment = self._liquidity_adjustment(option_contract, is_estimated_contract)

        raw_final = technical_confidence + news_adjustment + earnings_adjustment + liquidity_adjustment
        final_score = max(0.0, min(100.0, round(raw_final, 2)))

        return QualityScoreBreakdown(
            technical_score=technical_confidence, news_adjustment=news_adjustment,
            earnings_adjustment=earnings_adjustment, liquidity_adjustment=liquidity_adjustment,
            final_score=final_score,
        )

    @staticmethod
    def _news_adjustment(news_score: NewsScore, direction: SignalDirection) -> float:
        if news_score.item_count == 0:
            return 0.0

        opposed = (direction == SignalDirection.BUY and news_score.average_score < 0) or (
            direction == SignalDirection.SELL and news_score.average_score > 0
        )
        aligned = (direction == SignalDirection.BUY and news_score.average_score > 0) or (
            direction == SignalDirection.SELL and news_score.average_score < 0
        )
        magnitude = abs(news_score.average_score)

        if opposed:
            return round(-magnitude * _NEWS_OPPOSED_WEIGHT, 2)
        if aligned:
            return round(magnitude * _NEWS_ALIGNED_WEIGHT, 2)
        return 0.0

    @staticmethod
    def _earnings_adjustment(earnings_info: EarningsInfo | None) -> float:
        if earnings_info is None or earnings_info.hours_until >= _EARNINGS_WINDOW_HOURS:
            return 0.0
        closeness = max(0.0, (_EARNINGS_WINDOW_HOURS - earnings_info.hours_until) / _EARNINGS_WINDOW_HOURS)
        return round(-closeness * _EARNINGS_MAX_PENALTY, 2)

    @staticmethod
    def _liquidity_adjustment(option_contract: OptionContract | None, is_estimated: bool) -> float:
        if is_estimated or option_contract is None:
            return 0.0
        liquidity = option_contract.volume + option_contract.open_interest
        if liquidity >= _LIQUIDITY_HIGH_THRESHOLD:
            return _LIQUIDITY_HIGH_BONUS
        if liquidity >= _LIQUIDITY_MEDIUM_THRESHOLD:
            return _LIQUIDITY_MEDIUM_BONUS
        if liquidity < _LIQUIDITY_LOW_THRESHOLD:
            return _LIQUIDITY_LOW_PENALTY
        return 0.0
