"""
app/infrastructure/database/models/scan_log.py
----------------------------------------------------
ScanLog: سجل تنفيذ عملية فحص واحدة (بيانات فقط - لا منطق فحص فعلي هنا).

**استثناء متعمَّد عن القاعدة العامة**: يرث من Base مباشرة (وليس
BaseModel) - له id خاص به فقط، وبلا created_at/updated_at، لأن
started_at/finished_at يغطيان معنى الوقت هنا فعلياً، وتكرارهما مع
created_at/updated_at كان زائداً (بطلب صريح بعد المراجعة).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import Base


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    symbols_scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    signals_found: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
