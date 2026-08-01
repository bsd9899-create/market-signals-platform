"""
app/infrastructure/risk/models.py
------------------------------------
نماذج بيانات مدير المخاطرة (Dataclasses مُجمَّدة).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskSettings:
    default_risk_percent: float = 1.0            # % من رأس المال يُخاطَر به لكل صفقة
    default_risk_reward_ratio: float = 2.0        # نسبة العائد/المخاطرة الافتراضية
    atr_multiplier: float = 1.5                   # مضاعف ATR لحساب وقف الخسارة
    max_daily_risk_percent: float = 5.0           # أقصى مخاطرة إجمالية مسموحة في اليوم
    max_open_positions: int = 5                   # أقصى عدد مراكز مفتوحة في آن واحد


@dataclass(frozen=True)
class PositionSizeResult:
    units: float                # عدد الوحدات/العقود (كسري - التقريب مسؤولية المُستدعي)
    risk_amount: float          # المبلغ المُخاطَر به فعلياً بالعملة
    per_unit_risk: float        # المخاطرة لكل وحدة (|entry - stop|)
