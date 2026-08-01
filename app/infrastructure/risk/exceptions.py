"""
app/infrastructure/risk/exceptions.py
--------------------------------------------
استثناءات واضحة لمدير المخاطرة.
"""

from __future__ import annotations


class RiskError(Exception):
    """الأصل المشترك لكل أخطاء مدير المخاطرة."""


class InvalidRiskParametersError(RiskError):
    """معاملات غير منطقية (مثال: وقف الخسارة يساوي سعر الدخول)."""


class RiskLimitExceededError(RiskError):
    """تجاوز حد مخاطرة مضبوط (يومي أو عدد مراكز مفتوحة)."""
