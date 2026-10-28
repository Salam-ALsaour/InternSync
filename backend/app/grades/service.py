"""Grades: computation, preconditions, and the grade state machine (FR-WFL-02 – 07, Design 5.4, Table 5.4;
Increment 2 design, Section 7)."""
import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit, clock
from app.core.deps import Actor
from app.core.errors import ApiError, conflict, forbidden
from app.models import (
    Company,
    Evaluation,
    Grade,
    GradeComponent,
    GradeComponentScore,
    Placement,
    ReportSlot,
    TrainingCycle,
    User,
    Vacancy,
)
from app.notifications import events

COMPANY = "company_final_evaluation"
TWO = Decimal("0.01")


def round2(x: Decimal) -> Decimal:
    return x.quantize(TWO, ROUND_HALF_UP)


def company_score(db: Session, placement: Placement) -> Decimal | None:
    """Design 5.4: the final evaluation's mean ÷ 5 × 100, once the final evaluation is submitted."""
    mean = db.scalar(select(Evaluation.mean_score).where(Evaluation.placement_id == placement.id,
                                                          Evaluation.type == "final",
                                                          Evaluation.status == "submitted"))
    return None if mean is None else round2(Decimal(mean) / 5 * 100)


def components(db: Session, grade: Grade, placement: Placement) -> list[dict]:
    entered = {s.component_id: s.score for s in db.scalars(select(GradeComponentScore)
                                                             .where(GradeComponentScore.grade_id == grade.id))}
    company = company_score(db, placement)
    out = []
    for c in db.scalars(select(GradeComponent).where(GradeComponent.cycle_id == placement.cycle_id)
                        .order_by(GradeComponent.position)):
        computed = c.source == COMPANY
        out.append({"id": c.id, "name_en": c.name_en, "name_ar": c.name_ar, "weight": c.weight, "source": c.source,
                    "computed": computed, "score": company if computed else entered.get(c.id)})
    return out


def total(parts: list[dict]) -> Decimal | None:
    """Σ weight × score ÷ 100, rounded half up to two decimals; None until every component has a score."""
    if not parts or any(p["score"] is None for p in parts):
        return None
    return round2(sum((Decimal(p["weight"]) * Decimal(p["score"]) for p in parts), Decimal(0)) / 100)


def preconditions(db: Session, grade: Grade, placement: Placement) -> list[dict]:
    """FR-WFL-03: the checklist; `ok` is False for each missing item."""
    items = []
    final_eval = db.scalar(select(Evaluation.status).where(Evaluation.placement_id == placement.id,
                                                            Evaluation.type == "final"))
    items.append({"item": "final_evaluation", "ok": final_eval == "submitted", "week_no": None, "component_id": None})
    slots = db.scalars(select(ReportSlot).where(ReportSlot.placement_id == placement.id)
                       .order_by(ReportSlot.kind.desc(), ReportSlot.week_no)).all()
    final = next((s for s in slots if s.kind == "final"), None)
    items.append({"item": "final_report", "ok": final is not None and final.status == "accepted", "week_no": None,
                  "component_id": None})
    for s in slots:
        if s.kind == "weekly":
            items.append({"item": "weekly_report", "ok": s.status in ("accepted", "closed_missing"),
                          "week_no": s.week_no, "component_id": None})
    for c in components(db, grade, placement):
        if not c["computed"]:
            items.append({"item": "component", "ok": c["score"] is not None, "week_no": None, "component_id": c["id"]})
    return items


def grade_for(db: Session, placement: Placement) -> Grade:
    grade = db.scalar(select(Grade).where(Grade.placement_id == placement.id))
    if grade is None:  # placements are created with their grade; this covers data made before that rule
        grade = Grade(placement_id=placement.id)
        db.add(grade)
        db.flush()
    return grade


