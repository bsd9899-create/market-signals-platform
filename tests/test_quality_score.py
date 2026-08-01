"""
tests/test_quality_score.py
---------------------------------
اختبار حقيقي لـFinalScoreCalculator - بحت (بلا شبكة، بلا Mock) - بيانات
يدوية جاهزة فقط.
"""

from __future__ import annotations

from datetime import date, timedelta

from app.infrastructure.news.models import EarningsInfo
from app.infrastructure.news.scoring import NewsScore
from app.infrastructure.options.models import OptionContract
from app.infrastructure.signals.models import SignalDirection
from app.infrastructure.telegram.quality_score import FinalScoreCalculator

_NO_NEWS = NewsScore(symbol=None, average_score=0.0, item_count=0)


def _contract(volume: int, open_interest: int) -> OptionContract:
    return OptionContract(
        symbol="AAPL", option_type="CALL", strike=100.0, expiration="2026-08-07", bid=1.0, ask=1.1, last=1.05,
        volume=volume, open_interest=open_interest, implied_volatility=0.3, delta=0.5,
    )


def test_no_news_no_earnings_no_contract_keeps_technical_score() -> None:
    breakdown = FinalScoreCalculator().calculate(80.0, SignalDirection.BUY, _NO_NEWS, None, None, True)
    assert breakdown.final_score == 80.0
    assert breakdown.news_adjustment == 0.0
    assert breakdown.earnings_adjustment == 0.0
    assert breakdown.liquidity_adjustment == 0.0


def test_news_opposed_to_buy_direction_penalizes() -> None:
    negative_news = NewsScore(symbol="AAPL", average_score=-1.0, item_count=3)
    breakdown = FinalScoreCalculator().calculate(80.0, SignalDirection.BUY, negative_news, None, None, True)
    assert breakdown.news_adjustment < 0
    assert breakdown.final_score < 80.0


def test_news_aligned_with_sell_direction_boosts() -> None:
    negative_news = NewsScore(symbol="AAPL", average_score=-1.0, item_count=3)
    breakdown = FinalScoreCalculator().calculate(70.0, SignalDirection.SELL, negative_news, None, None, True)
    assert breakdown.news_adjustment > 0
    assert breakdown.final_score > 70.0


def test_earnings_within_window_penalizes_proportionally_to_closeness() -> None:
    soon = EarningsInfo(symbol="AAPL", earnings_date=date.today(), hours_until=2.0)
    far = EarningsInfo(symbol="AAPL", earnings_date=date.today() + timedelta(days=1), hours_until=40.0)

    soon_breakdown = FinalScoreCalculator().calculate(80.0, SignalDirection.BUY, _NO_NEWS, soon, None, True)
    far_breakdown = FinalScoreCalculator().calculate(80.0, SignalDirection.BUY, _NO_NEWS, far, None, True)

    assert soon_breakdown.earnings_adjustment < far_breakdown.earnings_adjustment < 0


def test_earnings_outside_48h_window_no_penalty() -> None:
    outside = EarningsInfo(symbol="AAPL", earnings_date=date.today() + timedelta(days=10), hours_until=240.0)
    breakdown = FinalScoreCalculator().calculate(80.0, SignalDirection.BUY, _NO_NEWS, outside, None, True)
    assert breakdown.earnings_adjustment == 0.0


def test_high_liquidity_contract_gets_bonus() -> None:
    contract = _contract(volume=4000, open_interest=2000)  # مجموع 6000 >= عتبة العالية
    breakdown = FinalScoreCalculator().calculate(80.0, SignalDirection.BUY, _NO_NEWS, None, contract, False)
    assert breakdown.liquidity_adjustment == 5.0


def test_low_liquidity_contract_gets_penalty() -> None:
    contract = _contract(volume=10, open_interest=5)  # مجموع 15 < 100
    breakdown = FinalScoreCalculator().calculate(80.0, SignalDirection.BUY, _NO_NEWS, None, contract, False)
    assert breakdown.liquidity_adjustment == -6.0


def test_estimated_contract_gets_no_liquidity_adjustment_even_if_present() -> None:
    contract = _contract(volume=4000, open_interest=2000)
    breakdown = FinalScoreCalculator().calculate(80.0, SignalDirection.BUY, _NO_NEWS, None, contract, True)
    assert breakdown.liquidity_adjustment == 0.0


def test_final_score_clamped_between_0_and_100() -> None:
    very_negative_news = NewsScore(symbol="AAPL", average_score=-1.0, item_count=5)
    imminent_earnings = EarningsInfo(symbol="AAPL", earnings_date=date.today(), hours_until=0.5)
    low_liquidity = _contract(volume=1, open_interest=1)

    breakdown = FinalScoreCalculator().calculate(
        5.0, SignalDirection.BUY, very_negative_news, imminent_earnings, low_liquidity, False,
    )
    assert 0.0 <= breakdown.final_score <= 100.0

    breakdown_high = FinalScoreCalculator().calculate(
        99.0, SignalDirection.SELL, very_negative_news, None, _contract(9999, 9999), False,
    )
    assert breakdown_high.final_score <= 100.0


def test_technical_score_field_echoes_input_unchanged() -> None:
    breakdown = FinalScoreCalculator().calculate(63.4, SignalDirection.BUY, _NO_NEWS, None, None, True)
    assert breakdown.technical_score == 63.4
