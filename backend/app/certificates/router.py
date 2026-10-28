"""API 3.16 – Certificates (FR-CER-01 – 03). The public check needs no login and never shows the grade."""
import uuid
from datetime import date, datetime
from typing import Literal

from fastapi import APIRouter, Depends, Path
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.certificates import service
from app.core.common import get_or_404
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import forbidden
from app.core.scope import placement_access
from app.models import Certificate, Placement

router = APIRouter(tags=["certificates"])


class StudentRef(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str


class CertificateOut(BaseModel):
    id: uuid.UUID
    placement_id: uuid.UUID
    code: str
    status: str
    verify_url: str
    file_id: uuid.UUID
    issued_at: datetime
    revoked_at: datetime | None
    revoke_reason: str | None
    student: StudentRef
    cycle: str
    company: str
    can_revoke: bool


class PlacementCertificate(BaseModel):
    certificate: CertificateOut | None
    can_issue: bool


class ReasonIn(BaseModel):
    reason: str = Field("", max_length=1000)


class Names(BaseModel):
    en: str
    ar: str


class PublicCertificate(BaseModel):
    status: Literal["valid", "revoked", "not_found"]
    name_removed: bool = False
    student_name: Names | None = None
    university: Names | None = None
    college: Names | None = None
    cycle: str | None = None
    company: str | None = None
    training_start: date | None = None
    training_end: date | None = None


def _placement(db: Session, actor: Actor, placement_id: uuid.UUID) -> tuple[Placement, str]:
    p = get_or_404(db, Placement, placement_id)
    relation = placement_access(db, actor, p)
    if relation not in ("st", "co"):
        raise forbidden()
    return p, relation


@router.get("/placements/{placement_id}/certificate", response_model=PlacementCertificate)
def placement_certificate(placement_id: uuid.UUID, actor: Actor = Depends(auth("st", "co")),
                          db: Session = Depends(get_db)):
    p, relation = _placement(db, actor, placement_id)
    return service.placement_view(db, p, relation)


@router.post("/placements/{placement_id}/certificate", response_model=PlacementCertificate, status_code=201)
def issue_certificate(placement_id: uuid.UUID, actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    p, relation = _placement(db, actor, placement_id)
    service.issue(db, actor, p)
    db.commit()
    return service.placement_view(db, p, relation)


@router.get("/certificates", response_model=list[CertificateOut])
def list_certificates(cycle_id: uuid.UUID | None = None, status: Literal["valid", "revoked"] | None = None,
                      actor: Actor = Depends(auth("co")), db: Session = Depends(get_db)):
    return service.listing(db, actor, cycle_id, status)


@router.get("/certificates/{certificate_id}", response_model=CertificateOut)
def get_certificate(certificate_id: uuid.UUID, actor: Actor = Depends(auth("st", "co")),
                    db: Session = Depends(get_db)):
    cert = get_or_404(db, Certificate, certificate_id)
    _, relation = _placement(db, actor, cert.placement_id)
    return service.out(db, cert, relation)


@router.post("/certificates/{certificate_id}/revoke", response_model=CertificateOut)
def revoke_certificate(certificate_id: uuid.UUID, body: ReasonIn, actor: Actor = Depends(auth("co")),
                       db: Session = Depends(get_db)):
    cert = get_or_404(db, Certificate, certificate_id)
    _, relation = _placement(db, actor, cert.placement_id)
    service.revoke(db, actor, cert, body.reason)
    db.commit()
    return service.out(db, cert, relation)


@router.get("/public/certificates/{code}", response_model=PublicCertificate)
def verify_certificate(code: str = Path(max_length=64), db: Session = Depends(get_db)):
    """Public (FR-CER-02): `200` in every case, `not_found` for an unknown or altered code."""
    return service.public(db, code)
