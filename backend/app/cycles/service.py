"""Training cycles of a college: weeks and deadlines, grade components, rubric (FR-CYC-01 – 03, FR-CYC-05,
Design 5.2)."""
import uuid
from datetime import date, time, timedelta
from decimal import Decimal

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.core import audit, clock
from app.core.deps import Actor
from app.core.errors import ApiError, conflict, field_error, forbidden, not_found
from app.models import (
    CycleWeek,
    Enrollment,
    Grade,
    GradeComponent,
    Major,
    Placement,
    ReportSlot,
    RubricCriterion,
    StudentProfile,
    TrainingCycle,
    User,
    Vacancy,
)

SCHEDULE_FIELDS = ("start_date", "end_date", "weeks", "working_days", "report_weekday", "report_time")


# ---------------------------------------------------------------- week generation (Design 5.2)
def build_weeks(start: date, end: date, weeks: int, working_days: list[int], report_weekday: int,
                report_time: time) -> list[dict]:
    out = []
    for k in range(1, weeks + 1):
        starts_on = start + timedelta(days=7 * (k - 1))
        ends_on = start + timedelta(days=7 * k - 1)
        report_day = next(starts_on + timedelta(days=i) for i in range(7)
                          if (starts_on + timedelta(days=i)).isoweekday() == report_weekday)
        days = (starts_on + timedelta(days=i) for i in range(7))
        scheduled = sum(1 for d in days if start <= d <= end and d.isoweekday() in working_days)
        out.append({"week_no": k, "starts_on": starts_on, "ends_on": ends_on,
                    "report_due_at": clock.riyadh_to_utc(report_day, report_time), "scheduled_days": scheduled})
    return out


def check_schedule(start: date, end: date, weeks: int) -> None:
    if end <= start:
        raise field_error("end_date", "VALIDATION_ERROR")
    if start + timedelta(days=7 * weeks - 1) > end:
        raise field_error("weeks", "VALIDATION_ERROR")


def regenerate_weeks(db: Session, cycle: TrainingCycle) -> None:
    for w in db.scalars(select(CycleWeek).where(CycleWeek.cycle_id == cycle.id)):
        db.delete(w)
    db.flush()
    for w in build_weeks(cycle.start_date, cycle.end_date, cycle.weeks, cycle.working_days, cycle.report_weekday,
                         cycle.report_time):
        db.add(CycleWeek(cycle_id=cycle.id, **w))


# ---------------------------------------------------------------- access
def can_view(db: Session, actor: Actor, cycle: TrainingCycle) -> bool:
    code = actor.code
    if code == "co":
        return cycle.college_id == actor.user.college_id
    if code == "st":
        return db.get(Enrollment, (cycle.id, actor.id)) is not None
    if code == "as":
        return bool(db.scalar(select(exists().where(Placement.cycle_id == cycle.id,
                                                    Placement.academic_supervisor_id == actor.id))))
    if code == "cs":
        cond = (Placement.vacancy_id == Vacancy.id) & (Vacancy.company_id == actor.user.company_id) \
            if actor.is_ca else Placement.company_supervisor_id == actor.id
        return bool(db.scalar(select(exists().where(Placement.cycle_id == cycle.id, cond))))
    return False


def cycles_query(actor: Actor):
    stmt = select(TrainingCycle).order_by(TrainingCycle.start_date.desc())
    code = actor.code
    if code == "co":
        return stmt.where(TrainingCycle.college_id == actor.user.college_id)
    if code == "st":
        return stmt.where(TrainingCycle.id.in_(select(Enrollment.cycle_id).where(Enrollment.student_id == actor.id)))
    if code == "as":
        return stmt.where(TrainingCycle.id.in_(select(Placement.cycle_id)
                                               .where(Placement.academic_supervisor_id == actor.id)))
    if actor.is_ca:
        company = (select(Placement.cycle_id).join(Vacancy, Vacancy.id == Placement.vacancy_id)
                   .where(Vacancy.company_id == actor.user.company_id))
        return stmt.where(TrainingCycle.id.in_(company))
    return stmt.where(TrainingCycle.id.in_(select(Placement.cycle_id)
                                           .where(Placement.company_supervisor_id == actor.id)))


def ensure_coordinator(actor: Actor, cycle: TrainingCycle) -> None:
    if actor.code != "co" or cycle.college_id != actor.user.college_id:
        raise forbidden()


def ensure_open(cycle: TrainingCycle) -> None:
    if cycle.status != "open":
        raise conflict("CYCLE_CLOSED")


def schedule_locked(db: Session, cycle: TrainingCycle) -> bool:
    return bool(db.scalar(select(exists().where(Placement.cycle_id == cycle.id, Placement.status != "cancelled"))))


