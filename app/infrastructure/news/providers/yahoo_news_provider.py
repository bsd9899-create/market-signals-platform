"""
app/infrastructure/news/providers/yahoo_news_provider.py
------------------------------------------------------------------
YahooNewsProvider: تطبيق حقيقي لـNewsProvider عبر yfinance (Ticker.news
+ Ticker.calendar + Ticker.upgrades_downgrades) بلا أي مفتاح API - نفس
فلسفة YahooFinanceProvider/AlpacaMarketProvider تماماً: صف واحد يطبّق
الواجهة الموجودة (get_latest_news/health_check) **بلا أي تعديل عليها**،
بالإضافة إلى دوال إضافية خاصة به (get_earnings_info/get_analyst_actions/
get_sec_filings) - تماماً كما فعل YahooFinanceProvider.get_best_option_contract
سابقاً، تُستدعى مباشرة من نقطة التركيب (app/main.py).

Earnings/Analyst: عبر yfinance مباشرة (Yahoo Finance).
SEC Filings: عبر SEC EDGAR الرسمي والمجاني (data.sec.gov) - بلا أي مفتاح:
  1. company_tickers.json لتحويل الرمز (Ticker) إلى CIK - يُجلَب مرة
     واحدة فقط ويُخزَّن في الذاكرة (Cache على مستوى الصف - عشرة آلاف رمز
     تقريباً، لا داعي لإعادة الجلب كل دورة فحص).
  2. submissions/CIK##########.json لآخر الإيداعات الفعلية للشركة.
SEC يشترط ترويسة User-Agent تحدد الجهة/جهة الاتصال - مُرفَقة أدناه.

قيد بيانات موثَّق: yfinance.Ticker.calendar يوفّر **تاريخ** الأرباح
القادمة فقط (بلا وقت دقيق) - لذا hours_until في EarningsInfo تقريبي
(فرق الأيام × 24)، وليس دقيقاً للساعة - قيد المصدر نفسه، وليس خللاً هنا.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

import httpx
import yfinance as yf
from loguru import logger

from app.infrastructure.news.models import AnalystAction, EarningsInfo, NewsItem, SecFiling
from app.infrastructure.news.providers.base import NewsProvider
from app.infrastructure.news.sentiment import KeywordSentimentAnalyzer, SentimentAnalyzer

_SEC_USER_AGENT = "MarketSignalsPlatform market-signals-platform@example.com"
_SEC_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
_SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"


class YahooNewsProvider(NewsProvider):
    _cik_by_ticker: dict[str, int] | None = None  # Cache على مستوى الصف - يُملأ مرة واحدة فقط لكل عملية تشغيل

    def __init__(self, sentiment_analyzer: SentimentAnalyzer | None = None, timeout_seconds: float = 10.0) -> None:
        self._sentiment_analyzer = sentiment_analyzer or KeywordSentimentAnalyzer()
        self._client = httpx.Client(timeout=timeout_seconds, headers={"User-Agent": _SEC_USER_AGENT})

    def get_latest_news(self, symbol: str | None = None, limit: int = 10) -> list[NewsItem]:
        if symbol is None:
            logger.warning("YahooNewsProvider.get_latest_news: symbol=None غير مدعوم (yfinance يتطلب رمزاً محدَّداً) - قائمة فارغة.")
            return []

        try:
            raw_items = yf.Ticker(symbol).news
        except Exception as exc:
            logger.error("YahooNewsProvider.get_latest_news: فشل جلب أخبار {}: {}", symbol, exc)
            return []

        items: list[NewsItem] = []
        for raw in raw_items[:limit]:
            content = raw.get("content", {})
            title = content.get("title") or ""
            if not title:
                continue
            published_at = self._parse_timestamp(content.get("pubDate"))
            source = (content.get("provider") or {}).get("displayName") or "Yahoo Finance"
            items.append(
                NewsItem(
                    symbol=symbol, headline=title, source=source,
                    sentiment=self._sentiment_analyzer.analyze(title), published_at=published_at,
                )
            )
        logger.info("YahooNewsProvider.get_latest_news: {} -> {} خبراً حقيقياً", symbol, len(items))
        return items

    def health_check(self) -> bool:
        try:
            ok = bool(yf.Ticker("SPY").news)
            logger.info("YahooNewsProvider.health_check: {}", ok)
            return ok
        except Exception as exc:
            logger.error("YahooNewsProvider.health_check: فشل - {}", exc)
            return False

    def get_earnings_info(self, symbol: str) -> EarningsInfo | None:
        try:
            calendar = yf.Ticker(symbol).calendar
        except Exception as exc:
            logger.warning("YahooNewsProvider.get_earnings_info: فشل جلب تقويم {}: {}", symbol, exc)
            return None

        earnings_dates: list[date] = (calendar or {}).get("Earnings Date") or []
        today = datetime.now(timezone.utc).date()
        upcoming = [d for d in earnings_dates if d >= today]
        if not upcoming:
            return None

        next_date = min(upcoming)
        hours_until = (next_date - today).days * 24.0
        info = EarningsInfo(symbol=symbol, earnings_date=next_date, hours_until=hours_until)
        logger.info("YahooNewsProvider.get_earnings_info: {} -> {} (~{}h)", symbol, next_date, hours_until)
        return info

    def get_analyst_actions(self, symbol: str, limit: int = 5) -> list[AnalystAction]:
        try:
            table = yf.Ticker(symbol).upgrades_downgrades
        except Exception as exc:
            logger.warning("YahooNewsProvider.get_analyst_actions: فشل جلب تقييمات {}: {}", symbol, exc)
            return []
        if table is None or table.empty:
            return []

        actions: list[AnalystAction] = []
        for graded_at, row in table.head(limit).iterrows():
            graded_dt = graded_at.to_pydatetime() if hasattr(graded_at, "to_pydatetime") else graded_at
            if graded_dt.tzinfo is None:
                graded_dt = graded_dt.replace(tzinfo=timezone.utc)
            actions.append(
                AnalystAction(
                    symbol=symbol, firm=str(row.get("Firm", "")), to_grade=str(row.get("ToGrade", "")),
                    from_grade=str(row.get("FromGrade", "")), action=str(row.get("Action", "")), graded_at=graded_dt,
                )
            )
        logger.info("YahooNewsProvider.get_analyst_actions: {} -> {} تقييماً", symbol, len(actions))
        return actions

    def get_sec_filings(self, symbol: str, limit: int = 5) -> list[SecFiling]:
        cik = self._resolve_cik(symbol)
        if cik is None:
            return []

        try:
            response = self._client.get(_SEC_SUBMISSIONS_URL.format(cik=cik))
        except httpx.HTTPError as exc:
            logger.warning("YahooNewsProvider.get_sec_filings: فشل جلب إيداعات {}: {}", symbol, exc)
            return []
        if response.status_code != 200:
            logger.warning("YahooNewsProvider.get_sec_filings: HTTP {} لـ{}", response.status_code, symbol)
            return []

        recent = response.json().get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        filing_dates = recent.get("filingDate", [])
        descriptions = recent.get("primaryDocDescription", [])

        filings = [
            SecFiling(
                symbol=symbol, form=form, filing_date=date.fromisoformat(filing_date),
                description=descriptions[i] if i < len(descriptions) else form,
            )
            for i, (form, filing_date) in enumerate(zip(forms, filing_dates))
            if i < limit
        ]
        logger.info("YahooNewsProvider.get_sec_filings: {} -> {} إيداعاً", symbol, len(filings))
        return filings

    def _resolve_cik(self, symbol: str) -> int | None:
        if YahooNewsProvider._cik_by_ticker is None:
            YahooNewsProvider._cik_by_ticker = self._fetch_cik_map()
        return YahooNewsProvider._cik_by_ticker.get(symbol.upper())

    def _fetch_cik_map(self) -> dict[str, int]:
        try:
            response = self._client.get(_SEC_TICKERS_URL)
        except httpx.HTTPError as exc:
            logger.error("YahooNewsProvider._fetch_cik_map: فشل جلب قائمة CIK: {}", exc)
            return {}
        if response.status_code != 200:
            logger.error("YahooNewsProvider._fetch_cik_map: HTTP {}", response.status_code)
            return {}

        raw = response.json()
        cik_map = {entry["ticker"].upper(): int(entry["cik_str"]) for entry in raw.values()}
        logger.info("YahooNewsProvider._fetch_cik_map: تم تحميل {} رمزاً من SEC.", len(cik_map))
        return cik_map

    @staticmethod
    def _parse_timestamp(raw: str | None) -> datetime:
        if not raw:
            return datetime.now(timezone.utc)
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now(timezone.utc)

    def close(self) -> None:
        self._client.close()
