"""API 3.12 – Evaluations by the company supervisor (FR-EVL-01 – 04), and the student's evaluation of the company
with the job-offer survey (FR-EVL-05, FR-DSH-03)."""
import uuid
from datetime import date, datetime
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
from app.evaluations import feedback, service
from app.models import Evaluation, Placement, TrainingCycle

router = APIRouter(tags=["evaluations"])
Type = Literal["periodic", "final"]


class ScoreIO(BaseModel):
    criterion_id: uuid.UUID
    score: int = Field(ge=1, le=5)


class ScoreOut(ScoreIO):
    name_en: str
    name_ar: str


class EvaluationOut(BaseModel):
    id: uuid.UUID
    type: str
    status: str
    overall_comment: str | None
    mean_score: Decimal | None
    scores: list[ScoreOut]
    submitted_at: datetime | None
    submitted_by_en: str | None
    submitted_by_ar: str | None
    reopen_count: int
    reopened_at: datetime | None
    reopen_reason: str | None


class EvaluationItem(BaseModel):
    type: str
    due_at: datetime
    evaluation: EvaluationOut | None
    can_edit: bool
    can_reopen: bool


class Criterion(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str
    levels: dict


class EvaluationOverview(BaseModel):
    placement_id: uuid.UUID
    rubric: list[Criterion]
    items: list[EvaluationItem]


class EvaluationDraftIn(BaseModel):
    scores: list[ScoreIO] = Field(default_factory=list, max_length=30)
    overall_comment: str | None = Field(None, max_length=4000)


class ReasonIn(BaseModel):
    reason: str = Field("", max_length=1000)


def _placement(db: Session, actor: Actor, placement_id: uuid.UUID) -> tuple[Placement, str]:
    p = get_or_404(db, Placement, placement_id)
    return p, placement_access(db, actor, p)


@router.get("/placements/{placement_id}/evaluations", response_model=EvaluationOverview)
def list_evaluations(placement_id: uuid.UUID, actor: Actor = Depends(auth("st", "cs", "as", "co")),
                     db: Session = Depends(get_db)):
    p, relation = _placement(db, actor, placement_id)
    return service.overview(db, actor, p, relation)


@router.put("/placements/{placement_id}/evaluations/{type}", response_model=EvaluationOverview)
def save_evaluation(placement_id: uuid.UUID, type: Type, body: EvaluationDraftIn, actor: Actor = Depends(auth("cs")),
                    db: Session = Depends(get_db)):
    p, relation = _placement(db, actor, placement_id)
    service.save(db, actor, p, type, [s.model_dump() for s in body.scores], body.overall_comment)
    db.commit()
    return service.overview(db, actor, p, relation)


@router.post("/placements/{placement_id}/evaluations/{type}/submit", response_model=EvaluationOverview)
def submit_evaluation(placement_id: uuid.UUID, type: Type, actor: Actor = Depends(auth("cs")),
                      db: Session = Depends(get_db)):
    p, relation = _placement(db, actor, placement_id)
    service.submit(db, actor, p, type)
    db.commit()
    return service.overview(db, actor, p, relation)


class CompanyEvaluationIn(BaseModel):
    learning_opportunities: int = Field(ge=1, le=5)
    supervision_quality: int = Field(ge=1, le=5)
    work_environment: int = Field(ge=1, le=5)
    relevance_to_major: int = Field(ge=1, le=5)
    would_recommend: bool
    comment: str | None = Field(None, max_length=2000)


class CompanyEvaluationOut(CompanyEvaluationIn):
    submitted_at: datetime


class SurveyIn(BaseModel):
    job_offer: Literal["yes", "no", "pending"]


class SurveyOut(SurveyIn):
    submitted_at: datetime
    updated_at: datetime


class Feedback(BaseModel):
    placement_id: uuid.UUID
    company: str
    vacancy: str
    open_from: date
    is_open: bool
    evaluation: CompanyEvaluationOut | None
    survey: SurveyOut | None
    can_evaluate: bool
    can_answer: bool


class RatingFigures(BaseModel):
    answers: int
    learning_opportunities: Decimal | None
    supervision_quality: Decimal | None
    work_environment: Decimal | None
    relevance_to_major: Decimal | None
    recommend_rate: float | None


class CompanyRatingFigures(RatingFigures):
    company_id: uuid.UUID
    company_name: str


class CompanyEvaluationSummary(BaseModel):
    cycle_id: uuid.UUID
    overall: RatingFigures
    companies: list[CompanyRatingFigures]


def _feedback(db: Session, actor: Actor, placement_id: uuid.UUID) -> tuple[Placement, dict]:
    p, relation = _placement(db, actor, placement_id)
    return p, feedback.view(db, p, relation)


@router.get("/placements/{placement_id}/feedback", response_model=Feedback)
def get_feedback(placement_id: uuid.UUID, actor: Actor = Depends(auth("st", "co")), db: Session = Depends(get_db)):
    """UC-14: the evaluation of the company and the survey answer, with what the student can still do."""
    return _feedback(db, actor, placement_id)[1]


@router.get("/placements/{placement_id}/company-evaluation", response_model=CompanyEvaluationOut | None)
def get_company_evaluation(placement_id: uuid.UUID, actor: Actor = Depends(auth("st", "co")),
                           db: Session = Depends(get_db)):
    return _feedback(db, actor, placement_id)[1]["evaluation"]


@router.put("/placements/{placement_id}/company-evaluation", response_model=Feedback)
def put_company_evaluation(placement_id: uuid.UUID, body: CompanyEvaluationIn, actor: Actor = Depends(auth("st")),
                           db: Session = Depends(get_db)):
    p, relation = _placement(db, actor, placement_id)
    feedback.evaluate(db, actor.user, p, body.model_dump())
    db.commit()
    return feedback.view(db, p, relation)


@router.get("/placements/{placement_id}/outcome-survey", response_model=SurveyOut | None)
def get_outcome_survey(placement_id: uuid.UUID, actor: Actor = Depends(auth("st", "co")),
                       db: Session = Depends(get_db)):
    return _feedback(db, actor, placement_id)[1]["survey"]


@router.put("/placements/{placement_id}/outcome-survey", response_model=Feedback)
def put_outcome_survey(placement_id: uuid.UUID, body: SurveyIn, actor: Actor = Depends(auth("st")),
                       db: Session = Depends(get_db)):
    p, relation = _placement(db, actor, placement_id)
    feedback.answer(db, actor.user, p, body.job_offer)
    db.commit()
    return feedback.view(db, p, relation)


@router.get("/cycles/{cycle_id}/company-evaluations", response_model=CompanyEvaluationSummary)
def cycle_company_evaluations(cycle_id: uuid.UUID, actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    cycle = get_or_404(db, TrainingCycle, cycle_id)
    if cycle.college_id != actor.user.college_id:
        raise forbidden()
    return feedback.company_evaluations(db, cycle)


@router.post("/evaluations/{evaluation_id}/reopen", response_model=EvaluationOverview)
def reopen_evaluation(evaluation_id: uuid.UUID, body: ReasonIn, actor: Actor = Depends(auth("co")),
                      db: Session = Depends(get_db)):
    e = get_or_404(db, Evaluation, evaluation_id)
    p, relation = _placement(db, actor, e.placement_id)
    if relation != "co":
        raise forbidden()
    service.reopen(db, actor, e, body.reason)
    db.commit()
    return service.overview(db, actor, p, relation)
