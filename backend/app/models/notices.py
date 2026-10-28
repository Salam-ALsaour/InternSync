"""Notifications, push subscriptions, and similarity (Design 4.3.1, 4.3.5, 4.3.8; Increment 3 design, Section 2)."""
import uuid
from datetime import datetime
from decimal import Decimal

from pgvector.sqlalchemy import HALFVEC
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import created_at, ts, uuid_pk

DELIVERY = "('pending','sent','failed','skipped')"


class Notification(Base):
    """One message to one user: the in-app list and the outbox of email and push (FR-NOT-01 – 06)."""
    __tablename__ = "notifications"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    event: Mapped[str] = mapped_column(Text, nullable=False)
    params: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"), default=dict)
    link: Mapped[str | None] = mapped_column(Text)
    idempotency_key: Mapped[str | None] = mapped_column(Text, unique=True)
    read_at: Mapped[datetime | None] = ts()
    email_status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"), default="pending")
    push_status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"), default="pending")
    emailed_at: Mapped[datetime | None] = ts()
    pushed_at: Mapped[datetime | None] = ts()
    email_attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"), default=0)
    created_at: Mapped[datetime] = created_at()
    __table_args__ = (
        CheckConstraint(f"email_status IN {DELIVERY}", name="email_status"),
        CheckConstraint(f"push_status IN {DELIVERY}", name="push_status"),
        Index("ix_notifications_user_read", "user_id", "read_at"),
        Index("ix_notifications_outbox", "created_at",
              postgresql_where=text("email_status = 'pending' OR push_status = 'pending'")),
    )


class PushSubscription(Base):
    """A browser's web push endpoint (FR-PWA-02)."""
    __tablename__ = "push_subscriptions"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    p256dh: Mapped[str] = mapped_column(Text, nullable=False)
    auth: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = created_at()
    last_success_at: Mapped[datetime | None] = ts()


class ReportPassage(Base):
    """A passage of a submitted report version with its embedding (FR-SIM-01)."""
    __tablename__ = "report_passages"
    id: Mapped[int] = mapped_column(BigInteger, Identity(always=True), primary_key=True)
    version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("report_versions.id"), nullable=False, index=True)
    slot_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("report_slots.id"), nullable=False)
    university_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("universities.id"), nullable=False)
    idx: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    char_start: Mapped[int] = mapped_column(Integer, nullable=False)
    char_end: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding = mapped_column(HALFVEC(384), nullable=False)
    __table_args__ = (
        Index("ix_report_passages_embedding", "embedding", postgresql_using="hnsw",
              postgresql_ops={"embedding": "halfvec_cosine_ops"}),
    )


class SimilarityCheck(Base):
    """One check per submitted version, with the supervisor's advisory decision (FR-SIM-01 – 03)."""
    __tablename__ = "similarity_checks"
    id: Mapped[uuid.UUID] = uuid_pk()
    version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("report_versions.id"), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'pending'"), default="pending")
    max_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    is_flagged: Mapped[bool] = mapped_column(nullable=False, server_default=text("false"), default=False)
    threshold: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False)
    model_version: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("0"), default=0)
    created_at: Mapped[datetime] = created_at()
    started_at: Mapped[datetime | None] = ts()
    finished_at: Mapped[datetime | None] = ts()
    error: Mapped[str | None] = mapped_column(Text)
    decision: Mapped[str | None] = mapped_column(Text)
    decision_comment: Mapped[str | None] = mapped_column(Text)
    decided_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = ts()
    __table_args__ = (
        CheckConstraint("status IN ('pending','done','failed')", name="status"),
        CheckConstraint("decision IS NULL OR decision IN ('no_issue','overlap_confirmed')", name="decision"),
        CheckConstraint("(decision IS NULL) = (decision_comment IS NULL)", name="decision_comment"),
    )


class SimilarityMatch(Base):
    """Overlap with one source report version, with the passage pairs (FR-SIM-02)."""
    __tablename__ = "similarity_matches"
    id: Mapped[uuid.UUID] = uuid_pk()
    check_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("similarity_checks.id", ondelete="CASCADE"), nullable=False)
    source_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("report_versions.id"), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    passages: Mapped[list] = mapped_column(JSONB, nullable=False)
    __table_args__ = (UniqueConstraint("check_id", "source_version_id"),)
