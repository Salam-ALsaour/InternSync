"""Report slots and versions (FR-REP-01 – 07, FR-WFL-01, Design Table 5.3, Design 5.2)."""
import uuid
from datetime import timedelta

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.text import extract_text
from app.core import audit, clock, files, settings
from app.core.deps import Actor
from app.core.errors import ApiError, conflict, forbidden, not_found
from app.core.scope import placement_access
from app.models import (
    Placement,
    ReportAttachment,
    ReportComment,
    ReportReview,
    ReportSlot,
    ReportVersion,
    StoredFile,
    TrainingCycle,
    User,
)
from app.notifications import events

TEXT_FIELDS = ("tasks_performed", "learning", "challenges", "next_week_plan")

# Allowed transitions (Design Table 5.3). Anything else is 409 INVALID_TRANSITION (FR-WFL-01).
TRANSITIONS = {
    ("draft", "submit"): "submitted",
    ("revision_requested", "submit"): "submitted",
    ("submitted", "accept"): "accepted",
    ("submitted", "request_revision"): "revision_requested",
    ("draft", "close_missing"): "closed_missing",
}


def next_state(current: str, action: str) -> str:
    try:
        return TRANSITIONS[(current, action)]
    except KeyError as exc:
        if action == "submit" and current == "closed_missing":
            raise conflict("SLOT_CLOSED") from exc
        raise conflict("INVALID_TRANSITION") from exc


def is_late(submitted_at, due_at) -> bool:
    """The deadline minute is inclusive (Design 5.2): 23:59:30 is on time for a 23:59 deadline."""
    return submitted_at >= due_at + timedelta(seconds=60)


# ---------------------------------------------------------------- loading and access
def load_slot(db: Session, actor: Actor, slot_id: uuid.UUID) -> tuple[ReportSlot, Placement, str]:
    slot = db.get(ReportSlot, slot_id)
    if slot is None:
        raise not_found()
    placement = db.get(Placement, slot.placement_id)
    relation = placement_access(db, actor, placement)
    return slot, placement, relation


def ensure_writable(db: Session, placement: Placement) -> None:
    if placement.status != "active":
        raise conflict("INVALID_TRANSITION")
    if db.get(TrainingCycle, placement.cycle_id).status != "open":
        raise conflict("CYCLE_CLOSED")


def submitted_versions(db: Session, slot: ReportSlot) -> list[ReportVersion]:
    return list(db.scalars(select(ReportVersion).where(ReportVersion.slot_id == slot.id,
                                                       ReportVersion.submitted_at.is_not(None))
                           .order_by(ReportVersion.version_no)))


def draft_version(db: Session, slot: ReportSlot) -> ReportVersion | None:
    return db.scalar(select(ReportVersion).where(ReportVersion.slot_id == slot.id,
                                                 ReportVersion.submitted_at.is_(None)))


def get_or_create_draft(db: Session, slot: ReportSlot) -> ReportVersion:
    draft = draft_version(db, slot)
    if draft:
        return draft
    last = (submitted_versions(db, slot) or [None])[-1]
    number = (db.scalar(select(func.max(ReportVersion.version_no)).where(ReportVersion.slot_id == slot.id)) or 0) + 1
    draft = ReportVersion(slot_id=slot.id, version_no=number)
    if last is not None:  # resubmission starts as a copy of the last submitted version (Design 5.1)
        for f in (*TEXT_FIELDS, "summary"):
            setattr(draft, f, getattr(last, f))
    db.add(draft)
    db.flush()
    if last is not None:
        for att in attachments(db, last):
            db.add(ReportAttachment(version_id=draft.id, file_id=att.file_id, role=att.role, position=att.position))
        db.flush()
    return draft


def attachments(db: Session, version: ReportVersion) -> list[ReportAttachment]:
    return list(db.scalars(select(ReportAttachment).where(ReportAttachment.version_id == version.id)
                           .order_by(ReportAttachment.role.desc(), ReportAttachment.position)))


# ---------------------------------------------------------------- output
def version_out(db: Session, v: ReportVersion) -> dict:
    review = db.scalar(select(ReportReview).where(ReportReview.version_id == v.id)
                       .order_by(ReportReview.created_at.desc()))
    reviewer = db.get(User, review.reviewer_id) if review else None
    atts = []
    for a in attachments(db, v):
        f = db.get(StoredFile, a.file_id)
        atts.append({"id": a.id, "file_id": a.file_id, "original_name": f.original_name, "role": a.role,
                     "size_bytes": f.size_bytes})
    return {"id": v.id, "version_no": v.version_no, "submitted_at": v.submitted_at, "is_late": v.is_late,
            **{f: getattr(v, f) for f in (*TEXT_FIELDS, "summary")}, "attachments": atts,
            "review": {"decision": review.decision, "comment": review.comment, "created_at": review.created_at,
                       "reviewer_en": reviewer.name_en, "reviewer_ar": reviewer.name_ar} if review else None}


