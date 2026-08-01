"""
app/infrastructure/database/models/signal.py
--------------------------------------------------
Signal: نموذج بيانات فقط (Schema) - لا يحتوي أي منطق توليد أو تقييم
إشارات (ذلك يخص مرحلة قادمة). id/created_at/updated_at من BaseModel.
"""

from __future__ import annotations

from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import BaseModel


class Signal(BaseModel):
    __tablename__ = "signals"

    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
