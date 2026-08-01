"""
app/infrastructure/database/repository.py
----------------------------------------------
Repository عام (Generic) يعمل مع أي نموذج يرث من Base - يوفّر عمليات
CRUD الأساسية مرة واحدة بدل تكرارها لكل نموذج على حدة.

**لا يفتح Session بنفسه ولا يديره** - يستقبل Session جاهزة من المُستدعي
(عادة داخل `with db_manager.session() as session:` - راجع session.py)،
تنفيذاً لمبدأ "لا تفتح Session يدوياً في كل مكان": نقطة الفتح/الإغلاق/
الـCommit موحّدة في session_scope فقط.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class Repository(Generic[ModelType]):
    def __init__(self, session: Session, model: type[ModelType]) -> None:
        self._session = session
        self._model = model

    def create(self, **fields: object) -> ModelType:
        instance = self._model(**fields)
        self._session.add(instance)
        self._session.flush()  # يمنح id فوراً دون الحاجة لانتظار commit خارجي
        logger.debug("Repository.create: {} id={}", self._model.__name__, instance.id)
        return instance

    def get_by_id(self, id_: int) -> ModelType | None:
        return self._session.get(self._model, id_)

    def get_all(self) -> list[ModelType]:
        return list(self._session.scalars(select(self._model)))

    def update(self, id_: int, **fields: object) -> ModelType | None:
        instance = self.get_by_id(id_)
        if instance is None:
            logger.debug("Repository.update: {} id={} غير موجود", self._model.__name__, id_)
            return None
        for key, value in fields.items():
            setattr(instance, key, value)
        self._session.flush()
        logger.debug("Repository.update: {} id={}", self._model.__name__, id_)
        return instance

    def delete(self, id_: int) -> bool:
        instance = self.get_by_id(id_)
        if instance is None:
            logger.debug("Repository.delete: {} id={} غير موجود", self._model.__name__, id_)
            return False
        self._session.delete(instance)
        self._session.flush()
        logger.debug("Repository.delete: {} id={}", self._model.__name__, id_)
        return True

    def exists(self, id_: int) -> bool:
        return self.get_by_id(id_) is not None

    def count(self) -> int:
        return self._session.scalar(select(func.count()).select_from(self._model)) or 0
