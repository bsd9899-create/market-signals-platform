"""
app/infrastructure/config/environment.py
---------------------------------------------
بيئة التشغيل كـ Enum بدل نص حر - يمنع قيماً غير صالحة بصمت (مثال: خطأ
إملائي في ENVIRONMENT داخل .env) ويجعل القيم المسموحة صريحة في الكود
نفسه بدل توثيق منفصل قد يصبح قديماً.
"""

from __future__ import annotations

from enum import Enum

from app.infrastructure.config.exceptions import ConfigurationError


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"

    @classmethod
    def from_str(cls, value: str | None) -> Environment:
        """يحوّل القيمة النصية من .env (ENVIRONMENT) إلى Environment.
        DEVELOPMENT افتراضياً إذا كانت القيمة فارغة/غير موجودة. يرفع
        ConfigurationError واضحاً إذا كانت القيمة موجودة لكن غير صالحة
        (بدل قبولها بصمت أو الانهيار برسالة غامضة)."""
        if not value:
            return cls.DEVELOPMENT
        normalized = value.strip().lower()
        try:
            return cls(normalized)
        except ValueError as exc:
            valid_values = ", ".join(member.value for member in cls)
            raise ConfigurationError(
                f"قيمة ENVIRONMENT غير صالحة: '{value}' - القيم المسموحة: {valid_values}"
            ) from exc