def cycle_out(db: Session, c: TrainingCycle, with_weeks: bool = False) -> dict:
    out = {k: getattr(c, k) for k in ("id", "college_id", "name", "type", "start_date", "end_date", "weeks",
                                       "working_days", "report_weekday", "report_time", "periodic_eval_due_at",
                                       "final_eval_due_at", "final_report_due_at", "status", "rubric_locked_at",
                                       "closed_at")}
    out["schedule_locked"] = schedule_locked(db, c)
    out["enrolled_students"] = db.scalar(select(func.count()).select_from(Enrollment)
                                         .where(Enrollment.cycle_id == c.id))
    if with_weeks:
        out["week_list"] = weeks_out(db, c)
    return out


def weeks_out(db: Session, c: TrainingCycle) -> list[dict]:
    return [{"week_no": w.week_no, "starts_on": w.starts_on, "ends_on": w.ends_on, "report_due_at": w.report_due_at,
             "scheduled_days": w.scheduled_days}
            for w in db.scalars(select(CycleWeek).where(CycleWeek.cycle_id == c.id).order_by(CycleWeek.week_no))]


# ---------------------------------------------------------------- create and edit
def _name_taken(db: Session, college_id: uuid.UUID, name: str, exclude: uuid.UUID | None = None) -> bool:
    stmt = select(TrainingCycle.id).where(TrainingCycle.college_id == college_id, TrainingCycle.name == name.strip())
    if exclude:
        stmt = stmt.where(TrainingCycle.id != exclude)
    return db.scalar(stmt) is not None


def create(db: Session, actor: Actor, data: dict) -> TrainingCycle:
    check_schedule(data["start_date"], data["end_date"], data["weeks"])
    if _name_taken(db, actor.user.college_id, data["name"]):
        raise conflict("DUPLICATE_NAME")
    fields = {**data, "name": data["name"].strip()}
    cycle = TrainingCycle(college_id=actor.user.college_id, created_by=actor.id, **fields)
    db.add(cycle)
    db.flush()
    regenerate_weeks(db, cycle)
    audit.record(db, actor.user, "create", "training_cycle", cycle.id, college_id=cycle.college_id, cycle_id=cycle.id,
                 new={"name": cycle.name, "type": cycle.type, "weeks": cycle.weeks})
    return cycle


def patch(db: Session, actor: Actor, cycle: TrainingCycle, data: dict) -> None:
    ensure_open(cycle)
    if data.get("name") and _name_taken(db, cycle.college_id, data["name"], exclude=cycle.id):
        raise conflict("DUPLICATE_NAME")
    schedule_change = any(k in data and data[k] != getattr(cycle, k) for k in SCHEDULE_FIELDS)
    if schedule_change and schedule_locked(db, cycle):
        raise conflict("SCHEDULE_LOCKED")
    if "working_days" in data and data["working_days"] is not None:
        days = data["working_days"]
        if not days or len(set(days)) != len(days) or any(d < 1 or d > 7 for d in days):
            raise field_error("working_days", "VALIDATION_ERROR")
    data = {k: v for k, v in data.items() if v is not None}
    check_schedule(data.get("start_date", cycle.start_date), data.get("end_date", cycle.end_date),
                   data.get("weeks", cycle.weeks))
    old, new = audit.changes(cycle, data)
    if schedule_change:
        regenerate_weeks(db, cycle)
    if new:
        audit.record(db, actor.user, "update", "training_cycle", cycle.id, college_id=cycle.college_id,
                     cycle_id=cycle.id, old=old, new=new)


def move_week(db: Session, actor: Actor, cycle: TrainingCycle, week_no: int, due_at, reason: str) -> CycleWeek:
    ensure_open(cycle)
    if not reason.strip():
        raise ApiError(422, "REASON_REQUIRED")
    week = db.get(CycleWeek, (cycle.id, week_no))
    if week is None:
        raise not_found()
    old = week.report_due_at
    week.report_due_at = due_at
    slots = db.scalars(select(ReportSlot).join(Placement, Placement.id == ReportSlot.placement_id)
                       .where(Placement.cycle_id == cycle.id, ReportSlot.kind == "weekly",
                              ReportSlot.week_no == week_no, ReportSlot.status == "draft"))
    for slot in slots:
        slot.due_at = due_at
    audit.record(db, actor.user, "move_deadline", "cycle_week", f"{cycle.id}:{week_no}", college_id=cycle.college_id,
                 cycle_id=cycle.id, old={"report_due_at": old}, new={"report_due_at": due_at}, reason=reason.strip())
    return week


def close(db: Session, actor: Actor, cycle: TrainingCycle) -> None:
    ensure_open(cycle)
    cycle.status, cycle.closed_at = "closed", clock.now()
    audit.record(db, actor.user, "close", "training_cycle", cycle.id, college_id=cycle.college_id, cycle_id=cycle.id,
                 old={"status": "open"}, new={"status": "closed"})


