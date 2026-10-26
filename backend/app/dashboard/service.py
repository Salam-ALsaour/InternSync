"""Dashboards with live counts (FR-DSH-01, FR-DSH-02, FR-DSH-05; Design 5.7; Increment 2 design, Section 8).
Counts are queries, so they always equal the database."""
import uuid
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.attendance.service import overdue_weeks
from app.core import clock
from app.core.deps import Actor
from app.evaluations.service import TYPES, due_at
from app.grades import service as grades
from app.models import (
    Application,
    AttendanceWeek,
    College,
    Company,
    Enrollment,
    Evaluation,
    Grade,
    Placement,
    ReportSlot,
    TrainingCycle,
    University,
    User,
    Vacancy,
    VerificationRequest,
)

SOON = timedelta(days=7)


def _item(type_: str, count: int, link: str, **extra) -> dict:
    return {"type": type_, "count": count, "link": link, **extra}


def _student(db: Session, actor: Actor) -> list[dict]:
    me, now = actor.user, clock.now()
    slots = (select(func.count()).select_from(ReportSlot).join(Placement, Placement.id == ReportSlot.placement_id)
             .where(Placement.student_id == me.id, Placement.status == "active"))
    due = db.scalar(slots.where(ReportSlot.status.in_(("draft", "revision_requested")),
                                ReportSlot.due_at <= now + SOON))
    revisions = db.scalar(slots.where(ReportSlot.status == "revision_requested"))
    apps = dict(db.execute(select(Application.status, func.count()).where(Application.student_id == me.id)
                           .group_by(Application.status)).all())
    final = db.scalar(select(func.count()).select_from(Grade).join(Placement, Placement.id == Grade.placement_id)
                      .where(Placement.student_id == me.id, Grade.status == "final"))
    items = []
    if me.verification_status in ("pending", "rejected"):
        items.append(_item("verification", 1, "/verification", status=me.verification_status))
    items += [_item("reports_due", due, "/student/reports"),
              _item("revisions_requested", revisions, "/student/reports"),
              _item("applications_submitted", apps.get("submitted", 0), "/student/applications"),
              _item("applications_accepted", apps.get("accepted", 0), "/student/applications"),
              _item("grade_final", final, "/student/reports")]
    return items


def _company_placements(db: Session, actor: Actor) -> list[Placement]:
    stmt = select(Placement).where(Placement.status == "active")
    if actor.is_ca:
        stmt = stmt.join(Vacancy, Vacancy.id == Placement.vacancy_id).where(Vacancy.company_id == actor.user.company_id)
    else:
        stmt = stmt.where(Placement.company_supervisor_id == actor.id)
    return list(db.scalars(stmt))


def _company(db: Session, actor: Actor) -> list[dict]:
    vacancies = select(Vacancy.id).where(Vacancy.company_id == actor.user.company_id)
    if not actor.is_ca:
        vacancies = vacancies.where(Vacancy.company_supervisor_id == actor.id)
    applicants = db.scalar(select(func.count()).select_from(Application)
                           .where(Application.vacancy_id.in_(vacancies), Application.status == "submitted"))
    placements = _company_placements(db, actor)
    now, evaluations_due = clock.now(), 0
    for p in placements:
        cycle = db.get(TrainingCycle, p.cycle_id)
        for type_ in TYPES:
            e = db.scalar(select(Evaluation.status).where(Evaluation.placement_id == p.id, Evaluation.type == type_))
            if e != "submitted" and due_at(cycle, type_) <= now + SOON:
                evaluations_due += 1
    return [_item("applicants_to_review", applicants, "/company/vacancies"),
            _item("attendance_to_record", overdue_weeks(db, placements), "/company/trainees"),
            _item("evaluations_due", evaluations_due, "/company/trainees")]


def _academic(db: Session, actor: Actor) -> list[dict]:
    mine = select(Placement.id).where(Placement.academic_supervisor_id == actor.id, Placement.status == "active")
    to_review = db.scalar(select(func.count()).select_from(ReportSlot)
                          .where(ReportSlot.placement_id.in_(mine), ReportSlot.status == "submitted"))
    ready = returned = 0
    for g, p in db.execute(select(Grade, Placement).join(Placement, Placement.id == Grade.placement_id)
                           .where(Placement.academic_supervisor_id == actor.id, Grade.status == "draft",
                                  Placement.status == "active")):
        if all(c["ok"] for c in grades.preconditions(db, g, p)):
            ready += 1
        if g.return_comment:
            returned += 1
    return [_item("reports_to_review", to_review, "/academic/students"),
            _item("grades_to_submit", ready, "/academic/grades?status=draft"),
            _item("grades_returned", returned, "/academic/grades?status=draft")]


def _coordinator(db: Session, actor: Actor) -> list[dict]:
    college = actor.user.college_id
    students = select(User.id).where(User.college_id == college, User.role == "student")
    verify = db.scalar(select(func.count()).select_from(VerificationRequest).where(
        VerificationRequest.kind == "student", VerificationRequest.college_id == college,
        VerificationRequest.status == "pending"))
    to_place = db.scalar(select(func.count()).select_from(Application).where(
        Application.student_id.in_(students), Application.status == "accepted"))
    to_approve = db.scalar(select(func.count()).select_from(Grade).join(Placement, Placement.id == Grade.placement_id)
                           .where(Placement.student_id.in_(students), Grade.status == "submitted"))
    return [_item("students_to_verify", verify, "/coordinator/students"),
            _item("placements_to_confirm", to_place, "/coordinator/placements"),
            _item("grades_to_approve", to_approve, "/coordinator/grades?status=submitted")]


