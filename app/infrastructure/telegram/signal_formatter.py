"""
app/infrastructure/telegram/signal_formatter.py
------------------------------------------------------
SignalFormatter: يحوّل Signal (وOptionContract اختياري) إلى نص رسالة
Telegram مختصرة وواضحة بالعربية - BUY تصبح "شراء (CALL)"، SELL تصبح
"بيع (PUT)" (SignalDirection نفسه في Signal.direction **لا يتغيّر
إطلاقاً** - التحويل هنا عرض فقط، عند التنسيق). سطر واحد لكل معلومة
تقريباً، بلا فاصل سميك ختامي (راجع include_separator=False أدناه).

مصدر بيانات العقد (Strike/نطاق الدخول/تاريخ الانتهاء):
- إذا مُرِّر option_contract (من YahooFinanceProvider حقيقي): تُستخدَم
  قيمه الحقيقية مباشرة (Strike، Bid/Ask، تاريخ الانتهاء).
- وإلا: Strike يُقرَّب لأقرب مضاعف معقول من سعر السهم (ATM تقديري)،
  وتاريخ الانتهاء يُقدَّر بأقرب جمعة، ونطاق الدخول/الوقف/الهدفين
  تُحسَب من علاوة مرجعية تقديرية ثابتة (Placeholder) - راجع
  _ESTIMATED_BASE_PREMIUM أدناه. **كل قيمة تقديرية تُوسَم بوضوح**
  (لاحقة "(تقديري)" مختصرة على السطر نفسه - بلا جملة شرح طويلة).

نسبة الوقف/الهدفين (سواء عقد حقيقي أو تقديري) تُستمَد من نفس نسبة
المخاطرة/العائد (Signal.risk_reward) التي حسبها RiskManager فعلياً على
مستوى السهم - وليست أرقاماً عشوائية.

معاملات اختيارية (لا تُغيّر شيئاً افتراضياً، يُمرِّرها app/main.py):
- better_entry/re_entry: شعار أعلى الرسالة.
- test_mode: شعار "🧪 توصية تجريبية" أعلى الرسالة (لوضع الاختبار عبر
  Telegram فقط - راجع _handle_test_command).
- confidence_override: Final Score للعرض فقط - Signal.confidence
  الأصلي **لا يتغيّر إطلاقاً** (Signal مُجمَّد أصلاً).

الأخبار/الأرباح/جودة العقد (Option Score) **لا تُعرَض في الرسالة إطلاقاً**
(بطلب صريح) - تستمر بالتأثير داخلياً على Final Score فقط عبر
FinalScoreCalculator في app/main.py، بلا أي تغيير في حساباتها."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from app.infrastructure.options.models import OptionContract
from app.infrastructure.signals.models import Signal, SignalDirection
from app.infrastructure.telegram.telegram_formatter import TelegramFormatter

_TITLE_BY_DIRECTION = {SignalDirection.BUY: ("🟢", "شراء (CALL)"), SignalDirection.SELL: ("🔴", "بيع (PUT)")}
_OPTION_TYPE_BY_DIRECTION = {SignalDirection.BUY: "CALL", SignalDirection.SELL: "PUT"}

_STRATEGY_DISPLAY_NAMES = {
    "trend_following": "Trend", "pullback": "Pullback", "breakout": "Breakout",
    "reversal": "Reversal", "momentum": "Momentum",
}
_MAX_REASON_TAGS = 5

# ثوابت تقدير علاوة العقد عند غياب بيانات خيارات حقيقية - راجع docstring
# الملف أعلاه؛ ليست حسابات Greeks حقيقية، فقط Placeholder واضح ومُوسَّم.
_ESTIMATED_BASE_PREMIUM = 1.00
_ESTIMATED_STOP_PCT = 0.30
_DEFAULT_RISK_REWARD = 2.0


@dataclass(frozen=True)
class SignalLevels:
    """كل القيم المُشتقّة من Signal (+OptionContract اختياري) - يحسبها
    compute_levels() مرة واحدة، يستهلكها format() للعرض، ويستهلكها
    app/main.py مباشرة لفتح صفقة في TradeJournal بنفس الأرقام
    المعروضة فعلياً للمستخدم - بلا أي ازدواج حساب بين الاثنين."""

    option_type: str
    strike: float
    expiration_text: str
    entry_low: float
    entry_high: float
    stop: float
    stop_pct: int
    t1: float
    t2: float
    is_estimated: bool


class SignalFormatter:
    def compute_levels(self, signal: Signal, option_contract: OptionContract | None = None) -> SignalLevels:
        option_type = _OPTION_TYPE_BY_DIRECTION.get(signal.direction, signal.direction.value.upper())
        is_estimated = option_contract is None

        if option_contract is not None:
            strike = option_contract.strike
            expiration_text = self._format_real_expiration(option_contract.expiration)
            entry_low = option_contract.bid
            entry_high = option_contract.ask
            premium_base = option_contract.last or ((option_contract.bid + option_contract.ask) / 2)
        else:
            strike = self._estimate_atm_strike(signal.entry)
            expiration_text = self._format_expiration(self._estimate_next_friday(signal.timestamp))
            premium_base = _ESTIMATED_BASE_PREMIUM
            entry_low = round(premium_base * 0.90, 2)
            entry_high = round(premium_base * 1.10, 2)

        stop, stop_pct, t1, t2 = self._estimate_risk_levels(premium_base, signal.risk_reward)
        return SignalLevels(
            option_type=option_type, strike=strike, expiration_text=expiration_text, entry_low=entry_low,
            entry_high=entry_high, stop=stop, stop_pct=stop_pct, t1=t1, t2=t2, is_estimated=is_estimated,
        )

    def format(
        self, signal: Signal, option_contract: OptionContract | None = None,
        better_entry: bool = False, re_entry: bool = False, test_mode: bool = False,
        confidence_override: float | None = None,
    ) -> str:
        levels = self.compute_levels(signal, option_contract)
        final_score = confidence_override if confidence_override is not None else signal.confidence
        circle, direction_text = _TITLE_BY_DIRECTION.get(signal.direction, ("⚪", signal.direction.value.upper()))
        estimated_suffix = " (تقديري)" if levels.is_estimated else ""

        sections: list[str] = []
        if test_mode:
            sections.append("🧪 توصية تجريبية")
        if re_entry:
            sections.append("🔁 Re-entry")
        elif better_entry:
            sections.append("🔄 Better Entry")

        sections += [
            f"{circle} {signal.symbol} | {direction_text}",
            f"📅 الانتهاء: {levels.expiration_text}{estimated_suffix}\n"
            f"🎯 Strike: {self._format_strike(levels.strike)}{estimated_suffix}",
            f"💵 الدخول: {levels.entry_low:.2f} - {levels.entry_high:.2f}$\n"
            f"🛑 الوقف: {levels.stop:.2f}$",
            f"🎯 الهدف 1: {levels.t1:.2f}$\n🎯 الهدف 2: {levels.t2:.2f}$",
            f"⭐ التقييم: {final_score:.0f}%",
            f"📌 السبب:\n{self._compose_reason_line(signal)}",
        ]
        return TelegramFormatter().render(sections, include_separator=False)

    @staticmethod
    def _format_strike(strike: float) -> str:
        return f"{strike:.0f}" if strike == int(strike) else f"{strike:.1f}"

    @staticmethod
    def _estimate_atm_strike(price: float) -> float:
        if price >= 500:
            step = 25.0
        elif price >= 200:
            step = 10.0
        elif price >= 100:
            step = 5.0
        elif price >= 50:
            step = 2.5
        elif price >= 20:
            step = 1.0
        else:
            step = 0.5
        return round(round(price / step) * step, 2)

    @staticmethod
    def _estimate_next_friday(from_dt: datetime) -> datetime:
        days_ahead = (4 - from_dt.weekday()) % 7  # الجمعة = 4
        if days_ahead == 0:
            days_ahead = 7
        return from_dt + timedelta(days=days_ahead)

    @staticmethod
    def _format_expiration(dt: datetime) -> str:
        return dt.strftime("%d/%m")

    @staticmethod
    def _format_real_expiration(expiration: str) -> str:
        try:
            return datetime.strptime(expiration, "%Y-%m-%d").strftime("%d/%m")
        except ValueError:
            return expiration

    @staticmethod
    def _estimate_risk_levels(premium_base: float, risk_reward: float | None) -> tuple[float, int, float, float]:
        rr = risk_reward if risk_reward and risk_reward > 0 else _DEFAULT_RISK_REWARD
        reward_pct_t2 = _ESTIMATED_STOP_PCT * rr
        reward_pct_t1 = reward_pct_t2 / 2

        stop = round(premium_base * (1 - _ESTIMATED_STOP_PCT), 2)
        stop_pct = round((stop - premium_base) / premium_base * 100)
        t1 = round(premium_base * (1 + reward_pct_t1), 2)
        t2 = round(premium_base * (1 + reward_pct_t2), 2)
        return stop, stop_pct, t1, t2

    @staticmethod
    def _compose_reason_line(signal: Signal) -> str:
        tags: list[str] = []
        for reason in signal.reasons:
            if ("اتجاه صاعد" in reason or "اتجاه هابط" in reason) and "EMA" not in tags:
                tags.append("EMA")
            elif ("زخم صاعد" in reason or "زخم هابط" in reason) and "Momentum" not in tags:
                tags.append("Momentum")
            elif "MACD" in reason and "MACD" not in tags:
                tags.append("MACD")
            elif reason.startswith("RSI=") and "RSI" not in tags:
                tags.append("RSI")

        for strategy in signal.strategy_used:
            display = _STRATEGY_DISPLAY_NAMES.get(strategy, strategy.title())
            if display not in tags:
                tags.append(display)

        return " + ".join(tags[:_MAX_REASON_TAGS]) if tags else "-"
