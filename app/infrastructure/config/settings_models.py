"""
app/infrastructure/config/settings_models.py
-------------------------------------------------
كائنات الإعدادات المكتوبة (Typed Dataclasses) - كل قسم إعدادات في
Dataclass منفصل بدل كائن واحد ضخم.

**تحديث المرحلة النهائية**: ScannerSettings وTelegramSettings لم تعودا
فارغتين (Future) - أصبحتا تحملان قيماً فعلية الآن. أُضيفت أيضاً
ReportSettings، NewsSettings، OptionsSettings. RiskSettings مُعرَّفة في
app.infrastructure.risk.models (أقرب لمجالها) وتُستورَد هنا فقط لتُدرَج
داخل Settings الرئيسية - بلا ازدواج تعريف.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.infrastructure.config.environment import Environment
from app.infrastructure.risk.models import RiskSettings


@dataclass(frozen=True)
class AppSettings:
    name: str
    version: str


@dataclass(frozen=True)
class LoggingSettings:
    level: str
    directory: str
    file_name: str
    rotation: str
    retention: str


@dataclass(frozen=True)
class DatabaseSettings:
    """إعدادات الاتصال بقاعدة البيانات - url فقط (SQLAlchemy يدعم أي
    قاعدة بيانات عبر رابط الاتصال نفسه؛ SQLite حالياً، والتبديل
    لـPostgreSQL لاحقاً يتم فقط بتغيير url من .env)."""

    url: str


@dataclass(frozen=True)
class TelegramSettings:
    """bot_token وadmin_chat_id يُقرآن من .env فقط (سرّيان) - **لا يوجد
    أي اتصال حقيقي بـTelegram في هذه المرحلة** (راجع
    app/infrastructure/telegram/sender.py) بغض النظر عن قيمتهما."""

    bot_token: str
    admin_chat_id: str
    enabled: bool


@dataclass(frozen=True)
class ScannerSettings:
    symbols: list[str]
    timeframes: list[str]
    interval_seconds: float
    max_workers: int


@dataclass(frozen=True)
class ReportSettings:
    enabled: bool


@dataclass(frozen=True)
class NewsSettings:
    enabled: bool
    provider: str  # "mock" فقط متاح حالياً


@dataclass(frozen=True)
class OptionsSettings:
    enabled: bool
    provider: str  # "mock" فقط متاح حالياً


@dataclass(frozen=True)
class Settings:
    environment: Environment
    app: AppSettings
    logging: LoggingSettings
    database: DatabaseSettings
    telegram: TelegramSettings
    scanner: ScannerSettings
    risk: RiskSettings
    reports: ReportSettings
    news: NewsSettings
    options: OptionsSettings
