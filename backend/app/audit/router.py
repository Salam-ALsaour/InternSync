"""API 3.18 – Audit log (FR-AUD-02). Read-only: no update or delete endpoint exists."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.common import Page, PageParams, paginate
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.models import AuditEntry, User

router = APIRouter(tags=["audit"])

PLATFORM_TYPES = ("user", "university", "college", "company", "verification_request", "skill", "major", "settings")


class AuditOut(BaseModel):
    id: int
    at: datetime
    user_id: uuid.UUID | None
    user_en: str | None
    user_ar: str | None
    role: str
    action: str
    entity_type: str
    entity_id: str
    student_id: uuid.UUID | None
    student_en: str | None
    student_ar: str | None
    old_value: dict | None
    new_value: dict | None
    reason: str | None


@router.get("/audit-log", response_model=Page[AuditOut])
def audit_log(student_id: uuid.UUID | None = None, user_id: uuid.UUID | None = None, entity_type: str | None = None,
              entity_id: str | None = None, date_from: datetime | None = None, date_to: datetime | None = None,
              params: PageParams = Depends(), actor: Actor = Depends(auth("co", "pa")), db: Session = Depends(get_db)):
    stmt = select(AuditEntry).order_by(AuditEntry.at.desc(), AuditEntry.id.desc())
    if actor.code == "co":
        stmt = stmt.where(AuditEntry.college_id == actor.user.college_id)
    else:
        stmt = stmt.where(AuditEntry.entity_type.in_(PLATFORM_TYPES))
    if student_id:
        stmt = stmt.where(AuditEntry.student_id == student_id)
    if user_id:
        stmt = stmt.where(AuditEntry.user_id == user_id)
    if entity_type:
        stmt = stmt.where(AuditEntry.entity_type == entity_type)
    if entity_id:
        stmt = stmt.where(AuditEntry.entity_id == entity_id)
    if date_from:
        stmt = stmt.where(AuditEntry.at >= date_from)
    if date_to:
        stmt = stmt.where(AuditEntry.at <= date_to)
    names: dict = {}

    def name(uid):
        if uid is None:
            return None
        if uid not in names:
            names[uid] = db.get(User, uid)
        return names[uid]

    def out(e: AuditEntry) -> dict:
        u, s = name(e.user_id), name(e.student_id)
        # The log is append-only; the entries of an anonymized student are shown without their values (NFR-PRV-04).
        masked = any(x is not None and x.anonymized_at is not None for x in (u, s))
        return {"id": e.id, "at": e.at, "user_id": e.user_id, "user_en": u.name_en if u else None,
                "user_ar": u.name_ar if u else None, "role": e.role, "action": e.action, "entity_type": e.entity_type,
                "entity_id": e.entity_id, "student_id": e.student_id, "student_en": s.name_en if s else None,
                "student_ar": s.name_ar if s else None, "old_value": None if masked else e.old_value,
                "new_value": None if masked else e.new_value, "reason": None if masked else e.reason}
    return paginate(db, stmt, params, out)
