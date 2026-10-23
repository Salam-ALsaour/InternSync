"""API 3.6 – Vacancies, 3.7 – Applications and placements."""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.common import Page, PageParams, get_or_404, paginate
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import ApiError, forbidden
from app.core.scope import placement_access, vacancy_owner_or_admin
from app.models import Application, Enrollment, Placement, User, Vacancy
from app.vacancies import schemas as s
from app.vacancies import service

router = APIRouter(tags=["vacancies"])


# ---------------------------------------------------------------- vacancies
@router.get("/vacancies", response_model=Page[s.VacancyOut])
def browse(q: str | None = None, city: str | None = None, company_id: uuid.UUID | None = None,
           major_id: uuid.UUID | None = None, skill_id: uuid.UUID | None = None,
           training_type: Literal["coop", "summer"] | None = None,
           status: Literal["draft", "published", "closed"] | None = None, params: PageParams = Depends(),
           actor: Actor = Depends(auth("st", "cs", "co", "pa", unverified=True)), db: Session = Depends(get_db)):
    if actor.user.verification_status in ("pending", "rejected") and actor.code != "st":
        raise ApiError(403, "VERIFICATION_REQUIRED")
    f = dict(q=q, city=city, company_id=company_id, major_id=major_id, skill_id=skill_id,
             training_type=training_type, status=status)
    return paginate(db, service.browse_query(db, actor, f), params, lambda v: service.vacancy_out(db, v, actor))


@router.post("/vacancies", status_code=201, response_model=s.VacancyOut)
def create_vacancy(body: s.VacancyIn, actor: Actor = Depends(auth("cs")), db: Session = Depends(get_db)):
    v = service.create(db, actor, body.model_dump())
    db.commit()
    return service.vacancy_out(db, v, actor)


@router.get("/vacancies/{vacancy_id}", response_model=s.VacancyOut)
def get_vacancy(vacancy_id: uuid.UUID, actor: Actor = Depends(auth("st", "cs", "co", "pa", unverified=True)),
                db: Session = Depends(get_db)):
    if actor.user.verification_status in ("pending", "rejected") and actor.code != "st":
        raise ApiError(403, "VERIFICATION_REQUIRED")
    v = get_or_404(db, Vacancy, vacancy_id)
    if not service.can_view(db, actor, v):
        raise forbidden()
    return service.vacancy_out(db, v, actor)


@router.patch("/vacancies/{vacancy_id}", response_model=s.VacancyOut)
def patch_vacancy(vacancy_id: uuid.UUID, body: s.VacancyPatch, actor: Actor = Depends(auth("cs")),
                  db: Session = Depends(get_db)):
    v = get_or_404(db, Vacancy, vacancy_id)
    vacancy_owner_or_admin(actor, v)
    service.patch(db, actor, v, body.model_dump(exclude_unset=True))
    db.commit()
    return service.vacancy_out(db, v, actor)


@router.post("/vacancies/{vacancy_id}/publish", response_model=s.VacancyOut)
def publish_vacancy(vacancy_id: uuid.UUID, actor: Actor = Depends(auth("cs")), db: Session = Depends(get_db)):
    v = get_or_404(db, Vacancy, vacancy_id)
    vacancy_owner_or_admin(actor, v)
    service.publish_vacancy(db, actor, v)
    db.commit()
    return service.vacancy_out(db, v, actor)


@router.post("/vacancies/{vacancy_id}/close", response_model=s.VacancyOut)
def close_vacancy(vacancy_id: uuid.UUID, actor: Actor = Depends(auth("cs")), db: Session = Depends(get_db)):
    v = get_or_404(db, Vacancy, vacancy_id)
    vacancy_owner_or_admin(actor, v)
    service.close_vacancy(db, actor, v)
    db.commit()
    return service.vacancy_out(db, v, actor)


# ---------------------------------------------------------------- applications
@router.post("/vacancies/{vacancy_id}/applications", status_code=201, response_model=s.ApplicationOut)
def apply(vacancy_id: uuid.UUID, actor: Actor = Depends(auth("st")), db: Session = Depends(get_db)):
    v = get_or_404(db, Vacancy, vacancy_id)
    a = service.apply(db, actor, v)
    db.commit()
    return service.application_out(db, a)


@router.get("/vacancies/{vacancy_id}/applications", response_model=list[s.ApplicantOut])
def vacancy_applicants(vacancy_id: uuid.UUID, actor: Actor = Depends(auth("cs")), db: Session = Depends(get_db)):
    v = get_or_404(db, Vacancy, vacancy_id)
    vacancy_owner_or_admin(actor, v)
    apps = db.scalars(select(Application).where(Application.vacancy_id == v.id).order_by(Application.created_at))
    return [service.applicant_out(db, a) for a in apps]


