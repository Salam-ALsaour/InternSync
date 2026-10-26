"""Weekly attendance (FR-ATT-01 – 04; Increment 2 design, Section 5)."""
from datetime import datetime, time, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import audit, clock, settings
from app.core.deps import Actor
from app.core.errors import ApiError, conflict, forbidden
from app.models import AttendanceWeek, CycleWeek, Placement, User
from app.reports.service import ensure_writable


def week_start(w: CycleWeek) -> datetime:
    return clock.riyadh_to_utc(w.starts_on, time(0, 0))


def week_end(w: CycleWeek) -> datetime:
    return clock.riyadh_to_utc(w.ends_on, time(23, 59, 59))


def state(db: Session, w: CycleWeek, row: AttendanceWeek | None, now: datetime | None = None) -> tuple[str, bool]:
    """The week's state (upcoming, open, pending, overdue, recorded) and whether it is locked for editing: more
    than `attendance.edit_days` days after its end and not unlocked by the coordinator (FR-ATT-02)."""
    now = now or clock.now()
    end = week_end(w)
    unlocked = row is not None and row.unlocked_until is not None and now <= row.unlocked_until
    locked = now > end + timedelta(days=settings.get(db, "attendance.edit_days")) and not unlocked
    if row is not None and row.attended_days is not None:
        return "recorded", locked
    if now < week_start(w):
        return "upcoming", False
    if now <= end:
        return "open", False
    if now > end + timedelta(days=settings.get(db, "attendance.pending_after_days")):
        return "overdue", locked
    return "pending", locked


def percent(attended: int, scheduled: int) -> float | None:
    if scheduled == 0:
        return None
    return float((Decimal(100 * attended) / Decimal(scheduled)).quantize(Decimal("0.1"), ROUND_HALF_UP))


def summary(db: Session, placement: Placement) -> dict:
    rows = {r.week_no: r for r in db.scalars(select(AttendanceWeek).where(AttendanceWeek.placement_id == placement.id))}
    weeks = db.scalars(select(CycleWeek).where(CycleWeek.cycle_id == placement.cycle_id).order_by(CycleWeek.week_no))
    out, attended, scheduled = [], 0, 0
    now = clock.now()
    for w in weeks:
        row = rows.get(w.week_no)
        recorded = row is not None and row.attended_days is not None
        if recorded:
            attended, scheduled = attended + row.attended_days, scheduled + row.scheduled_days
        recorder = db.get(User, row.recorded_by) if recorded else None
        st, locked = state(db, w, row, now)
        out.append({"week_no": w.week_no, "starts_on": w.starts_on, "ends_on": w.ends_on,
                    "scheduled_days": row.scheduled_days if recorded else w.scheduled_days,
                    "attended_days": row.attended_days if recorded else None, "note": row.note if row else None,
                    "state": st, "locked": locked, "recorded_at": row.recorded_at if row else None,
                    "recorded_by_en": recorder.name_en if recorder else None,
                    "recorded_by_ar": recorder.name_ar if recorder else None,
                    "unlocked_until": row.unlocked_until if row else None})
    return {"placement_id": placement.id, "weeks": out, "attended_days": attended, "scheduled_days": scheduled,
            "percent": percent(attended, scheduled)}


def placement_percent(db: Session, placement: Placement) -> float | None:
    rows = db.execute(select(AttendanceWeek.attended_days, AttendanceWeek.scheduled_days)
                      .where(AttendanceWeek.placement_id == placement.id,
                             AttendanceWeek.attended_days.is_not(None))).all()
    return percent(sum(a for a, _ in rows), sum(s for _, s in rows))


def _week(db: Session, placement: Placement, week_no: int) -> CycleWeek:
    w = db.get(CycleWeek, (placement.cycle_id, week_no))
    if w is None:
        raise ApiError(404, "NOT_FOUND")
    return w


def record(db: Session, actor: Actor, placement: Placement, week_no: int, full: bool, attended: int | None,
           note: str | None) -> None:
    """FR-ATT-01: by the placement's company supervisor; "full" records every scheduled day in one action."""
    if placement.company_supervisor_id != actor.id:
        raise forbidden()
    ensure_writable(db, placement)
    w = _week(db, placement, week_no)
    row = db.scalar(select(AttendanceWeek).where(AttendanceWeek.placement_id == placement.id,
                                                 AttendanceWeek.week_no == week_no))
    current, locked = state(db, w, row)
    if current == "upcoming":
        raise conflict("WEEK_NOT_STARTED")
    if locked:
        raise conflict("WEEK_LOCKED")
    days = w.scheduled_days if full else attended
    if days is None:
        raise ApiError(422, "VALIDATION_ERROR", errors=[{"field": "attended_days", "code": "VALIDATION_ERROR"}])
    if days > w.scheduled_days:
        raise ApiError(422, "ATTENDED_EXCEEDS_SCHEDULED")
    now = clock.now()
    old = {"attended_days": row.attended_days} if row is not None and row.attended_days is not None else None
    if row is None:
        row = AttendanceWeek(placement_id=placement.id, week_no=week_no, scheduled_days=w.scheduled_days)
        db.add(row)
    row.scheduled_days, row.attended_days = w.scheduled_days, days
    row.note = (note or "").strip() or None
    row.recorded_by, row.recorded_at = actor.id, now
    student = db.get(User, placement.student_id)
    audit.record(db, actor.user, "record_attendance", "attendance_week", f"{placement.id}:{week_no}",
                 student_id=student.id, college_id=student.college_id, cycle_id=placement.cycle_id, old=old,
                 new={"attended_days": days, "scheduled_days": w.scheduled_days, "full": full})


def unlock(db: Session, actor: Actor, placement: Placement, week_no: int, reason: str,
           until: datetime | None) -> None:
    """FR-ATT-02: the coordinator reopens a locked week until `until` (default: 7 days from now)."""
    if not reason.strip():
        raise ApiError(422, "REASON_REQUIRED")
    ensure_writable(db, placement)
    w = _week(db, placement, week_no)
    now = clock.now()
    until = until or now + timedelta(days=7)
    if until <= now:
        raise ApiError(422, "VALIDATION_ERROR", errors=[{"field": "until", "code": "VALIDATION_ERROR"}])
    row = db.scalar(select(AttendanceWeek).where(AttendanceWeek.placement_id == placement.id,
                                                 AttendanceWeek.week_no == week_no))
    if row is None:
        row = AttendanceWeek(placement_id=placement.id, week_no=week_no, scheduled_days=w.scheduled_days)
        db.add(row)
    row.unlocked_until, row.unlocked_by, row.unlock_reason = until, actor.id, reason.strip()
    student = db.get(User, placement.student_id)
    audit.record(db, actor.user, "unlock_attendance", "attendance_week", f"{placement.id}:{week_no}",
                 student_id=student.id, college_id=student.college_id, cycle_id=placement.cycle_id,
                 new={"unlocked_until": until}, reason=reason.strip())


def overdue_weeks(db: Session, placements: list[Placement]) -> int:
    """FR-ATT-04: ended weeks without a record, more than `attendance.pending_after_days` days after the end."""
    now, count = clock.now(), 0
    for p in placements:
        rows = {r.week_no: r for r in db.scalars(select(AttendanceWeek).where(AttendanceWeek.placement_id == p.id))}
        for w in db.scalars(select(CycleWeek).where(CycleWeek.cycle_id == p.cycle_id)):
            if state(db, w, rows.get(w.week_no), now)[0] == "overdue":
                count += 1
    return count
