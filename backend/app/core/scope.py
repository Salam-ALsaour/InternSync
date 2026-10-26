"""Record scope rules of Design 7.2, shared by the modules. The Platform Admin never reaches academic records."""
import uuid

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.core.deps import Actor
from app.core.errors import forbidden
from app.models import Application, Placement, User, Vacancy


def can_see_student(db: Session, actor: Actor, student_id: uuid.UUID) -> bool:
    code = actor.code
    if code == "st":
        return actor.id == student_id
    if code == "co":
        student = db.get(User, student_id)
        return student is not None and student.role == "student" and student.college_id == actor.user.college_id
    if code == "as":
        return bool(db.scalar(select(exists().where(Placement.student_id == student_id,
                                                    Placement.academic_supervisor_id == actor.id))))
    if code == "cs":
        own = Vacancy.company_id == actor.user.company_id if actor.is_ca else Vacancy.company_supervisor_id == actor.id
        applied = select(exists().where(Application.student_id == student_id, Application.vacancy_id == Vacancy.id,
                                        own))
        placed_cond = (Placement.vacancy_id == Vacancy.id) & (Vacancy.company_id == actor.user.company_id) \
            if actor.is_ca else Placement.company_supervisor_id == actor.id
        placed = select(exists().where(Placement.student_id == student_id, placed_cond))
        return bool(db.scalar(applied) or db.scalar(placed))
    return False


def placement_access(db: Session, actor: Actor, placement: Placement) -> str:
    """Return the caller's relation to the placement ('st', 'cs', 'as', 'co') or raise 403."""
    code = actor.code
    if code == "st" and placement.student_id == actor.id:
        return "st"
    if code == "as" and placement.academic_supervisor_id == actor.id:
        return "as"
    if code == "cs":
        if placement.company_supervisor_id == actor.id:
            return "cs"
        if actor.is_ca and db.get(Vacancy, placement.vacancy_id).company_id == actor.user.company_id:
            return "cs"
    if code == "co" and db.get(User, placement.student_id).college_id == actor.user.college_id:
        return "co"
    raise forbidden()


def vacancy_owner_or_admin(actor: Actor, vacancy: Vacancy) -> None:
    if actor.code != "cs" or vacancy.company_id != actor.user.company_id:
        raise forbidden()
    if not actor.is_ca and vacancy.company_supervisor_id != actor.id:
        raise forbidden()
