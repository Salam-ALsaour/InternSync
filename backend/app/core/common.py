"""Small helpers shared by the modules: lookups, pagination, and common response pieces."""
import uuid
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import not_found

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    page: int
    page_size: int
    total: int


class PageParams:
    def __init__(self, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
        self.page = page
        self.page_size = page_size


def paginate(db: Session, stmt, params: PageParams, mapper) -> dict:
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery()))
    rows = db.execute(stmt.limit(params.page_size).offset((params.page - 1) * params.page_size)).scalars().all()
    return {"items": [mapper(r) for r in rows], "page": params.page, "page_size": params.page_size,
            "total": total or 0}


def get_or_404(db: Session, model, id_: uuid.UUID):
    obj = db.get(model, id_)
    if obj is None:
        raise not_found()
    return obj


class Name(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str
