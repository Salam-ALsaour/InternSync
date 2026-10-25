"""API 3.11 – Attendance (FR-ATT-01 – 04)."""
import uuid
from datetime import date, datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.attendance import service
from app.core.common import get_or_404
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import forbidden
from app.core.scope import placement_access
from app.models import Placement

router = APIRouter(tags=["attendance"])


class AttendanceWeekOut(BaseModel):
    week_no: int
    starts_on: date
    ends_on: date
    scheduled_days: int
    attended_days: int | None
    note: str | None
    state: str
    locked: bool
    recorded_at: datetime | None
    recorded_by_en: str | None
    recorded_by_ar: str | None
    unlocked_until: datetime | None


class AttendanceOut(BaseModel):
    placement_id: uuid.UUID
    weeks: list[AttendanceWeekOut]
    attended_days: int
    scheduled_days: int
    percent: float | None
    can_record: bool
    can_unlock: bool


class AttendanceIn(BaseModel):
    full: bool = False
    attended_days: int | None = Field(None, ge=0, le=7)
    note: str | None = Field(None, max_length=500)


class UnlockIn(BaseModel):
    reason: str = Field("", max_length=1000)
    until: datetime | None = None


def _out(db: Session, actor: Actor, p: Placement, relation: str) -> dict:
    active = p.status == "active"
    return {**service.summary(db, p), "can_record": active and p.company_supervisor_id == actor.id,
            "can_unlock": active and relation == "co"}


@router.get("/placements/{placement_id}/attendance", response_model=AttendanceOut)
def get_attendance(placement_id: uuid.UUID, actor: Actor = Depends(auth("st", "cs", "as", "co")),
                   db: Session = Depends(get_db)):
    p = get_or_404(db, Placement, placement_id)
    return _out(db, actor, p, placement_access(db, actor, p))


@router.put("/placements/{placement_id}/attendance/{week_no}", response_model=AttendanceOut)
def record_week(placement_id: uuid.UUID, week_no: int, body: AttendanceIn, actor: Actor = Depends(auth("cs")),
                db: Session = Depends(get_db)):
    p = get_or_404(db, Placement, placement_id)
    relation = placement_access(db, actor, p)
    service.record(db, actor, p, week_no, body.full, body.attended_days, body.note)
    db.commit()
    return _out(db, actor, p, relation)


@router.post("/placements/{placement_id}/attendance/{week_no}/unlock", response_model=AttendanceOut)
def unlock_week(placement_id: uuid.UUID, week_no: int, body: UnlockIn, actor: Actor = Depends(auth("co")),
                db: Session = Depends(get_db)):
    p = get_or_404(db, Placement, placement_id)
    relation = placement_access(db, actor, p)
    if relation != "co":
        raise forbidden()
    service.unlock(db, actor, p, week_no, body.reason, body.until)
    db.commit()
    return _out(db, actor, p, relation)