def view(db: Session, actor: Actor, grade: Grade, placement: Placement, relation: str) -> dict:
    if relation == "st" and grade.status != "final":
        return {"visible": False, "status": None}
    cycle = db.get(TrainingCycle, placement.cycle_id)
    parts = components(db, grade, placement)
    open_cycle = cycle.status == "open"
    checks = preconditions(db, grade, placement) if relation in ("as", "co") else []
    assigned = relation == "as" and placement.academic_supervisor_id == actor.id
    return {
        "visible": True, "id": grade.id, "placement_id": placement.id, "status": grade.status,
        "components": parts, "total": grade.total if grade.status != "draft" else total(parts),
        "preconditions": checks, "submitted_at": grade.submitted_at, "approved_at": grade.approved_at,
        "return_comment": grade.return_comment, "reopen_reason": grade.reopen_reason,
        "can_edit": assigned and open_cycle and grade.status == "draft",
        "can_submit": assigned and open_cycle and grade.status == "draft" and all(c["ok"] for c in checks),
        "can_decide": relation == "co" and open_cycle and grade.status == "submitted",
        "can_reopen": relation == "co" and open_cycle and grade.status == "final",
    }


def _ensure_open(db: Session, placement: Placement) -> None:
    if db.get(TrainingCycle, placement.cycle_id).status != "open":
        raise conflict("CYCLE_CLOSED")


def _audit(db: Session, actor: Actor, action: str, grade: Grade, placement: Placement, **kw) -> None:
    student = db.get(User, placement.student_id)
    audit.record(db, actor.user, action, "grade", grade.id, student_id=student.id, college_id=student.college_id,
                 cycle_id=placement.cycle_id, **kw)


def _editable(db: Session, actor: Actor, grade: Grade, placement: Placement) -> None:
    if placement.academic_supervisor_id != actor.id:
        raise forbidden()
    if grade.status == "final":
        raise conflict("GRADE_LOCKED")
    if grade.status != "draft":
        raise conflict("INVALID_TRANSITION")
    _ensure_open(db, placement)


def save_scores(db: Session, actor: Actor, grade: Grade, placement: Placement, scores: list[dict]) -> None:
    """FR-WFL-02: the academic supervisor enters the components that are not computed."""
    _editable(db, actor, grade, placement)
    editable = {c.id for c in db.scalars(select(GradeComponent).where(GradeComponent.cycle_id == placement.cycle_id,
                                                                       GradeComponent.source != COMPANY))}
    wrong = [s for s in scores if s["component_id"] not in editable]
    if wrong:
        raise ApiError(422, "VALIDATION_ERROR", errors=[{"field": "component_scores", "code": "VALIDATION_ERROR",
                                                         "message": f"component {wrong[0]['component_id']}"}])
    old = {str(c["id"]): c["score"] for c in components(db, grade, placement) if not c["computed"]}
    for s in scores:
        row = db.get(GradeComponentScore, (grade.id, s["component_id"]))
        if row is None:
            db.add(GradeComponentScore(grade_id=grade.id, component_id=s["component_id"], score=s["score"]))
        else:
            row.score = s["score"]
    db.flush()
    grade.total = total(components(db, grade, placement))
    _audit(db, actor, "update", grade, placement, old={"scores": old},
           new={"scores": {str(s["component_id"]): s["score"] for s in scores}})


def submit(db: Session, actor: Actor, grade: Grade, placement: Placement) -> None:
    """FR-WFL-03: only with every precondition met; otherwise 409 with the missing items."""
    _editable(db, actor, grade, placement)
    missing = [c for c in preconditions(db, grade, placement) if not c["ok"]]
    if missing:
        raise ApiError(409, "PRECONDITIONS_UNMET", missing=[{k: str(v) if isinstance(v, uuid.UUID) else v
                                                            for k, v in c.items() if k != "ok"} for c in missing])
    parts = components(db, grade, placement)
    for c in parts:  # keep the computed company component with the submitted grade
        if c["computed"]:
            row = db.get(GradeComponentScore, (grade.id, c["id"]))
            if row is None:
                db.add(GradeComponentScore(grade_id=grade.id, component_id=c["id"], score=c["score"]))
            else:
                row.score = c["score"]
    grade.total = total(parts)
    grade.status, grade.submitted_by, grade.submitted_at = "submitted", actor.id, clock.now()
    grade.return_comment = None
    _audit(db, actor, "submit", grade, placement, old={"status": "draft"},
           new={"status": "submitted", "total": grade.total})
    events.grade_event(db, "grade.submitted", grade, placement)


