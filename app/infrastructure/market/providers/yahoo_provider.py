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
اختيار "أفضل عقد": تُفحَص **كل** العقود ضمن نطاق قريب من السعر الحالي
(ATM ± عدة Strike؛ مُطبَّق كنطاق ±15% من السعر - يلتقط عملياً عدة
Strikes حول ATM لأي رمز نشط)، ثم يُحسَب Option Score (0-100) لكل عقد
عبر get_best_option_contract -> ScoredOption، ويُختار الأعلى Score.

Option Score = مجموع مرجَّح لـ: السيولة (Volume+OpenInterest)، OpenInterest
وحده، Volume وحده، ضيق فارق Bid/Ask، وIV (تُفضَّل قيمة معتدلة - راجع
_iv_score للتوثيق الكامل) - كل عنصر مُطبَّع لمقياس 0-100 بوضوح أدناه.
**Delta غير متوفرة من Yahoo Finance فعلياً - لا تُستخدَم في Score ولا
تُخترَع (OptionContract.delta تبقى None)**، امتثالاً لطلب صريح بعدم
اختلاق بيانات غير متوفرة من المزود.

"الثقة التقنية (Technical Confidence)" ليست معياراً هنا لأنها خاصية
للإشارة (Signal) نفسها لا للعقد - راجع app/main.py: يُختار الرمز الأعلى
ثقة أولاً، ثم تُستدعى هذه الدالة لاختيار أفضل عقد ضمن رموزه هو تحديداً؛
Option Score الناتج هنا يُستخدَم لاحقاً كأحد مكوّنات Final Score (راجع
app/infrastructure/telegram/quality_score.py).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone

import yfinance as yf
from loguru import logger

from app.infrastructure.market.exceptions import MarketUnavailableError, SymbolNotFoundError
from app.infrastructure.market.models import Candle, MarketStatus, Quote
from app.infrastructure.market.providers.base import MarketDataProvider
from app.infrastructure.options.models import OptionContract
from app.infrastructure.signals.models import SignalDirection

_REFERENCE_SYMBOL_FOR_MARKET_STATUS = "SPY"
_NEAR_MONEY_BAND_PCT = 0.15  # ابحث عن "أفضل عقد" ضمن ±15% من السعر الحالي فقط (عدة Strikes عملياً)

# أوزان Option Score (0-100) - مجموعها 1.0، موثَّقة صراحة:
_OPTION_SCORE_WEIGHT_LIQUIDITY = 0.30    # Volume+OpenInterest معاً
_OPTION_SCORE_WEIGHT_OPEN_INTEREST = 0.20
_OPTION_SCORE_WEIGHT_VOLUME = 0.15
_OPTION_SCORE_WEIGHT_SPREAD = 0.20       # فارق Bid/Ask أضيق = أفضل
_OPTION_SCORE_WEIGHT_IV = 0.15           # IV معتدلة (وليست متطرفة) = أفضل - راجع _iv_score

_LIQUIDITY_SATURATION = 5000.0   # Volume+OpenInterest عند/فوق هذه القيمة -> 100
_OPEN_INTEREST_SATURATION = 2000.0
_VOLUME_SATURATION = 5000.0
_IV_CENTER = 0.375  # مركز "المعتدل" الافتراضي (~37.5%) - راجع _iv_score
_IV_BAND_HALF_WIDTH = 0.225  # ضمن [15%,60%] تقريباً يبقى Score قريباً من 100


