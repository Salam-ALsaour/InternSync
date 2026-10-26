"""API 3.5 – Student profile, CV upload, skill extraction and confirmation (FR-PRF-02 – 05)."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, File, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.ai import skills as extractor
from app.ai.text import detect_language, extract_text
from app.auth.service import _gpa, _student_number_taken
from app.core import audit, clock, files, settings
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import conflict, field_error, forbidden, not_found
from app.core.scope import can_see_student
from app.cycles.service import student_open_enrollment
from app.matching.service import embed_profile
from app.models import (
    College,
    Cv,
    CvExtractedSkill,
    Major,
    Skill,
    StoredFile,
    StudentProfile,
    StudentSkill,
    University,
    User,
)

router = APIRouter(tags=["profiles"])


class SkillRef(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str


class ConfirmedSkill(SkillRef):
    source: str


class CvOut(BaseModel):
    id: uuid.UUID
    version_no: int
    file_id: uuid.UUID
    original_name: str
    text_status: str
    language: str | None
    uploaded_at: datetime


class ProfileOut(BaseModel):
    user_id: uuid.UUID
    name_en: str
    name_ar: str
    email: str
    verification_status: str
    university_en: str
    university_ar: str
    college_en: str
    college_ar: str
    student_number: str
    major: SkillRef
    gpa: Decimal
    gpa_scale: Decimal
    level: int | None
    languages: list[str]
    interests: list[str]
    academic_read_only: bool
    skills: list[ConfirmedSkill]
    skills_confirmed_at: datetime | None
    current_cv: CvOut | None
    enrolled_cycle_id: uuid.UUID | None
    enrolled_cycle_name: str | None
    enrolled_cycle_type: str | None


class ProfilePatch(BaseModel):
    languages: list[str] | None = Field(None, max_length=10)
    interests: list[str] | None = Field(None, max_length=20)
    student_number: str | None = Field(None, min_length=4, max_length=20)
    major_id: uuid.UUID | None = None
    gpa: Decimal | None = None
    level: int | None = Field(None, ge=1, le=12)


class ExtractedSkill(SkillRef):
    evidence: str | None


class CvUploadOut(BaseModel):
    cv: CvOut
    text_status: str
    language: str | None
    extracted_skills: list[ExtractedSkill]
    advisory: bool = True


class SkillChoice(BaseModel):
    skill_id: uuid.UUID
    source: Literal["extracted", "manual"]


class SkillsIn(BaseModel):
    skills: list[SkillChoice] = Field(max_length=80)


def cv_out(db: Session, cv: Cv) -> dict:
    f = db.get(StoredFile, cv.file_id)
    return {"id": cv.id, "version_no": cv.version_no, "file_id": cv.file_id, "original_name": f.original_name,
            "text_status": cv.text_status, "language": cv.language, "uploaded_at": cv.uploaded_at}


def current_cv(db: Session, student_id: uuid.UUID) -> Cv | None:
    return db.scalar(select(Cv).where(Cv.student_id == student_id).order_by(Cv.version_no.desc()))


def confirmed_skills(db: Session, student_id: uuid.UUID) -> list[dict]:
    rows = db.execute(select(StudentSkill, Skill).join(Skill, Skill.id == StudentSkill.skill_id)
                      .where(StudentSkill.student_id == student_id).order_by(Skill.name_en)).all()
    return [{"id": k.id, "name_en": k.name_en, "name_ar": k.name_ar, "source": ss.source} for ss, k in rows]


def profile_out(db: Session, user: User) -> dict:
    p = db.get(StudentProfile, user.id)
    college = db.get(College, user.college_id)
    uni = db.get(University, college.university_id)
    major = db.get(Major, p.major_id)
    cv = current_cv(db, user.id)
    cycle = student_open_enrollment(db, user.id)
    return {"user_id": user.id, "name_en": user.name_en, "name_ar": user.name_ar, "email": user.email,
            "verification_status": user.verification_status, "university_en": uni.name_en,
            "university_ar": uni.name_ar, "college_en": college.name_en, "college_ar": college.name_ar,
            "student_number": p.student_number, "major": {"id": major.id, "name_en": major.name_en,
                                                          "name_ar": major.name_ar},
            "gpa": p.gpa, "gpa_scale": uni.gpa_scale, "level": p.level, "languages": p.languages,
            "interests": p.interests, "academic_read_only": user.verification_status == "verified",
            "skills": confirmed_skills(db, user.id), "skills_confirmed_at": p.skills_confirmed_at,
            "current_cv": cv_out(db, cv) if cv else None,
            "enrolled_cycle_id": cycle.id if cycle else None, "enrolled_cycle_name": cycle.name if cycle else None,
            "enrolled_cycle_type": cycle.type if cycle else None}


@router.get("/students/me/profile", response_model=ProfileOut)
def my_profile(actor: Actor = Depends(auth("st", unverified=True)), db: Session = Depends(get_db)):
    return profile_out(db, actor.user)


@router.patch("/students/me/profile", response_model=ProfileOut)
def patch_my_profile(body: ProfilePatch, actor: Actor = Depends(auth("st", unverified=True)),
                     db: Session = Depends(get_db)):
    user = db.merge(actor.user)
    p = db.get(StudentProfile, user.id)
    data = body.model_dump(exclude_unset=True)
    academic = {k: data.pop(k) for k in ("student_number", "major_id", "gpa", "level") if k in data}
    if academic and user.verification_status == "verified" and any(
            k != "level" and academic[k] is not None for k in academic):
        raise field_error(next(k for k in academic if k != "level"), "READ_ONLY_FIELD")
    college = db.get(College, user.college_id)
    if academic.get("student_number") and _student_number_taken(db, academic["student_number"], college,
                                                                exclude_user=user.id):
        raise conflict("STUDENT_NUMBER_TAKEN")
    if academic.get("major_id") and db.get(Major, academic["major_id"]) is None:
        raise field_error("major_id", "VALIDATION_ERROR")
    if academic.get("gpa") is not None:
        academic["gpa"] = _gpa(db, str(academic["gpa"]), college)
    for key in ("languages", "interests"):
        if key in data and data[key] is not None:
            data[key] = [x.strip() for x in data[key] if x and x.strip()][:20]
    old, new = audit.changes(p, {k: v for k, v in {**data, **academic}.items() if v is not None})
    if new:
        audit.record(db, user, "update", "student_profile", user.id, student_id=user.id, college_id=user.college_id,
                     old=old, new=new)
    if "interests" in new:
        embed_profile(db, user.id)
    db.commit()
    return profile_out(db, user)


@router.get("/students/me/cvs", response_model=list[CvOut])
def my_cvs(actor: Actor = Depends(auth("st", unverified=True)), db: Session = Depends(get_db)):
    return [cv_out(db, cv) for cv in db.scalars(select(Cv).where(Cv.student_id == actor.id)
                                                .order_by(Cv.version_no.desc()))]


@router.post("/students/me/cvs", status_code=201, response_model=CvUploadOut)
def upload_cv(file: UploadFile = File(...), actor: Actor = Depends(auth("st", unverified=True)),
              db: Session = Depends(get_db)):
    user = db.merge(actor.user)
    data = files.read_upload(file, settings.get(db, "files.cv_max_mb"))
    stored = files.store(db, data, file.filename or "cv", "cv", files.DOCUMENTS, user)
    text, status = extract_text(data, stored.mime_type)
    version = (db.scalar(select(func.max(Cv.version_no)).where(Cv.student_id == user.id)) or 0) + 1
    cv = Cv(student_id=user.id, version_no=version, file_id=stored.id, extracted_text=text or None,
            text_status=status, language=detect_language(text) if status == "ok" else None, uploaded_at=clock.now())
    db.add(cv)
    db.flush()
    matches = extractor.extract(db, text) if status == "ok" else []
    for m in matches:
        db.add(CvExtractedSkill(cv_id=cv.id, skill_id=m.skill_id, evidence=m.evidence))
    audit.record(db, user, "upload_cv", "cv", cv.id, student_id=user.id, college_id=user.college_id,
                 new={"version_no": version, "text_status": status, "extracted": len(matches)})
    embed_profile(db, user.id)
    db.commit()
    names = {k.id: k for k in db.scalars(select(Skill).where(Skill.id.in_([m.skill_id for m in matches])))}
    extracted = [{"id": m.skill_id, "name_en": names[m.skill_id].name_en, "name_ar": names[m.skill_id].name_ar,
                  "evidence": m.evidence} for m in matches]
    extracted.sort(key=lambda x: x["name_en"].lower())
    return {"cv": cv_out(db, cv), "text_status": status, "language": cv.language, "extracted_skills": extracted}


@router.get("/students/me/skills", response_model=list[ConfirmedSkill])
def my_skills(actor: Actor = Depends(auth("st", unverified=True)), db: Session = Depends(get_db)):
    return confirmed_skills(db, actor.id)


@router.put("/students/me/skills", response_model=list[ConfirmedSkill])
def confirm_skills(body: SkillsIn, actor: Actor = Depends(auth("st", unverified=True)),
                   db: Session = Depends(get_db)):
    user = db.merge(actor.user)
    ids = list(dict.fromkeys(s.skill_id for s in body.skills))
    valid = set(db.scalars(select(Skill.id).where(Skill.id.in_(ids), Skill.is_active)))
    if len(valid) != len(ids):
        raise field_error("skills", "VALIDATION_ERROR")
    source = {s.skill_id: s.source for s in body.skills}
    before = [s["name_en"] for s in confirmed_skills(db, user.id)]
    db.execute(delete(StudentSkill).where(StudentSkill.student_id == user.id))
    now = clock.now()
    for sid in ids:
        db.add(StudentSkill(student_id=user.id, skill_id=sid, source=source[sid], confirmed_at=now))
    db.get(StudentProfile, user.id).skills_confirmed_at = now
    db.flush()
    after = [s["name_en"] for s in confirmed_skills(db, user.id)]
    audit.record(db, user, "confirm_skills", "student_profile", user.id, student_id=user.id,
                 college_id=user.college_id, old={"skills": before}, new={"skills": after})
    embed_profile(db, user.id)
    db.commit()
    return confirmed_skills(db, user.id)


@router.get("/students/{student_id}/profile", response_model=ProfileOut)
def student_profile(student_id: uuid.UUID, actor: Actor = Depends(auth("cs", "as", "co")),
                    db: Session = Depends(get_db)):
    student = db.get(User, student_id)
    if student is None or student.role != "student":
        raise not_found()
    if not can_see_student(db, actor, student_id):
        raise forbidden()
    return profile_out(db, student)

