"""API 3.14 – Dashboards and statistics (FR-DSH-01, FR-DSH-02, FR-DSH-05)."""
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.common import get_or_404
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import forbidden
from app.dashboard import service
from app.models import TrainingCycle

router = APIRouter(tags=["dashboard"])


class DashboardItem(BaseModel):
    type: str
    count: int
    link: str
    status: str | None = None
    oldest_days: int | None = None


class Dashboard(BaseModel):
    role: str
    items: list[DashboardItem]


class Figures(BaseModel):
    placed: int
    reports_due: int
    reports_submitted: int
    submission_rate: float | None
    late_rate: float | None
    attended_days: int
    scheduled_days: int
    attendance_rate: float | None
    evaluations_expected: int
    evaluations_submitted: int
    evaluation_completion: float | None
    enrolled: int | None = None
    unplaced: int | None = None


class CompanyFigures(Figures):
    company_id: uuid.UUID
    company_name: str


class CycleStats(BaseModel):
    cycle_id: uuid.UUID
    overall: Figures
    companies: list[CompanyFigures]


class PlatformStats(BaseModel):
    universities: int
    colleges: int
    colleges_with_coordinator: int
    colleges_without_coordinator: int
    verified_companies: int
    users_by_role: dict[str, int]
    pending_verifications: int
    oldest_pending_days: int | None
    published_vacancies: int


@router.get("/dashboard", response_model=Dashboard)
def get_dashboard(actor: Actor = Depends(auth(unverified=True)), db: Session = Depends(get_db)):
    return service.dashboard(db, actor)


@router.get("/cycles/{cycle_id}/stats", response_model=CycleStats)
def get_cycle_stats(cycle_id: uuid.UUID, company_id: uuid.UUID | None = None, actor: Actor = Depends(auth("co")),
                    db: Session = Depends(get_db)):
    cycle = get_or_404(db, TrainingCycle, cycle_id)
    if cycle.college_id != actor.user.college_id:
        raise forbidden()
    return service.cycle_stats(db, cycle, company_id)


@router.get("/platform/stats", response_model=PlatformStats)
def get_platform_stats(actor: Actor = Depends(auth("pa")), db: Session = Depends(get_db)):
    return service.platform_stats(db)
