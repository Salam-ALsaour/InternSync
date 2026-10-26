"""Training cycles, weeks, grade components, rubric, and enrolments (Design 4.3.2, 4.3.3)."""
import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    Text,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import created_at, ts, updated_at, uuid_pk


class TrainingCycle(Base):
    __tablename__ = "training_cycles"
    id: Mapped[uuid.UUID] = uuid_pk()
    college_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("colleges.id"), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    weeks: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    working_days: Mapped[list[int]] = mapped_column(ARRAY(SmallInteger), nullable=False,
                                                    server_default=text("'{7,1,2,3,4}'"))
    report_weekday: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    report_time: Mapped[time] = mapped_column(Time, nullable=False)
    periodic_eval_due_at: Mapped[datetime] = ts(nullable=False)
    final_eval_due_at: Mapped[datetime] = ts(nullable=False)
    final_report_due_at: Mapped[datetime] = ts(nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="open", default="open")
    rubric_locked_at: Mapped[datetime | None] = ts()
    closed_at: Mapped[datetime | None] = ts()
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (
        UniqueConstraint("college_id", "name"),
        CheckConstraint("type IN ('coop','summer')", name="type"),
        CheckConstraint("end_date > start_date", name="dates"),
        CheckConstraint("weeks BETWEEN 1 AND 30", name="weeks"),
        CheckConstraint("report_weekday BETWEEN 1 AND 7", name="report_weekday"),
        CheckConstraint("status IN ('open','closed')", name="status"),
    )


class CycleWeek(Base):
    __tablename__ = "cycle_weeks"
    cycle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_cycles.id"), primary_key=True)
    week_no: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    starts_on: Mapped[date] = mapped_column(Date, nullable=False)
    ends_on: Mapped[date] = mapped_column(Date, nullable=False)
    report_due_at: Mapped[datetime] = ts(nullable=False)
    scheduled_days: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    __table_args__ = (
        CheckConstraint("week_no >= 1", name="week_no"),
        CheckConstraint("scheduled_days BETWEEN 0 AND 7", name="scheduled_days"),
    )


class GradeComponent(Base):
    __tablename__ = "grade_components"
    id: Mapped[uuid.UUID] = uuid_pk()
    cycle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_cycles.id"), nullable=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    name_ar: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    __table_args__ = (
        UniqueConstraint("cycle_id", "name_en"),
        CheckConstraint("weight > 0 AND weight <= 100", name="weight"),
        CheckConstraint("source IN ('company_final_evaluation','academic_supervisor')", name="source"),
        Index("uq_grade_components_company_eval", "cycle_id", unique=True,
              postgresql_where=text("source = 'company_final_evaluation'")),
    )


class RubricCriterion(Base):
    __tablename__ = "rubric_criteria"
    id: Mapped[uuid.UUID] = uuid_pk()
    cycle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_cycles.id"), nullable=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    name_ar: Mapped[str] = mapped_column(Text, nullable=False)
    levels: Mapped[dict] = mapped_column(JSONB, nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    __table_args__ = (UniqueConstraint("cycle_id", "position"),)


class Enrollment(Base):
    __tablename__ = "enrollments"
    cycle_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("training_cycles.id"), primary_key=True)
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    verification_request_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("verification_requests.id"))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = created_at()
