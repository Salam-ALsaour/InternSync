"""API 3.15 – Exports (FR-EXP-01 – 03, NFR-PER-05). Files are built on request and streamed; each export is audited."""
import re
import uuid
from typing import Literal
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core import audit
from app.core.common import get_or_404
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import forbidden
from app.exports import service
from app.models import Placement, TrainingCycle, User

router = APIRouter(tags=["exports"])
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
FILE = {"description": "The file", "content": {"application/pdf": {}, XLSX: {}}}


def _file(data: bytes, media_type: str, name: str) -> Response:
    ascii_name = re.sub(r"[^A-Za-z0-9._-]+", "-", name).strip("-") or "export"
    disposition = f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(name)}"
    return Response(content=data, media_type=media_type,
                    headers={"Content-Disposition": disposition, "Cache-Control": "private, no-store",
                             "X-Content-Type-Options": "nosniff"})


def _own_cycle(db: Session, actor: Actor, cycle_id: uuid.UUID) -> TrainingCycle:
    cycle = get_or_404(db, TrainingCycle, cycle_id)
    if cycle.college_id != actor.user.college_id:
        raise forbidden()
    return cycle


def _audit(db: Session, actor: Actor, entity_type: str, entity_id, kind: str, **kw) -> None:
    audit.record(db, actor.user, "export", entity_type, entity_id, college_id=actor.user.college_id,
                 new={"export": kind, **kw.pop("new", {})}, **kw)
    db.commit()


@router.get("/cycles/{cycle_id}/exports/grade-sheet", response_class=Response, responses={200: FILE})
def grade_sheet(cycle_id: uuid.UUID, format: Literal["xlsx", "pdf"] = "xlsx", actor: Actor = Depends(auth("co")),
                db: Session = Depends(get_db)):
    cycle = _own_cycle(db, actor, cycle_id)
    lang = actor.user.language
    if format == "xlsx":
        data, media = service.grade_sheet_xlsx(db, cycle, lang), XLSX
    else:
        data, media = service.grade_sheet_pdf(db, cycle, lang), "application/pdf"
    _audit(db, actor, "training_cycle", cycle.id, "grade_sheet", cycle_id=cycle.id, new={"format": format})
    return _file(data, media, f"grade-sheet-{cycle.name}.{format}")


@router.get("/cycles/{cycle_id}/exports/term-summary", response_class=Response, responses={200: FILE})
def term_summary(cycle_id: uuid.UUID, actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    cycle = _own_cycle(db, actor, cycle_id)
    data = service.term_summary_pdf(db, cycle, actor.user.language)
    _audit(db, actor, "training_cycle", cycle.id, "term_summary", cycle_id=cycle.id)
    return _file(data, "application/pdf", f"term-summary-{cycle.name}.pdf")


@router.get("/placements/{placement_id}/exports/training-record", response_class=Response, responses={200: FILE})
def training_record(placement_id: uuid.UUID, actor: Actor = Depends(auth("co", "as")), db: Session = Depends(get_db)):
    placement = get_or_404(db, Placement, placement_id)
    student = db.get(User, placement.student_id)
    if actor.code == "as" and placement.academic_supervisor_id != actor.id:
        raise forbidden()
    if actor.code == "co" and student.college_id != actor.user.college_id:
        raise forbidden()
    data = service.training_record_pdf(db, placement, actor.user.language)
    audit.record(db, actor.user, "export", "placement", placement.id, student_id=student.id,
                 college_id=student.college_id, cycle_id=placement.cycle_id, new={"export": "training_record"})
    db.commit()
    return _file(data, "application/pdf", f"training-record-{student.name_en}.pdf")
