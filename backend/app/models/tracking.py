"""Attendance, evaluations, grades, and certificates (Design 4.3.6, 4.3.7; Increment 2 design, Section 2;
Increment 4 design, Section 2)."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Numeric, SmallInteger, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import created_at, ts, updated_at, uuid_pk


class AttendanceWeek(Base):
    """A recorded week, or only the unlock of a week that was never recorded (FR-ATT-01, FR-ATT-02)."""
    __tablename__ = "attendance_weeks"
    id: Mapped[uuid.UUID] = uuid_pk()
    placement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("placements.id"), nullable=False)
    week_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    scheduled_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    attended_days: Mapped[int | None] = mapped_column(SmallInteger)
    note: Mapped[str | None] = mapped_column(Text)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    recorded_at: Mapped[datetime | None] = ts()
    unlocked_until: Mapped[datetime | None] = ts()
    unlocked_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    unlock_reason: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (
        UniqueConstraint("placement_id", "week_no"),
        CheckConstraint("scheduled_days BETWEEN 0 AND 7", name="scheduled_days"),
        CheckConstraint("attended_days IS NULL OR attended_days BETWEEN 0 AND scheduled_days", name="attended_days"),
        CheckConstraint("(attended_days IS NULL) = (recorded_by IS NULL) AND (attended_days IS NULL) = "
                        "(recorded_at IS NULL)", name="recorded_together"),
    )


class Evaluation(Base):
    __tablename__ = "evaluations"
    id: Mapped[uuid.UUID] = uuid_pk()
    placement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("placements.id"), nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="draft", default="draft")
    overall_comment: Mapped[str | None] = mapped_column(Text)
    mean_score: Mapped[Decimal | None] = mapped_column(Numeric(4, 3))
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    submitted_at: Mapped[datetime | None] = ts()
    reopen_count: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0", default=0)
    reopened_at: Mapped[datetime | None] = ts()
    reopened_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    reopen_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (
        UniqueConstraint("placement_id", "type"),
        CheckConstraint("type IN ('periodic','final')", name="type"),
        CheckConstraint("status IN ('draft','submitted')", name="status"),
        CheckConstraint("reopen_count <= 1", name="reopen_once"),
    )


class EvaluationScore(Base):
    __tablename__ = "evaluation_scores"
    evaluation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("evaluations.id"), primary_key=True)
    criterion_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("rubric_criteria.id"), primary_key=True)
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    __table_args__ = (CheckConstraint("score BETWEEN 1 AND 5", name="score"),)


class Grade(Base):
    __tablename__ = "grades"
    id: Mapped[uuid.UUID] = uuid_pk()
    placement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("placements.id"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="draft", default="draft")
    total: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    submitted_at: Mapped[datetime | None] = ts()
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    approved_at: Mapped[datetime | None] = ts()
    return_comment: Mapped[str | None] = mapped_column(Text)
    reopen_reason: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (CheckConstraint("status IN ('draft','submitted','final')", name="status"),)


class GradeComponentScore(Base):
    __tablename__ = "grade_component_scores"
    grade_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grades.id"), primary_key=True)
    component_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grade_components.id"), primary_key=True)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (CheckConstraint("score >= 0 AND score <= 100", name="score"),)


RATINGS = ("learning_opportunities", "supervision_quality", "work_environment", "relevance_to_major")


class CompanyEvaluation(Base):
    """The student's evaluation of the training entity (FR-EVL-05); never visible to company supervisors."""
    __tablename__ = "company_evaluations"
    placement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("placements.id"), primary_key=True)
    learning_opportunities: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    supervision_quality: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    work_environment: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    relevance_to_major: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    would_recommend: Mapped[bool] = mapped_column(Boolean, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime] = ts(nullable=False)
    __table_args__ = tuple(CheckConstraint(f"{r} BETWEEN 1 AND 5", name=r) for r in RATINGS)


class OutcomeSurvey(Base):
    """The job-offer answer of FR-DSH-03."""
    __tablename__ = "outcome_surveys"
    placement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("placements.id"), primary_key=True)
    job_offer: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = ts(nullable=False)
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (CheckConstraint("job_offer IN ('yes','no','pending')", name="job_offer"),)


class Certificate(Base):
    """Completion certificate (FR-CER-01 – 03); `code` is the public ID in the QR code."""
    __tablename__ = "certificates"
    id: Mapped[uuid.UUID] = uuid_pk()
    placement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("placements.id"), nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("files.id"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="valid", default="valid")
    issued_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    issued_at: Mapped[datetime] = ts(nullable=False)
    revoked_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    revoked_at: Mapped[datetime | None] = ts()
    revoke_reason: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint("status IN ('valid','revoked')", name="status"),
        CheckConstraint("status <> 'revoked' OR (revoke_reason IS NOT NULL AND length(trim(revoke_reason)) > 0)",
                        name="revoke_reason"),
        Index("uq_certificates_valid_placement", "placement_id", unique=True,
              postgresql_where=text("status = 'valid'")),
    )