def allowed_actions(db: Session, slot: ReportSlot, placement: Placement, relation: str) -> list[str]:
    if placement.status != "active" or db.get(TrainingCycle, placement.cycle_id).status != "open":
        return []
    if relation == "st" and slot.status in ("draft", "revision_requested"):
        return ["save_draft", "submit"]
    if relation == "as":
        if slot.status == "submitted":
            return ["accept", "request_revision"]
        if slot.status == "draft" and not submitted_versions(db, slot) and clock.now() > slot.due_at:
            return ["close_missing"]
    return []


def slot_summary(db: Session, slot: ReportSlot) -> dict:
    versions = submitted_versions(db, slot)
    return {"id": slot.id, "placement_id": slot.placement_id, "kind": slot.kind, "week_no": slot.week_no,
            "due_at": slot.due_at, "status": slot.status, "is_late": slot.is_late, "is_missing": slot.is_missing,
            "versions": len(versions), "last_submitted_at": versions[-1].submitted_at if versions else None,
            "has_draft": draft_version(db, slot) is not None}


def slot_out(db: Session, slot: ReportSlot, placement: Placement, relation: str) -> dict:
    out = slot_summary(db, slot)
    out["submitted"] = [version_out(db, v) for v in submitted_versions(db, slot)]
    draft = draft_version(db, slot) if relation == "st" else None
    out["draft"] = version_out(db, draft) if draft else None
    out["allowed_actions"] = allowed_actions(db, slot, placement, relation)
    out["can_comment"] = relation in ("st", "as") and placement.status == "active"
    student = db.get(User, placement.student_id)
    out["student"] = {"id": student.id, "name_en": student.name_en, "name_ar": student.name_ar}
    out["max_attachments"] = settings.get(db, "reports.max_attachments")
    out["attachment_max_mb"] = settings.get(db, "files.attachment_max_mb")
    return out


# ---------------------------------------------------------------- student actions
def _audit(db, actor, action, slot, placement, **kw):
    student = db.get(User, placement.student_id)
    audit.record(db, actor.user if actor else None, action, "report_slot", slot.id, student_id=student.id,
                 college_id=student.college_id, cycle_id=placement.cycle_id, **kw)


def save_draft(db: Session, actor: Actor, slot: ReportSlot, placement: Placement, data: dict) -> ReportVersion:
    ensure_writable(db, placement)
    if slot.status not in ("draft", "revision_requested"):
        raise conflict("SLOT_CLOSED" if slot.status == "closed_missing" else "INVALID_TRANSITION")
    draft = get_or_create_draft(db, slot)
    for f in (*TEXT_FIELDS, "summary"):
        if f in data:
            setattr(draft, f, (data[f] or "").strip() or None)
    return draft


def add_attachment(db: Session, actor: Actor, slot: ReportSlot, placement: Placement, upload: UploadFile,
                   role: str) -> ReportAttachment:
    ensure_writable(db, placement)
    if slot.status not in ("draft", "revision_requested"):
        raise conflict("SLOT_CLOSED" if slot.status == "closed_missing" else "INVALID_TRANSITION")
    if role == "main" and slot.kind != "final":
        raise ApiError(422, "VALIDATION_ERROR", errors=[{"field": "role", "code": "VALIDATION_ERROR",
                                                         "message": "main is for the final report only"}])
    draft = get_or_create_draft(db, slot)
    current = attachments(db, draft)
    if role == "attachment" and sum(a.role == "attachment" for a in current) >= settings.get(db,
                                                                                            "reports.max_attachments"):
        raise conflict("TOO_MANY_ATTACHMENTS")
    data = files.read_upload(upload, settings.get(db, "files.attachment_max_mb"))
    allowed = files.DOCUMENTS if role == "main" else files.DOCUMENTS_AND_IMAGES
    stored = files.store(db, data, upload.filename or "attachment",
                         "report_document" if role == "main" else "report_attachment", allowed, actor.user)
    if role == "main":
        for a in current:
            if a.role == "main":
                db.delete(a)
    position = max((a.position for a in current if a.role == role), default=0) + 1
    att = ReportAttachment(version_id=draft.id, file_id=stored.id, role=role, position=position)
    db.add(att)
    db.flush()
    return att


def remove_attachment(db: Session, slot: ReportSlot, placement: Placement, attachment_id: uuid.UUID) -> None:
    ensure_writable(db, placement)
    draft = draft_version(db, slot)
    att = db.get(ReportAttachment, attachment_id)
    if draft is None or att is None or att.version_id != draft.id:
        raise not_found()
    db.delete(att)


