"""Reminders, Missing notices, and escalations (FR-NOT-02 – 04; Design 5.3). Each selects work by state and keys
every message, so a run repeated or delayed by downtime never sends a message twice (NFR-REL-03)."""
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.attendance.service import week_end
from app.core import clock, settings
from app.evaluations.service import due_at
from app.models import (
    AttendanceWeek,
    CycleWeek,
    Evaluation,
    Placement,
    ReportSlot,
    ReportVersion,
    TrainingCycle,
    User,
)
from app.notifications.events import EVALUATION, due_text
from app.notifications.service import coordinator_of, notify
from app.notifications.texts import names, report_label


def send_reminders(db: Session) -> int:
    """FR-NOT-02: unsubmitted slots due within `notifications.reminder_hours_before` hours."""
    now = clock.now()
    until = now + timedelta(hours=settings.get(db, "notifications.reminder_hours_before"))
    rows = db.execute(select(ReportSlot, Placement).join(Placement, Placement.id == ReportSlot.placement_id)
                      .where(ReportSlot.status.in_(("draft", "revision_requested")), ReportSlot.due_at > now,
                             ReportSlot.due_at <= until, Placement.status == "active")).all()
    sent = 0
    for slot, p in rows:
        params = {**report_label(slot.week_no), "due": due_text(slot.due_at)}
        sent += notify(db, [p.student_id], "report.reminder", params, f"/reports/{slot.id}", key=f"reminder:{slot.id}")
    return sent


def report_missing(db: Session, slot: ReportSlot, p: Placement) -> None:
    """FR-NOT-03: called by the Missing flag for each slot it flags."""
    student = db.get(User, p.student_id)
    params = {**names("student", student.name_en, student.name_ar), **report_label(slot.week_no),
              "due": due_text(slot.due_at)}
    notify(db, [p.student_id, p.academic_supervisor_id], "report.missing", params, f"/reports/{slot.id}",
           key=f"missing:{slot.id}")


@dataclass
class Overdue:
    kind: str  # report, attendance, evaluation
    key: str
    placement: Placement
    item_en: str
    item_ar: str
    due: datetime


def overdue_items(db: Session, college_id: uuid.UUID | None = None) -> list[Overdue]:
    """FR-NOT-04: reports not submitted, attendance weeks not recorded, and evaluations not submitted, at least
    `notifications.escalation_days` days after their deadline, for active placements (of one college if given)."""
    cutoff = clock.now() - timedelta(days=settings.get(db, "notifications.escalation_days"))
    stmt = select(Placement).where(Placement.status == "active")
    if college_id is not None:
        stmt = stmt.join(User, User.id == Placement.student_id).where(User.college_id == college_id)
    placements = db.scalars(stmt).all()
    if not placements:
        return []
    ids = [p.id for p in placements]
    by_id = {p.id: p for p in placements}
    out: list[Overdue] = []
    submitted = select(ReportVersion.id).where(ReportVersion.slot_id == ReportSlot.id,
                                               ReportVersion.submitted_at.is_not(None))
    for slot in db.scalars(select(ReportSlot).where(ReportSlot.placement_id.in_(ids), ReportSlot.status == "draft",
                                                    ReportSlot.due_at <= cutoff, ~submitted.exists())):
        label = report_label(slot.week_no)
        out.append(Overdue("report", f"report:{slot.id}", by_id[slot.placement_id], f"The {label['report_en']}",
                           label["report_ar"], slot.due_at))
    recorded = {(r.placement_id, r.week_no) for r in db.scalars(select(AttendanceWeek).where(
        AttendanceWeek.placement_id.in_(ids), AttendanceWeek.attended_days.is_not(None)))}
    cycles = {c.id: c for c in db.scalars(select(TrainingCycle).where(
        TrainingCycle.id.in_({p.cycle_id for p in placements})))}
    weeks = db.scalars(select(CycleWeek).where(CycleWeek.cycle_id.in_(cycles))).all()
    submitted_evals = {(e.placement_id, e.type) for e in db.scalars(select(Evaluation).where(
        Evaluation.placement_id.in_(ids), Evaluation.status == "submitted"))}
    for p in placements:
        for w in weeks:
            if w.cycle_id == p.cycle_id and week_end(w) <= cutoff and (p.id, w.week_no) not in recorded:
                out.append(Overdue("attendance", f"attendance:{p.id}:{w.week_no}", p,
                                   f"The attendance of week {w.week_no}", f"حضور الأسبوع {w.week_no}", week_end(w)))
        for type_, (label_en, label_ar) in EVALUATION.items():
            due = due_at(cycles[p.cycle_id], type_)
            if due is not None and due <= cutoff and (p.id, type_) not in submitted_evals:
                out.append(Overdue("evaluation", f"evaluation:{p.id}:{type_}", p, f"The {label_en}", label_ar, due))
    return out


def escalate_overdue(db: Session) -> int:
    days = settings.get(db, "notifications.escalation_days")
    sent = 0
    for item in overdue_items(db):
        student = db.get(User, item.placement.student_id)
        params = {**names("student", student.name_en, student.name_ar), "item_en": item.item_en,
                  "item_ar": item.item_ar, "days": days}
        sent += notify(db, [coordinator_of(db, student.college_id)], "escalation.overdue", params,
                       f"/placements/{item.placement.id}", key=f"escalation:{item.key}")
    return sent
