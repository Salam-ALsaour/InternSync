"""API 3.8 – Matching (FR-MAT-01 – 07). Every response is advisory."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.common import get_or_404
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import forbidden
from app.matching import service
from app.models import Vacancy
from app.vacancies.service import can_view

router = APIRouter(tags=["matching"])


class SkillRef(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str


class VacancyBrief(BaseModel):
    id: uuid.UUID
    title: str
    company: str
    city: str
    training_type: str
    application_deadline: datetime
    seats: int


class Parts(BaseModel):
    semantic: float | None
    required: float
    preferred: float | None


class MatchItem(BaseModel):
    vacancy: VacancyBrief
    fit_score: float
    mode: str
    parts: Parts
    matched_skills: list[SkillRef]
    missing_skills: list[SkillRef]
    already_applied: bool


class MatchList(BaseModel):
    mode: str
    model_version: str | None
    advisory: bool
    total: int
    items: list[MatchItem]


class MatchDetail(MatchItem):
    model_version: str | None
    advisory: bool


class Resource(BaseModel):
    title: str
    url: str
    estimated_effort: str | None
    language: str | None


class PlanSkill(BaseModel):
    skill: SkillRef
    resources: list[Resource]


class Plan(BaseModel):
    vacancy_id: uuid.UUID
    missing_skills: list[PlanSkill]
    advisory: bool


def _vacancy(db: Session, actor: Actor, vacancy_id: uuid.UUID) -> Vacancy:
    v = get_or_404(db, Vacancy, vacancy_id)
    if not can_view(db, actor, v):
        raise forbidden()
    return v


@router.get("/students/me/matches", response_model=MatchList)
def my_matches(limit: int = Query(20, ge=1, le=100), actor: Actor = Depends(auth("st")),
               db: Session = Depends(get_db)):
    out = service.rank(db, actor.user, limit)
    db.commit()
    return out


@router.get("/students/me/matches/{vacancy_id}", response_model=MatchDetail)
def my_match(vacancy_id: uuid.UUID, actor: Actor = Depends(auth("st")), db: Session = Depends(get_db)):
    out = service.one(db, actor.user, _vacancy(db, actor, vacancy_id))
    db.commit()
    return out


@router.get("/students/me/matches/{vacancy_id}/plan", response_model=Plan)
def my_plan(vacancy_id: uuid.UUID, actor: Actor = Depends(auth("st")), db: Session = Depends(get_db)):
    out = service.plan(db, actor.user, _vacancy(db, actor, vacancy_id))
    db.commit()
    return out
