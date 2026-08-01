"""
app/infrastructure/telegram/quality_score.py
------------------------------------------------
FinalScoreCalculator: Final Score = مجموع مرجَّح لخمسة مكوّنات، كل واحد
مُطبَّع إلى مقياس 0-100 بوضوح، ثم يُقارَن بعتبة الإرسال (70%) في
app/main.py. Signal.confidence الأصلي **لا يتغيّر إطلاقاً** (Signal
مُجمَّد أصلاً؛ SignalEngine نفسه بلا أي تعديل).

المكوّنات الخمسة:
- Technical Score  = Signal.confidence كما هو (SignalEngine يحسبه فعلياً
  من TrendDetection/MomentumDetection/MACD/RSI - بلا أي إعادة حساب هنا).
- Strategy Score    = نسبة الاستراتيجيات المسجَّلة (5) المتوافقة مع نفس
  اتجاه الإشارة (Signal.strategy_used) - مقياس تعزيز مستقل عن Technical
  Score رغم أن الأخير يتضمن أصلاً مكافأة استراتيجية داخلية (تصميم
  SignalEngine نفسه، غير مُعدَّل) - هذا مقياس تصويت إضافي صريح كما طُلِب.
- News Score        = معنويات الأخبار الحقيقية (NewsScore) مُعاد توجيهها
  حسب اتجاه الإشارة (خبر سلبي يرفع News Score لإشارة SELL، والعكس).
- Earnings Score     = 100 إذا لا أرباح خلال 48 ساعة، تنخفض خطياً كلما
  اقترب الموعد (0 عند اقتراب لحظي).
- Option Score       = من YahooFinanceProvider.get_best_option_contract
  مباشرة (Liquidity/OpenInterest/Volume/Spread/IV حقيقية بالكامل) -
  50 (محايد) إذا كان العقد تقديرياً (بلا بيانات خيارات حقيقية).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.news.models import EarningsInfo
from app.infrastructure.news.scoring import NewsScore
from app.infrastructure.signals.models import SignalDirection

_WEIGHT_TECHNICAL = 0.40
_WEIGHT_STRATEGY = 0.15
_WEIGHT_NEWS = 0.15
_WEIGHT_EARNINGS = 0.15
_WEIGHT_OPTION = 0.15

_TOTAL_REGISTERED_STRATEGIES = 5  # breakout/momentum/pullback/reversal/trend_following (StrategyEngine - غير مُعدَّل)
_EARNINGS_WINDOW_HOURS = 48.0
_NEUTRAL_SCORE = 50.0


@dataclass(frozen=True)
class QualityScoreBreakdown:
    technical_score: float
    strategy_score: float
    news_score: float
    earnings_score: float
    option_score: float
    final_score: float


class FinalScoreCalculator:
    def calculate(
        self, technical_confidence: float, strategy_used_count: int, direction: SignalDirection,
        news_score: NewsScore, earnings_info: EarningsInfo | None, option_score: float | None,
    ) -> QualityScoreBreakdown:
        technical = max(0.0, min(100.0, technical_confidence))
        strategy = self._strategy_score(strategy_used_count)
        news = self._news_score(news_score, direction)
        earnings = self._earnings_score(earnings_info)
        option = option_score if option_score is not None else _NEUTRAL_SCORE

        final = (
            technical * _WEIGHT_TECHNICAL + strategy * _WEIGHT_STRATEGY + news * _WEIGHT_NEWS
            + earnings * _WEIGHT_EARNINGS + option * _WEIGHT_OPTION
        )
        final_score = max(0.0, min(100.0, round(final, 2)))

        return QualityScoreBreakdown(
            technical_score=round(technical, 2), strategy_score=round(strategy, 2), news_score=round(news, 2),
            earnings_score=round(earnings, 2), option_score=round(option, 2), final_score=final_score,
        )

    @staticmethod
    def _strategy_score(strategy_used_count: int) -> float:
        ratio = strategy_used_count / _TOTAL_REGISTERED_STRATEGIES
        return max(0.0, min(100.0, ratio * 100.0))

    @staticmethod
    def _news_score(news_score: NewsScore, direction: SignalDirection) -> float:
        if news_score.item_count == 0:
            return _NEUTRAL_SCORE
        alignment = news_score.average_score if direction == SignalDirection.BUY else -news_score.average_score
        return max(0.0, min(100.0, (alignment + 1.0) / 2.0 * 100.0))

    @staticmethod
    def _earnings_score(earnings_info: EarningsInfo | None) -> float:
        if earnings_info is None or earnings_info.hours_until >= _EARNINGS_WINDOW_HOURS:
            return 100.0
        closeness = max(0.0, (_EARNINGS_WINDOW_HOURS - earnings_info.hours_until) / _EARNINGS_WINDOW_HOURS)
        return max(0.0, min(100.0, 100.0 - closeness * 100.0))
