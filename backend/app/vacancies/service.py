"""Vacancies, applications, and placements (FR-VAC-01 – 08, Design Tables 5.1 and 5.2, CR-06)."""
import uuid
from datetime import date

from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from app.attendance.service import placement_percent
from app.core import audit, clock, settings
from app.core.deps import Actor
from app.core.errors import ApiError, conflict, field_error, forbidden, not_found
from app.cycles.service import ensure_open, student_open_enrollment
from app.matching import service as matching
from app.models import (
    Application,
    College,
    Company,
    CycleWeek,
    Grade,
    Major,
    Placement,
    ReportSlot,
    Skill,
    StudentProfile,
    TrainingCycle,
    University,
    User,
    Vacancy,
    VacancyMajor,
    VacancySkill,
    VacancyUniversity,
)
from app.notifications import events
from app.notifications.texts import names

ACTIVE = ("submitted", "accepted")


def ref(obj) -> dict:
    return {"id": obj.id, "name_en": obj.name_en, "name_ar": obj.name_ar}


def seats_taken(db: Session, vacancy_id: uuid.UUID) -> int:
    return db.scalar(select(func.count()).select_from(Placement).where(Placement.vacancy_id == vacancy_id,
                                                                       Placement.status != "cancelled")) or 0


# ---------------------------------------------------------------- vacancy output and visibility
def student_university(db: Session, student: User) -> uuid.UUID:
    return db.get(College, student.college_id).university_id


def open_to_university(db: Session, vacancy_id: uuid.UUID, university_id: uuid.UUID) -> bool:
    targets = set(db.scalars(select(VacancyUniversity.university_id).where(VacancyUniversity.vacancy_id == vacancy_id)))
    return not targets or university_id in targets


def eligibility(db: Session, student: User, vacancy: Vacancy) -> str | None:
    """Return None when eligible, otherwise the reason (FR-MAT-03, FR-VAC-04, CR-06)."""
    cycle = student_open_enrollment(db, student.id)
    if student.verification_status != "verified" or cycle is None:
        return "not_enrolled"
    profile = db.get(StudentProfile, student.id)
    majors = set(db.scalars(select(VacancyMajor.major_id).where(VacancyMajor.vacancy_id == vacancy.id)))
    if profile.major_id not in majors:
        return "major_not_eligible"
    if vacancy.min_gpa is not None and profile.gpa < vacancy.min_gpa:
        return "gpa_below_minimum"
    if vacancy.training_type != cycle.type:
        return "training_type_mismatch"
    if vacancy.application_deadline <= clock.now():
        return "deadline_passed"
    return None


def vacancy_out(db: Session, v: Vacancy, actor: Actor | None = None) -> dict:
    company = db.get(Company, v.company_id)
    owner = db.get(User, v.company_supervisor_id)
    skills = db.execute(select(VacancySkill.kind, Skill).join(Skill, Skill.id == VacancySkill.skill_id)
                        .where(VacancySkill.vacancy_id == v.id).order_by(Skill.name_en)).all()
    majors = db.scalars(select(Major).join(VacancyMajor, VacancyMajor.major_id == Major.id)
                        .where(VacancyMajor.vacancy_id == v.id).order_by(Major.name_en))
    unis = db.scalars(select(University).join(VacancyUniversity, VacancyUniversity.university_id == University.id)
                      .where(VacancyUniversity.vacancy_id == v.id).order_by(University.name_en))
    out = {k: getattr(v, k) for k in ("id", "company_id", "title", "city", "description", "training_type",
                                      "training_start", "training_end", "min_gpa", "seats", "application_deadline",
                                      "status", "published_at", "closed_at")}
    out.update(company_name=company.name, company_supervisor=ref(owner), seats_taken=seats_taken(db, v.id),
               required_skills=[ref(k) for kind, k in skills if kind == "required"],
               preferred_skills=[ref(k) for kind, k in skills if kind == "preferred"],
               majors=[ref(m) for m in majors], target_universities=[ref(u) for u in unis])
    if actor is not None and actor.code == "cs":
        out["applicants"] = db.scalar(select(func.count()).select_from(Application)
                                      .where(Application.vacancy_id == v.id))
    if actor is not None and actor.code == "st":
        reason = eligibility(db, actor.user, v)
        out["eligible"], out["ineligible_reason"] = reason is None, reason
        applied = select(Application.id).where(Application.vacancy_id == v.id, Application.student_id == actor.id)
        out["already_applied"] = db.scalar(applied) is not None
    return out


