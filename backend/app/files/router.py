"""API 3.19 – Files (NFR-SEC-04, FR-ORG-08). A file is served only after the permission rule of the record
that owns it; verification documents only to the uploader and the reviewer; 410 after the purge."""
import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import files
from app.core.common import get_or_404
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import ApiError, forbidden
from app.core.scope import can_see_student, placement_access
from app.models import (
    Certificate,
    Cv,
    Placement,
    ReportAttachment,
    ReportSlot,
    ReportVersion,
    StoredFile,
    VerificationDocument,
    VerificationRequest,
)
from app.orgs.service import can_review

router = APIRouter(tags=["files"])


def _check(db: Session, actor: Actor, f: StoredFile) -> None:
    _owner_check(db, actor, f)
    if f.purged_at is not None:  # removed from storage by an anonymization (NFR-PRV-04)
        raise ApiError(410, "FILE_PURGED")


def _owner_check(db: Session, actor: Actor, f: StoredFile) -> None:
    if f.purpose == "certificate":  # the student and the coordinator of the student's college (FR-CER-01)
        cert = db.scalar(select(Certificate).where(Certificate.file_id == f.id))
        if cert is None or placement_access(db, actor, db.get(Placement, cert.placement_id)) not in ("st", "co"):
            raise forbidden()
        return
    if f.purpose == "verification_document":
        doc = db.scalar(select(VerificationDocument).where(VerificationDocument.file_id == f.id))
        if doc is None:
            raise forbidden()
        req = db.get(VerificationRequest, doc.request_id)
        if req.user_id != actor.id and not can_review(actor, req):
            raise forbidden()
        if doc.purged_at is not None:
            raise ApiError(410, "FILE_PURGED")
        return
    if f.purpose == "cv":
        cv = db.scalar(select(Cv).where(Cv.file_id == f.id))
        if cv is None or not can_see_student(db, actor, cv.student_id):
            raise forbidden()
        return
    if f.purpose in ("report_attachment", "report_document"):
        rows = db.execute(select(ReportVersion, ReportSlot)
                          .join(ReportAttachment, ReportAttachment.version_id == ReportVersion.id)
                          .join(ReportSlot, ReportSlot.id == ReportVersion.slot_id)
                          .where(ReportAttachment.file_id == f.id)).all()
        for version, slot in rows:
            placement = db.get(Placement, slot.placement_id)
            try:
                relation = placement_access(db, actor, placement)
            except ApiError:
                continue
            if version.submitted_at is not None or relation == "st":
                return
        raise forbidden()
    raise forbidden()


@router.get("/files/{file_id}")
def download(file_id: uuid.UUID, actor: Actor = Depends(auth(unverified=True)), db: Session = Depends(get_db)):
    f = get_or_404(db, StoredFile, file_id)
    _check(db, actor, f)
    data = files.storage().read(f.storage_key)
    disposition = f"attachment; filename*=UTF-8''{quote(f.original_name)}"
    return Response(content=data, media_type=f.mime_type,
                    headers={"Content-Disposition": disposition, "X-Content-Type-Options": "nosniff",
                             "Cache-Control": "private, no-store"})
