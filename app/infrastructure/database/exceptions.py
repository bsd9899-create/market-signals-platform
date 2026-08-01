"""
app/infrastructure/database/exceptions.py
----------------------------------------------
استثناءات واضحة لطبقة قاعدة البيانات - بدل ترك استثناءات SQLAlchemy
الخام (OperationalError إلخ) تنفجر بدون سياق مفهوم.
"""

from __future__ import annotations


class DatabaseError(Exception):
    """الأصل المشترك لكل أخطاء قاعدة البيانات."""


class DatabaseConnectionError(DatabaseError):
    """تعذّر الاتصال بقاعدة البيانات فعلياً (راجع DatabaseManager.test_connection)."""

    def __init__(self, database_url: str, original_error: Exception) -> None:
        super().__init__(
            f"تعذّر الاتصال بقاعدة البيانات ({database_url}).\nالسبب: {original_error}"
        )
        self.database_url = database_url
        self.original_error = original_error


class DatabaseNotConnectedError(DatabaseError):
    """استُخدِم DatabaseManager قبل استدعاء connect() أولاً."""

    def __init__(self) -> None:
        super().__init__(
            "لم يتم الاتصال بقاعدة البيانات بعد - استدعِ DatabaseManager.connect() أولاً."
        )