def can_view(db: Session, actor: Actor, v: Vacancy) -> bool:
    code = actor.code
    if code == "pa":
        return True
    if code == "cs":
        return v.company_id == actor.user.company_id
    if code in ("st", "co"):
        return v.status == "published" and open_to_university(db, v.id, student_university(db, actor.user))
    return False


def browse_query(db: Session, actor: Actor, f: dict):
    stmt = select(Vacancy)
    code = actor.code
    if code == "cs":
        stmt = stmt.where(Vacancy.company_id == actor.user.company_id)
        if f.get("status"):
            stmt = stmt.where(Vacancy.status == f["status"])
    elif code in ("st", "co"):
        uni = student_university(db, actor.user)
        targeted = select(VacancyUniversity.vacancy_id).where(VacancyUniversity.vacancy_id == Vacancy.id)
        mine = select(VacancyUniversity.vacancy_id).where(VacancyUniversity.vacancy_id == Vacancy.id,
                                                          VacancyUniversity.university_id == uni)
        stmt = stmt.where(Vacancy.status == "published", or_(~targeted.exists(), mine.exists()))
    elif f.get("status"):
        stmt = stmt.where(Vacancy.status == f["status"])
    if f.get("q"):
        like = f"%{f['q'].strip()}%"
        stmt = stmt.where(or_(Vacancy.title.ilike(like), Vacancy.description.ilike(like)))
    if f.get("city"):
        stmt = stmt.where(Vacancy.city.ilike(f["city"].strip()))
    if f.get("company_id"):
        stmt = stmt.where(Vacancy.company_id == f["company_id"])
    if f.get("training_type"):
        stmt = stmt.where(Vacancy.training_type == f["training_type"])
    if f.get("major_id"):
        stmt = stmt.where(select(VacancyMajor.vacancy_id).where(VacancyMajor.vacancy_id == Vacancy.id,
                                                                VacancyMajor.major_id == f["major_id"]).exists())
    if f.get("skill_id"):
        stmt = stmt.where(select(VacancySkill.vacancy_id).where(VacancySkill.vacancy_id == Vacancy.id,
                                                                VacancySkill.skill_id == f["skill_id"]).exists())
    return stmt.order_by(Vacancy.application_deadline, Vacancy.created_at)


# ---------------------------------------------------------------- create, edit, publish, close
def _check_refs(db: Session, data: dict) -> None:
    skill_ids = set(data.get("required_skill_ids") or []) | set(data.get("preferred_skill_ids") or [])
    if skill_ids and len(set(db.scalars(select(Skill.id).where(Skill.id.in_(skill_ids))))) != len(skill_ids):
        raise field_error("required_skill_ids", "VALIDATION_ERROR")
    if set(data.get("required_skill_ids") or []) & set(data.get("preferred_skill_ids") or []):
        raise field_error("preferred_skill_ids", "VALIDATION_ERROR")
    majors = set(data.get("major_ids") or [])
    if majors and len(set(db.scalars(select(Major.id).where(Major.id.in_(majors))))) != len(majors):
        raise field_error("major_ids", "VALIDATION_ERROR")
    unis = set(data.get("target_university_ids") or [])
    if unis and len(set(db.scalars(select(University.id).where(University.id.in_(unis))))) != len(unis):
        raise field_error("target_university_ids", "VALIDATION_ERROR")


