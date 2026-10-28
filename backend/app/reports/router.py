"""API 3.9 – Weekly and final reports."""
import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.common import get_or_404
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import forbidden, not_found
from app.core.scope import placement_access
from app.models import Placement, ReportSlot, ReportVersion
from app.reports import service
from app.similarity import service as similarity

router = APIRouter(tags=["reports"])


class SlotSummary(BaseModel):
    id: uuid.UUID
    placement_id: uuid.UUID
    kind: str
    week_no: int | None
    due_at: datetime
    status: str
    is_late: bool
    is_missing: bool
    versions: int
    last_submitted_at: datetime | None
    has_draft: bool


class AttachmentOut(BaseModel):
    id: uuid.UUID
    file_id: uuid.UUID
    original_name: str
    role: str
    size_bytes: int


class ReviewOut(BaseModel):
    decision: str
    comment: str | None
    created_at: datetime
    reviewer_en: str
    reviewer_ar: str


class VersionOut(BaseModel):
    id: uuid.UUID
    version_no: int
    submitted_at: datetime | None
    is_late: bool | None
    tasks_performed: str | None
    learning: str | None
    challenges: str | None
    next_week_plan: str | None
    summary: str | None
    attachments: list[AttachmentOut]
    review: ReviewOut | None


class StudentRef(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str


class SlotOut(SlotSummary):
    submitted: list[VersionOut]
    draft: VersionOut | None
    allowed_actions: list[str]
    can_comment: bool
    student: StudentRef
    max_attachments: int
    attachment_max_mb: int


class DraftIn(BaseModel):
    tasks_performed: str | None = Field(None, max_length=8000)
    learning: str | None = Field(None, max_length=8000)
    challenges: str | None = Field(None, max_length=8000)
    next_week_plan: str | None = Field(None, max_length=8000)
    summary: str | None = Field(None, max_length=8000)


class CommentIn(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class RevisionIn(BaseModel):
    comment: str = Field("", max_length=2000)


class CommentOut(BaseModel):
    id: uuid.UUID
    body: str
    created_at: datetime
    author_id: uuid.UUID
    author_en: str
    author_ar: str
    author_role: str


ALL = ("st", "cs", "as", "co")


def _slot(db: Session, actor: Actor, slot_id: uuid.UUID):
    return service.load_slot(db, actor, slot_id)


@router.get("/placements/{placement_id}/report-slots", response_model=list[SlotSummary])
def list_slots(placement_id: uuid.UUID, actor: Actor = Depends(auth(*ALL)), db: Session = Depends(get_db)):
    placement = get_or_404(db, Placement, placement_id)
    placement_access(db, actor, placement)
    slots = db.scalars(select(ReportSlot).where(ReportSlot.placement_id == placement.id)
                       .order_by(ReportSlot.kind.desc(), ReportSlot.week_no))
    return [service.slot_summary(db, s) for s in slots]


@router.get("/report-slots/{slot_id}", response_model=SlotOut)
def get_slot(slot_id: uuid.UUID, actor: Actor = Depends(auth(*ALL)), db: Session = Depends(get_db)):
    slot, placement, relation = _slot(db, actor, slot_id)
    return service.slot_out(db, slot, placement, relation)


def _student_slot(db: Session, actor: Actor, slot_id: uuid.UUID):
    slot, placement, relation = _slot(db, actor, slot_id)
    if relation != "st":
        raise forbidden()
    return slot, placement, relation


def _supervisor_slot(db: Session, actor: Actor, slot_id: uuid.UUID):
    slot, placement, relation = _slot(db, actor, slot_id)
    if relation != "as":
        raise forbidden()
    return slot, placement, relation


@router.put("/report-slots/{slot_id}/draft", response_model=SlotOut)
def save_draft(slot_id: uuid.UUID, body: DraftIn, actor: Actor = Depends(auth("st")), db: Session = Depends(get_db)):
    slot, placement, relation = _student_slot(db, actor, slot_id)
    service.save_draft(db, actor, slot, placement, body.model_dump(exclude_unset=True))
    db.commit()
    return service.slot_out(db, slot, placement, relation)


@router.post("/report-slots/{slot_id}/draft/attachments", status_code=201, response_model=SlotOut)
def upload_attachment(slot_id: uuid.UUID, file: UploadFile = File(...),
                      role: Literal["main", "attachment"] = Form("attachment"), actor: Actor = Depends(auth("st")),
                      db: Session = Depends(get_db)):
    slot, placement, relation = _student_slot(db, actor, slot_id)
    service.add_attachment(db, actor, slot, placement, file, role)
    db.commit()
    return service.slot_out(db, slot, placement, relation)


@router.delete("/report-slots/{slot_id}/draft/attachments/{attachment_id}", response_model=SlotOut)
def delete_attachment(slot_id: uuid.UUID, attachment_id: uuid.UUID, actor: Actor = Depends(auth("st")),
                      db: Session = Depends(get_db)):
    slot, placement, relation = _student_slot(db, actor, slot_id)
    service.remove_attachment(db, slot, placement, attachment_id)
    db.commit()
    return service.slot_out(db, slot, placement, relation)


@router.post("/report-slots/{slot_id}/submit", response_model=SlotOut)
def submit(slot_id: uuid.UUID, background: BackgroundTasks, actor: Actor = Depends(auth("st")),
           db: Session = Depends(get_db)):
    slot, placement, relation = _student_slot(db, actor, slot_id)
    version = service.submit(db, actor, slot, placement)
    check = similarity.create_check(db, version)
    db.commit()
    background.add_task(similarity.run_in_background, check.id)  # FR-SIM-01, after the answer is sent
    return service.slot_out(db, slot, placement, relation)


@router.post("/report-slots/{slot_id}/accept", response_model=SlotOut)
def accept(slot_id: uuid.UUID, actor: Actor = Depends(auth("as")), db: Session = Depends(get_db)):
    slot, placement, relation = _supervisor_slot(db, actor, slot_id)
    service.accept(db, actor, slot, placement)
    db.commit()
    return service.slot_out(db, slot, placement, relation)


@router.post("/report-slots/{slot_id}/request-revision", response_model=SlotOut)
def request_revision(slot_id: uuid.UUID, body: RevisionIn, actor: Actor = Depends(auth("as")),
                     db: Session = Depends(get_db)):
    slot, placement, relation = _supervisor_slot(db, actor, slot_id)
    service.request_revision(db, actor, slot, placement, body.comment)
    db.commit()
    return service.slot_out(db, slot, placement, relation)


@router.post("/report-slots/{slot_id}/close-missing", response_model=SlotOut)
def close_missing(slot_id: uuid.UUID, actor: Actor = Depends(auth("as")), db: Session = Depends(get_db)):
    slot, placement, relation = _supervisor_slot(db, actor, slot_id)
    service.close_missing(db, actor, slot, placement)
    db.commit()
    return service.slot_out(db, slot, placement, relation)


@router.get("/report-slots/{slot_id}/comments", response_model=list[CommentOut])
def list_comments(slot_id: uuid.UUID, actor: Actor = Depends(auth(*ALL)), db: Session = Depends(get_db)):
    slot, _, _ = _slot(db, actor, slot_id)
    return service.comments_out(db, slot)


@router.post("/report-slots/{slot_id}/comments", status_code=201, response_model=list[CommentOut])
def add_comment(slot_id: uuid.UUID, body: CommentIn, actor: Actor = Depends(auth("st", "as")),
                db: Session = Depends(get_db)):
    slot, placement, relation = _slot(db, actor, slot_id)
    service.add_comment(db, actor, slot, placement, relation, body.body)
    db.commit()
    return service.comments_out(db, slot)


@router.get("/report-versions/{version_id}", response_model=VersionOut)
def get_version(version_id: uuid.UUID, actor: Actor = Depends(auth(*ALL)), db: Session = Depends(get_db)):
    version = db.get(ReportVersion, version_id)
    if version is None:
        raise not_found()
    _, _, relation = _slot(db, actor, version.slot_id)
    if version.submitted_at is None and relation != "st":
        raise not_found()
    return service.version_out(db, version)

