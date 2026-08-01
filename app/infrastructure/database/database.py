"""
app/infrastructure/database/database.py
--------------------------------------------
DatabaseManager: مسؤول حصراً عن دورة حياة الاتصال بقاعدة البيانات -
إنشاء المحرك (Engine)، إنشاء Session Factory، إنشاء الجداول، اختبار
الاتصال، وإغلاقه. لا يحتوي أي منطق أعمال - فقط البنية التحتية.

SQLite حالياً - التبديل لاحقاً إلى PostgreSQL (أو أي قاعدة بيانات أخرى
يدعمها SQLAlchemy) يتم فقط بتغيير database_url (عبر DATABASE_URL في
.env) دون أي تعديل على هذا الملف أو أي كود آخر.
"""

from __future__ import annotations

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

# يضمن استيراد app/infrastructure/database/models قبل create_tables()
# أن كل النماذج مسجَّلة في Base.metadata فعلياً (راجع models/__init__.py).
from app.infrastructure.database import models  # noqa: F401
from app.infrastructure.database.base import Base
from app.infrastructure.database.exceptions import DatabaseConnectionError, DatabaseNotConnectedError
from app.infrastructure.database.session import session_scope


class DatabaseManager:
    """يُنشأ بـ database_url واحد، ثم connect() قبل أي استخدام آخر."""

    def __init__(self, database_url: str) -> None:
        self._database_url = database_url
        self._engine = None
        self._session_factory: sessionmaker[Session] | None = None

    def connect(self) -> None:
        """ينشئ Engine وSession Factory - لا يُنشئ أي جدول بعد (راجع create_tables)."""
        self._engine = create_engine(self._database_url, echo=False)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)
        logger.info("تم إنشاء محرك قاعدة البيانات: {}", self._database_url)

    def test_connection(self) -> bool:
        """يُنفِّذ استعلاماً بسيطاً (SELECT 1) للتأكد من صحة الاتصال فعلياً.
        يرفع DatabaseConnectionError برسالة واضحة إذا فشل الاتصال."""
        if self._engine is None:
            raise DatabaseNotConnectedError()
        try:
            with self._engine.connect() as connection:
                connection.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            logger.error("فشل اختبار الاتصال بقاعدة البيانات: {}", exc)
            raise DatabaseConnectionError(self._database_url, exc) from exc

        logger.info("نجح اختبار الاتصال بقاعدة البيانات.")
        return True

    def create_tables(self) -> None:
        """ينشئ كل الجداول غير الموجودة (Base.metadata.create_all عملية
        آمنة للتكرار - Idempotent، لا تلمس الجداول الموجودة أصلاً). هذا
        ما يجعل إنشاء قاعدة البيانات تلقائياً عند أول تشغيل يعمل بدون
        أي خطوة يدوية إضافية."""
        if self._engine is None:
            raise DatabaseNotConnectedError()
        Base.metadata.create_all(self._engine)
        table_names = sorted(Base.metadata.tables.keys())
        logger.info("تم التأكد من وجود كل الجداول: {}", table_names)

    def session(self):
        """يُعيد Context Manager لجلسة عمل - الطريقة الوحيدة المسموحة
        لفتح Session في كامل المشروع (راجع session.py)."""
        if self._session_factory is None:
            raise DatabaseNotConnectedError()
        return session_scope(self._session_factory)

    def close(self) -> None:
        """يُغلق كل الاتصالات المفتوحة في تجمّع الاتصالات (Connection Pool)."""
        if self._engine is not None:
            self._engine.dispose()
            logger.info("تم إغلاق الاتصال بقاعدة البيانات.")