@dataclass(frozen=True)
class ScoredOption:
    contract: OptionContract
    score: float

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
    ) -> ScoredOption | None:
        """يفحص **كل** العقود القريبة من السعر الحالي (ATM ± عدة Strike)
        ويُرجِع الأعلى Option Score (0-100) منها كـScoredOption، أو None
        إذا لم تتوفر بيانات خيارات لهذا الرمز إطلاقاً (لا يرفع استثناء -
        غياب سلسلة خيارات حالة طبيعية لرموز كثيرة)."""
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
        for column in ("volume", "openInterest", "bid", "ask", "impliedVolatility"):
            table[column] = table[column].fillna(0)

        low, high = reference_price * (1 - _NEAR_MONEY_BAND_PCT), reference_price * (1 + _NEAR_MONEY_BAND_PCT)
        near_money = table[(table["strike"] >= low) & (table["strike"] <= high)]
        candidates = near_money if not near_money.empty else table

        candidates = candidates.copy()
        candidates["_option_score"] = candidates.apply(
            lambda row: self._option_score(
                volume=self._safe_float(row["volume"]), open_interest=self._safe_float(row["openInterest"]),
                bid=self._safe_float(row["bid"]), ask=self._safe_float(row["ask"]),
                implied_volatility=self._safe_float(row["impliedVolatility"]),
            ),
            axis=1,
        )
        best = candidates.sort_values(by="_option_score", ascending=False).iloc[0]

        option_type = "CALL" if direction == SignalDirection.BUY else "PUT"
        contract = OptionContract(
            symbol=symbol, option_type=option_type, strike=self._safe_float(best["strike"]), expiration=expiration,
            bid=self._safe_float(best["bid"]), ask=self._safe_float(best["ask"]), last=self._safe_float(best["lastPrice"]),
            volume=int(best["volume"]), open_interest=int(best["openInterest"]),
            implied_volatility=self._safe_float(best["impliedVolatility"]),
            # delta غير متوفرة من Yahoo Finance فعلياً - None (لا تُخترَع).
        )
        score = round(float(best["_option_score"]), 2)
        logger.info(
            "YahooFinanceProvider.get_best_option_contract: {} {} strike={} exp={} option_score={}",
            symbol, option_type, contract.strike, expiration, score,
        )
        return ScoredOption(contract=contract, score=score)

    @classmethod
    def _option_score(
        cls, volume: float, open_interest: float, bid: float, ask: float, implied_volatility: float,
    ) -> float:
        liquidity_score = cls._saturating_score(volume + open_interest, _LIQUIDITY_SATURATION)
        oi_score = cls._saturating_score(open_interest, _OPEN_INTEREST_SATURATION)
        volume_score = cls._saturating_score(volume, _VOLUME_SATURATION)
        spread_score = cls._spread_score(bid, ask)
        iv_score = cls._iv_score(implied_volatility)

        weighted = (
            liquidity_score * _OPTION_SCORE_WEIGHT_LIQUIDITY
            + oi_score * _OPTION_SCORE_WEIGHT_OPEN_INTEREST
            + volume_score * _OPTION_SCORE_WEIGHT_VOLUME
            + spread_score * _OPTION_SCORE_WEIGHT_SPREAD
            + iv_score * _OPTION_SCORE_WEIGHT_IV
        )
        return max(0.0, min(100.0, weighted))

    @staticmethod
    def _saturating_score(value: float, saturation_point: float) -> float:
        if saturation_point <= 0:
            return 0.0
        return max(0.0, min(100.0, (value / saturation_point) * 100.0))

    @staticmethod
    def _spread_score(bid: float, ask: float) -> float:
        mid = (bid + ask) / 2
        if mid <= 0:
            return 0.0
        spread_pct = max(0.0, (ask - bid) / mid)
        return max(0.0, min(100.0, 100.0 - spread_pct * 200.0))

    @staticmethod
    def _iv_score(implied_volatility: float) -> float:
        """يُفضِّل IV معتدلة (حول ~37.5%) بدل التطرّف في أي اتجاه - عقد
        بـIV منخفضة جداً غالباً راكد/غير نشط فعلياً رغم رقمه المعروض،
        وعقد بـIV مرتفعة جداً باهظ العلاوة ومخاطرة زمنية أعلى. هذا حكم
        موثَّق صراحة على بيانات IV **حقيقية** من Yahoo - وليس اختلاقاً
        لأي قيمة."""
        if implied_volatility <= 0:
            return 50.0  # لا بيانات IV فعلية - محايد، بلا مكافأة أو عقوبة
        distance = abs(implied_volatility - _IV_CENTER)
        return max(0.0, min(100.0, 100.0 - (distance / _IV_BAND_HALF_WIDTH) * 60.0))

    @staticmethod
    def _safe_float(value: object, default: float = 0.0) -> float:
        try:
            result = float(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return default
        return default if math.isnan(result) else result
