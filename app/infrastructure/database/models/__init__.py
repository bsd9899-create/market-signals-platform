"""
app/infrastructure/database/models
--------------------------------------
يستورد كل النماذج هنا حتى تُسجَّل فعلياً في Base.metadata قبل أي
استدعاء لـ create_tables() - نموذج لم يُستورَد لن يُنشأ جدوله إطلاقاً،
حتى لو كان يرث من BaseModel بشكل صحيح.
"""

from app.infrastructure.database.models.bot_state import BotState
from app.infrastructure.database.models.daily_report import DailyReport
from app.infrastructure.database.models.scan_log import ScanLog
from app.infrastructure.database.models.signal import Signal
from app.infrastructure.database.models.trade import Trade

__all__ = ["BotState", "DailyReport", "ScanLog", "Signal", "Trade"]
