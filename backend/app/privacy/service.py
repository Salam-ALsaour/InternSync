"""Retention period and anonymization of a closed cycle (NFR-PRV-04; Design 4.5; Increment 4 design, Section 7).

Everything runs in the caller's transaction. Personal data is removed or replaced; statuses, scores, dates, majors,
companies, and survey answers stay, so the statistics of the cycle do not change. The audit log is append-only and
is masked when it is read instead."""
import calendar
import uuid
from datetime import datetime

from sqlalchemy import delete, or_, select, update
from sqlalchemy.orm import Session

from app.core import audit, clock, files
from app.core.deps import Actor
from app.core.errors import ApiError, conflict
from app.models import (
    AccountToken,
    AttendanceWeek,
    Certificate,
    College,
    CompanyEvaluation,
    Cv,
    CvExtractedSkill,
    Enrollment,
    Evaluation,
    Grade,
    MatchScore,
    Notification,
    Placement,
    PushSubscription,
    ReportAttachment,
    ReportComment,
    ReportPassage,
    ReportReview,
    ReportSlot,
    ReportVersion,
    SimilarityCheck,
    StoredFile,
    StudentProfile,
    StudentSkill,
    TrainingCycle,
    User,
    UserSession,
    VerificationDocument,
    VerificationRequest,
)

PLACEHOLDER = "—"  # for texts that must not be empty


def add_months(at: datetime, months: int) -> datetime:
    month = at.month - 1 + months
    year, month = at.year + month // 12, month % 12 + 1
    return at.replace(year=year, month=month, day=min(at.day, calendar.monthrange(year, month)[1]))


def eligible_at(db: Session, cycle: TrainingCycle) -> datetime | None:
    if cycle.status != "closed" or cycle.closed_at is None:
        return None
    return add_months(cycle.closed_at, db.get(College, cycle.college_id).retention_months)


def _past_retention(db: Session, cycle: TrainingCycle, now: datetime) -> bool:
    at = eligible_at(db, cycle)
    return at is not None and now >= at


def _students(db: Session, cycle: TrainingCycle) -> set[uuid.UUID]:
    placed = db.scalars(select(Placement.student_id).where(Placement.cycle_id == cycle.id))
    enrolled = db.scalars(select(Enrollment.student_id).where(Enrollment.cycle_id == cycle.id))
    return set(placed) | set(enrolled)


def _other_cycles(db: Session, student_id: uuid.UUID, cycle: TrainingCycle) -> set[uuid.UUID]:
    placed = db.scalars(select(Placement.cycle_id).where(Placement.student_id == student_id))
    enrolled = db.scalars(select(Enrollment.cycle_id).where(Enrollment.student_id == student_id))
    return (set(placed) | set(enrolled)) - {cycle.id}


def plan(db: Session, cycle: TrainingCycle) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
    """The students to anonymize now and the ones skipped because another of their cycles is still kept."""
    now, todo, skipped = clock.now(), [], []
    for sid in sorted(_students(db, cycle)):
        if db.get(User, sid).anonymized_at is not None:
            continue
        others = [db.get(TrainingCycle, c) for c in _other_cycles(db, sid, cycle)]
        (todo if all(_past_retention(db, c, now) for c in others) else skipped).append(sid)
    return todo, skipped


def preview(db: Session, cycle: TrainingCycle) -> dict:
    at = eligible_at(db, cycle)
    todo, skipped = plan(db, cycle)
    if cycle.status != "closed":
        status = "open"
    elif clock.now() < at:
        status = "waiting"
    elif todo:
        status = "ready"
    else:
        status = "done" if cycle.anonymized_at else "ready"
    return {"cycle_id": cycle.id, "status": status, "closed_at": cycle.closed_at, "eligible_at": at,
            "retention_months": db.get(College, cycle.college_id).retention_months,
            "students": len(todo), "skipped": len(skipped), "anonymized_at": cycle.anonymized_at}


def set_retention(db: Session, actor: Actor, college: College, months: int) -> None:
    if not 0 <= months <= 120:
        raise ApiError(422, "VALIDATION_ERROR", errors=[{"field": "retention_months", "code": "OUT_OF_RANGE",
                                                         "message": "0–120"}])
    old, college.retention_months = college.retention_months, months
    audit.record(db, actor.user, "update", "college", college.id, college_id=college.id,
                 old={"retention_months": old}, new={"retention_months": months})


def _purge(db: Session, file_id: uuid.UUID | None, now: datetime) -> None:
    f = db.get(StoredFile, file_id) if file_id else None
    if f is None or f.purged_at is not None:
        return
    files.storage().delete(f.storage_key)
    f.purged_at, f.original_name = now, "removed"


