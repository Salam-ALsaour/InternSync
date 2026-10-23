"""Column helpers shared by the models (Design 4.1)."""
import uuid
from datetime import datetime

from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core import clock


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
                         server_default=text("gen_random_uuid()"))


def created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, default=clock.now, server_default=text("now()"))


def updated_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, default=clock.now, onupdate=clock.now,
                         server_default=text("now()"))


def ts(nullable: bool = True) -> Mapped[datetime | None]:
    return mapped_column(DateTime(timezone=True), nullable=nullable)
