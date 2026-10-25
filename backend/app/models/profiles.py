"""Student profiles, CVs, and skills (Design 4.3.3)."""
import uuid
from datetime import datetime
from decimal import Decimal

from pgvector.sqlalchemy import HALFVEC
from sqlalchemy import CheckConstraint, ForeignKey, Numeric, SmallInteger, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models._base import ts, updated_at, uuid_pk


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    student_number: Mapped[str] = mapped_column(Text, nullable=False)
    major_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("majors.id"), nullable=False)
    gpa: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    level: Mapped[int | None] = mapped_column(SmallInteger)
    languages: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default=text("'{}'"),
                                                 default=list)
    interests: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default=text("'{}'"),
                                                 default=list)
    skills_confirmed_at: Mapped[datetime | None] = ts()
    embedding = mapped_column(HALFVEC(384))  # profile text embedding (Design 6.2)
    embedding_model: Mapped[str | None] = mapped_column(Text)
    embedded_at: Mapped[datetime | None] = ts()
    updated_at: Mapped[datetime] = updated_at()
    __table_args__ = (
        CheckConstraint("length(student_number) BETWEEN 4 AND 20", name="student_number"),
        CheckConstraint("gpa >= 0 AND gpa <= 5", name="gpa"),
    )


class Cv(Base):
    __tablename__ = "cvs"
    id: Mapped[uuid.UUID] = uuid_pk()
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    version_no: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    file_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("files.id"), nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    text_status: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(Text)
    uploaded_at: Mapped[datetime] = ts(nullable=False)
    __table_args__ = (
        UniqueConstraint("student_id", "version_no"),
        CheckConstraint("text_status IN ('ok','no_text','failed')", name="text_status"),
        CheckConstraint("language IS NULL OR language IN ('ar','en','mixed')", name="language"),
    )


class CvExtractedSkill(Base):
    __tablename__ = "cv_extracted_skills"
    cv_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cvs.id"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    evidence: Mapped[str | None] = mapped_column(Text)


class StudentSkill(Base):
    __tablename__ = "student_skills"
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)
    skill_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("skills.id"), primary_key=True)
    source: Mapped[str] = mapped_column(Text, nullable=False)
    confirmed_at: Mapped[datetime] = ts(nullable=False)
    __table_args__ = (CheckConstraint("source IN ('extracted','manual')", name="source"),)
