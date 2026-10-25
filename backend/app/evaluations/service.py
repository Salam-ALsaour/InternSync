"""Periodic and final evaluations by the company supervisor (FR-EVL-01 – 04; Increment 2 design, Section 6)."""
import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core import audit, clock
from app.core.deps import Actor
from app.core.errors import ApiError, conflict, forbidden
from app.models import Evaluation, EvaluationScore, Grade, Placement, RubricCriterion, TrainingCycle, User
from app.reports.service import ensure_writable

TYPES = ("periodic", "final")


def criteria(db: Session, cycle_id: uuid.UUID) -> list[RubricCriterion]:
    return list(db.scalars(select(RubricCriterion).where(RubricCriterion.cycle_id == cycle_id)
                           .order_by(RubricCriterion.position)))


def find(db: Session, placement: Placement, type_: str) -> Evaluation | None:
    return db.scalar(select(Evaluation).where(Evaluation.placement_id == placement.id, Evaluation.type == type_))


def due_at(cycle: TrainingCycle, type_: str):
    return cycle.periodic_eval_due_at if type_ == "periodic" else cycle.final_eval_due_at


def grade_status(db: Session, placement: Placement) -> str | None:
    return db.scalar(select(Grade.status).where(Grade.placement_id == placement.id))


def visible_to(db: Session, relation: str, actor: Actor, placement: Placement, e: Evaluation | None) -> bool:
    """FR-EVL-03: the student sees the periodic evaluation once submitted and the final one when the grade is Final.
    Drafts are visible only to the company supervisor writing them."""
    if e is None:
        return False
    if relation == "cs":
        return e.status == "submitted" or placement.company_supervisor_id == actor.id
    if e.status != "submitted":
        return False
    if relation == "st" and e.type == "final":
        return grade_status(db, placement) == "final"
    return True


def evaluation_out(db: Session, e: Evaluation) -> dict:
    names = {c.id: c for c in db.scalars(
        select(RubricCriterion).join(EvaluationScore, EvaluationScore.criterion_id == RubricCriterion.id)
        .where(EvaluationScore.evaluation_id == e.id))}
    scores = [{"criterion_id": s.criterion_id, "name_en": names[s.criterion_id].name_en,
               "name_ar": names[s.criterion_id].name_ar, "score": s.score}
              for s in db.scalars(select(EvaluationScore).where(EvaluationScore.evaluation_id == e.id))]
    scores.sort(key=lambda x: names[x["criterion_id"]].position)
    by = db.get(User, e.submitted_by) if e.submitted_by else None
    return {"id": e.id, "type": e.type, "status": e.status, "overall_comment": e.overall_comment,
            "mean_score": e.mean_score, "scores": scores, "submitted_at": e.submitted_at,
            "submitted_by_en": by.name_en if by else None, "submitted_by_ar": by.name_ar if by else None,
            "reopen_count": e.reopen_count, "reopened_at": e.reopened_at, "reopen_reason": e.reopen_reason}


def overview(db: Session, actor: Actor, placement: Placement, relation: str) -> dict:
    cycle = db.get(TrainingCycle, placement.cycle_id)
    writable = placement.status == "active" and cycle.status == "open"
    items = []
    for type_ in TYPES:
        e = find(db, placement, type_)
        shown = visible_to(db, relation, actor, placement, e)
        grade = grade_status(db, placement)
        items.append({
            "type": type_, "due_at": due_at(cycle, type_),
            "evaluation": evaluation_out(db, e) if shown else None,
            "can_edit": writable and placement.company_supervisor_id == actor.id and (e is None or e.status == "draft"),
            "can_reopen": writable and relation == "co" and e is not None and e.status == "submitted"
            and e.reopen_count == 0 and not (type_ == "final" and grade in ("submitted", "final")),
        })
    rubric = [{"id": c.id, "name_en": c.name_en, "name_ar": c.name_ar, "levels": c.levels}
              for c in criteria(db, placement.cycle_id)]
    return {"placement_id": placement.id, "rubric": rubric, "items": items}