def _check_dates(start: date, end: date) -> None:
    if end <= start:
        raise field_error("training_end", "VALIDATION_ERROR")


def _set_links(db: Session, v: Vacancy, data: dict) -> None:
    if "required_skill_ids" in data or "preferred_skill_ids" in data:
        required = data.get("required_skill_ids")
        preferred = data.get("preferred_skill_ids")
        current = {s.skill_id: s.kind for s in db.scalars(select(VacancySkill).where(VacancySkill.vacancy_id == v.id))}
        if required is None:
            required = [k for k, kind in current.items() if kind == "required"]
        if preferred is None:
            preferred = [k for k, kind in current.items() if kind == "preferred"]
        db.execute(delete(VacancySkill).where(VacancySkill.vacancy_id == v.id))
        for sid in dict.fromkeys(required):
            db.add(VacancySkill(vacancy_id=v.id, skill_id=sid, kind="required"))
        for sid in dict.fromkeys(preferred):
            if sid not in required:
                db.add(VacancySkill(vacancy_id=v.id, skill_id=sid, kind="preferred"))
    if data.get("major_ids") is not None:
        db.execute(delete(VacancyMajor).where(VacancyMajor.vacancy_id == v.id))
        for mid in dict.fromkeys(data["major_ids"]):
            db.add(VacancyMajor(vacancy_id=v.id, major_id=mid))
    if data.get("target_university_ids") is not None:
        db.execute(delete(VacancyUniversity).where(VacancyUniversity.vacancy_id == v.id))
        for uid in dict.fromkeys(data["target_university_ids"]):
            db.add(VacancyUniversity(vacancy_id=v.id, university_id=uid))


def require_verified_company(db: Session, actor: Actor) -> Company:
    company = db.get(Company, actor.user.company_id)
    if company.status != "verified":
        raise conflict("COMPANY_NOT_VERIFIED")
    return company


def create(db: Session, actor: Actor, data: dict) -> Vacancy:
    company = require_verified_company(db, actor)
    _check_dates(data["training_start"], data["training_end"])
    _check_refs(db, data)
    publish = data.pop("publish")
    fields = {k: data[k] for k in ("title", "city", "description", "training_type", "training_start",
                                   "training_end", "min_gpa", "seats", "application_deadline")}
    v = Vacancy(company_id=company.id, company_supervisor_id=actor.id, created_by=actor.id, **fields)
    db.add(v)
    db.flush()
    _set_links(db, v, data)
    matching.embed_vacancy(db, v)
    audit.record(db, actor.user, "create", "vacancy", v.id, company_id=company.id,
                 new={"title": v.title, "seats": v.seats})
    if publish:
        publish_vacancy(db, actor, v)
    return v


def publish_vacancy(db: Session, actor: Actor, v: Vacancy) -> None:
    require_verified_company(db, actor)
    if v.status != "draft":
        raise conflict("INVALID_TRANSITION")
    if v.application_deadline <= clock.now():
        raise field_error("application_deadline", "DEADLINE_PASSED")
    if not db.scalar(select(VacancyMajor.vacancy_id).where(VacancyMajor.vacancy_id == v.id)):
        raise field_error("major_ids", "VALIDATION_ERROR")
    v.status, v.published_at = "published", clock.now()
    audit.record(db, actor.user, "publish", "vacancy", v.id, company_id=v.company_id, old={"status": "draft"},
                 new={"status": "published"})


def close_vacancy(db: Session, actor: Actor | None, v: Vacancy) -> None:
    """Close a published vacancy; its active applications are withdrawn (Design 5.1)."""
    if v.status != "published":
        raise conflict("INVALID_TRANSITION")
    now = clock.now()
    v.status, v.closed_at = "closed", now
    for a in db.scalars(select(Application).where(Application.vacancy_id == v.id, Application.status.in_(ACTIVE))):
        a.status, a.withdraw_reason, a.withdrawn_at = "withdrawn", "vacancy_closed", now
        events.application_withdrawn(db, a, v, "vacancy_closed")
    audit.record(db, actor.user if actor else None, "close", "vacancy", v.id, company_id=v.company_id,
                 old={"status": "published"}, new={"status": "closed"})