def _coordinator(actor: Actor, placement: Placement, db: Session) -> None:
    if db.get(User, placement.student_id).college_id != actor.user.college_id:
        raise forbidden()
    _ensure_open(db, placement)


def approve(db: Session, actor: Actor, grade: Grade, placement: Placement) -> None:
    """FR-WFL-04: Final with a timestamp; the placement is completed."""
    _coordinator(actor, placement, db)
    if grade.status != "submitted":
        raise conflict("INVALID_TRANSITION")
    grade.status, grade.approved_by, grade.approved_at = "final", actor.id, clock.now()
    grade.total = total(components(db, grade, placement)) or grade.total
    placement.status = "completed"
    _audit(db, actor, "approve", grade, placement, old={"status": "submitted"},
           new={"status": "final", "total": grade.total})
    events.grade_event(db, "grade.final", grade, placement)


def return_grade(db: Session, actor: Actor, grade: Grade, placement: Placement, comment: str) -> None:
    _coordinator(actor, placement, db)
    if grade.status != "submitted":
        raise conflict("INVALID_TRANSITION")
    if not comment.strip():
        raise ApiError(422, "COMMENT_REQUIRED")
    grade.status, grade.return_comment = "draft", comment.strip()
    _audit(db, actor, "return", grade, placement, old={"status": "submitted"}, new={"status": "draft"},
           reason=grade.return_comment)
    events.grade_event(db, "grade.returned", grade, placement, comment=grade.return_comment)


def reopen(db: Session, actor: Actor, grade: Grade, placement: Placement, reason: str) -> None:
    """FR-WFL-05: only the coordinator, with a reason; back to Draft and the placement back to active."""
    _coordinator(actor, placement, db)
    if grade.status != "final":
        raise conflict("INVALID_TRANSITION")
    if not reason.strip():
        raise ApiError(422, "REASON_REQUIRED")
    grade.status, grade.reopen_reason = "draft", reason.strip()
    grade.approved_by = grade.approved_at = None
    placement.status = "active"
    _audit(db, actor, "reopen", grade, placement, old={"status": "final"}, new={"status": "draft"},
           reason=grade.reopen_reason)
    events.grade_event(db, "grade.reopened", grade, placement, reason=grade.reopen_reason)


def bulk_approve(db: Session, actor: Actor, grade_ids: list[uuid.UUID]) -> list[dict]:
    """FR-WFL-07: each grade is approved on its own, with its own audit entry and result."""
    results = []
    for gid in dict.fromkeys(grade_ids):
        grade = db.get(Grade, gid)
        if grade is None:
            results.append({"grade_id": gid, "ok": False, "code": "NOT_FOUND"})
            continue
        try:
            with db.begin_nested():
                approve(db, actor, grade, db.get(Placement, grade.placement_id))
            results.append({"grade_id": gid, "ok": True, "code": None})
        except ApiError as e:
            results.append({"grade_id": gid, "ok": False, "code": e.code})
    return results


def listing(db: Session, actor: Actor, cycle_id: uuid.UUID | None, status: str | None) -> list[dict]:
    stmt = (select(Grade, Placement, User).join(Placement, Placement.id == Grade.placement_id)
            .join(User, User.id == Placement.student_id).order_by(User.name_en))
    if actor.code == "as":
        stmt = stmt.where(Placement.academic_supervisor_id == actor.id)
    else:
        stmt = stmt.where(User.college_id == actor.user.college_id)
    if cycle_id:
        stmt = stmt.where(Placement.cycle_id == cycle_id)
    if status:
        stmt = stmt.where(Grade.status == status)
    stmt = stmt.where(Placement.status != "cancelled")
    out = []
    for g, p, u in db.execute(stmt):
        v = db.get(Vacancy, p.vacancy_id)
        out.append({"id": g.id, "placement_id": p.id, "status": g.status,
                    "total": g.total if g.status != "draft" else total(components(db, g, p)),
                    "student": {"id": u.id, "name_en": u.name_en, "name_ar": u.name_ar},
                    "company_name": db.get(Company, v.company_id).name, "submitted_at": g.submitted_at,
                    "approved_at": g.approved_at})
    return out
