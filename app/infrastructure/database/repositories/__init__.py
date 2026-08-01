"""
app/infrastructure/database/repositories
---------------------------------------------
Repositories متخصصة (واحد لكل نموذج) - كل واحد يرث Repository العام
(repository.py) دون أي منطق إضافي حتى الآن.
"""

from app.infrastructure.database.repositories.bot_state_repository import BotStateRepository
from app.infrastructure.database.repositories.daily_report_repository import DailyReportRepository
from app.infrastructure.database.repositories.scan_log_repository import ScanLogRepository
from app.infrastructure.database.repositories.signal_repository import SignalRepository
from app.infrastructure.database.repositories.trade_repository import TradeRepository

__all__ = ["BotStateRepository", "DailyReportRepository", "ScanLogRepository", "SignalRepository", "TradeRepository"]
