"""Vacancies, applications, placements, and match scores (Design 4.3.4)."""
import uuid
from datetime import date, datetime
from decimal import Decimal

from pgvector.sqlalchemy import HALFVEC
from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, SmallInteger, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import created_at, ts, updated_at, uuid_pk


class Vacancy(Base):
    __tablename__ = "vacancies"
    id: Mapped[uuid.UUID] = uuid_pk()
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"), nullable=False)
    company_supervisor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    training_type: Mapped[str] = mapped_column(Text, nullable=False)
    training_start: Mapped[date] = mapped_column(Date, nullable=False)
    training_end: Mapped[date] = mapped_column(Date, nullable=False)
    min_gpa: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    seats: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    application_deadline: Mapped[datetime] = ts(nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="draft", default="draft")
    published_at: Mapped[datetime | None] = ts()
    closed_at: Mapped[datetime | None] = ts()
    embedding = mapped_column(HALFVEC(384))  # vacancy text embedding (Design 6.2)
    embedding_model: Mapped[str | None] = mapped_column(Text)
    embedded_at: Mapped[datetime | None] = ts()
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (
        CheckConstraint("training_type IN ('coop','summer')", name="training_type"),
        CheckConstraint("training_end > training_start", name="training_dates"),
        CheckConstraint("seats > 0", name="seats"),
        CheckConstraint("status IN ('draft','published','closed')", name="status"),
        Index("ix_vacancies_status_company", "status", "company_id"),
    )


class VacancySkill(Base):
    __tablename__ = "vacancy_skills"
    vacancy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vacancies.id"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    __table_args__ = (CheckConstraint("kind IN ('required','preferred')", name="kind"),)


class VacancyMajor(Base):
    __tablename__ = "vacancy_majors"
    vacancy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vacancies.id"), primary_key=True)
    major_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("majors.id"), primary_key=True)


class VacancyUniversity(Base):
    __tablename__ = "vacancy_universities"
    vacancy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vacancies.id"), primary_key=True)
    university_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("universities.id"), primary_key=True)


class Application(Base):
    __tablename__ = "applications"
    id: Mapped[uuid.UUID] = uuid_pk()
    vacancy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vacancies.id"), nullable=False)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="submitted", default="submitted")
    withdraw_reason: Mapped[str | None] = mapped_column(Text)
    fit_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    match_mode: Mapped[str | None] = mapped_column(Text)
    model_version: Mapped[str | None] = mapped_column(Text)
    decided_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = ts()
    withdrawn_at: Mapped[datetime | None] = ts()
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (
        UniqueConstraint("vacancy_id", "student_id"),
        CheckConstraint("status IN ('submitted','accepted','declined','withdrawn','placed','placement_cancelled')",
                        name="status"),
        CheckConstraint("withdraw_reason IS NULL OR withdraw_reason IN ('student','placed_elsewhere','vacancy_closed')",
                        name="withdraw_reason"),
        CheckConstraint("match_mode IS NULL OR match_mode IN ('semantic','basic')", name="match_mode"),
        Index("ix_applications_student_status", "student_id", "status"),
    )


class Placement(Base):
    __tablename__ = "placements"
    id: Mapped[uuid.UUID] = uuid_pk()
    application_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("applications.id"), nullable=False, unique=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    cycle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_cycles.id"), nullable=False)
    vacancy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vacancies.id"), nullable=False)
    company_supervisor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    academic_supervisor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="active", default="active")
    confirmed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    confirmed_at: Mapped[datetime] = ts(nullable=False)
    cancelled_at: Mapped[datetime | None] = ts()
    cancel_reason: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint("status IN ('active','completed','cancelled')", name="status"),
        CheckConstraint("status <> 'cancelled' OR cancel_reason IS NOT NULL", name="cancel_reason"),
        Index("uq_placements_student_cycle", "student_id", "cycle_id", unique=True,
              postgresql_where=text("status <> 'cancelled'")),
    )


class MatchScore(Base):
    """Last computed fit per student and vacancy (FR-MAT-01 – 05, NFR-AI-02)."""
    __tablename__ = "match_scores"
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    vacancy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vacancies.id"), primary_key=True)
    fit_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    semantic: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    required_ratio: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    preferred_ratio: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    mode: Mapped[str] = mapped_column(Text, nullable=False)
    matched_skill_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False)
    missing_skill_ids: Mapped[list[uuid.UUID]] = mapped_column(ARRAY(UUID(as_uuid=True)), nullable=False)
    model_version: Mapped[str | None] = mapped_column(Text)
    computed_at: Mapped[datetime] = ts(nullable=False)
    __table_args__ = (CheckConstraint("mode IN ('semantic','basic')", name="mode"),
                      Index("ix_match_scores_student_fit", "student_id", "fit_score"))
