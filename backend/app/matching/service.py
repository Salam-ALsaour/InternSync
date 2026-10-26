"""Matching: profile and vacancy texts, embedding on write, ranking, and the application snapshot (FR-MAT-01 – 07,
Design 6.2; Increment 2 design, Section 4). Results are advisory; nothing here changes an application."""
import logging
import uuid
from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.ai.embeddings import PASSAGE, QUERY, get_embedder
from app.core import clock, settings
from app.core.errors import ApiError, conflict
from app.cycles.service import student_open_enrollment
from app.matching.scoring import Fit, Weights, score
from app.models import (
    Application,
    College,
    Company,
    Cv,
    MatchScore,
    Skill,
    SkillResource,
    StudentProfile,
    StudentSkill,
    User,
    Vacancy,
    VacancyMajor,
    VacancySkill,
    VacancyUniversity,
)

log = logging.getLogger("internsync.matching")
CV_CHARS = 2000


def weights(db: Session) -> Weights:
    g = settings.get
    return Weights(semantic=g(db, "matching.weight_semantic"), required=g(db, "matching.weight_required"),
                   preferred=g(db, "matching.weight_preferred"), floor=g(db, "matching.semantic_floor"),
                   ceiling=g(db, "matching.semantic_ceiling"))


# ---------------------------------------------------------------- texts and embeddings
def profile_text(db: Session, student_id: uuid.UUID) -> str:
    profile = db.get(StudentProfile, student_id)
    skills = db.execute(select(Skill.name_en, Skill.name_ar).join(StudentSkill, StudentSkill.skill_id == Skill.id)
                        .where(StudentSkill.student_id == student_id).order_by(Skill.name_en)).all()
    cv = db.scalar(select(Cv.extracted_text).where(Cv.student_id == student_id, Cv.text_status == "ok")
                   .order_by(Cv.version_no.desc()).limit(1))
    parts = [", ".join(f"{en} ({ar})" for en, ar in skills), ", ".join(profile.interests or []), (cv or "")[:CV_CHARS]]
    return QUERY + "\n".join(p for p in parts if p)


def vacancy_text(db: Session, v: Vacancy) -> str:
    skills = db.scalars(select(Skill.name_en).join(VacancySkill, VacancySkill.skill_id == Skill.id)
                        .where(VacancySkill.vacancy_id == v.id).order_by(Skill.name_en)).all()
    return PASSAGE + "\n".join([v.title, v.description, ", ".join(skills)])


def _embed(text: str) -> tuple[list[float], str] | None:
    embedder = get_embedder()
    if embedder is None:
        return None
    try:
        return embedder.encode([text])[0], embedder.version
    except Exception:  # the request still succeeds; the embed_missing job retries
        log.exception("embedding failed")
        return None


def embed_profile(db: Session, student_id: uuid.UUID) -> None:
    """Called after the profile's skills, interests, or CV change (decision RQ-3)."""
    profile = db.get(StudentProfile, student_id)
    out = _embed(profile_text(db, student_id)) if profile.skills_confirmed_at else None
    profile.embedding, profile.embedding_model = (out[0], out[1]) if out else (None, None)
    profile.embedded_at = clock.now() if out else None


def embed_vacancy(db: Session, v: Vacancy) -> None:
    """Called after a vacancy is created or edited (decision RQ-3)."""
    db.flush()
    out = _embed(vacancy_text(db, v))
    v.embedding, v.embedding_model = (out[0], out[1]) if out else (None, None)
    v.embedded_at = clock.now() if out else None


def embed_missing(db: Session) -> int:
    """Job: embed profiles and open vacancies that have no embedding or one from another model version."""
    embedder = get_embedder()
    if embedder is None:
        return 0
    version, done = embedder.version, 0
    profiles = db.scalars(select(StudentProfile).where(StudentProfile.skills_confirmed_at.is_not(None), or_(
        StudentProfile.embedding.is_(None), StudentProfile.embedding_model != version)).limit(200)).all()
    for p in profiles:
        embed_profile(db, p.user_id)
        done += p.embedding is not None
    vacancies = db.scalars(select(Vacancy).where(Vacancy.status != "closed", or_(
        Vacancy.embedding.is_(None), Vacancy.embedding_model != version)).limit(200)).all()
    for v in vacancies:
        embed_vacancy(db, v)
        done += v.embedding is not None
    return done