def submit(db: Session, actor: Actor, slot: ReportSlot, placement: Placement) -> ReportVersion:
    ensure_writable(db, placement)
    new_state = next_state(slot.status, "submit")
    draft = draft_version(db, slot)
    if draft is None:
        raise conflict("NOTHING_TO_SUBMIT")
    atts = attachments(db, draft)
    if slot.kind == "weekly":
        missing = [f for f in TEXT_FIELDS if not (getattr(draft, f) or "").strip()]
        if missing:
            raise ApiError(422, "REQUIRED_FIELDS_MISSING", errors=[{"field": f, "code": "REQUIRED_FIELDS_MISSING",
                                                                     "message": ""} for f in missing])
        draft.body_text = "\n\n".join(getattr(draft, f) for f in TEXT_FIELDS)
    else:
        main = next((a for a in atts if a.role == "main"), None)
        if main is None:
            raise ApiError(422, "MAIN_DOCUMENT_REQUIRED")
        stored = db.get(StoredFile, main.file_id)
        text, status = extract_text(files.storage().read(stored.storage_key), stored.mime_type)
        draft.body_text = text if status == "ok" else (draft.summary or None)
    if sum(a.role == "attachment" for a in atts) > settings.get(db, "reports.max_attachments"):
        raise conflict("TOO_MANY_ATTACHMENTS")
    now = clock.now()
    first = not submitted_versions(db, slot)
    draft.submitted_at, draft.is_late = now, is_late(now, slot.due_at)
    if first and draft.is_late:
        slot.is_late = True
    old = slot.status
    slot.status = new_state
    _audit(db, actor, "submit", slot, placement, old={"status": old},
           new={"status": new_state, "version_no": draft.version_no, "is_late": draft.is_late})
    events.report_event(db, "report.submitted", slot, placement)
    return draft


# ---------------------------------------------------------------- academic supervisor actions
def _review(db: Session, actor: Actor, slot: ReportSlot, placement: Placement, action: str,
            comment: str | None) -> None:
    ensure_writable(db, placement)
    new_state = next_state(slot.status, action)
    if action == "request_revision" and not (comment or "").strip():
        raise ApiError(422, "COMMENT_REQUIRED")
    last = submitted_versions(db, slot)[-1]
    decision = "accepted" if action == "accept" else "revision_requested"
    db.add(ReportReview(version_id=last.id, reviewer_id=actor.id, decision=decision,
                        comment=(comment or "").strip() or None))
    old = slot.status
    slot.status = new_state
    if action == "accept":
        slot.accepted_at = clock.now()
    _audit(db, actor, action, slot, placement, old={"status": old}, new={"status": new_state},
           reason=(comment or "").strip() or None)
    if action == "accept":
        events.report_event(db, "report.accepted", slot, placement)
    else:
        events.report_event(db, "report.revision_requested", slot, placement, comment=comment.strip())


def accept(db, actor, slot, placement):
    _review(db, actor, slot, placement, "accept", None)


def request_revision(db, actor, slot, placement, comment: str):
    _review(db, actor, slot, placement, "request_revision", comment)


def close_missing(db: Session, actor: Actor, slot: ReportSlot, placement: Placement) -> None:
    ensure_writable(db, placement)
    new_state = next_state(slot.status, "close_missing")
    if submitted_versions(db, slot):
        raise conflict("INVALID_TRANSITION")
    if clock.now() <= slot.due_at:
        raise conflict("DEADLINE_NOT_PASSED")
    now = clock.now()
    slot.status, slot.closed_at, slot.closed_by = new_state, now, actor.id
    if not slot.is_missing:
        slot.is_missing, slot.missing_flagged_at = True, now
    _audit(db, actor, "close_missing", slot, placement, old={"status": "draft"}, new={"status": new_state})


# ---------------------------------------------------------------- comments
def comments_out(db: Session, slot: ReportSlot) -> list[dict]:
    rows = db.execute(select(ReportComment, User).join(User, User.id == ReportComment.author_id)
                      .where(ReportComment.slot_id == slot.id).order_by(ReportComment.created_at)).all()
    return [{"id": c.id, "body": c.body, "created_at": c.created_at, "author_id": u.id, "author_en": u.name_en,
             "author_ar": u.name_ar, "author_role": u.role} for c, u in rows]


def add_comment(db: Session, actor: Actor, slot: ReportSlot, placement: Placement, relation: str, body: str) -> None:
    if relation not in ("st", "as"):
        raise forbidden()
    if placement.status != "active":
        raise conflict("INVALID_TRANSITION")
    db.add(ReportComment(slot_id=slot.id, author_id=actor.id, body=body.strip()))
    _audit(db, actor, "comment", slot, placement)
