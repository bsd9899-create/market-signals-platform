"""
app/infrastructure/database/models/bot_state.py
----------------------------------------------------
BotState: مخزن Key/Value عام لحالة البوت (id/created_at/updated_at من
BaseModel + key/value هنا). لا يحمل أي منطق تداول - مجرد نموذج بيانات.
"""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database.base import BaseModel


class BotState(BaseModel):
    __tablename__ = "bot_state"

    key: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
