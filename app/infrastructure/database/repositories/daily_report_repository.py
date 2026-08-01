"""
app/infrastructure/database/repositories/daily_report_repository.py
--------------------------------------------------------------------------
Repository متخصص لـDailyReport - يرث كل شيء من Repository العام بلا
أي منطق إضافي حتى الآن (محجوز لمرحلة قادمة).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database.models import DailyReport
from app.infrastructure.database.repository import Repository


class DailyReportRepository(Repository[DailyReport]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, DailyReport)