# ---------------------------------------------------------------- ranking
def _ref(k) -> dict:
    return {"id": k.id, "name_en": k.name_en, "name_ar": k.name_ar}


def _require_ready(db: Session, student: User):
    cycle = student_open_enrollment(db, student.id)
    if student.verification_status != "verified" or cycle is None:
        raise ApiError(403, "VERIFICATION_REQUIRED")
    profile = db.get(StudentProfile, student.id)
    if profile.skills_confirmed_at is None:
        raise conflict("SKILLS_NOT_CONFIRMED")
    return cycle, profile


def _eligible(db: Session, student: User, profile: StudentProfile, cycle):
    """Vacancies the student may apply to (FR-MAT-03, CR-06), as one query."""
    university = db.get(College, student.college_id).university_id
    targeted = select(VacancyUniversity.vacancy_id).where(VacancyUniversity.vacancy_id == Vacancy.id)
    ours = targeted.where(VacancyUniversity.university_id == university)
    major = select(VacancyMajor.vacancy_id).where(VacancyMajor.vacancy_id == Vacancy.id,
                                                   VacancyMajor.major_id == profile.major_id)
    return (Vacancy.status == "published", Vacancy.application_deadline > clock.now(),
            or_(~targeted.exists(), ours.exists()), major.exists(),
            or_(Vacancy.min_gpa.is_(None), Vacancy.min_gpa <= profile.gpa), Vacancy.training_type == cycle.type)


def _semantic_vector(profile: StudentProfile):
    """The profile vector when it can be compared: the model is loaded and the vector is from that model."""
    embedder = get_embedder()
    if embedder is None or profile.embedding is None or profile.embedding_model != embedder.version:
        return None, None
    return profile.embedding, embedder.version


def _score_rows(db: Session, student_id: uuid.UUID, rows, w: Weights) -> list[tuple[Vacancy, Fit]]:
    ids = [v.id for v, _ in rows]
    by_vacancy: dict[uuid.UUID, tuple[set, set]] = {i: (set(), set()) for i in ids}
    for vid, sid, kind in db.execute(select(VacancySkill.vacancy_id, VacancySkill.skill_id, VacancySkill.kind)
                                     .where(VacancySkill.vacancy_id.in_(ids))):
        by_vacancy[vid][0 if kind == "required" else 1].add(sid)
    mine = set(db.scalars(select(StudentSkill.skill_id).where(StudentSkill.student_id == student_id)))
    return [(v, score(mine, *by_vacancy[v.id], cosine, w)) for v, cosine in rows]


def _store(db: Session, student_id: uuid.UUID, scored: list[tuple[Vacancy, Fit]], version: str | None) -> None:
    if not scored:
        return
    now = clock.now()

    def dec(x, places="0.0001"):
        return None if x is None else Decimal(str(x)).quantize(Decimal(places))
    rows = [{"student_id": student_id, "vacancy_id": v.id, "fit_score": dec(f.score, "0.01"),
             "semantic": dec(f.semantic), "required_ratio": dec(f.required), "preferred_ratio": dec(f.preferred),
             "mode": f.mode, "matched_skill_ids": list(f.matched), "missing_skill_ids": list(f.missing),
             "model_version": version if f.mode == "semantic" else None, "computed_at": now} for v, f in scored]
    stmt = insert(MatchScore).values(rows)
    keys = ("student_id", "vacancy_id")
    stmt = stmt.on_conflict_do_update(index_elements=list(keys),
                                      set_={c: stmt.excluded[c] for c in rows[0] if c not in keys})
    db.execute(stmt)


