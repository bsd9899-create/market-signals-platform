"""
app/infrastructure/database/models/daily_report.py
--------------------------------------------------------
DailyReport: نموذج بيانات فقط (Schema) لملخص يومي - لا يحتوي أي منطق
حساب فعلي (ذلك يخص مرحلة قادمة). id/created_at/updated_at من BaseModel.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import Date, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import BaseModel


class DailyReport(BaseModel):
    __tablename__ = "daily_reports"

    report_date: Mapped[date] = mapped_column(Date, unique=True, index=True, nullable=False)
    total_scans: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    signals_sent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    wins: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    losses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    win_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