def patch(db: Session, actor: Actor, v: Vacancy, data: dict) -> None:
    if v.status == "closed":
        raise conflict("INVALID_TRANSITION")
    _check_refs(db, data)
    _check_dates(data.get("training_start") or v.training_start, data.get("training_end") or v.training_end)
    if data.get("seats") is not None and data["seats"] < seats_taken(db, v.id):
        raise field_error("seats", "SEATS_BELOW_PLACEMENTS")
    if "company_supervisor_id" in data and data["company_supervisor_id"] is not None:
        if not actor.is_ca:
            raise forbidden()
        sup = db.get(User, data["company_supervisor_id"])
        if sup is None or sup.company_id != v.company_id or not sup.is_active or sup.password_hash is None:
            raise field_error("company_supervisor_id", "COMPANY_SUPERVISOR_INVALID")
    if v.status == "published" and data.get("application_deadline") and data["application_deadline"] <= clock.now():
        raise field_error("application_deadline", "DEADLINE_PASSED")
    fields = {k: data[k] for k in ("title", "city", "description", "training_type", "training_start", "training_end",
                                   "min_gpa", "seats", "application_deadline", "company_supervisor_id")
              if k in data and (data[k] is not None or k == "min_gpa")}
    old, new = audit.changes(v, fields)
    _set_links(db, v, {k: data[k] for k in ("required_skill_ids", "preferred_skill_ids", "major_ids",
                                            "target_university_ids") if k in data})
    if new or any(k in data for k in ("required_skill_ids", "preferred_skill_ids")):
        matching.embed_vacancy(db, v)
    audit.record(db, actor.user, "update", "vacancy", v.id, company_id=v.company_id, old=old,
                 new={**new, **{k: data[k] for k in data if k.endswith("_ids") and data[k] is not None}})


# ---------------------------------------------------------------- applications
def apply(db: Session, actor: Actor, v: Vacancy) -> Application:
    student = actor.user
    if v.status != "published":
        raise conflict("VACANCY_NOT_OPEN")
    if not open_to_university(db, v.id, student_university(db, student)):
        raise forbidden()
    cycle = student_open_enrollment(db, student.id)
    if cycle is None:
        raise ApiError(403, "VERIFICATION_REQUIRED")
    if v.application_deadline <= clock.now():
        raise conflict("DEADLINE_PASSED")
    if db.scalar(select(Application.id).where(Application.vacancy_id == v.id, Application.student_id == student.id)):
        raise conflict("DUPLICATE_APPLICATION")
    reason = eligibility(db, student, v)
    if reason:
        raise conflict("NOT_ELIGIBLE", reason=reason)
    if db.scalar(select(Placement.id).where(Placement.student_id == student.id, Placement.cycle_id == cycle.id,
                                            Placement.status != "cancelled")):
        raise conflict("ALREADY_PLACED")
    active = db.scalar(select(func.count()).select_from(Application)
                       .where(Application.student_id == student.id, Application.status.in_(ACTIVE)))
    if active >= settings.get(db, "applications.max_active"):
        raise conflict("APPLICATION_LIMIT_REACHED")
    a = Application(vacancy_id=v.id, student_id=student.id)
    db.add(a)
    db.flush()
    matching.snapshot(db, student, a, v)
    audit.record(db, student, "apply", "application", a.id, student_id=student.id, college_id=student.college_id,
                 company_id=v.company_id, new={"vacancy_id": v.id})
    events.application_received(db, a, v)
    return a


def application_out(db: Session, a: Application) -> dict:
    v = db.get(Vacancy, a.vacancy_id)
    student = db.get(User, a.student_id)
    placement = db.scalar(select(Placement.id).where(Placement.application_id == a.id))
    return {"id": a.id, "status": a.status, "withdraw_reason": a.withdraw_reason, "created_at": a.created_at,
            "decided_at": a.decided_at, "vacancy_id": v.id, "vacancy_title": v.title,
            "company_name": db.get(Company, v.company_id).name, "student_id": student.id,
            "student_name_en": student.name_en, "student_name_ar": student.name_ar, "placement_id": placement}


