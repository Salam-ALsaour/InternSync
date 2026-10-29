"""Shared set-up of the Increment 4 tests: placements with a Final grade and cycles with many final evaluations."""
from decimal import Decimal

from sqlalchemy import select

from app.core.deps import Actor
from app.grades import service as grades
from app.models import Grade, GradeComponent, Placement, User

API = "/api/v1"


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r


def prepare(f, cycle) -> None:
    """Rubric and grade components of the cycle (once per cycle)."""
    f.rubric(cycle)
    f.components(cycle)


def final_grade(f, db, w, p: Placement, scores=(4, 5, 3)) -> Grade:
    """Reports accepted, final evaluation submitted, the other components entered, submitted and approved."""
    f.finish_reports(p)
    f.evaluation(p, db.get(User, p.company_supervisor_id), "final", list(scores))
    g = db.scalar(select(Grade).where(Grade.placement_id == p.id))
    entered = db.scalars(select(GradeComponent).where(GradeComponent.cycle_id == p.cycle_id,
                                                      GradeComponent.source != "company_final_evaluation")).all()
    academic = Actor(db.get(User, p.academic_supervisor_id), None)
    grades.save_scores(db, academic, g, p, [{"component_id": c.id, "score": Decimal(90)} for c in entered])
    grades.submit(db, academic, g, p)
    grades.approve(db, Actor(w.coA1, None), g, p)
    db.commit()
    return g


def placed_students(f, w, n: int, owner, cycle=None):
    """`n` new students of college A1, enrolled and placed in a vacancy of `owner`'s company."""
    cycle = cycle or w.cycle
    v = f.vacancy(owner, [w.cs_major], seats=max(n, 1))
    out = []
    for _ in range(n):
        s = f.student(w.A1, w.cs_major, "4.00")
        f.enroll(cycle, s, w.coA1)
        out.append(f.placement(s, v, owner, w.coA1, w.asA1))
    f.commit()
    return out
