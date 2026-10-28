"""API 3.18 – History of a report, an evaluation, or a grade (FR-AUD-03; Increment 3 design, Section 8).

The entries are the record's audit log, shown to whoever may view the record itself. A student does not see the
similarity decision on a report (the check is for supervisors)."""
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.common import get_or_404
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import forbidden
from app.core.scope import placement_access
from app.evaluations.service import visible_to
from app.models import AuditEntry, Evaluation, Grade, Placement, ReportSlot, User

router = APIRouter(tags=["audit"])
HIDDEN_FROM_STUDENT = {"similarity_decision"}


class HistoryEntry(BaseModel):
    at: datetime
    action: str
    role: str
    user_en: str | None
    user_ar: str | None
    old: dict | None
    new: dict | None
    reason: str | None


def _relation(db: Session, actor: Actor, entity_type: str, entity_id: uuid.UUID) -> str:
    if entity_type == "report_slot":
        slot = get_or_404(db, ReportSlot, entity_id)
        return placement_access(db, actor, db.get(Placement, slot.placement_id))
    if entity_type == "evaluation":
        e = get_or_404(db, Evaluation, entity_id)
        placement = db.get(Placement, e.placement_id)
        relation = placement_access(db, actor, placement)
        if not visible_to(db, relation, actor, placement, e):
            raise forbidden()
        return relation
    grade = get_or_404(db, Grade, entity_id)
    placement = db.get(Placement, grade.placement_id)
    relation = placement_access(db, actor, placement)
    if relation == "cs" or (relation == "st" and grade.status != "final"):  # FR-WFL-06
        raise forbidden()
    return relation


@router.get("/history/{entity_type}/{entity_id}", response_model=list[HistoryEntry])
def history(entity_type: Literal["report_slot", "evaluation", "grade"], entity_id: uuid.UUID,
            actor: Actor = Depends(auth("st", "cs", "as", "co")), db: Session = Depends(get_db)):
    relation = _relation(db, actor, entity_type, entity_id)
    rows = db.execute(select(AuditEntry, User).outerjoin(User, User.id == AuditEntry.user_id)
                      .where(AuditEntry.entity_type == entity_type, AuditEntry.entity_id == str(entity_id))
                      .order_by(AuditEntry.at, AuditEntry.id)).all()
    return [{"at": e.at, "action": e.action, "role": e.role, "user_en": u.name_en if u else None,
             "user_ar": u.name_ar if u else None, "old": e.old_value, "new": e.new_value, "reason": e.reason}
            for e, u in rows if not (relation == "st" and e.action in HIDDEN_FROM_STUDENT)]