def applicant_out(db: Session, a: Application) -> dict:
    from app.profiles.router import confirmed_skills, current_cv
    out = application_out(db, a)
    student = db.get(User, a.student_id)
    college = db.get(College, student.college_id)
    uni = db.get(University, college.university_id)
    profile = db.get(StudentProfile, student.id)
    major = db.get(Major, profile.major_id)
    cv = current_cv(db, student.id)
    out.update(university_en=uni.name_en, university_ar=uni.name_ar, college_en=college.name_en,
               college_ar=college.name_ar, major_en=major.name_en, major_ar=major.name_ar, gpa=profile.gpa,
               skills=[{k: s[k] for k in ("id", "name_en", "name_ar")} for s in confirmed_skills(db, student.id)],
               cv_file_id=cv.file_id if cv else None, fit_score=a.fit_score, match_mode=a.match_mode)
    return out


def can_view_application(db: Session, actor: Actor, a: Application) -> bool:
    code = actor.code
    if code == "st":
        return a.student_id == actor.id
    if code == "co":
        return db.get(User, a.student_id).college_id == actor.user.college_id
    if code == "cs":
        v = db.get(Vacancy, a.vacancy_id)
        return v.company_id == actor.user.company_id and (actor.is_ca or v.company_supervisor_id == actor.id)
    return False


def decide(db: Session, actor: Actor, a: Application, accept: bool) -> None:
    v = db.get(Vacancy, a.vacancy_id)
    if v.company_id != actor.user.company_id or not (actor.is_ca or v.company_supervisor_id == actor.id):
        raise forbidden()
    if a.status != "submitted":
        raise conflict("INVALID_TRANSITION")
    a.status = "accepted" if accept else "declined"
    a.decided_by, a.decided_at = actor.id, clock.now()
    student = db.get(User, a.student_id)
    audit.record(db, actor.user, "accept" if accept else "decline", "application", a.id, student_id=student.id,
                 college_id=student.college_id, company_id=v.company_id, old={"status": "submitted"},
                 new={"status": a.status})
    events.application_decided(db, a, v)


def withdraw(db: Session, actor: Actor, a: Application) -> None:
    if a.student_id != actor.id:
        raise forbidden()
    if a.status != "submitted":
        raise conflict("INVALID_TRANSITION")
    a.status, a.withdraw_reason, a.withdrawn_at = "withdrawn", "student", clock.now()
    v = db.get(Vacancy, a.vacancy_id)
    audit.record(db, actor.user, "withdraw", "application", a.id, student_id=actor.id,
                 college_id=actor.user.college_id, company_id=v.company_id, old={"status": "submitted"},
                 new={"status": "withdrawn"})


