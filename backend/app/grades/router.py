"""API 3.13 – Grades (FR-WFL-02 – 07)."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.common import get_or_404
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import forbidden
from app.core.scope import placement_access
from app.grades import service
from app.models import Grade, Placement

router = APIRouter(tags=["grades"])


class ComponentOut(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str
    weight: Decimal
    source: str
    computed: bool
    score: Decimal | None


class Check(BaseModel):
    item: str
    ok: bool
    week_no: int | None
    component_id: uuid.UUID | None


class GradeOut(BaseModel):
    visible: bool
    status: str | None
    id: uuid.UUID | None = None
    placement_id: uuid.UUID | None = None
    components: list[ComponentOut] = []
    total: Decimal | None = None
    preconditions: list[Check] = []
    submitted_at: datetime | None = None
    approved_at: datetime | None = None
    return_comment: str | None = None
    reopen_reason: str | None = None
    can_edit: bool = False
    can_submit: bool = False
    can_decide: bool = False
    can_reopen: bool = False


class ScoreIn(BaseModel):
    component_id: uuid.UUID
    score: Decimal = Field(ge=0, le=100, max_digits=5, decimal_places=2)


class ScoresIn(BaseModel):
    component_scores: list[ScoreIn] = Field(max_length=10)


class GradeCommentIn(BaseModel):
    comment: str = Field("", max_length=2000)


class ReasonIn(BaseModel):
    reason: str = Field("", max_length=1000)


class BulkIn(BaseModel):
    grade_ids: list[uuid.UUID] = Field(min_length=1, max_length=200)


class BulkResult(BaseModel):
    grade_id: uuid.UUID
    ok: bool
    code: str | None


class Ref(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str


class GradeRow(BaseModel):
    id: uuid.UUID
    placement_id: uuid.UUID
    status: str
    total: Decimal | None
    student: Ref
    company_name: str
    submitted_at: datetime | None
    approved_at: datetime | None


def _placement(db: Session, actor: Actor, placement_id: uuid.UUID):
    p = get_or_404(db, Placement, placement_id)
    relation = placement_access(db, actor, p)
    if relation == "cs":  # the company sees evaluations, not grades
        raise forbidden()
    return p, relation, service.grade_for(db, p)


def _by_id(db: Session, actor: Actor, grade_id: uuid.UUID):
    g = get_or_404(db, Grade, grade_id)
    p = db.get(Placement, g.placement_id)
    relation = placement_access(db, actor, p)
    if relation not in ("as", "co"):
        raise forbidden()
    return g, p, relation


@router.get("/placements/{placement_id}/grade", response_model=GradeOut)
def get_grade(placement_id: uuid.UUID, actor: Actor = Depends(auth("st", "as", "co")), db: Session = Depends(get_db)):
    p, relation, g = _placement(db, actor, placement_id)
    out = service.view(db, actor, g, p, relation)
    db.commit()
    return out


@router.put("/placements/{placement_id}/grade", response_model=GradeOut)
def put_grade(placement_id: uuid.UUID, body: ScoresIn, actor: Actor = Depends(auth("as")),
              db: Session = Depends(get_db)):
    p, relation, g = _placement(db, actor, placement_id)
    service.save_scores(db, actor, g, p, [s.model_dump() for s in body.component_scores])
    db.commit()
    return service.view(db, actor, g, p, relation)


@router.get("/placements/{placement_id}/grade/preconditions", response_model=list[Check])
def get_preconditions(placement_id: uuid.UUID, actor: Actor = Depends(auth("as", "co")),
                      db: Session = Depends(get_db)):
    p, _, g = _placement(db, actor, placement_id)
    return service.preconditions(db, g, p)


@router.post("/grades/{grade_id}/submit", response_model=GradeOut)
def submit_grade(grade_id: uuid.UUID, actor: Actor = Depends(auth("as")), db: Session = Depends(get_db)):
    g, p, relation = _by_id(db, actor, grade_id)
    service.submit(db, actor, g, p)
    db.commit()
    return service.view(db, actor, g, p, relation)


@router.post("/grades/{grade_id}/approve", response_model=GradeOut)
def approve_grade(grade_id: uuid.UUID, actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    g, p, relation = _by_id(db, actor, grade_id)
    service.approve(db, actor, g, p)
    db.commit()
    return service.view(db, actor, g, p, relation)


@router.post("/grades/{grade_id}/return", response_model=GradeOut)
def return_grade(grade_id: uuid.UUID, body: GradeCommentIn, actor: Actor = Depends(auth("co")),
                 db: Session = Depends(get_db)):
    g, p, relation = _by_id(db, actor, grade_id)
    service.return_grade(db, actor, g, p, body.comment)
    db.commit()
    return service.view(db, actor, g, p, relation)


@router.post("/grades/{grade_id}/reopen", response_model=GradeOut)
def reopen_grade(grade_id: uuid.UUID, body: ReasonIn, actor: Actor = Depends(auth("co")),
                 db: Session = Depends(get_db)):
    g, p, relation = _by_id(db, actor, grade_id)
    service.reopen(db, actor, g, p, body.reason)
    db.commit()
    return service.view(db, actor, g, p, relation)


@router.post("/grades/bulk-approve", response_model=list[BulkResult])
def bulk_approve(body: BulkIn, actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    out = service.bulk_approve(db, actor, body.grade_ids)
    db.commit()
    return out


@router.get("/grades", response_model=list[GradeRow])
def list_grades(cycle_id: uuid.UUID | None = None,
                status: Literal["draft", "submitted", "final"] | None = None,
                actor: Actor = Depends(auth("as", "co")), db: Session = Depends(get_db)):
    return service.listing(db, actor, cycle_id, status)
