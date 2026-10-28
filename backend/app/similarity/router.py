"""API 3.10 – Similarity (FR-SIM-01 – 03)."""
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
from app.models import ReportVersion
from app.similarity import service

router = APIRouter(tags=["similarity"])


class PassagePair(BaseModel):
    report: list[int]
    source: list[int]
    cosine: float
    report_text: str
    source_text: str


class Author(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str
    student_number: str | None


class SimilaritySource(BaseModel):
    version_id: uuid.UUID
    slot_id: uuid.UUID
    kind: str
    week_no: int | None
    version_no: int
    cycle_id: uuid.UUID
    cycle_name: str
    score: Decimal
    author: Author | None  # only for the coordinator of the author's college (FR-SIM-02)
    passages: list[PassagePair]


class SimilarityResult(BaseModel):
    status: str  # none, pending, done, failed
    advisory: bool
    max_score: Decimal | None = None
    is_flagged: bool | None = None
    threshold: Decimal | None = None
    model_version: str | None = None
    checked_at: datetime | None = None
    error: str | None = None
    decision: str | None = None
    decision_comment: str | None = None
    decided_at: datetime | None = None
    decided_by_en: str | None = None
    decided_by_ar: str | None = None
    can_decide: bool
    sources: list[SimilaritySource]


class DecisionIn(BaseModel):
    decision: Literal["no_issue", "overlap_confirmed"]
    comment: str = Field(max_length=2000)


class StudentRef(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str


class SimilarityCheckItem(BaseModel):
    check_id: uuid.UUID
    version_id: uuid.UUID
    slot_id: uuid.UUID
    placement_id: uuid.UUID
    kind: str
    week_no: int | None
    version_no: int
    student: StudentRef
    status: str
    max_score: Decimal | None
    is_flagged: bool
    decision: str | None
    checked_at: datetime | None


@router.get("/report-versions/{version_id}/similarity", response_model=SimilarityResult)
def get_result(version_id: uuid.UUID, actor: Actor = Depends(auth("as", "co")), db: Session = Depends(get_db)):
    return service.result(db, actor, get_or_404(db, ReportVersion, version_id))


@router.post("/report-versions/{version_id}/similarity/decision", response_model=SimilarityResult)
def record_decision(version_id: uuid.UUID, body: DecisionIn, actor: Actor = Depends(auth("as")),
                    db: Session = Depends(get_db)):
    version = get_or_404(db, ReportVersion, version_id)
    service.decide(db, actor, version, body.decision, body.comment)
    db.commit()
    return service.result(db, actor, version)


@router.get("/similarity-checks", response_model=list[SimilarityCheckItem])
def list_checks(cycle_id: uuid.UUID | None = None, flagged: bool | None = None, decided: bool | None = None,
                actor: Actor = Depends(auth("as", "co")), db: Session = Depends(get_db)):
    return service.listing(db, actor, cycle_id, flagged, decided)
