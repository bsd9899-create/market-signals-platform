"""
app/infrastructure/database/repositories/signal_repository.py
-------------------------------------------------------------------
Repository متخصص لـSignal - يرث كل شيء من Repository العام بلا أي
منطق إضافي حتى الآن (محجوز لمرحلة قادمة).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database.models import Signal
from app.infrastructure.database.repository import Repository


class SignalRepository(Repository[Signal]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Signal)