# ---------------------------------------------------------------- placements
def confirm_placement(db: Session, actor: Actor, application_id: uuid.UUID, academic_supervisor_id: uuid.UUID,
                      company_supervisor_id: uuid.UUID | None) -> Placement:
    a = db.get(Application, application_id)
    if a is None:
        raise not_found()
    student = db.get(User, a.student_id)
    if student.college_id != actor.user.college_id:
        raise forbidden()
    if a.status != "accepted":
        raise conflict("INVALID_TRANSITION")
    cycle = student_open_enrollment(db, student.id)
    if cycle is None:
        raise conflict("CYCLE_NOT_OPEN")
    ensure_open(cycle)
    if db.scalar(select(Placement.id).where(Placement.student_id == student.id, Placement.cycle_id == cycle.id,
                                            Placement.status != "cancelled")):
        raise conflict("ALREADY_PLACED")
    v = db.get(Vacancy, a.vacancy_id)
    if seats_taken(db, v.id) >= v.seats:
        raise conflict("NO_SEATS")
    academic = db.get(User, academic_supervisor_id)
    if academic is None or academic.role != "academic_supervisor" or academic.college_id != student.college_id \
            or not academic.is_active:
        raise field_error("academic_supervisor_id", "ACADEMIC_SUPERVISOR_INVALID")
    company_sup = db.get(User, company_supervisor_id or v.company_supervisor_id)
    if company_sup is None or company_sup.company_id != v.company_id or not company_sup.is_active:
        raise field_error("company_supervisor_id", "COMPANY_SUPERVISOR_INVALID")
    now = clock.now()
    p = Placement(application_id=a.id, student_id=student.id, cycle_id=cycle.id, vacancy_id=v.id,
                  company_supervisor_id=company_sup.id, academic_supervisor_id=academic.id, confirmed_by=actor.id,
                  confirmed_at=now)
    db.add(p)
    db.flush()
    for w in db.scalars(select(CycleWeek).where(CycleWeek.cycle_id == cycle.id).order_by(CycleWeek.week_no)):
        db.add(ReportSlot(placement_id=p.id, kind="weekly", week_no=w.week_no, due_at=w.report_due_at))
    db.add(ReportSlot(placement_id=p.id, kind="final", week_no=None, due_at=cycle.final_report_due_at))
    db.add(Grade(placement_id=p.id))
    a.status = "placed"
    for other in db.scalars(select(Application).where(Application.student_id == student.id, Application.id != a.id,
                                                      Application.status.in_(ACTIVE))):
        other.status, other.withdraw_reason, other.withdrawn_at = "withdrawn", "placed_elsewhere", now
        events.application_withdrawn(db, other, db.get(Vacancy, other.vacancy_id), "placed_elsewhere")
    audit.record(db, actor.user, "confirm", "placement", p.id, student_id=student.id, college_id=student.college_id,
                 company_id=v.company_id, cycle_id=cycle.id,
                 new={"vacancy_id": v.id, "academic_supervisor_id": academic.id,
                      "company_supervisor_id": company_sup.id})
    events.placement_event(db, "placement.confirmed", p)
    db.flush()
    if seats_taken(db, v.id) >= v.seats and v.status == "published":
        close_vacancy(db, None, v)
    return p


def placement_out(db: Session, p: Placement) -> dict:
    student = db.get(User, p.student_id)
    v = db.get(Vacancy, p.vacancy_id)
    cycle = db.get(TrainingCycle, p.cycle_id)
    slots = db.scalars(select(ReportSlot).where(ReportSlot.placement_id == p.id)).all()
    summary = {"total": len(slots), "submitted": sum(s.status == "submitted" for s in slots),
               "accepted": sum(s.status == "accepted" for s in slots),
               "revision_requested": sum(s.status == "revision_requested" for s in slots),
               "late": sum(s.is_late for s in slots), "missing": sum(s.is_missing for s in slots)}
    return {"id": p.id, "status": p.status, "cycle_id": cycle.id, "cycle_name": cycle.name, "student": ref(student),
            "student_email": student.email, "vacancy_id": v.id, "vacancy_title": v.title,
            "company_name": db.get(Company, v.company_id).name,
            "company_supervisor": ref(db.get(User, p.company_supervisor_id)),
            "academic_supervisor": ref(db.get(User, p.academic_supervisor_id)), "confirmed_at": p.confirmed_at,
            "cancel_reason": p.cancel_reason, "reports": summary, "attendance_percent": placement_percent(db, p),
            "grade_status": db.scalar(select(Grade.status).where(Grade.placement_id == p.id))}


