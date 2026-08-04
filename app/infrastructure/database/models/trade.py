"""
app/infrastructure/database/models/trade.py
--------------------------------------------------
Trade: سجل دائم (Trade Journal) لكل صفقة أُرسِلت فعلياً إلى Telegram -
بيانات فقط (Schema)، بلا أي منطق مراقبة/قرار هنا (ذلك في
app/infrastructure/tracking/).

entry/stop/tp1/tp2 هنا هي مستويات **السهم الأساسي** (Underlying Stock)
- نفس القيم التي حسبها RiskManager فعلياً (وليست علاوة الخيار) - لأن
مراقبة علاوة عقد خيار حي كل دقيقة تتطلب إعادة جلب سلسلة الخيارات كاملة
في كل دورة (مكلف جداً)، بينما سعر السهم متاح فعلياً عبر
MarketService.get_quote() المخزَّن مؤقتاً أصلاً. option_entry_low/high
تُحفَظ منفصلة فقط لعرض نفس الأرقام التي وصلت المستخدم فعلياً في السجل.

profit_loss_percent عند الإغلاق = نسبة تحرك **السهم الأساسي** من الدخول
إلى الخروج (وليس عائد علاوة الخيار الفعلي) - نفس القيد أعلاه بالضبط.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import BaseModel


class Trade(BaseModel):
    __tablename__ = "trades"

    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    direction: Mapped[str] = mapped_column(String(10), nullable=False)  # "buy" / "sell" (Signal.direction.value)
    option_type: Mapped[str] = mapped_column(String(4), nullable=False)  # "CALL" / "PUT"

    strike: Mapped[float] = mapped_column(Float, nullable=False)
    expiration: Mapped[str] = mapped_column(String(20), nullable=False)
    option_entry_low: Mapped[float] = mapped_column(Float, nullable=False)
    option_entry_high: Mapped[float] = mapped_column(Float, nullable=False)

    entry: Mapped[float] = mapped_column(Float, nullable=False)
    stop: Mapped[float] = mapped_column(Float, nullable=False)
    tp1: Mapped[float] = mapped_column(Float, nullable=False)
    tp2: Mapped[float] = mapped_column(Float, nullable=False)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    profit_loss_percent: Mapped[float | None] = mapped_column(Float, nullable=True)

    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    risk_reward: Mapped[float] = mapped_column(Float, nullable=False)
    strategy: Mapped[str] = mapped_column(String(200), nullable=False)  # strategy_used مفصولة بفاصلة
    reasons: Mapped[str] = mapped_column(String(2000), nullable=False)  # reasons مفصولة بـ " | "

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="OPEN", index=True)  # OPEN/TP1_HIT/TP2_HIT/STOPPED
    better_entry_sent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # يسمح بـBetter Entry واحدة فقط لكل صفقة مفتوحة (بطلب صريح)

    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tp1_hit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tp1_hit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