def _platform(db: Session) -> list[dict]:
    pending = select(VerificationRequest).where(VerificationRequest.kind.in_(("coordinator", "company")),
                                                VerificationRequest.status == "pending")
    count = db.scalar(select(func.count()).select_from(pending.subquery()))
    oldest = db.scalar(select(func.min(VerificationRequest.created_at)).where(
        VerificationRequest.kind.in_(("coordinator", "company")), VerificationRequest.status == "pending"))
    age = (clock.now() - oldest).days if oldest else None
    return [_item("verifications_pending", count, "/platform/verifications", oldest_days=age)]


def dashboard(db: Session, actor: Actor) -> dict:
    handlers = {"st": _student, "cs": _company, "as": _academic, "co": _coordinator}
    items = _platform(db) if actor.code == "pa" else handlers[actor.code](db, actor)
    return {"role": actor.user.role, "items": items}


# ---------------------------------------------------------------- coordinator cycle statistics (FR-DSH-02)
def _rate(part: int, whole: int) -> float | None:
    return round(100 * part / whole, 1) if whole else None


def _figures(db: Session, cycle: TrainingCycle, placements: list[Placement], enrolled: int | None) -> dict:
    now = clock.now()
    ids = [p.id for p in placements]
    due_slots = list(db.scalars(select(ReportSlot).where(ReportSlot.placement_id.in_(ids), ReportSlot.due_at < now))) \
        if ids else []
    submitted = [s for s in due_slots if s.status in ("submitted", "revision_requested", "accepted")]
    late = [s for s in submitted if s.is_late]
    weeks = db.execute(select(func.sum(AttendanceWeek.attended_days), func.sum(AttendanceWeek.scheduled_days))
                       .where(AttendanceWeek.placement_id.in_(ids), AttendanceWeek.attended_days.is_not(None))
                       ).one() if ids else (0, 0)
    expected = done = 0
    for type_ in TYPES:
        if due_at(cycle, type_) <= now:
            expected += len(ids)
            done += db.scalar(select(func.count()).select_from(Evaluation).where(
                Evaluation.placement_id.in_(ids), Evaluation.type == type_, Evaluation.status == "submitted")) \
                if ids else 0
    out = {"placed": len(placements), "reports_due": len(due_slots), "reports_submitted": len(submitted),
           "submission_rate": _rate(len(submitted), len(due_slots)), "late_rate": _rate(len(late), len(submitted)),
           "attended_days": int(weeks[0] or 0), "scheduled_days": int(weeks[1] or 0),
           "attendance_rate": _rate(int(weeks[0] or 0), int(weeks[1] or 0)),
           "evaluations_expected": expected, "evaluations_submitted": done,
           "evaluation_completion": _rate(done, expected)}
    if enrolled is not None:
        out.update(enrolled=enrolled, unplaced=enrolled - len(placements))
    return out


def cycle_stats(db: Session, cycle: TrainingCycle, company_id: uuid.UUID | None) -> dict:
    stmt = select(Placement).where(Placement.cycle_id == cycle.id, Placement.status != "cancelled")
    placements = list(db.scalars(stmt))
    enrolled = db.scalar(select(func.count()).select_from(Enrollment).where(Enrollment.cycle_id == cycle.id))
    vacancies = {v.id: v for v in db.scalars(select(Vacancy).where(Vacancy.id.in_({p.vacancy_id for p in placements})))}
    by_company: dict[uuid.UUID, list[Placement]] = {}
    for p in placements:
        by_company.setdefault(vacancies[p.vacancy_id].company_id, []).append(p)
    companies = []
    for cid, items in sorted(by_company.items(), key=lambda kv: db.get(Company, kv[0]).name):
        if company_id and cid != company_id:
            continue
        companies.append({"company_id": cid, "company_name": db.get(Company, cid).name,
                          **_figures(db, cycle, items, None)})
    return {"cycle_id": cycle.id, "overall": _figures(db, cycle, placements, enrolled), "companies": companies}


# ---------------------------------------------------------------- platform figures (FR-DSH-05)
def platform_stats(db: Session) -> dict:
    colleges = db.scalars(select(College).where(College.is_active)).all()
    with_coordinator = set(db.scalars(select(User.college_id).where(
        User.role == "coordinator", User.verification_status == "verified", User.is_active)))
    users = dict(db.execute(select(User.role, func.count()).where(User.is_active).group_by(User.role)).all())
    pending = _platform(db)[0]
    return {
        "universities": db.scalar(select(func.count()).select_from(University).where(University.is_active)),
        "colleges": len(colleges),
        "colleges_with_coordinator": sum(c.id in with_coordinator for c in colleges),
        "colleges_without_coordinator": sum(c.id not in with_coordinator for c in colleges),
        "verified_companies": db.scalar(select(func.count()).select_from(Company).where(Company.status == "verified")),
        "users_by_role": {r: users.get(r, 0) for r in ("student", "company_supervisor", "academic_supervisor",
                                                        "coordinator", "platform_admin")},
        "pending_verifications": pending["count"], "oldest_pending_days": pending["oldest_days"],
        "published_vacancies": db.scalar(select(func.count()).select_from(Vacancy)
                                         .where(Vacancy.status == "published")),
    }