def placements_query(actor: Actor, f: dict):
    stmt = select(Placement).join(User, User.id == Placement.student_id).order_by(Placement.confirmed_at.desc())
    code = actor.code
    if code == "st":
        stmt = stmt.where(Placement.student_id == actor.id)
    elif code == "as":
        stmt = stmt.where(Placement.academic_supervisor_id == actor.id)
    elif code == "co":
        stmt = stmt.where(User.college_id == actor.user.college_id)
    elif actor.is_ca:
        stmt = stmt.join(Vacancy, Vacancy.id == Placement.vacancy_id).where(Vacancy.company_id == actor.user.company_id)
    else:
        stmt = stmt.where(Placement.company_supervisor_id == actor.id)
    if f.get("cycle_id"):
        stmt = stmt.where(Placement.cycle_id == f["cycle_id"])
    if f.get("status"):
        stmt = stmt.where(Placement.status == f["status"])
    if f.get("academic_supervisor_id"):
        stmt = stmt.where(Placement.academic_supervisor_id == f["academic_supervisor_id"])
    if f.get("company_id"):
        stmt = stmt.where(Placement.vacancy_id.in_(select(Vacancy.id).where(Vacancy.company_id == f["company_id"])))
    return stmt


def change_supervisor(db: Session, actor: Actor, p: Placement, academic_supervisor_id: uuid.UUID,
                      reason: str) -> None:
    if p.status != "active":
        raise conflict("INVALID_TRANSITION")
    if not reason.strip():
        raise ApiError(422, "REASON_REQUIRED")
    student = db.get(User, p.student_id)
    academic = db.get(User, academic_supervisor_id)
    if academic is None or academic.role != "academic_supervisor" or academic.college_id != student.college_id \
            or not academic.is_active:
        raise field_error("academic_supervisor_id", "ACADEMIC_SUPERVISOR_INVALID")
    old = p.academic_supervisor_id
    p.academic_supervisor_id = academic.id
    audit.record(db, actor.user, "change_supervisor", "placement", p.id, student_id=student.id,
                 college_id=student.college_id, cycle_id=p.cycle_id, old={"academic_supervisor_id": old},
                 new={"academic_supervisor_id": academic.id}, reason=reason.strip())
    events.placement_event(db, "placement.supervisor_changed", p,
                           **names("supervisor", academic.name_en, academic.name_ar))


def cancel(db: Session, actor: Actor, p: Placement, reason: str) -> None:
    if p.status != "active":
        raise conflict("INVALID_TRANSITION")
    if not reason.strip():
        raise ApiError(422, "REASON_REQUIRED")
    p.status, p.cancelled_at, p.cancel_reason = "cancelled", clock.now(), reason.strip()
    db.get(Application, p.application_id).status = "placement_cancelled"
    student = db.get(User, p.student_id)
    audit.record(db, actor.user, "cancel", "placement", p.id, student_id=student.id, college_id=student.college_id,
                 cycle_id=p.cycle_id, old={"status": "active"}, new={"status": "cancelled"}, reason=p.cancel_reason)
    events.placement_event(db, "placement.cancelled", p, reason=p.cancel_reason)


def accepted_waiting(db: Session, actor: Actor) -> list[dict]:
    rows = db.execute(select(Application, User).join(User, User.id == Application.student_id)
                      .where(Application.status == "accepted", User.college_id == actor.user.college_id)
                      .order_by(Application.decided_at)).all()
    out = []
    for a, student in rows:
        v = db.get(Vacancy, a.vacancy_id)
        company = db.get(Company, v.company_id)
        sups = db.scalars(select(User).where(User.company_id == company.id, User.is_active,
                                             User.password_hash.is_not(None)).order_by(User.name_en))
        cycle = student_open_enrollment(db, student.id)
        out.append({"application_id": a.id, "student": ref(student),
                    "student_number": db.get(StudentProfile, student.id).student_number, "vacancy_id": v.id,
                    "vacancy_title": v.title, "company_id": company.id, "company_name": company.name,
                    "vacancy_owner": ref(db.get(User, v.company_supervisor_id)),
                    "company_supervisors": [ref(u) for u in sups], "decided_at": a.decided_at,
                    "cycle_id": cycle.id if cycle else None, "cycle_name": cycle.name if cycle else None})
    return out
