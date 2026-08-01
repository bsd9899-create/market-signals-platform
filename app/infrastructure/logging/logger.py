"""
app/infrastructure/logging/logger.py
----------------------------------------
LoggerService: مسؤول حصراً عن تهيئة (setup) وتوفير (get_logger) نظام
التسجيل عبر Loguru - طرفية ملوّنة + ملف log دوّار داخل logs/.

الاستخدام:
    logger_service = LoggerService()
    logger_service.setup(settings.logging)
    logger = logger_service.get_logger()
"""

from __future__ import annotations

import sys

from loguru import logger as _logger

from app.infrastructure.config.settings_models import LoggingSettings
from app.infrastructure.paths import ProjectPaths


class LoggerService:
    """يُغلِّف Loguru بواجهة صريحة بدل دوال معزولة على مستوى الوحدة -
    setup() تُهيّئ المخرجين (طرفية + ملف) مرة واحدة، get_logger() يُعيد
    الكائن الجاهز."""

    def __init__(self) -> None:
        self._configured = False

    def setup(self, settings: LoggingSettings) -> None:
        """يهيّئ Loguru بمخرجين: طرفية (Console) وملف دوّار داخل logs/.
        آمن عند الاستدعاء أكثر من مرة (لن يكرر المخرجات)."""
        if self._configured:
            return

        ProjectPaths.LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = ProjectPaths.LOG_DIR / settings.file_name

        _logger.remove()  # يزيل المخرج الافتراضي حتى لا تتكرر الرسائل

        _logger.add(
            sys.stderr,
            level=settings.level,
            colorize=True,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level: <8}</level> | "
                "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                "<level>{message}</level>"
            ),
        )

        _logger.add(
            log_file,
            level=settings.level,
            rotation=settings.rotation,
            retention=settings.retention,
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        )

        self._configured = True

    def get_logger(self):
        """يُعيد كائن logger الجاهز - يجب استدعاء setup() قبله أولاً."""
        if not self._configured:
            raise RuntimeError("يجب استدعاء LoggerService.setup() قبل get_logger().")
        return _logger
