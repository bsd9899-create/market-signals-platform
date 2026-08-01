"""
app/infrastructure/database/base.py
---------------------------------------
Base: جذر التسجيل (Registry) لكل النماذج - SQLAlchemy 2.x الحديث عبر
DeclarativeBase (وليس declarative_base() القديمة).

BaseModel: نموذج مجرّد (Abstract) يحتوي id/created_at/updated_at - كل
نموذج فعلي (BotState, Signal, ScanLog, DailyReport) يرث منه بدل تكرار
هذه الأعمدة الثلاثة في كل مرة.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """جذر Metadata المشترك - Base.metadata.create_all() يُنشئ كل جدول
    لأي نموذج يرث (مباشرة أو عبر BaseModel) من هذا الصف."""


class BaseModel(Base):
    """نموذج مجرّد - لا يُنشئ جدولاً خاصاً به (__abstract__ = True)،
    فقط يوفّر id/created_at/updated_at لكل من يرث منه."""

    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utc_now, onupdate=_utc_now, nullable=False,
    )