def _items(db: Session, student_id: uuid.UUID, scored: list[tuple[Vacancy, Fit]]) -> list[dict]:
    if not scored:
        return []
    skill_ids = {s for _, f in scored for s in (*f.matched, *f.missing)}
    skills = {k.id: k for k in db.scalars(select(Skill).where(Skill.id.in_(skill_ids)))} if skill_ids else {}
    companies = {c.id: c.name for c in db.scalars(select(Company).where(
        Company.id.in_({v.company_id for v, _ in scored})))}
    applied = set(db.scalars(select(Application.vacancy_id).where(
        Application.student_id == student_id, Application.vacancy_id.in_([v.id for v, _ in scored]))))
    return [{
        "vacancy": {"id": v.id, "title": v.title, "company": companies[v.company_id], "city": v.city,
                    "training_type": v.training_type, "application_deadline": v.application_deadline,
                    "seats": v.seats},
        "fit_score": f.score, "mode": f.mode,
        "parts": {"semantic": f.semantic, "required": f.required, "preferred": f.preferred},
        "matched_skills": [_ref(skills[s]) for s in f.matched], "missing_skills": [_ref(skills[s]) for s in f.missing],
        "already_applied": v.id in applied,
    } for v, f in scored]


def rank(db: Session, student: User, limit: int) -> dict:
    """FR-MAT-01: the eligible vacancies by fit, highest first; ties by the required part, then the deadline."""
    cycle, profile = _require_ready(db, student)
    vector, version = _semantic_vector(profile)
    eligible = _eligible(db, student, profile, cycle)
    if vector is None:
        rows = [(v, None) for v in db.scalars(select(Vacancy).where(*eligible))]
    else:  # a vacancy without an embedding of this model version is scored by the rules
        cosine = (1 - Vacancy.embedding.cosine_distance(vector)).label("cosine")
        rows = [(v, float(c) if model == version and c is not None else None)
                for v, model, c in db.execute(select(Vacancy, Vacancy.embedding_model, cosine).where(*eligible))]
    w = weights(db)
    scored = _score_rows(db, student.id, rows, w)
    scored.sort(key=lambda vf: (-vf[1].score, -vf[1].required, vf[0].application_deadline))
    _store(db, student.id, scored, version)
    modes = {f.mode for _, f in scored}
    return {"mode": "semantic" if modes == {"semantic"} else "basic" if modes <= {"basic"} else "mixed",
            "model_version": version, "advisory": True, "total": len(scored),
            "items": _items(db, student.id, scored[:limit])}


def match_one(db: Session, student: User, vacancy: Vacancy) -> tuple[Fit, str | None]:
    """The fit of one vacancy, computed exactly as in the ranking (detail view and application snapshot)."""
    profile = db.get(StudentProfile, student.id)
    vector, version = _semantic_vector(profile)
    cosine = None
    if vector is not None and vacancy.embedding is not None and vacancy.embedding_model == version:
        cosine = float(db.scalar(select(1 - Vacancy.embedding.cosine_distance(vector)).where(Vacancy.id == vacancy.id)))
    ((_, fit),) = _score_rows(db, student.id, [(vacancy, cosine)], weights(db))
    return fit, version if fit.mode == "semantic" else None


def one(db: Session, student: User, vacancy: Vacancy) -> dict:
    from app.vacancies.service import eligibility

    _require_ready(db, student)
    reason = eligibility(db, student, vacancy)
    if reason:
        raise conflict("NOT_ELIGIBLE", reason=reason)
    fit, version = match_one(db, student, vacancy)
    _store(db, student.id, [(vacancy, fit)], version)
    return {**_items(db, student.id, [(vacancy, fit)])[0], "model_version": version, "advisory": True}


def snapshot(db: Session, student: User, application: Application, vacancy: Vacancy) -> None:
    """Store the fit at the moment of applying (API 3.7, NFR-AI-02); skipped when the skills are not confirmed."""
    if db.scalar(select(StudentProfile.skills_confirmed_at).where(StudentProfile.user_id == student.id)) is None:
        return
    fit, version = match_one(db, student, vacancy)
    application.fit_score = Decimal(str(fit.score)).quantize(Decimal("0.01"))
    application.match_mode, application.model_version = fit.mode, version


def plan(db: Session, student: User, vacancy: Vacancy) -> dict:
    """FR-MAT-06: each missing required skill with its learning resources."""
    item = one(db, student, vacancy)
    out = []
    for skill in item["missing_skills"]:
        resources = [{"title": r.title, "url": r.url, "estimated_effort": r.estimated_effort, "language": r.language}
                     for r in db.scalars(select(SkillResource).where(SkillResource.skill_id == skill["id"])
                                         .order_by(SkillResource.position))]
        out.append({"skill": skill, "resources": resources})
    return {"vacancy_id": vacancy.id, "missing_skills": out, "advisory": True}

