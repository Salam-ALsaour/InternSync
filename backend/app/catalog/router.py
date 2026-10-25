"""API 3.4 – Skill vocabulary, majors, and settings (FR-CYC-04, NFR-MNT-03). Maintained by the Platform Admin."""
import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.ai.skills import normalize, refresh_index
from app.core import audit, settings
from app.core.common import Page, PageParams, get_or_404, paginate
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import conflict
from app.models import Major, Skill, SkillResource, SystemSetting

router = APIRouter(tags=["catalog"])


class SkillOut(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str
    synonyms: list[str]
    is_active: bool
    resources: int = 0


class SkillIn(BaseModel):
    name_en: str = Field(min_length=1, max_length=80)
    name_ar: str = Field(min_length=1, max_length=80)
    synonyms: list[str] = Field(default_factory=list, max_length=30)


class SkillPatch(BaseModel):
    name_en: str | None = Field(None, min_length=1, max_length=80)
    name_ar: str | None = Field(None, min_length=1, max_length=80)
    synonyms: list[str] | None = Field(None, max_length=30)
    is_active: bool | None = None


class ResourceIO(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    url: str = Field(pattern=r"^https?://", max_length=500)
    estimated_effort: str | None = Field(None, max_length=60)
    language: str | None = Field(None, pattern="^(ar|en)$")


class MajorIO(BaseModel):
    id: uuid.UUID | None = None
    name_en: str = Field(min_length=2, max_length=120)
    name_ar: str = Field(min_length=2, max_length=120)


def match_terms(name_en: str, name_ar: str, synonyms: list[str]) -> list[str]:
    terms = {normalize(t) for t in [name_en, name_ar, *synonyms] if t and t.strip()}
    return sorted(t for t in terms if t)


def skill_out(db: Session, k: Skill) -> dict:
    count = db.scalar(select(func.count()).select_from(SkillResource).where(SkillResource.skill_id == k.id))
    return {"id": k.id, "name_en": k.name_en, "name_ar": k.name_ar, "synonyms": k.synonyms, "is_active": k.is_active,
            "resources": count}


def _skill_name_taken(db: Session, name_en: str, exclude: uuid.UUID | None = None) -> bool:
    stmt = select(Skill.id).where(func.lower(Skill.name_en) == name_en.strip().lower())
    if exclude:
        stmt = stmt.where(Skill.id != exclude)
    return db.scalar(stmt) is not None


@router.get("/skills", response_model=Page[SkillOut])
def list_skills(q: str | None = None, include_inactive: bool = False, params: PageParams = Depends(),
                actor: Actor = Depends(auth(unverified=True)), db: Session = Depends(get_db)):
    stmt = select(Skill).order_by(Skill.name_en)
    if not (include_inactive and actor.code == "pa"):
        stmt = stmt.where(Skill.is_active)
    if q and q.strip():
        like, norm = f"%{q.strip()}%", f"%{normalize(q)}%"
        stmt = stmt.where(or_(Skill.name_en.ilike(like), Skill.name_ar.ilike(like),
                              func.array_to_string(Skill.match_terms, " ").ilike(norm)))
    return paginate(db, stmt, params, lambda k: skill_out(db, k))


@router.post("/skills", status_code=201, response_model=SkillOut)
def create_skill(body: SkillIn, actor: Actor = Depends(auth("pa")), db: Session = Depends(get_db)):
    if _skill_name_taken(db, body.name_en):
        raise conflict("DUPLICATE_NAME")
    synonyms = [x.strip() for x in body.synonyms if x.strip()]
    skill = Skill(name_en=body.name_en.strip(), name_ar=body.name_ar.strip(), synonyms=synonyms,
                  match_terms=match_terms(body.name_en, body.name_ar, synonyms))
    db.add(skill)
    db.flush()
    audit.record(db, actor.user, "create", "skill", skill.id, new={"name_en": skill.name_en})
    db.commit()
    refresh_index()
    return skill_out(db, skill)


@router.patch("/skills/{skill_id}", response_model=SkillOut)
def patch_skill(skill_id: uuid.UUID, body: SkillPatch, actor: Actor = Depends(auth("pa")),
                db: Session = Depends(get_db)):
    skill = get_or_404(db, Skill, skill_id)
    data = body.model_dump(exclude_unset=True)
    if data.get("name_en") and _skill_name_taken(db, data["name_en"], exclude=skill.id):
        raise conflict("DUPLICATE_NAME")
    if "synonyms" in data:
        data["synonyms"] = [x.strip() for x in data["synonyms"] or [] if x.strip()]
    old, new = audit.changes(skill, data)
    skill.match_terms = match_terms(skill.name_en, skill.name_ar, skill.synonyms)
    if new:
        audit.record(db, actor.user, "update", "skill", skill.id, old=old, new=new)
    db.commit()
    refresh_index()
    return skill_out(db, skill)


@router.get("/skills/{skill_id}/resources", response_model=list[ResourceIO])
def get_resources(skill_id: uuid.UUID, actor: Actor = Depends(auth(unverified=True)), db: Session = Depends(get_db)):
    get_or_404(db, Skill, skill_id)
    return [{"title": r.title, "url": r.url, "estimated_effort": r.estimated_effort, "language": r.language}
            for r in db.scalars(select(SkillResource).where(SkillResource.skill_id == skill_id)
                                .order_by(SkillResource.position))]


@router.put("/skills/{skill_id}/resources", response_model=list[ResourceIO])
def put_resources(skill_id: uuid.UUID, body: list[ResourceIO], actor: Actor = Depends(auth("pa")),
                  db: Session = Depends(get_db)):
    get_or_404(db, Skill, skill_id)
    for r in db.scalars(select(SkillResource).where(SkillResource.skill_id == skill_id)):
        db.delete(r)
    db.flush()
    for pos, r in enumerate(body[:20], start=1):
        db.add(SkillResource(skill_id=skill_id, position=pos, **r.model_dump()))
    audit.record(db, actor.user, "replace_resources", "skill", skill_id, new={"count": len(body[:20])})
    db.commit()
    return get_resources(skill_id, actor, db)


@router.get("/majors", response_model=list[MajorIO])
def list_majors(db: Session = Depends(get_db)):
    """Public: majors for the registration form."""
    return [{"id": m.id, "name_en": m.name_en, "name_ar": m.name_ar}
            for m in db.scalars(select(Major).order_by(Major.name_en))]


@router.post("/majors", status_code=201, response_model=MajorIO)
def create_major(body: MajorIO, actor: Actor = Depends(auth("pa")), db: Session = Depends(get_db)):
    if db.scalar(select(Major.id).where(func.lower(Major.name_en) == body.name_en.strip().lower())):
        raise conflict("DUPLICATE_NAME")
    major = Major(name_en=body.name_en.strip(), name_ar=body.name_ar.strip())
    db.add(major)
    db.flush()
    audit.record(db, actor.user, "create", "major", major.id, new={"name_en": major.name_en})
    db.commit()
    return {"id": major.id, "name_en": major.name_en, "name_ar": major.name_ar}


@router.patch("/majors/{major_id}", response_model=MajorIO)
def patch_major(major_id: uuid.UUID, body: MajorIO, actor: Actor = Depends(auth("pa")),
                db: Session = Depends(get_db)):
    major = get_or_404(db, Major, major_id)
    if db.scalar(select(Major.id).where(func.lower(Major.name_en) == body.name_en.strip().lower(),
                                        Major.id != major.id)):
        raise conflict("DUPLICATE_NAME")
    old, new = audit.changes(major, {"name_en": body.name_en.strip(), "name_ar": body.name_ar.strip()})
    if new:
        audit.record(db, actor.user, "update", "major", major.id, old=old, new=new)
    db.commit()
    return {"id": major.id, "name_en": major.name_en, "name_ar": major.name_ar}


@router.get("/settings", response_model=dict[str, int | float])
def get_settings_values(actor: Actor = Depends(auth("pa")), db: Session = Depends(get_db)):
    return settings.all_values(db)


@router.patch("/settings", response_model=dict[str, int | float])
def patch_settings(body: dict[str, int | float], actor: Actor = Depends(auth("pa")), db: Session = Depends(get_db)):
    clean = settings.validate(body)
    current = settings.all_values(db)
    for key, value in clean.items():
        row = db.get(SystemSetting, key)
        if row is None:
            db.add(SystemSetting(key=key, value=value, updated_by=actor.id))
        else:
            row.value, row.updated_by = value, actor.id
    changed = {k: v for k, v in clean.items() if current.get(k) != v}
    if changed:
        audit.record(db, actor.user, "update", "settings", "system",
                     old={k: current.get(k) for k in changed}, new=changed)
    db.commit()
    return settings.all_values(db)
