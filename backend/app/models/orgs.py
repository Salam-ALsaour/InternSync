"""Organizations, accounts, and access (Design 4.3.1)."""
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Index, Numeric, SmallInteger, String, Text, func, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import created_at, ts, updated_at, uuid_pk

ROLES = ("student", "company_supervisor", "academic_supervisor", "coordinator", "platform_admin")


class University(Base):
    __tablename__ = "universities"
    id: Mapped[uuid.UUID] = uuid_pk()
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    name_ar: Mapped[str] = mapped_column(Text, nullable=False)
    email_domains: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default=text("'{}'"),
                                                     default=list)
    gpa_scale: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, server_default=text("5.00"),
                                               default=Decimal("5.00"))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    created_at: Mapped[datetime] = created_at()
    __table_args__ = (
        CheckConstraint("gpa_scale IN (4.00, 5.00)", name="gpa_scale"),
        Index("uq_universities_lower_name_en", func.lower(text("name_en")), unique=True),
    )


class College(Base):
    __tablename__ = "colleges"
    id: Mapped[uuid.UUID] = uuid_pk()
    university_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("universities.id"), nullable=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    name_ar: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    # NFR-PRV-04: months after a cycle closes before its personal data may be anonymized (Increment 4, RQ-5)
    retention_months: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="12", default=12)
    created_at: Mapped[datetime] = created_at()
    __table_args__ = (
        Index("uq_colleges_university_lower_name_en", "university_id", func.lower(text("name_en")), unique=True),
        CheckConstraint("retention_months BETWEEN 0 AND 120", name="retention_months"),
    )


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    commercial_reg_no: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    city: Mapped[str] = mapped_column(Text, nullable=False)
    website: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending", default="pending")
    verified_at: Mapped[datetime | None] = ts()
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (CheckConstraint("status IN ('pending','verified','rejected','suspended')", name="status"),)


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = uuid_pk()
    email: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str | None] = mapped_column(Text)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[str] = mapped_column(Text, nullable=False)
    name_ar: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(2), nullable=False, server_default="ar", default="ar")
    college_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("colleges.id"))
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id"))
    is_company_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"),
                                                   default=False)
    email_confirmed_at: Mapped[datetime | None] = ts()
    verification_status: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"), default=True)
    failed_logins: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default="0", default=0)
    locked_until: Mapped[datetime | None] = ts()
    consent_at: Mapped[datetime | None] = ts()
    last_login_at: Mapped[datetime | None] = ts()
    anonymized_at: Mapped[datetime | None] = ts()  # NFR-PRV-04
    created_at: Mapped[datetime] = created_at()
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (
        CheckConstraint(f"role IN {ROLES}", name="role"),
        CheckConstraint("language IN ('ar','en')", name="language"),
        CheckConstraint("verification_status IN ('pending','verified','rejected','not_required')",
                        name="verification_status"),
        CheckConstraint("(college_id IS NOT NULL) = (role IN ('student','academic_supervisor','coordinator'))",
                        name="college_scope"),
        CheckConstraint("(company_id IS NOT NULL) = (role = 'company_supervisor')", name="company_scope"),
        CheckConstraint("NOT is_company_admin OR role = 'company_supervisor'", name="company_admin_role"),
        Index("uq_users_lower_email", func.lower(text("email")), unique=True),
        Index("uq_users_company_admin", "company_id", unique=True, postgresql_where=text("is_company_admin")),
        Index("uq_users_college_coordinator", "college_id", unique=True,
              postgresql_where=text("role = 'coordinator' AND verification_status = 'verified' AND is_active")),
    )


class AccountToken(Base):
    __tablename__ = "account_tokens"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[datetime] = ts(nullable=False)
    used_at: Mapped[datetime | None] = ts()
    revoked_at: Mapped[datetime | None] = ts()
    created_at: Mapped[datetime] = created_at()
    __table_args__ = (
        CheckConstraint("purpose IN ('email_confirmation','invitation','password_reset')", name="purpose"),
    )


class VerificationRequest(Base):
    __tablename__ = "verification_requests"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    college_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("colleges.id"))
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id"))
    submitted_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default="pending", default="pending")
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    decided_at: Mapped[datetime | None] = ts()
    reason: Mapped[str | None] = mapped_column(Text)
    cycle_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("training_cycles.id"))
    created_at: Mapped[datetime] = created_at()
    __table_args__ = (
        CheckConstraint("kind IN ('coordinator','company','student')", name="kind"),
        CheckConstraint("status IN ('pending','approved','rejected')", name="status"),
        CheckConstraint("status <> 'rejected' OR (reason IS NOT NULL AND length(trim(reason)) > 0)",
                        name="reason_when_rejected"),
        Index("uq_verification_requests_pending_user", "user_id", unique=True,
              postgresql_where=text("status = 'pending'")),
    )


class VerificationDocument(Base):
    __tablename__ = "verification_documents"
    id: Mapped[uuid.UUID] = uuid_pk()
    request_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("verification_requests.id"), nullable=False)
    kind: Mapped[str] = mapped_column(Text, nullable=False)
    file_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("files.id"))
    purged_at: Mapped[datetime | None] = ts()
    __table_args__ = (
        CheckConstraint("kind IN ('appointment_letter','commercial_registration','authorization_letter',"
                        "'course_registration','other')", name="kind"),
    )


class UserSession(Base):
    __tablename__ = "user_sessions"
    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = created_at()
    last_seen_at: Mapped[datetime] = ts(nullable=False)
    expires_at: Mapped[datetime] = ts(nullable=False)
    revoked_at: Mapped[datetime | None] = ts()
    revoke_reason: Mapped[str | None] = mapped_column(Text)
    user_agent: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        CheckConstraint("revoke_reason IS NULL OR revoke_reason IN "
                        "('logout','idle','password_reset','deactivated','expired')", name="revoke_reason"),
    )
