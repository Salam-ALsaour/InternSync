"""Report slots, versions, attachments, reviews, and comments (Design 4.3.5). Similarity tables arrive later."""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, SmallInteger, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import created_at, ts, updated_at, uuid_pk

SLOT_STATES = ("draft", "submitted", "revision_requested", "accepted", "closed_missing")


class ReportSlot(Base):
    __tablename__ = "report_slots"
    id: Mapped[uuid.UUID] = uuid_pk()
    placement_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("placements.id"), nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    week_no: Mapped[int | None] = mapped_column(SmallInteger)
    due_at: Mapped[datetime] = ts(nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="draft", default="draft")
    is_late: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), default=False)
    is_missing: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"), default=False)
    missing_flagged_at: Mapped[datetime | None] = ts()
    accepted_at: Mapped[datetime | None] = ts()
    closed_at: Mapped[datetime | None] = ts()
    closed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (
        CheckConstraint("kind IN ('weekly','final')", name="kind"),
        CheckConstraint("(week_no IS NOT NULL) = (kind = 'weekly')", name="week_no"),
        CheckConstraint(f"status IN {SLOT_STATES}", name="status"),
        Index("ix_report_slots_status_due_at", "status", "due_at"),
        Index("ix_report_slots_placement", "placement_id"),
    )


class ReportVersion(Base):
    __tablename__ = "report_versions"
    id: Mapped[uuid.UUID] = uuid_pk()
    slot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("report_slots.id"), nullable=False)
    version_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    tasks_performed: Mapped[str | None] = mapped_column(Text)
    learning: Mapped[str | None] = mapped_column(Text)
    challenges: Mapped[str | None] = mapped_column(Text)
    next_week_plan: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    body_text: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = ts()
    is_late: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (
        UniqueConstraint("slot_id", "version_no"),
        Index("uq_report_versions_one_draft", "slot_id", unique=True, postgresql_where=text("submitted_at IS NULL")),
    )


class ReportAttachment(Base):
    __tablename__ = "report_attachments"
    id: Mapped[uuid.UUID] = uuid_pk()
    version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("report_versions.id"), nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("files.id"), nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    __table_args__ = (CheckConstraint("role IN ('main','attachment')", name="role"),)


class ReportReview(Base):
    __tablename__ = "report_reviews"
    id: Mapped[uuid.UUID] = uuid_pk()
    version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("report_versions.id"), nullable=False)
    reviewer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    decision: Mapped[str] = mapped_column(Text, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = created_at()
    __table_args__ = (
        CheckConstraint("decision IN ('accepted','revision_requested')", name="decision"),
        CheckConstraint("decision <> 'revision_requested' OR (comment IS NOT NULL AND length(trim(comment)) > 0)",
                        name="comment_required"),
    )


class ReportComment(Base):
    __tablename__ = "report_comments"
    id: Mapped[uuid.UUID] = uuid_pk()
    slot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("report_slots.id"), nullable=False)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = created_at()
    __table_args__ = (CheckConstraint("length(body) BETWEEN 1 AND 2000", name="body"),)
