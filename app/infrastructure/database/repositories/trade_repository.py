"""
app/infrastructure/database/repositories/trade_repository.py
-------------------------------------------------------------------
Repository متخصص لـTrade - يرث Repository العام + استعلامات إضافية
بسيطة (get_open/get_closed_between) يحتاجها فعلياً TradeJournal/التقارير،
بلا أي منطق قرار (ذلك في app/infrastructure/tracking/).
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.database.models import Trade
from app.infrastructure.database.repository import Repository


class TradeRepository(Repository[Trade]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, Trade)

    def get_open(self) -> list[Trade]:
        stmt = select(Trade).where(Trade.status.in_(("OPEN", "TP1_HIT")))
        return list(self._session.scalars(stmt))

    def get_closed_between(self, start: datetime, end: datetime) -> list[Trade]:
        stmt = select(Trade).where(
            Trade.exit_time.is_not(None), Trade.exit_time >= start, Trade.exit_time < end,
        )
        return list(self._session.scalars(stmt))

    def get_sent_between(self, start: datetime, end: datetime) -> list[Trade]:
        stmt = select(Trade).where(Trade.entry_time >= start, Trade.entry_time < end)
        return list(self._session.scalars(stmt))

    def get_tp1_hits_between(self, start: datetime, end: datetime) -> list[Trade]:
        stmt = select(Trade).where(Trade.tp1_hit_at.is_not(None), Trade.tp1_hit_at >= start, Trade.tp1_hit_at < end)
        return list(self._session.scalars(stmt))
