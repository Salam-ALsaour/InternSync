"""API 3.3 – Training cycles."""
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.common import get_or_404
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import forbidden
from app.cycles import schemas as s
from app.cycles import service
from app.models import TrainingCycle

router = APIRouter(tags=["cycles"])


def _viewable(db: Session, actor: Actor, cycle_id: uuid.UUID) -> TrainingCycle:
    cycle = get_or_404(db, TrainingCycle, cycle_id)
    if not service.can_view(db, actor, cycle):
        raise forbidden()
    return cycle


def _own(db: Session, actor: Actor, cycle_id: uuid.UUID) -> TrainingCycle:
    cycle = get_or_404(db, TrainingCycle, cycle_id)
    service.ensure_coordinator(actor, cycle)
    return cycle


@router.get("/cycles", response_model=list[s.CycleOut])
def list_cycles(actor: Actor = Depends(auth("st", "cs", "as", "co")), db: Session = Depends(get_db)):
    return [service.cycle_out(db, c) for c in db.scalars(service.cycles_query(actor))]


@router.post("/cycles", status_code=201, response_model=s.CycleWithWeeks)
def create_cycle(body: s.CycleIn, actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    cycle = service.create(db, actor, body.model_dump())
    db.commit()
    return service.cycle_out(db, cycle, with_weeks=True)


@router.get("/cycles/{cycle_id}", response_model=s.CycleWithWeeks)
def get_cycle(cycle_id: uuid.UUID, actor: Actor = Depends(auth("st", "cs", "as", "co")),
              db: Session = Depends(get_db)):
    return service.cycle_out(db, _viewable(db, actor, cycle_id), with_weeks=True)


@router.patch("/cycles/{cycle_id}", response_model=s.CycleWithWeeks)
def patch_cycle(cycle_id: uuid.UUID, body: s.CyclePatch, actor: Actor = Depends(auth("co")),
                db: Session = Depends(get_db)):
    cycle = _own(db, actor, cycle_id)
    service.patch(db, actor, cycle, body.model_dump(exclude_unset=True))
    db.commit()
    return service.cycle_out(db, cycle, with_weeks=True)


@router.get("/cycles/{cycle_id}/weeks", response_model=list[s.WeekOut])
def list_weeks(cycle_id: uuid.UUID, actor: Actor = Depends(auth("st", "cs", "as", "co")),
               db: Session = Depends(get_db)):
    return service.weeks_out(db, _viewable(db, actor, cycle_id))


@router.patch("/cycles/{cycle_id}/weeks/{week_no}", response_model=s.WeekOut)
def move_week_deadline(cycle_id: uuid.UUID, week_no: int, body: s.WeekPatch, actor: Actor = Depends(auth("co")),
                       db: Session = Depends(get_db)):
    cycle = _own(db, actor, cycle_id)
    week = service.move_week(db, actor, cycle, week_no, body.report_due_at, body.reason)
    db.commit()
    return {"week_no": week.week_no, "starts_on": week.starts_on, "ends_on": week.ends_on,
            "report_due_at": week.report_due_at, "scheduled_days": week.scheduled_days}


@router.post("/cycles/{cycle_id}/close", response_model=s.CycleOut)
def close_cycle(cycle_id: uuid.UUID, actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    cycle = _own(db, actor, cycle_id)
    service.close(db, actor, cycle)
    db.commit()
    return service.cycle_out(db, cycle)


@router.post("/cycles/{cycle_id}/reopen", response_model=s.CycleOut)
def reopen_cycle(cycle_id: uuid.UUID, body: s.ReasonIn, actor: Actor = Depends(auth("co")),
                 db: Session = Depends(get_db)):
    cycle = _own(db, actor, cycle_id)
    service.reopen(db, actor, cycle, body.reason)
    db.commit()
    return service.cycle_out(db, cycle)


@router.get("/cycles/{cycle_id}/grade-components", response_model=list[s.ComponentIO])
def get_components(cycle_id: uuid.UUID, actor: Actor = Depends(auth("co", "as")), db: Session = Depends(get_db)):
    return service.components_out(db, _viewable(db, actor, cycle_id))


@router.put("/cycles/{cycle_id}/grade-components", response_model=list[s.ComponentIO])
def put_components(cycle_id: uuid.UUID, body: s.ComponentsIn, actor: Actor = Depends(auth("co")),
                   db: Session = Depends(get_db)):
    cycle = _own(db, actor, cycle_id)
    service.replace_components(db, actor, cycle, [c.model_dump() for c in body.components])
    db.commit()
    return service.components_out(db, cycle)


@router.get("/cycles/{cycle_id}/rubric", response_model=s.RubricOut)
def get_rubric(cycle_id: uuid.UUID, actor: Actor = Depends(auth("st", "cs", "as", "co")),
               db: Session = Depends(get_db)):
    return service.rubric_out(db, _viewable(db, actor, cycle_id))


@router.put("/cycles/{cycle_id}/rubric", response_model=s.RubricOut)
def put_rubric(cycle_id: uuid.UUID, body: s.RubricIn, actor: Actor = Depends(auth("co")),
               db: Session = Depends(get_db)):
    cycle = _own(db, actor, cycle_id)
    service.replace_rubric(db, actor, cycle, [c.model_dump() for c in body.criteria])
    db.commit()
    return service.rubric_out(db, cycle)


@router.get("/cycles/{cycle_id}/enrollments", response_model=list[s.EnrollmentOut])
def list_enrollments(cycle_id: uuid.UUID, actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    return service.enrollments_out(db, _own(db, actor, cycle_id))