def _anonymize_placement(db: Session, p: Placement, now: datetime) -> None:
    slots = list(db.scalars(select(ReportSlot.id).where(ReportSlot.placement_id == p.id)))
    versions = list(db.scalars(select(ReportVersion.id).where(ReportVersion.slot_id.in_(slots)))) if slots else []
    if versions:
        db.execute(update(ReportVersion).where(ReportVersion.id.in_(versions)).values(
            tasks_performed=None, learning=None, challenges=None, next_week_plan=None, summary=None, body_text=None))
        for file_id in db.scalars(select(ReportAttachment.file_id).where(ReportAttachment.version_id.in_(versions))):
            _purge(db, file_id, now)
        db.execute(delete(ReportPassage).where(ReportPassage.version_id.in_(versions)))
        for review in db.scalars(select(ReportReview).where(ReportReview.version_id.in_(versions))):
            review.comment = PLACEHOLDER if review.decision == "revision_requested" else None
        db.execute(update(SimilarityCheck).where(SimilarityCheck.version_id.in_(versions),
                                                 SimilarityCheck.decision.is_not(None))
                   .values(decision_comment=PLACEHOLDER))
    if slots:
        db.execute(update(ReportComment).where(ReportComment.slot_id.in_(slots)).values(body=PLACEHOLDER))
    db.execute(update(AttendanceWeek).where(AttendanceWeek.placement_id == p.id).values(note=None, unlock_reason=None))
    db.execute(update(Evaluation).where(Evaluation.placement_id == p.id).values(overall_comment=None,
                                                                              reopen_reason=None))
    db.execute(update(Grade).where(Grade.placement_id == p.id).values(return_comment=None, reopen_reason=None))
    db.execute(update(CompanyEvaluation).where(CompanyEvaluation.placement_id == p.id).values(comment=None))
    for file_id in db.scalars(select(Certificate.file_id).where(Certificate.placement_id == p.id)):
        _purge(db, file_id, now)
    if p.status == "cancelled":
        p.cancel_reason = PLACEHOLDER
    links = [f"/placements/{p.id}%"] + [f"/reports/{s}%" for s in slots]
    db.execute(delete(Notification).where(or_(*[Notification.link.like(link) for link in links])))


def _anonymize_student(db: Session, sid: uuid.UUID, now: datetime) -> None:
    user = db.get(User, sid)
    short = sid.hex[:6].upper()
    user.name_en, user.name_ar = f"Student {short}", f"طالب {short}"
    user.email, user.password_hash, user.is_active = f"anonymized+{sid.hex}@invalid", None, False
    user.anonymized_at = now
    for model, column in ((UserSession, UserSession.user_id), (AccountToken, AccountToken.user_id),
                          (PushSubscription, PushSubscription.user_id), (Notification, Notification.user_id),
                          (StudentSkill, StudentSkill.student_id), (MatchScore, MatchScore.student_id)):
        db.execute(delete(model).where(column == sid))
    profile = db.get(StudentProfile, sid)
    if profile is not None:
        profile.student_number = "A" + sid.hex[:16].upper()
        profile.interests, profile.languages = [], []
        profile.embedding = profile.embedding_model = profile.embedded_at = None
    for cv in db.scalars(select(Cv).where(Cv.student_id == sid)):
        _purge(db, cv.file_id, now)
        cv.extracted_text = None
        db.execute(delete(CvExtractedSkill).where(CvExtractedSkill.cv_id == cv.id))
    for req in db.scalars(select(VerificationRequest).where(VerificationRequest.user_id == sid)):
        req.submitted_data = {"anonymized": True}
        if req.reason:
            req.reason = PLACEHOLDER
        for doc in db.scalars(select(VerificationDocument).where(VerificationDocument.request_id == req.id)):
            _purge(db, doc.file_id, now)
            doc.purged_at = doc.purged_at or now
    for p in db.scalars(select(Placement).where(Placement.student_id == sid)):
        _anonymize_placement(db, p, now)


def anonymize(db: Session, actor: Actor, cycle: TrainingCycle) -> dict:
    if cycle.status != "closed":
        raise conflict("CYCLE_NOT_CLOSED")
    now = clock.now()
    if now < eligible_at(db, cycle):
        raise conflict("RETENTION_NOT_OVER", eligible_at=eligible_at(db, cycle).isoformat())
    todo, skipped = plan(db, cycle)
    if not todo and cycle.anonymized_at is not None:
        raise conflict("ALREADY_ANONYMIZED")
    for sid in todo:
        _anonymize_student(db, sid, now)
    cycle.anonymized_at, cycle.anonymized_by = now, actor.id
    audit.record(db, actor.user, "anonymize", "training_cycle", cycle.id, college_id=cycle.college_id,
                 cycle_id=cycle.id, new={"students": len(todo), "skipped": len(skipped)})
    db.flush()
    return preview(db, cycle)
