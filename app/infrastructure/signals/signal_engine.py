"""
app/infrastructure/signals/signal_engine.py
--------------------------------------------------
SignalEngine: خط الأنابيب الكامل - يدمج IndicatorService (مباشرة) و
StrategyEngine وRiskManager في Signal واحد نهائي كامل الحقول (entry،
stop_loss، take_profit، risk_reward، strategy_used، indicators_used،
reasons).

خوارزمية الثقة (ConfidenceWeights قابلة للتخصيص بالكامل - راجع
signals/models.py):
  البداية من 50 (محايد تماماً)، ثم:
  ± trend_weight     إذا كان TrendDetection صاعداً/هابطاً
  ± momentum_weight  إذا كان MomentumDetection صاعداً/هابطاً
  ± macd_weight      إذا كانت MACD histogram موجبة/سالبة
  + (RSI-50) * rsi_multiplier
  + strategy_match_bonus لكل استراتيجية مسجَّلة تتوافق مع نفس الاتجاه
  النتيجة النهائية تُحصَر بين 0 و100.

  confidence >= buy_threshold   -> BUY
  confidence <= sell_threshold  -> SELL
  خلاف ذلك                      -> NEUTRAL

عند BUY/SELL: RiskManager يحسب stop_loss (عبر ATR) وtake_profit
ونسبة العائد/المخاطرة - تُترَك None إذا تعذّر حسابها (بيانات غير كافية
لـATR مثلاً) بدل فشل توليد الإشارة بالكامل.
"""

from __future__ import annotations

from datetime import datetime, timezone

from loguru import logger

from app.infrastructure.indicators.exceptions import InsufficientDataError
from app.infrastructure.indicators.service import IndicatorService
from app.infrastructure.market.models import Candle
from app.infrastructure.risk.exceptions import RiskError
from app.infrastructure.risk.risk_manager import RiskManager
from app.infrastructure.signals.exceptions import InsufficientCandlesError
from app.infrastructure.signals.models import ConfidenceWeights, Signal, SignalDirection
from app.infrastructure.strategies.strategy_engine import StrategyEngine


class SignalEngine:
    def __init__(
        self,
        indicator_service: IndicatorService | None = None,
        strategy_engine: StrategyEngine | None = None,
        risk_manager: RiskManager | None = None,
        weights: ConfidenceWeights | None = None,
    ) -> None:
        self._indicators = indicator_service or IndicatorService()
        self._strategies = strategy_engine or StrategyEngine()
        self._risk_manager = risk_manager or RiskManager()
        self._weights = weights or ConfidenceWeights()

    def min_candles_required(self) -> int:
        # القيد الأكبر عملياً هو TrendDetection (slow_period=50 افتراضياً)
        return 50

    def generate(self, symbol: str, candles: list[Candle]) -> Signal:
        required = self.min_candles_required()
        if len(candles) < required:
            raise InsufficientCandlesError(required, len(candles))

        try:
            trend = self._indicators.calculate("trend_detection", candles)
            momentum = self._indicators.calculate("momentum_detection", candles)
            rsi_series = self._indicators.calculate("rsi", candles)
            macd = self._indicators.calculate("macd", candles)
        except InsufficientDataError as exc:
            raise InsufficientCandlesError(required, len(candles)) from exc

        rsi = rsi_series[-1]
        macd_histogram = macd.histogram[-1]
        w = self._weights

        score = 50.0
        reasons: list[str] = []

        if trend.trend == "bullish":
            score += w.trend_weight
            reasons.append(f"اتجاه صاعد (EMA سريع={trend.fast_ema:.2f} > EMA بطيء={trend.slow_ema:.2f}).")
        elif trend.trend == "bearish":
            score -= w.trend_weight
            reasons.append(f"اتجاه هابط (EMA سريع={trend.fast_ema:.2f} < EMA بطيء={trend.slow_ema:.2f}).")

        if momentum.momentum == "bullish":
            score += w.momentum_weight
            reasons.append(f"زخم صاعد (roc%={momentum.rate_of_change_percent:.2f}).")
        elif momentum.momentum == "bearish":
            score -= w.momentum_weight
            reasons.append(f"زخم هابط (roc%={momentum.rate_of_change_percent:.2f}).")

        if macd_histogram is not None:
            if macd_histogram > 0:
                score += w.macd_weight
                reasons.append(f"MACD histogram موجبة ({macd_histogram:.4f}).")
            elif macd_histogram < 0:
                score -= w.macd_weight
                reasons.append(f"MACD histogram سالبة ({macd_histogram:.4f}).")

        if rsi is not None:
            score += (rsi - 50) * w.rsi_multiplier
            reasons.append(f"RSI={rsi:.1f}.")

        confidence = max(0.0, min(100.0, score))

        if confidence >= w.buy_threshold:
            direction = SignalDirection.BUY
        elif confidence <= w.sell_threshold:
            direction = SignalDirection.SELL
        else:
            direction = SignalDirection.NEUTRAL

        strategy_used: list[str] = []
        if direction != SignalDirection.NEUTRAL:
            strategy_results = self._strategies.evaluate_all(candles)
            for name, result in strategy_results.items():
                if result.matched and result.direction == direction:
                    strategy_used.append(name)
                    confidence = min(100.0, confidence + w.strategy_match_bonus)
                    reasons.append(f"استراتيجية '{name}' متوافقة: {result.reason}")

        entry = candles[-1].close
        stop_loss: float | None = None
        take_profit: float | None = None
        risk_reward: float | None = None

        if direction != SignalDirection.NEUTRAL:
            try:
                stop_loss = self._risk_manager.atr_stop_loss(candles, direction)
                take_profit = self._risk_manager.take_profit(entry, stop_loss, direction)
                risk_reward = self._risk_manager.risk_reward_ratio(entry, stop_loss, take_profit)
            except RiskError as exc:
                logger.warning("SignalEngine.generate: تعذّر حساب مستويات المخاطرة لـ{}: {}", symbol, exc)
                reasons.append(f"تعذّر حساب مستويات المخاطرة: {exc}")

        signal = Signal(
            symbol=symbol,
            timeframe=candles[-1].timeframe,
            direction=direction,
            confidence=round(confidence, 2),
            entry=entry,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_reward=round(risk_reward, 2) if risk_reward is not None else None,
            strategy_used=strategy_used,
            indicators_used=["trend_detection", "momentum_detection", "rsi", "macd"],
            reasons=reasons,
            timestamp=datetime.now(timezone.utc),
        )
        logger.info(
            "SignalEngine.generate: {} ({}) -> {} (confidence={}, entry={}, sl={}, tp={}, rr={}, strategies={})",
            symbol, signal.timeframe, direction.value, signal.confidence,
            signal.entry, signal.stop_loss, signal.take_profit, signal.risk_reward, strategy_used,
        )
        return signal