@router.get("/applications", response_model=Page[s.ApplicationOut])
def list_applications(status: str | None = None, cycle_id: uuid.UUID | None = None, placed: bool | None = None,
                      params: PageParams = Depends(), actor: Actor = Depends(auth("st", "co")),
                      db: Session = Depends(get_db)):
    stmt = select(Application).join(User, User.id == Application.student_id).order_by(Application.created_at.desc())
    if actor.code == "st":
        stmt = stmt.where(Application.student_id == actor.id)
    else:
        stmt = stmt.where(User.college_id == actor.user.college_id)
    if status:
        stmt = stmt.where(Application.status == status)
    if placed is False:
        stmt = stmt.where(Application.status == "accepted")
    if cycle_id:
        stmt = stmt.where(Application.student_id.in_(select(Enrollment.student_id)
                                                     .where(Enrollment.cycle_id == cycle_id)))
    return paginate(db, stmt, params, lambda a: service.application_out(db, a))


@router.get("/applications/{application_id}", response_model=s.ApplicationOut)
def get_application(application_id: uuid.UUID, actor: Actor = Depends(auth("st", "cs", "co")),
                    db: Session = Depends(get_db)):
    a = get_or_404(db, Application, application_id)
    if not service.can_view_application(db, actor, a):
        raise forbidden()
    return service.application_out(db, a)


@router.post("/applications/{application_id}/withdraw", response_model=s.ApplicationOut)
def withdraw(application_id: uuid.UUID, actor: Actor = Depends(auth("st")), db: Session = Depends(get_db)):
    a = get_or_404(db, Application, application_id)
    service.withdraw(db, actor, a)
    db.commit()
    return service.application_out(db, a)


@router.post("/applications/{application_id}/accept", response_model=s.ApplicationOut)
def accept(application_id: uuid.UUID, actor: Actor = Depends(auth("cs")), db: Session = Depends(get_db)):
    a = get_or_404(db, Application, application_id)
    service.decide(db, actor, a, accept=True)
    db.commit()
    return service.application_out(db, a)


@router.post("/applications/{application_id}/decline", response_model=s.ApplicationOut)
def decline(application_id: uuid.UUID, actor: Actor = Depends(auth("cs")), db: Session = Depends(get_db)):
    a = get_or_404(db, Application, application_id)
    service.decide(db, actor, a, accept=False)
    db.commit()
    return service.application_out(db, a)


# ---------------------------------------------------------------- placements
@router.get("/placements/candidates", response_model=list[s.AcceptedApplicant])
def placement_candidates(actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    """Accepted applicants of the college waiting for a placement, with the company's supervisors."""
    return service.accepted_waiting(db, actor)


@router.post("/placements", status_code=201, response_model=s.PlacementOut)
def confirm_placement(body: s.PlacementIn, actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    p = service.confirm_placement(db, actor, body.application_id, body.academic_supervisor_id,
                                  body.company_supervisor_id)
    db.commit()
    return service.placement_out(db, p)


@router.get("/placements", response_model=Page[s.PlacementOut])
def list_placements(cycle_id: uuid.UUID | None = None, status: str | None = None,
                    academic_supervisor_id: uuid.UUID | None = None, params: PageParams = Depends(),
                    actor: Actor = Depends(auth("st", "cs", "as", "co")), db: Session = Depends(get_db)):
    f = dict(cycle_id=cycle_id, status=status, academic_supervisor_id=academic_supervisor_id)
    return paginate(db, service.placements_query(actor, f), params, lambda p: service.placement_out(db, p))


@router.get("/placements/{placement_id}", response_model=s.PlacementOut)
def get_placement(placement_id: uuid.UUID, actor: Actor = Depends(auth("st", "cs", "as", "co")),
                  db: Session = Depends(get_db)):
    p = get_or_404(db, Placement, placement_id)
    placement_access(db, actor, p)
    return service.placement_out(db, p)


@router.patch("/placements/{placement_id}/academic-supervisor", response_model=s.PlacementOut)
def change_academic_supervisor(placement_id: uuid.UUID, body: s.SupervisorChange,
                               actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    p = get_or_404(db, Placement, placement_id)
    placement_access(db, actor, p)
    service.change_supervisor(db, actor, p, body.academic_supervisor_id, body.reason)
    db.commit()
    return service.placement_out(db, p)


@router.post("/placements/{placement_id}/cancel", response_model=s.PlacementOut)
def cancel_placement(placement_id: uuid.UUID, body: s.ReasonIn, actor: Actor = Depends(auth("co")),
                     db: Session = Depends(get_db)):
    p = get_or_404(db, Placement, placement_id)
    placement_access(db, actor, p)
    service.cancel(db, actor, p, body.reason)
    db.commit()
    return service.placement_out(db, p)
