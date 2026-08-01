"""
app/infrastructure/signals/models.py
------------------------------------------
Signal: نموذج بيانات فقط (Dataclass مُجمَّدة) - نتيجة حساب في الذاكرة،
**مستقل تماماً عن app.infrastructure.database.models.Signal** (نموذج
قاعدة البيانات) عمداً - هذا يبقي signals/ مستقلة قابلة للاختبار بلا أي
حاجة لقاعدة بيانات حقيقية؛ ربط الاثنين (تخزين نتيجة SignalEngine في
جدول signals) مسؤولية طبقة تكامل لاحقة، وليس هذا الملف.

ConfidenceWeights: أوزان محرك الثقة - قابلة للتخصيص بالكامل (تُقرأ من
config/settings.yaml عبر SignalSettings)، بدل أرقام ثابتة داخل الكود.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class SignalDirection(str, Enum):
    BUY = "buy"
    SELL = "sell"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class ConfidenceWeights:
    trend_weight: float = 20.0             # مساهمة TrendDetection (صاعد/هابط)
    momentum_weight: float = 15.0          # مساهمة MomentumDetection (صاعد/هابط)
    macd_weight: float = 15.0              # مساهمة إشارة MACD histogram (موجب/سالب)
    rsi_multiplier: float = 0.2            # مضاعف مساهمة RSI: (RSI-50) * rsi_multiplier
    strategy_match_bonus: float = 2.0      # مكافأة لكل استراتيجية متوافقة مع نفس الاتجاه
    buy_threshold: float = 65.0
    sell_threshold: float = 35.0


@dataclass(frozen=True)
class Signal:
    symbol: str
    timeframe: str
    direction: SignalDirection
    confidence: float
    entry: float
    stop_loss: float | None
    take_profit: float | None
    risk_reward: float | None
    strategy_used: list[str] = field(default_factory=list)
    indicators_used: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
