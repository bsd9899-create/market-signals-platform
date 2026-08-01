"""
app/infrastructure/config/loader.py
---------------------------------------
نقطة القراءة الوحيدة لإعدادات التطبيق عبر ConfigLoader: يدمج
config/settings.yaml (عام، غير سرّي) + config/scanner.yaml +
config/telegram.yaml (غير سرّي - القيم السرّية من .env فقط) مع .env،
ويقرأ config/symbols.yaml كقائمة رموز مستقلة.

الاستخدام:
    loader = ConfigLoader()
    settings = loader.settings   # Settings (Typed Dataclass)
    symbols = loader.symbols     # list[str]
    env = loader.env             # dict[str, str | None] الخام من .env

يرفع ConfigurationError (أو أحد فرعيها) برسالة واضحة إذا كان
settings.yaml أو symbols.yaml غير موجودَين، أو بصيغة YAML غير صحيحة -
بدل السماح بانهيار غامض لاحقاً. scanner.yaml وtelegram.yaml اختياريان
(القيم الافتراضية تُستخدَم إذا لم يوجدا أو كانا فارغين).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from dotenv import dotenv_values

from app.infrastructure.config.environment import Environment
from app.infrastructure.config.exceptions import ConfigFileNotFoundError, ConfigParseError
from app.infrastructure.config.settings_models import (
    AppSettings,
    DatabaseSettings,
    LoggingSettings,
    NewsSettings,
    OptionsSettings,
    ReportSettings,
    ScannerSettings,
    Settings,
    TelegramSettings,
)
from app.infrastructure.paths import ProjectPaths
from app.infrastructure.risk.models import RiskSettings
from app.infrastructure.scanner.models import DEFAULT_TIMEFRAMES


def _read_yaml(path: Path) -> dict:
    """يقرأ ملف YAML مع تحقق واضح: يرفع ConfigFileNotFoundError إذا لم
    يوجد الملف، وConfigParseError إذا كانت صيغته غير صحيحة."""
    if not path.exists():
        raise ConfigFileNotFoundError(path)
    try:
        with path.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise ConfigParseError(path, exc) from exc
    return data or {}


def _read_optional_yaml(path: Path) -> dict:
    """مثل _read_yaml لكن لا يرفع خطأ إذا لم يوجد الملف - يُستخدم للملفات
    الاختيارية (scanner.yaml/telegram.yaml) التي لها قيم افتراضية معقولة."""
    if not path.exists():
        return {}
    return _read_yaml(path)


class ConfigLoader:
    """يحمّل كل الإعدادات مرة واحدة عند الإنشاء (Eager Loading) ويتيحها
    عبر خصائص جاهزة: .settings, .symbols, .env"""

    def __init__(self) -> None:
        self.env: dict[str, str | None] = self._load_env()

        settings_raw = _read_yaml(ProjectPaths.CONFIG_DIR / "settings.yaml")
        symbols_raw = _read_yaml(ProjectPaths.CONFIG_DIR / "symbols.yaml")
        scanner_raw = _read_optional_yaml(ProjectPaths.CONFIG_DIR / "scanner.yaml")
        telegram_raw = _read_optional_yaml(ProjectPaths.CONFIG_DIR / "telegram.yaml")

        self.symbols: list[str] = list(symbols_raw.get("symbols") or [])
        self.settings: Settings = self._build_settings(settings_raw, scanner_raw, telegram_raw)

    @staticmethod
    def _load_env() -> dict[str, str | None]:
        env_file = ProjectPaths.ROOT / ".env"
        return dotenv_values(env_file) if env_file.exists() else {}

    def _build_settings(self, raw: dict, scanner_raw: dict, telegram_raw: dict) -> Settings:
        app_raw = raw.get("app", {})
        logging_raw = raw.get("logging", {})
        risk_raw = raw.get("risk", {})
        reports_raw = raw.get("reports", {})
        news_raw = raw.get("news", {})
        options_raw = raw.get("options", {})

        return Settings(
            environment=Environment.from_str(self.env.get("ENVIRONMENT")),
            app=AppSettings(
                name=app_raw.get("name", "Market Signals Platform"),
                version=app_raw.get("version", "0.1.0"),
            ),
            logging=LoggingSettings(
                level=self.env.get("LOG_LEVEL") or logging_raw.get("level", "INFO"),
                directory=logging_raw.get("directory", "logs"),
                file_name=logging_raw.get("file_name", "app.log"),
                rotation=logging_raw.get("rotation", "10 MB"),
                retention=logging_raw.get("retention", "14 days"),
            ),
            database=DatabaseSettings(url=self._resolve_database_url()),
            telegram=TelegramSettings(
                bot_token=self.env.get("TELEGRAM_BOT_TOKEN") or "",
                admin_chat_id=self.env.get("TELEGRAM_ADMIN_CHAT_ID") or "",
                enabled=bool(telegram_raw.get("enabled", False)),
            ),
            scanner=ScannerSettings(
                symbols=list(scanner_raw.get("symbols") or self.symbols),
                timeframes=list(scanner_raw.get("timeframes") or DEFAULT_TIMEFRAMES),
                interval_seconds=float(scanner_raw.get("interval_seconds", 300.0)),
                max_workers=int(scanner_raw.get("max_workers", 4)),
            ),
            risk=RiskSettings(
                default_risk_percent=float(risk_raw.get("default_risk_percent", 1.0)),
                default_risk_reward_ratio=float(risk_raw.get("default_risk_reward_ratio", 2.0)),
                atr_multiplier=float(risk_raw.get("atr_multiplier", 1.5)),
                max_daily_risk_percent=float(risk_raw.get("max_daily_risk_percent", 5.0)),
                max_open_positions=int(risk_raw.get("max_open_positions", 5)),
            ),
            reports=ReportSettings(enabled=bool(reports_raw.get("enabled", True))),
            news=NewsSettings(
                enabled=bool(news_raw.get("enabled", True)), provider=news_raw.get("provider", "mock"),
            ),
            options=OptionsSettings(
                enabled=bool(options_raw.get("enabled", True)), provider=options_raw.get("provider", "mock"),
            ),
        )

    def _resolve_database_url(self) -> str:
        """DATABASE_URL من .env إن وُجد، وإلا SQLite افتراضي داخل
        ProjectPaths.DATABASE_DIR - هذا هو المكان الوحيد في المشروع الذي
        "يعرف" أن القاعدة الحالية SQLite؛ التبديل لاحقاً يتم بتعيين
        DATABASE_URL في .env فقط."""
        configured = self.env.get("DATABASE_URL")
        if configured:
            return configured
        default_path = (ProjectPaths.DATABASE_DIR / "app.db").as_posix()
        return f"sqlite:///{default_path}"
