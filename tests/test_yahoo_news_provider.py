"""
tests/test_yahoo_news_provider.py
----------------------------------------
اختبار حقيقي لـYahooNewsProvider - **بلا أي اتصال شبكة إطلاقاً**:
yf.Ticker تُستبدَل بكائن وهمي، وhttpx.Client الخاص بطلبات SEC يُستبدَل
بدالة وهمية تُرجِع httpx.Response حقيقية (نفس أسلوب test_alpaca_provider.py).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import httpx
import pandas as pd
import pytest

from app.infrastructure.news.providers import yahoo_news_provider as yahoo_news_provider_module
from app.infrastructure.news.providers.yahoo_news_provider import YahooNewsProvider

_DUMMY_REQUEST = httpx.Request("GET", "https://example.invalid/")


class _FakeTicker:
    def __init__(self, news=None, calendar=None, upgrades_downgrades=None) -> None:
        self.news = news if news is not None else []
        self.calendar = calendar if calendar is not None else {}
        self.upgrades_downgrades = upgrades_downgrades


def _patch_ticker(monkeypatch: pytest.MonkeyPatch, ticker: _FakeTicker) -> None:
    monkeypatch.setattr(yahoo_news_provider_module.yf, "Ticker", lambda symbol: ticker)


def _news_item(title: str, source: str = "Yahoo Finance", pub_date: str = "2026-08-01T10:00:00Z") -> dict:
    return {"content": {"title": title, "pubDate": pub_date, "provider": {"displayName": source}}}


def _response(status_code: int, json_body: dict) -> httpx.Response:
    return httpx.Response(status_code=status_code, json=json_body, request=_DUMMY_REQUEST)


# ---------------------------------------------------------------------
# get_latest_news
# ---------------------------------------------------------------------


def test_get_latest_news_maps_fields_and_analyzes_sentiment(monkeypatch: pytest.MonkeyPatch) -> None:
    ticker = _FakeTicker(news=[_news_item("Company beats earnings expectations with strong growth")])
    _patch_ticker(monkeypatch, ticker)

    items = YahooNewsProvider().get_latest_news("AAPL", limit=5)
    assert len(items) == 1
    assert items[0].symbol == "AAPL"
    assert items[0].source == "Yahoo Finance"
    assert items[0].sentiment == "positive"  # "beat"/"growth" كلمات إيجابية في KeywordSentimentAnalyzer
    assert items[0].published_at.tzinfo is not None


def test_get_latest_news_respects_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    ticker = _FakeTicker(news=[_news_item(f"Headline {i}") for i in range(10)])
    _patch_ticker(monkeypatch, ticker)
    items = YahooNewsProvider().get_latest_news("AAPL", limit=3)
    assert len(items) == 3


def test_get_latest_news_skips_items_without_title(monkeypatch: pytest.MonkeyPatch) -> None:
    ticker = _FakeTicker(news=[{"content": {"title": "", "pubDate": "2026-08-01T10:00:00Z"}}])
    _patch_ticker(monkeypatch, ticker)
    assert YahooNewsProvider().get_latest_news("AAPL") == []


def test_get_latest_news_none_symbol_returns_empty_without_network_call(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = []
    monkeypatch.setattr(yahoo_news_provider_module.yf, "Ticker", lambda symbol: calls.append(symbol))
    assert YahooNewsProvider().get_latest_news(None) == []
    assert calls == []


def test_get_latest_news_handles_fetch_failure_gracefully(monkeypatch: pytest.MonkeyPatch) -> None:
    class _BrokenTicker:
        @property
        def news(self):
            raise RuntimeError("network down")

    monkeypatch.setattr(yahoo_news_provider_module.yf, "Ticker", lambda symbol: _BrokenTicker())
    assert YahooNewsProvider().get_latest_news("AAPL") == []


# ---------------------------------------------------------------------
# get_earnings_info - عتبة الـ48 ساعة (المطلب 2)
# ---------------------------------------------------------------------


def test_get_earnings_info_returns_nearest_upcoming_date(monkeypatch: pytest.MonkeyPatch) -> None:
    tomorrow = date.today() + timedelta(days=1)
    far_future = date.today() + timedelta(days=60)
    ticker = _FakeTicker(calendar={"Earnings Date": [far_future, tomorrow]})
    _patch_ticker(monkeypatch, ticker)

    info = YahooNewsProvider().get_earnings_info("AAPL")
    assert info is not None
    assert info.earnings_date == tomorrow
    assert 0 < info.hours_until <= 48


def test_get_earnings_info_ignores_past_dates(monkeypatch: pytest.MonkeyPatch) -> None:
    past = date.today() - timedelta(days=5)
    ticker = _FakeTicker(calendar={"Earnings Date": [past]})
    _patch_ticker(monkeypatch, ticker)
    assert YahooNewsProvider().get_earnings_info("AAPL") is None


def test_get_earnings_info_no_calendar_data_returns_none(monkeypatch: pytest.MonkeyPatch) -> None:
    ticker = _FakeTicker(calendar={})
    _patch_ticker(monkeypatch, ticker)
    assert YahooNewsProvider().get_earnings_info("AAPL") is None


# ---------------------------------------------------------------------
# get_analyst_actions
# ---------------------------------------------------------------------


def test_get_analyst_actions_maps_dataframe_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    df = pd.DataFrame(
        {
            "Firm": ["JP Morgan", "TD Cowen"], "ToGrade": ["Overweight", "Buy"], "FromGrade": ["Overweight", "Hold"],
            "Action": ["main", "up"],
        },
        index=pd.to_datetime(["2026-07-31 18:07:40", "2026-07-30 10:00:00"]),
    )
    df.index.name = "GradeDate"
    ticker = _FakeTicker(upgrades_downgrades=df)
    _patch_ticker(monkeypatch, ticker)

    actions = YahooNewsProvider().get_analyst_actions("AAPL", limit=5)
    assert len(actions) == 2
    assert actions[0].firm == "JP Morgan"
    assert actions[1].action == "up"
    assert actions[0].graded_at.tzinfo is not None


def test_get_analyst_actions_none_table_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    ticker = _FakeTicker(upgrades_downgrades=None)
    _patch_ticker(monkeypatch, ticker)
    assert YahooNewsProvider().get_analyst_actions("AAPL") == []


def test_get_analyst_actions_empty_dataframe_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    ticker = _FakeTicker(upgrades_downgrades=pd.DataFrame())
    _patch_ticker(monkeypatch, ticker)
    assert YahooNewsProvider().get_analyst_actions("AAPL") == []


# ---------------------------------------------------------------------
# health_check
# ---------------------------------------------------------------------


def test_health_check_true_when_news_present(monkeypatch: pytest.MonkeyPatch) -> None:
    ticker = _FakeTicker(news=[_news_item("headline")])
    _patch_ticker(monkeypatch, ticker)
    assert YahooNewsProvider().health_check() is True


def test_health_check_false_on_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    class _BrokenTicker:
        @property
        def news(self):
            raise RuntimeError("down")

    monkeypatch.setattr(yahoo_news_provider_module.yf, "Ticker", lambda symbol: _BrokenTicker())
    assert YahooNewsProvider().health_check() is False


# ---------------------------------------------------------------------
# get_sec_filings - CIK lookup (Cache) + submissions - عبر httpx مباشرة
# ---------------------------------------------------------------------


def test_get_sec_filings_resolves_cik_and_parses_filings(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YahooNewsProvider()
    YahooNewsProvider._cik_by_ticker = None  # تصفير الـCache المشترك بين الاختبارات

    tickers_response = _response(200, {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}})
    submissions_response = _response(200, {
        "filings": {"recent": {
            "form": ["10-Q", "8-K"], "filingDate": ["2026-07-31", "2026-07-30"],
            "primaryDocDescription": ["10-Q", "8-K"],
        }},
    })
    call_log: list[str] = []

    def fake_get(url: str, *args, **kwargs) -> httpx.Response:
        call_log.append(url)
        return tickers_response if "company_tickers" in url else submissions_response

    monkeypatch.setattr(provider._client, "get", fake_get)

    filings = provider.get_sec_filings("AAPL", limit=5)
    assert len(filings) == 2
    assert filings[0].form == "10-Q"
    assert filings[0].filing_date == date(2026, 7, 31)
    assert any("company_tickers" in u for u in call_log)
    assert any("CIK0000320193" in u for u in call_log)


def test_get_sec_filings_unknown_symbol_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YahooNewsProvider()
    YahooNewsProvider._cik_by_ticker = None

    tickers_response = _response(200, {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}})
    monkeypatch.setattr(provider._client, "get", lambda url, *a, **kw: tickers_response)

    assert provider.get_sec_filings("NOTAREALTICKER", limit=5) == []


def test_get_sec_filings_cik_map_cached_across_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = YahooNewsProvider()
    YahooNewsProvider._cik_by_ticker = None

    tickers_response = _response(200, {"0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}})
    submissions_response = _response(200, {"filings": {"recent": {"form": [], "filingDate": [], "primaryDocDescription": []}}})
    call_log: list[str] = []

    def fake_get(url: str, *args, **kwargs) -> httpx.Response:
        call_log.append(url)
        return tickers_response if "company_tickers" in url else submissions_response

    monkeypatch.setattr(provider._client, "get", fake_get)

    provider.get_sec_filings("AAPL")
    provider.get_sec_filings("AAPL")

    tickers_calls = [u for u in call_log if "company_tickers" in u]
    assert len(tickers_calls) == 1  # جُلبت مرة واحدة فقط - مُخزَّنة (Cache) لبقية الاستدعاءات
