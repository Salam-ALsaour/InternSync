"""Retention period and anonymization (NFR-PRV-04; Increment 4 design, Sections 3 and 7). Coordinator only."""
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.common import get_or_404
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import ApiError, forbidden
from app.models import College, TrainingCycle
from app.privacy import service

router = APIRouter(tags=["privacy"])


class Retention(BaseModel):
    retention_months: int = Field(ge=0, le=120)


class Anonymization(BaseModel):
    cycle_id: uuid.UUID
    status: Literal["open", "waiting", "ready", "done"]
    closed_at: datetime | None
    eligible_at: datetime | None
    retention_months: int
    students: int
    skipped: int
    anonymized_at: datetime | None


class ConfirmIn(BaseModel):
    confirm: bool = False


def _own_college(actor: Actor, college_id: uuid.UUID, db: Session) -> College:
    college = get_or_404(db, College, college_id)
    if college.id != actor.user.college_id:
        raise forbidden()
    return college


def _own_cycle(db: Session, actor: Actor, cycle_id: uuid.UUID) -> TrainingCycle:
    cycle = get_or_404(db, TrainingCycle, cycle_id)
    if cycle.college_id != actor.user.college_id:
        raise forbidden()
    return cycle


@router.get("/colleges/{college_id}/retention", response_model=Retention)
def get_retention(college_id: uuid.UUID, actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    return {"retention_months": _own_college(actor, college_id, db).retention_months}


@router.put("/colleges/{college_id}/retention", response_model=Retention)
def put_retention(college_id: uuid.UUID, body: Retention, actor: Actor = Depends(auth("co")),
                  db: Session = Depends(get_db)):
    college = _own_college(actor, college_id, db)
    service.set_retention(db, actor, college, body.retention_months)
    db.commit()
    return {"retention_months": college.retention_months}


@router.get("/cycles/{cycle_id}/anonymization", response_model=Anonymization)
def get_anonymization(cycle_id: uuid.UUID, actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    return service.preview(db, _own_cycle(db, actor, cycle_id))


@router.post("/cycles/{cycle_id}/anonymize", response_model=Anonymization)
def anonymize(cycle_id: uuid.UUID, body: ConfirmIn, actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    cycle = _own_cycle(db, actor, cycle_id)
    if not body.confirm:
        raise ApiError(422, "CONFIRM_REQUIRED")
    out = service.anonymize(db, actor, cycle)
    db.commit()
    return out
