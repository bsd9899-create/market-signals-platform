"""
app/infrastructure/database/repositories/scan_log_repository.py
------------------------------------------------------------------
Repository متخصص لـScanLog - يرث كل شيء من Repository العام بلا أي
منطق إضافي حتى الآن (محجوز لمرحلة قادمة).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.infrastructure.database.models import ScanLog
from app.infrastructure.database.repository import Repository


class ScanLogRepository(Repository[ScanLog]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, ScanLog)
