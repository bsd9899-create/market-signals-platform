"""
app/infrastructure/database/session.py
-------------------------------------------
نقطة فتح Session الوحيدة في كامل المشروع - عبر session_scope() فقط.
يضمن: Commit عند النجاح، Rollback عند أي استثناء، وإغلاق Session دائماً
(Context Manager) - لا يُفتح Session يدوياً في أي مكان آخر.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from loguru import logger
from sqlalchemy.orm import Session, sessionmaker


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """يفتح Session، يُسلِّمها للاستخدام، ثم:
    - Commit تلقائي إذا انتهى الكتلة (Block) بدون استثناء.
    - Rollback تلقائي + إعادة رفع الاستثناء إذا حدث أي خطأ.
    - إغلاق Session دائماً (finally) بغض النظر عن النتيجة."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("فشلت عملية قاعدة بيانات - تم التراجع (Rollback) عن كل التغييرات.")
        raise
    finally:
        session.close()
