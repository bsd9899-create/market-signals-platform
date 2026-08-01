"""
app/infrastructure/market/providers/yahoo_provider.py
-------------------------------------------------------------
YahooFinanceProvider: تطبيق حقيقي مؤقت لواجهة MarketDataProvider
(**بلا أي تعديل عليها**) عبر مكتبة yfinance - بديل مؤقت عن
AlpacaMarketProvider لا يحتاج مفاتيح API إطلاقاً (Yahoo Finance غير
الرسمي، بلا توكن). نفس نمط AlpacaMarketProvider تماماً: صف واحد جديد
يطبّق الواجهة، بلا أي تعديل على MarketService/Scanner/SignalEngine.

قيود موثَّقة (خاصة بـyfinance نفسها، وليست قيوداً في التصميم):
- لا يوجد إطار "4h" أصلي في yfinance - يُبنى هنا بتجميع كل 4 شموع 1h
  متتالية (Resampling) إلى شمعة واحدة (Open=أول، High=أعلى، Low=أدنى،
  Close=آخر، Volume=مجموع).
- get_market_status() يعتمد على رمز مرجعي واحد ("SPY") لأن yfinance لا
  يوفّر نقطة "ساعة سوق" عامة مثل Alpaca - و next_open/next_close غير
  متاحين من marketState نفسه، لذا يبقيان None (نفس أسلوب التوثيق
  المُستخدَم في AlpacaMarketProvider لقيود Alpaca الخاصة به).
- بيانات Yahoo Finance غير الرسمية قد تتأخر دقائق عن السوق الحقيقي،
  وهذا مقبول لغرض هذا المزوّد المؤقت.

get_best_option_contract(): **ليس جزءاً من MarketDataProvider** (الواجهة
المجرَّدة نفسها لم تُعدَّل، ولا MarketService يعرف بوجود هذه الدالة) -
دالة إضافية صريحة على YahooFinanceProvider فقط، لجلب بيانات خيارات
حقيقية (Strike/Bid/Ask/Last/Volume/OpenInterest/IV) عند توفّرها، تُستدعى
مباشرة من نقطة التركيب (app/main.py) قبل التنسيق عبر SignalFormatter -
دون أي حاجة لطبقة OptionsProvider منفصلة في هذه المرحلة المؤقتة.
اختيار "أفضل عقد" ضمن نطاق قريب من السعر الحالي (±15% - لتفادي عقد بعيد
جداً عن ATM رغم سيولته) يُرتَّب بالتسلسل: 1) السيولة (Volume+OpenInterest)
2) OpenInterest وحده 3) Volume وحده 4) أضيق فارق Bid/Ask - كل معيار
يكسر التعادل في الذي قبله. "الثقة (Confidence)" ليست معياراً هنا لأنها
خاصية للإشارة (Signal) نفسها لا للعقد - وهي أصلاً ما حدَّد أي رمز/اتجاه
وصل لهذه الدالة أساساً (راجع app/main.py: يُختار الرمز الأعلى ثقة أولاً،
ثم تُستدعى هذه الدالة لاختيار أفضل عقد ضمن رموزه هو تحديداً).
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

import yfinance as yf
from loguru import logger

from app.infrastructure.market.exceptions import MarketUnavailableError, SymbolNotFoundError
from app.infrastructure.market.models import Candle, MarketStatus, Quote
from app.infrastructure.market.providers.base import MarketDataProvider
from app.infrastructure.options.models import OptionContract
from app.infrastructure.signals.models import SignalDirection

_REFERENCE_SYMBOL_FOR_MARKET_STATUS = "SPY"
_NEAR_MONEY_BAND_PCT = 0.15  # ابحث عن "أفضل عقد" ضمن ±15% من السعر الحالي فقط

_TIMEFRAME_TO_YF_INTERVAL: dict[str, str] = {
    "1m": "1m", "5m": "5m", "15m": "15m", "30m": "30m", "1h": "60m", "4h": "60m", "1D": "1d",
}
_TIMEFRAME_TO_YF_PERIOD: dict[str, str] = {
    "1m": "7d", "5m": "60d", "15m": "60d", "30m": "60d", "1h": "730d", "4h": "730d", "1D": "2y",
}
_RESAMPLE_GROUP_SIZE: dict[str, int] = {"4h": 4}  # كل 4 شموع 1h -> شمعة 4h واحدة


class YahooFinanceProvider(MarketDataProvider):
    def get_quote(self, symbol: str) -> Quote:
        try:
            info = yf.Ticker(symbol).info
        except Exception as exc:
            raise MarketUnavailableError(f"فشل الاتصال بـYahoo Finance لـ{symbol}: {exc}") from exc

        last = info.get("regularMarketPrice") or info.get("previousClose")
        if last is None:
            raise SymbolNotFoundError(symbol)

        bid = info.get("bid") or last
        ask = info.get("ask") or last

        logger.info("YahooFinanceProvider.get_quote: {} -> bid={}, ask={}, last={}", symbol, bid, ask, last)
        return Quote(
            symbol=symbol, bid=float(bid), ask=float(ask), last=float(last),
            spread=round(float(ask) - float(bid), 4), timestamp=datetime.now(timezone.utc),
        )

    def get_candles(self, symbol: str, timeframe: str, limit: int = 100) -> list[Candle]:
        interval = _TIMEFRAME_TO_YF_INTERVAL.get(timeframe)
        if interval is None:
            raise MarketUnavailableError(
                f"إطار زمني غير مدعوم: {timeframe} - المدعوم: {sorted(_TIMEFRAME_TO_YF_INTERVAL.keys())}"
            )
        period = _TIMEFRAME_TO_YF_PERIOD[timeframe]

        try:
            history = yf.Ticker(symbol).history(period=period, interval=interval)
        except Exception as exc:
            raise MarketUnavailableError(f"فشل جلب الشموع من Yahoo Finance لـ{symbol}: {exc}") from exc

        if history.empty:
            raise SymbolNotFoundError(symbol)

        candles = [
            Candle(
                symbol=symbol, timeframe=timeframe, timestamp=row_index.to_pydatetime().astimezone(timezone.utc),
                open=float(row.Open), high=float(row.High), low=float(row.Low), close=float(row.Close),
                volume=int(row.Volume),
            )
            for row_index, row in history.iterrows()
        ]

        group_size = _RESAMPLE_GROUP_SIZE.get(timeframe)
        if group_size:
            candles = self._resample(candles, group_size)

        candles = candles[-limit:]
        logger.info("YahooFinanceProvider.get_candles: {} {} -> {} شمعة", symbol, timeframe, len(candles))
        return candles

    @staticmethod
    def _resample(candles: list[Candle], group_size: int) -> list[Candle]:
        """يجمّع كل group_size شمعة متتالية إلى شمعة واحدة (لبناء 4h من 1h)."""
        resampled: list[Candle] = []
        for i in range(0, len(candles), group_size):
            group = candles[i : i + group_size]
            if len(group) < group_size:
                break  # مجموعة غير مكتملة في النهاية - تُهمَل بدل شمعة جزئية مضلِّلة
            resampled.append(
                Candle(
                    symbol=group[0].symbol, timeframe="4h", timestamp=group[0].timestamp,
                    open=group[0].open, high=max(c.high for c in group), low=min(c.low for c in group),
                    close=group[-1].close, volume=sum(c.volume for c in group),
                )
            )
        return resampled

    def get_market_status(self) -> MarketStatus:
        try:
            info = yf.Ticker(_REFERENCE_SYMBOL_FOR_MARKET_STATUS).info
        except Exception as exc:
            raise MarketUnavailableError(f"فشل جلب حالة السوق من Yahoo Finance: {exc}") from exc

        market_state = info.get("marketState", "CLOSED")
        status = MarketStatus(
            is_open=market_state == "REGULAR",
            premarket=market_state == "PRE",
            after_hours=market_state in ("POST", "POSTPOST"),
            next_open=None,
            next_close=None,
        )
        logger.info("YahooFinanceProvider.get_market_status: marketState={} -> is_open={}", market_state, status.is_open)
        return status

    def health_check(self) -> bool:
        try:
            info = yf.Ticker(_REFERENCE_SYMBOL_FOR_MARKET_STATUS).info
            ok = bool(info.get("regularMarketPrice"))
            logger.info("YahooFinanceProvider.health_check: {}", ok)
            return ok
        except Exception as exc:
            logger.error("YahooFinanceProvider.health_check: فشل - {}", exc)
            return False

    def get_best_option_contract(
        self, symbol: str, direction: SignalDirection, reference_price: float,
    ) -> OptionContract | None:
        """يُرجع أفضل عقد حقيقي (Calls لـBUY، Puts لـSELL) من أقرب تاريخ
        انتهاء متاح، أو None إذا لم تتوفر بيانات خيارات لهذا الرمز إطلاقاً
        (لا يرفع استثناء - غياب سلسلة خيارات حالة طبيعية لرموز كثيرة)."""
        ticker = yf.Ticker(symbol)

        try:
            expirations = ticker.options
        except Exception as exc:
            logger.warning("YahooFinanceProvider.get_best_option_contract: تعذّر جلب تواريخ الانتهاء لـ{}: {}", symbol, exc)
            return None
        if not expirations:
            logger.info("YahooFinanceProvider.get_best_option_contract: لا توجد بيانات خيارات لـ{}", symbol)
            return None

        expiration = expirations[0]
        try:
            chain = ticker.option_chain(expiration)
        except Exception as exc:
            logger.warning("YahooFinanceProvider.get_best_option_contract: فشل جلب سلسلة الخيارات لـ{}: {}", symbol, exc)
            return None

        table = chain.calls if direction == SignalDirection.BUY else chain.puts
        if table.empty:
            return None

        table = table.copy()
        table["volume"] = table["volume"].fillna(0)
        table["openInterest"] = table["openInterest"].fillna(0)
        table["bid"] = table["bid"].fillna(0)
        table["ask"] = table["ask"].fillna(0)

        low, high = reference_price * (1 - _NEAR_MONEY_BAND_PCT), reference_price * (1 + _NEAR_MONEY_BAND_PCT)
        near_money = table[(table["strike"] >= low) & (table["strike"] <= high)]
        candidates = near_money if not near_money.empty else table

        candidates = candidates.copy()
        candidates["_liquidity_score"] = candidates["volume"] + candidates["openInterest"]
        candidates["_spread"] = (candidates["ask"] - candidates["bid"]).clip(lower=0)
        best = candidates.sort_values(
            by=["_liquidity_score", "openInterest", "volume", "_spread"],
            ascending=[False, False, False, True],
        ).iloc[0]

        option_type = "CALL" if direction == SignalDirection.BUY else "PUT"
        contract = OptionContract(
            symbol=symbol, option_type=option_type, strike=self._safe_float(best["strike"]), expiration=expiration,
            bid=self._safe_float(best["bid"]), ask=self._safe_float(best["ask"]), last=self._safe_float(best["lastPrice"]),
            volume=int(best["volume"]), open_interest=int(best["openInterest"]),
            implied_volatility=self._safe_float(best["impliedVolatility"]), delta=0.5,
        )
        logger.info(
            "YahooFinanceProvider.get_best_option_contract: {} {} strike={} exp={} liquidity_score={}",
            symbol, option_type, contract.strike, expiration, best["_liquidity_score"],
        )
        return contract

    @staticmethod
    def _safe_float(value: object, default: float = 0.0) -> float:
        try:
            result = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return default
        return default if math.isnan(result) else result
