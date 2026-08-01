"""
tests/test_quality_score.py
---------------------------------
اختبار حقيقي لـFinalScoreCalculator (Technical/Strategy/News/Earnings/
Option -> Final Score مرجَّح) - بحت (بلا شبكة، بلا Mock) - بيانات يدوية
جاهزة فقط.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.infrastructure.news.models import EarningsInfo
from app.infrastructure.news.scoring import NewsScore
from app.infrastructure.signals.models import SignalDirection
from app.infrastructure.telegram.quality_score import FinalScoreCalculator

_NO_NEWS = NewsScore(symbol=None, average_score=0.0, item_count=0)


def test_all_neutral_inputs_give_expected_weighted_baseline() -> None:
    # Technical=80, Strategy=0/5=0, News=50(محايد), Earnings=100(لا خطر), Option=50(محايد)
    # 80*0.40 + 0*0.15 + 50*0.15 + 100*0.15 + 50*0.15 = 32 + 0 + 7.5 + 15 + 7.5 = 62.0
    breakdown = FinalScoreCalculator().calculate(80.0, 0, SignalDirection.BUY, _NO_NEWS, None, None)
    assert breakdown.technical_score == 80.0
    assert breakdown.strategy_score == 0.0
    assert breakdown.news_score == 50.0
    assert breakdown.earnings_score == 100.0
    assert breakdown.option_score == 50.0
    assert breakdown.final_score == 62.0


def test_full_strategy_agreement_maxes_strategy_score() -> None:
    breakdown = FinalScoreCalculator().calculate(80.0, 5, SignalDirection.BUY, _NO_NEWS, None, None)
    assert breakdown.strategy_score == 100.0


def test_news_aligned_with_buy_direction_raises_news_score() -> None:
    positive_news = NewsScore(symbol="AAPL", average_score=1.0, item_count=3)
    breakdown = FinalScoreCalculator().calculate(80.0, 0, SignalDirection.BUY, positive_news, None, None)
    assert breakdown.news_score == 100.0


def test_news_opposed_to_buy_direction_lowers_news_score() -> None:
    negative_news = NewsScore(symbol="AAPL", average_score=-1.0, item_count=3)
    breakdown = FinalScoreCalculator().calculate(80.0, 0, SignalDirection.BUY, negative_news, None, None)
    assert breakdown.news_score == 0.0


def test_news_direction_is_inverted_for_sell() -> None:
    negative_news = NewsScore(symbol="AAPL", average_score=-1.0, item_count=3)
    breakdown = FinalScoreCalculator().calculate(80.0, 0, SignalDirection.SELL, negative_news, None, None)
    assert breakdown.news_score == 100.0  # أخبار سلبية تدعم SELL فعلياً


def test_earnings_outside_48h_window_full_score() -> None:
    far = EarningsInfo(symbol="AAPL", earnings_date=date.today() + timedelta(days=10), hours_until=240.0)
    breakdown = FinalScoreCalculator().calculate(80.0, 0, SignalDirection.BUY, _NO_NEWS, far, None)
    assert breakdown.earnings_score == 100.0


def test_earnings_imminent_drops_score_toward_zero() -> None:
    imminent = EarningsInfo(symbol="AAPL", earnings_date=date.today(), hours_until=0.5)
    breakdown = FinalScoreCalculator().calculate(80.0, 0, SignalDirection.BUY, _NO_NEWS, imminent, None)
    assert breakdown.earnings_score < 5.0


def test_earnings_score_decreases_monotonically_with_closeness() -> None:
    calc = FinalScoreCalculator()
    far = EarningsInfo(symbol="AAPL", earnings_date=date.today(), hours_until=40.0)
    near = EarningsInfo(symbol="AAPL", earnings_date=date.today(), hours_until=4.0)
    far_score = calc.calculate(80.0, 0, SignalDirection.BUY, _NO_NEWS, far, None).earnings_score
    near_score = calc.calculate(80.0, 0, SignalDirection.BUY, _NO_NEWS, near, None).earnings_score
    assert near_score < far_score


def test_no_earnings_data_full_score() -> None:
    breakdown = FinalScoreCalculator().calculate(80.0, 0, SignalDirection.BUY, _NO_NEWS, None, None)
    assert breakdown.earnings_score == 100.0


def test_option_score_passed_through_directly() -> None:
    breakdown = FinalScoreCalculator().calculate(80.0, 0, SignalDirection.BUY, _NO_NEWS, None, 92.5)
    assert breakdown.option_score == 92.5


def test_missing_option_score_defaults_to_neutral_50() -> None:
    breakdown = FinalScoreCalculator().calculate(80.0, 0, SignalDirection.BUY, _NO_NEWS, None, None)
    assert breakdown.option_score == 50.0


def test_final_score_clamped_between_0_and_100() -> None:
    negative_news = NewsScore(symbol="AAPL", average_score=-1.0, item_count=5)
    imminent = EarningsInfo(symbol="AAPL", earnings_date=date.today(), hours_until=0.1)
    low = FinalScoreCalculator().calculate(0.0, 0, SignalDirection.BUY, negative_news, imminent, 0.0)
    assert 0.0 <= low.final_score <= 100.0

    positive_news = NewsScore(symbol="AAPL", average_score=1.0, item_count=5)
    high = FinalScoreCalculator().calculate(100.0, 5, SignalDirection.BUY, positive_news, None, 100.0)
    assert high.final_score <= 100.0


def test_technical_score_echoes_input_clamped() -> None:
    breakdown = FinalScoreCalculator().calculate(63.4, 0, SignalDirection.BUY, _NO_NEWS, None, None)
    assert breakdown.technical_score == 63.4
