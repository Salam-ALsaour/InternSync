"""Certificates: issue, revoke, and the public check (FR-CER-01 – 03; Increment 4 design, Section 4)."""
import base64
import re
import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.certificates import pdf
from app.core import audit, clock, files
from app.core.config import get_settings
from app.core.deps import Actor
from app.core.errors import ApiError, conflict, forbidden
from app.models import (
    Certificate,
    College,
    Company,
    Grade,
    Placement,
    TrainingCycle,
    University,
    User,
    Vacancy,
)
from app.notifications import events

CODE_LENGTH = 26
_NOT_CODE = re.compile(r"[\s-]+")


def new_code() -> str:
    """128 random bits in base32 without padding: 26 characters of A–Z and 2–7."""
    return base64.b32encode(secrets.token_bytes(16)).decode("ascii").rstrip("=")


def normalize(code: str) -> str:
    return _NOT_CODE.sub("", code or "").upper()


def verify_url(code: str) -> str:
    return f"{get_settings().frontend_base_url.rstrip('/')}/verify/{code}"


def _context(db: Session, p: Placement) -> dict:
    student = db.get(User, p.student_id)
    college = db.get(College, student.college_id)
    vacancy = db.get(Vacancy, p.vacancy_id)
    return {"student": student, "college": college, "university": db.get(University, college.university_id),
            "cycle": db.get(TrainingCycle, p.cycle_id), "vacancy": vacancy,
            "company": db.get(Company, vacancy.company_id)}


def _ensure_coordinator(db: Session, actor: Actor, p: Placement) -> None:
    if db.get(User, p.student_id).college_id != actor.user.college_id:
        raise forbidden()


def current(db: Session, p: Placement) -> Certificate | None:
    """The valid certificate, else the latest revoked one."""
    return db.scalar(select(Certificate).where(Certificate.placement_id == p.id)
                     .order_by((Certificate.status == "valid").desc(), Certificate.issued_at.desc()).limit(1))


def issue(db: Session, actor: Actor, p: Placement) -> Certificate:
    """FR-CER-01: only for a Final grade and when no valid certificate exists."""
    _ensure_coordinator(db, actor, p)
    if db.scalar(select(Grade.status).where(Grade.placement_id == p.id)) != "final":
        raise conflict("GRADE_NOT_FINAL")
    if db.scalar(select(Certificate.id).where(Certificate.placement_id == p.id, Certificate.status == "valid")):
        raise conflict("CERTIFICATE_EXISTS")
    c = _context(db, p)
    if c["student"].anonymized_at is not None:
        raise conflict("ALREADY_ANONYMIZED")
    code, now = new_code(), clock.now()
    data = pdf.render(pdf.Facts(
        code=code, url=verify_url(code), name_en=c["student"].name_en, name_ar=c["student"].name_ar,
        university_en=c["university"].name_en, university_ar=c["university"].name_ar,
        college_en=c["college"].name_en, college_ar=c["college"].name_ar, cycle=c["cycle"].name,
        training_type=c["cycle"].type, company=c["company"].name, start=c["vacancy"].training_start,
        end=c["vacancy"].training_end, issued_at=now))
    stored = files.store(db, data, f"certificate-{code}.pdf", "certificate", {files.PDF}, actor.user)
    cert = Certificate(placement_id=p.id, code=code, file_id=stored.id, status="valid", issued_by=actor.id,
                       issued_at=now)
    db.add(cert)
    db.flush()
    audit.record(db, actor.user, "issue", "certificate", cert.id, student_id=p.student_id,
                 college_id=c["college"].id, cycle_id=p.cycle_id, new={"status": "valid", "placement_id": str(p.id)})
    events.certificate_event(db, "certificate.issued", p)
    return cert


def revoke(db: Session, actor: Actor, cert: Certificate, reason: str) -> Certificate:
    """FR-CER-03: with a reason; a new certificate can be issued afterwards."""
    p = db.get(Placement, cert.placement_id)
    _ensure_coordinator(db, actor, p)
    if cert.status != "valid":
        raise conflict("CERTIFICATE_REVOKED")
    reason = (reason or "").strip()
    if not reason:
        raise ApiError(422, "REASON_REQUIRED")
    cert.status, cert.revoked_by, cert.revoked_at, cert.revoke_reason = "revoked", actor.id, clock.now(), reason
    student = db.get(User, p.student_id)
    audit.record(db, actor.user, "revoke", "certificate", cert.id, student_id=student.id,
                 college_id=student.college_id, cycle_id=p.cycle_id, old={"status": "valid"},
                 new={"status": "revoked"}, reason=reason)
    events.certificate_event(db, "certificate.revoked", p, reason=reason)
    return cert


def out(db: Session, cert: Certificate, relation: str) -> dict:
    p = db.get(Placement, cert.placement_id)
    c = _context(db, p)
    valid = cert.status == "valid"
    return {"id": cert.id, "placement_id": p.id, "code": cert.code, "status": cert.status,
            "verify_url": verify_url(cert.code), "file_id": cert.file_id, "issued_at": cert.issued_at,
            "revoked_at": cert.revoked_at, "revoke_reason": cert.revoke_reason,
            "student": {"id": c["student"].id, "name_en": c["student"].name_en, "name_ar": c["student"].name_ar},
            "cycle": c["cycle"].name, "company": c["company"].name,
            "can_revoke": relation == "co" and valid}


def placement_view(db: Session, p: Placement, relation: str) -> dict:
    cert = current(db, p)
    final = db.scalar(select(Grade.status).where(Grade.placement_id == p.id)) == "final"
    has_valid = cert is not None and cert.status == "valid"
    return {"certificate": out(db, cert, relation) if cert else None,
            "can_issue": relation == "co" and final and not has_valid}


def listing(db: Session, actor: Actor, cycle_id: uuid.UUID | None, status: str | None) -> list[dict]:
    stmt = (select(Certificate).join(Placement, Placement.id == Certificate.placement_id)
            .join(User, User.id == Placement.student_id).where(User.college_id == actor.user.college_id)
            .order_by((Certificate.status == "valid").desc(), Certificate.issued_at.desc()))
    if cycle_id:
        stmt = stmt.where(Placement.cycle_id == cycle_id)
    if status:
        stmt = stmt.where(Certificate.status == status)
    return [out(db, c, "co") for c in db.scalars(stmt)]


def public(db: Session, code: str) -> dict:
    """FR-CER-02: status, name, university and college, cycle, company, and training dates; never the grade."""
    code = normalize(code)
    cert = db.scalar(select(Certificate).where(Certificate.code == code)) if len(code) == CODE_LENGTH else None
    if cert is None:
        return {"status": "not_found"}
    c = _context(db, db.get(Placement, cert.placement_id))
    removed = c["student"].anonymized_at is not None
    return {"status": cert.status, "name_removed": removed,
            "student_name": None if removed else {"en": c["student"].name_en, "ar": c["student"].name_ar},
            "university": {"en": c["university"].name_en, "ar": c["university"].name_ar},
            "college": {"en": c["college"].name_en, "ar": c["college"].name_ar},
            "cycle": c["cycle"].name, "company": c["company"].name,
            "training_start": c["vacancy"].training_start, "training_end": c["vacancy"].training_end}
