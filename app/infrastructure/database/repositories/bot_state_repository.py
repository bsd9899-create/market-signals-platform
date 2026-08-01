"""
app/infrastructure/database/repositories/bot_state_repository.py
----------------------------------------------------------------------
Repository متخصص لـBotState - يرث كل شيء من Repository العام (create/
get_by_id/get_all/update/delete/exists/count) بلا أي منطق إضافي حتى
الآن (محجوز لمرحلة قادمة).
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import BotState
from app.infrastructure.database.repository import Repository


class BotStateRepository(Repository[BotState]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, BotState)

    def get_by_key(self, key: str) -> BotState | None:
        return self._session.scalar(select(BotState).where(BotState.key == key))

    def set_value(self, key: str, value: str) -> BotState:
        existing = self.get_by_key(key)
        if existing is not None:
            existing.value = value
            self._session.flush()
            return existing
        return self.create(key=key, value=value)
