"""API 3.14 – Dashboards, statistics, and escalations (FR-DSH-01, FR-DSH-02, FR-DSH-05, FR-NOT-04)."""
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core import clock
from app.core.common import get_or_404
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import forbidden
from app.dashboard import service
from app.models import TrainingCycle, User
from app.notifications.scheduled import overdue_items

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


class Escalation(BaseModel):
    kind: str
    placement_id: uuid.UUID
    student_en: str
    student_ar: str
    item_en: str
    item_ar: str
    due_at: datetime
    days_overdue: int


@router.get("/escalations", response_model=list[Escalation])
def escalations(cycle_id: uuid.UUID | None = None,
                kind: Literal["report", "attendance", "evaluation"] | None = Query(None, alias="type"),
                actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    """FR-NOT-04: items of the college still outstanding `notifications.escalation_days` days after the deadline."""
    out = []
    for item in overdue_items(db, actor.user.college_id):
        if (cycle_id and item.placement.cycle_id != cycle_id) or (kind and item.kind != kind):
            continue
        student = db.get(User, item.placement.student_id)
        out.append({"kind": item.kind, "placement_id": item.placement.id, "student_en": student.name_en,
                    "student_ar": student.name_ar, "item_en": item.item_en, "item_ar": item.item_ar,
                    "due_at": item.due, "days_overdue": (clock.now() - item.due).days})
    return sorted(out, key=lambda e: e["due_at"])


@router.get("/platform/stats", response_model=PlatformStats)
def get_platform_stats(actor: Actor = Depends(auth("pa")), db: Session = Depends(get_db)):
    return service.platform_stats(db)