def reopen(db: Session, actor: Actor, cycle: TrainingCycle, reason: str) -> None:
    if cycle.status != "closed":
        raise conflict("INVALID_TRANSITION")
    if cycle.anonymized_at is not None:  # its personal data is gone (NFR-PRV-04)
        raise conflict("ALREADY_ANONYMIZED")
    if not reason.strip():
        raise ApiError(422, "REASON_REQUIRED")
    cycle.status, cycle.closed_at = "open", None
    audit.record(db, actor.user, "reopen", "training_cycle", cycle.id, college_id=cycle.college_id, cycle_id=cycle.id,
                 old={"status": "closed"}, new={"status": "open"}, reason=reason.strip())


# ---------------------------------------------------------------- grade components and rubric
def components_out(db: Session, cycle: TrainingCycle) -> list[dict]:
    return [{"id": c.id, "name_en": c.name_en, "name_ar": c.name_ar, "weight": c.weight, "source": c.source}
            for c in db.scalars(select(GradeComponent).where(GradeComponent.cycle_id == cycle.id)
                                .order_by(GradeComponent.position))]


def replace_components(db: Session, actor: Actor, cycle: TrainingCycle, items: list[dict]) -> None:
    ensure_open(cycle)
    if db.scalar(select(Grade.id).join(Placement, Placement.id == Grade.placement_id)
                 .where(Placement.cycle_id == cycle.id, Grade.status != "draft").limit(1)):
        raise conflict("GRADES_EXIST")  # FR-CYC-02: weights are fixed once a grade is submitted
    total = sum((Decimal(str(i["weight"])) for i in items), Decimal(0))
    if total != Decimal(100):
        raise field_error("weights", "WEIGHTS_NOT_100")
    if sum(1 for i in items if i["source"] == "company_final_evaluation") > 1:
        raise field_error("components", "VALIDATION_ERROR")
    names = [i["name_en"].strip().lower() for i in items]
    if len(set(names)) != len(names):
        raise field_error("components", "DUPLICATE_NAME")
    old = components_out(db, cycle)
    for c in db.scalars(select(GradeComponent).where(GradeComponent.cycle_id == cycle.id)):
        db.delete(c)
    db.flush()
    for pos, i in enumerate(items, start=1):
        db.add(GradeComponent(cycle_id=cycle.id, name_en=i["name_en"].strip(), name_ar=i["name_ar"].strip(),
                              weight=i["weight"], source=i["source"], position=pos))
    audit.record(db, actor.user, "replace_components", "training_cycle", cycle.id, college_id=cycle.college_id,
                 cycle_id=cycle.id, old={"components": old},
                 new={"components": [{k: i[k] for k in ("name_en", "weight", "source")} for i in items]})


def rubric_out(db: Session, cycle: TrainingCycle) -> dict:
    criteria = [{"id": c.id, "name_en": c.name_en, "name_ar": c.name_ar, "levels": c.levels}
                for c in db.scalars(select(RubricCriterion).where(RubricCriterion.cycle_id == cycle.id)
                                    .order_by(RubricCriterion.position))]
    return {"locked": cycle.rubric_locked_at is not None, "criteria": criteria}


def replace_rubric(db: Session, actor: Actor, cycle: TrainingCycle, criteria: list[dict]) -> None:
    ensure_open(cycle)
    if cycle.rubric_locked_at is not None:
        raise conflict("RUBRIC_LOCKED")
    for c in db.scalars(select(RubricCriterion).where(RubricCriterion.cycle_id == cycle.id)):
        db.delete(c)
    db.flush()
    for pos, c in enumerate(criteria, start=1):
        db.add(RubricCriterion(cycle_id=cycle.id, name_en=c["name_en"].strip(), name_ar=c["name_ar"].strip(),
                               levels=c["levels"], position=pos))
    audit.record(db, actor.user, "replace_rubric", "training_cycle", cycle.id, college_id=cycle.college_id,
                 cycle_id=cycle.id, new={"criteria": [c["name_en"] for c in criteria]})


def enrollments_out(db: Session, cycle: TrainingCycle) -> list[dict]:
    rows = db.execute(select(Enrollment, User, StudentProfile, Major)
                      .join(User, User.id == Enrollment.student_id)
                      .join(StudentProfile, StudentProfile.user_id == User.id)
                      .join(Major, Major.id == StudentProfile.major_id)
                      .where(Enrollment.cycle_id == cycle.id).order_by(User.name_en)).all()
    placed = set(db.scalars(select(Placement.student_id).where(Placement.cycle_id == cycle.id,
                                                               Placement.status != "cancelled")))
    return [{"student_id": u.id, "name_en": u.name_en, "name_ar": u.name_ar, "email": u.email,
             "student_number": p.student_number, "major_en": m.name_en, "major_ar": m.name_ar, "gpa": p.gpa,
             "is_active": u.is_active, "placed": u.id in placed, "enrolled_at": e.created_at}
            for e, u, p, m in rows]


def student_open_enrollment(db: Session, student_id: uuid.UUID) -> TrainingCycle | None:
    return db.scalar(select(TrainingCycle).join(Enrollment, Enrollment.cycle_id == TrainingCycle.id)
                     .where(Enrollment.student_id == student_id, TrainingCycle.status == "open")
                     .order_by(TrainingCycle.start_date.desc()))