def _writable(db: Session, actor: Actor, placement: Placement, type_: str) -> Evaluation:
    if placement.company_supervisor_id != actor.id:
        raise forbidden()
    ensure_writable(db, placement)
    e = find(db, placement, type_)
    if e is not None and e.status != "draft":
        raise conflict("INVALID_TRANSITION")
    if e is None:
        e = Evaluation(placement_id=placement.id, type=type_)
        db.add(e)
        db.flush()
    return e


def save(db: Session, actor: Actor, placement: Placement, type_: str, scores: list[dict], comment: str | None):
    """Save the draft; scores must be for criteria of the placement's cycle (FR-EVL-02)."""
    e = _writable(db, actor, placement, type_)
    allowed = {c.id for c in criteria(db, placement.cycle_id)}
    wrong = [s["criterion_id"] for s in scores if s["criterion_id"] not in allowed]
    if wrong:
        raise ApiError(422, "VALIDATION_ERROR", errors=[{"field": "scores", "code": "VALIDATION_ERROR",
                                                         "message": f"criterion {wrong[0]} is not in this rubric"}])
    db.execute(delete(EvaluationScore).where(EvaluationScore.evaluation_id == e.id))
    for s in {s["criterion_id"]: s for s in scores}.values():
        db.add(EvaluationScore(evaluation_id=e.id, criterion_id=s["criterion_id"], score=s["score"]))
    e.overall_comment = (comment or "").strip() or None
    return e


def submit(db: Session, actor: Actor, placement: Placement, type_: str) -> Evaluation:
    """FR-EVL-01: every criterion rated and the comment present; the first submission locks the rubric."""
    e = _writable(db, actor, placement, type_)
    db.flush()
    rated = {s.criterion_id: s.score for s in db.scalars(select(EvaluationScore)
                                                          .where(EvaluationScore.evaluation_id == e.id))}
    rubric = criteria(db, placement.cycle_id)
    errors = [{"field": f"scores.{c.id}", "code": "EVALUATION_INCOMPLETE", "message": c.name_en}
              for c in rubric if c.id not in rated]
    if not (e.overall_comment or "").strip():
        errors.append({"field": "overall_comment", "code": "COMMENT_REQUIRED"})
    if errors or not rubric:
        raise ApiError(422, "EVALUATION_INCOMPLETE", errors=errors)
    now = clock.now()
    e.mean_score = (Decimal(sum(rated.values())) / Decimal(len(rated))).quantize(Decimal("0.001"), ROUND_HALF_UP)
    e.status, e.submitted_by, e.submitted_at = "submitted", actor.id, now
    cycle = db.get(TrainingCycle, placement.cycle_id)
    if cycle.rubric_locked_at is None:
        cycle.rubric_locked_at = now
    student = db.get(User, placement.student_id)
    audit.record(db, actor.user, "submit", "evaluation", e.id, student_id=student.id, college_id=student.college_id,
                 cycle_id=placement.cycle_id, new={"type": type_, "mean_score": e.mean_score})
    return e


def reopen(db: Session, actor: Actor, e: Evaluation, reason: str) -> None:
    """FR-EVL-04: once, by the coordinator, with a reason; not while the grade is submitted or Final."""
    placement = db.get(Placement, e.placement_id)
    ensure_writable(db, placement)
    if e.status != "submitted":
        raise conflict("INVALID_TRANSITION")
    if e.reopen_count >= 1:
        raise conflict("ALREADY_REOPENED")
    if not reason.strip():
        raise ApiError(422, "REASON_REQUIRED")
    if e.type == "final" and grade_status(db, placement) in ("submitted", "final"):
        raise conflict("INVALID_TRANSITION")
    e.status, e.reopen_count = "draft", e.reopen_count + 1
    e.reopened_at, e.reopened_by, e.reopen_reason = clock.now(), actor.id, reason.strip()
    student = db.get(User, placement.student_id)
    audit.record(db, actor.user, "reopen", "evaluation", e.id, student_id=student.id, college_id=student.college_id,
                 cycle_id=placement.cycle_id, old={"status": "submitted"}, new={"status": "draft"},
                 reason=reason.strip())
