"""Skill vocabulary, majors, and platform settings (Design 4.3.2)."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, SmallInteger, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import created_at, updated_at, uuid_pk


class Major(Base):
    __tablename__ = "majors"
    id: Mapped[uuid.UUID] = uuid_pk()
    name_en: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name_ar: Mapped[str] = mapped_column(Text, nullable=False)


class Skill(Base):
    __tablename__ = "skills"
    id: Mapped[uuid.UUID] = uuid_pk()
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    name_ar: Mapped[str] = mapped_column(Text, nullable=False)
    synonyms: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default=text("'{}'"),
                                                default=list)
    match_terms: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default=text("'{}'"),
                                                   default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (Index("uq_skills_lower_name_en", func.lower(text("name_en")), unique=True),)


class SkillResource(Base):
    __tablename__ = "skill_resources"
    id: Mapped[uuid.UUID] = uuid_pk()
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    estimated_effort: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(Text)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    __table_args__ = (
        CheckConstraint("url LIKE 'https://%' OR url LIKE 'http://%'", name="url"),
        CheckConstraint("language IS NULL OR language IN ('ar','en')", name="language"),
    )


class SystemSetting(Base):
    __tablename__ = "system_settings"
    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[dict | list | int | float | str] = mapped_column(JSONB, nullable=False)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = updated_at()
