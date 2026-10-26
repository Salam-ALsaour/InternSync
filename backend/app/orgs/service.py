"""Universities, colleges, companies, verification, invitations, and accounts (FR-ORG-01 – 06, FR-ORG-08,
FR-AUT-06, Design Table 5.5)."""
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.auth.service import find_user_by_email, issue_token, link, revoke_sessions
from app.core import audit, clock, mail, settings
from app.core.deps import Actor
from app.core.errors import ApiError, conflict, forbidden, not_found
from app.models import (
    College,
    Company,
    Enrollment,
    Placement,
    StoredFile,
    TrainingCycle,
    University,
    User,
    Vacancy,
    VerificationDocument,
    VerificationRequest,
)


# ---------------------------------------------------------------- universities and colleges
def university_out(db: Session, uni: University, active_colleges_only: bool) -> dict:
    stmt = select(College).where(College.university_id == uni.id).order_by(College.name_en)
    if active_colleges_only:
        stmt = stmt.where(College.is_active)
    colleges = [{"id": c.id, "name_en": c.name_en, "name_ar": c.name_ar, "is_active": c.is_active}
                for c in db.scalars(stmt)]
    return {"id": uni.id, "name_en": uni.name_en, "name_ar": uni.name_ar, "email_domains": uni.email_domains,
            "gpa_scale": uni.gpa_scale, "is_active": uni.is_active, "colleges": colleges}


def _name_taken(db: Session, model, name_en: str, exclude: uuid.UUID | None = None, **filters) -> bool:
    stmt = select(model.id).where(func.lower(model.name_en) == name_en.strip().lower())
    for k, v in filters.items():
        stmt = stmt.where(getattr(model, k) == v)
    if exclude:
        stmt = stmt.where(model.id != exclude)
    return db.scalar(stmt) is not None


def _check_scale(value) -> None:
    if value is not None and str(value) not in ("4.00", "5.00", "4", "5", "4.0", "5.0"):
        raise ApiError(422, "VALIDATION_ERROR", errors=[{"field": "gpa_scale", "code": "VALIDATION_ERROR",
                                                         "message": "4.00 or 5.00"}])


def create_university(db: Session, actor: Actor, data: dict) -> University:
    _check_scale(data["gpa_scale"])
    if _name_taken(db, University, data["name_en"]):
        raise conflict("DUPLICATE_NAME")
    uni = University(name_en=data["name_en"].strip(), name_ar=data["name_ar"].strip(),
                     email_domains=[d.strip().lower() for d in data["email_domains"] if d.strip()],
                     gpa_scale=data["gpa_scale"])
    db.add(uni)
    db.flush()
    audit.record(db, actor.user, "create", "university", uni.id, new={"name_en": uni.name_en})
    return uni


def patch_university(db: Session, actor: Actor, uni: University, data: dict) -> None:
    _check_scale(data.get("gpa_scale"))
    if data.get("name_en") and _name_taken(db, University, data["name_en"], exclude=uni.id):
        raise conflict("DUPLICATE_NAME")
    if "email_domains" in data:
        data["email_domains"] = [d.strip().lower() for d in data["email_domains"] if d.strip()]
    old, new = audit.changes(uni, data)
    if new:
        audit.record(db, actor.user, "update", "university", uni.id, old=old, new=new)


def create_college(db: Session, actor: Actor, uni: University, data: dict) -> College:
    if _name_taken(db, College, data["name_en"], university_id=uni.id):
        raise conflict("DUPLICATE_NAME")
    college = College(university_id=uni.id, name_en=data["name_en"].strip(), name_ar=data["name_ar"].strip())
    db.add(college)
    db.flush()
    audit.record(db, actor.user, "create", "college", college.id, college_id=college.id,
                 new={"name_en": college.name_en})
    return college


def patch_college(db: Session, actor: Actor, college: College, data: dict) -> None:
    if data.get("name_en") and _name_taken(db, College, data["name_en"], exclude=college.id,
                                           university_id=college.university_id):
        raise conflict("DUPLICATE_NAME")
    old, new = audit.changes(college, data)
    if new:
        audit.record(db, actor.user, "update", "college", college.id, college_id=college.id, old=old, new=new)


def person(u: User | None) -> dict | None:
    return {"id": u.id, "name_en": u.name_en, "name_ar": u.name_ar, "email": u.email} if u else None


def college_detail(db: Session, college: College) -> dict:
    uni = db.get(University, college.university_id)
    coordinator = db.scalar(select(User).where(User.college_id == college.id, User.role == "coordinator",
                                               User.verification_status == "verified", User.is_active))
    students = db.scalar(select(func.count()).select_from(User).where(
        User.college_id == college.id, User.role == "student", User.verification_status == "verified"))
    supervisors = db.scalar(select(func.count()).select_from(User).where(
        User.college_id == college.id, User.role == "academic_supervisor"))
    return {"id": college.id, "name_en": college.name_en, "name_ar": college.name_ar, "is_active": college.is_active,
            "university_id": uni.id, "university_en": uni.name_en, "university_ar": uni.name_ar,
            "coordinator": person(coordinator), "verified_students": students, "academic_supervisors": supervisors}


def ensure_college_access(actor: Actor, college_id: uuid.UUID) -> None:
    if actor.code == "co" and actor.user.college_id != college_id:
        raise forbidden()


def ensure_company_access(actor: Actor, company_id: uuid.UUID) -> None:
    if actor.code == "cs" and actor.user.company_id != company_id:
        raise forbidden()


# ---------------------------------------------------------------- members and invitations
def member_out(db: Session, u: User) -> dict:
    field = Placement.academic_supervisor_id if u.role == "academic_supervisor" else Placement.company_supervisor_id
    active = db.scalar(select(func.count()).select_from(Placement).where(field == u.id,
                                                                          Placement.status == "active"))
    return {"id": u.id, "name_en": u.name_en, "name_ar": u.name_ar, "email": u.email, "is_active": u.is_active,
            "is_company_admin": u.is_company_admin, "invitation_pending": u.password_hash is None,
            "active_students": active}


def members(db: Session, role: str, college_id=None, company_id=None) -> list[dict]:
    stmt = select(User).where(User.role == role).order_by(User.name_en)
    stmt = stmt.where(User.college_id == college_id) if college_id else stmt.where(User.company_id == company_id)
    return [member_out(db, u) for u in db.scalars(stmt)]


def invite(db: Session, actor: Actor, role: str, data: dict, college: College | None = None,
           company: Company | None = None) -> tuple[User, str]:
    if find_user_by_email(db, data["email"]):
        raise conflict("EMAIL_TAKEN")
    user = User(email=data["email"].strip(), role=role, name_en=data["name_en"].strip(),
                name_ar=data["name_ar"].strip(), language=actor.user.language, verification_status="not_required",
                college_id=college.id if college else None, company_id=company.id if company else None)
    db.add(user)
    db.flush()
    raw = issue_token(db, user, "invitation")
    audit.record(db, actor.user, "invite", "user", user.id, college_id=user.college_id, company_id=user.company_id,
                 new={"email": user.email, "role": role})
    return user, raw


def mail_invitation(db: Session, actor: Actor, user: User, raw: str) -> None:
    lang = user.language
    if user.college_id:
        org = db.get(College, user.college_id)
        org_name = org.name_ar if lang == "ar" else org.name_en
    else:
        org_name = db.get(Company, user.company_id).name
    mail.send("invitation", user.email, lang, name=user.name_ar if lang == "ar" else user.name_en,
              inviter=actor.user.name_ar if lang == "ar" else actor.user.name_en,
              role=mail.ROLE_NAMES[user.role][lang], org=org_name, link=link("invite", raw),
              hours=settings.get(db, "auth.email_link_hours"))


# ---------------------------------------------------------------- companies
def company_out(db: Session, c: Company) -> dict:
    admin = db.scalar(select(User).where(User.company_id == c.id, User.is_company_admin))
    supervisors = db.scalar(select(func.count()).select_from(User).where(User.company_id == c.id))
    return {"id": c.id, "name": c.name, "commercial_reg_no": c.commercial_reg_no, "city": c.city,
            "website": c.website, "status": c.status, "verified_at": c.verified_at, "admin": person(admin),
            "supervisors": supervisors}


def suspend_company(db: Session, actor: Actor, company: Company, reason: str) -> None:
    from app.vacancies.service import close_vacancy
    if company.status != "verified":
        raise conflict("INVALID_TRANSITION")
    if not reason.strip():
        raise ApiError(422, "REASON_REQUIRED")
    company.status = "suspended"
    for v in db.scalars(select(Vacancy).where(Vacancy.company_id == company.id, Vacancy.status == "published")):
        close_vacancy(db, None, v)
    audit.record(db, actor.user, "suspend", "company", company.id, company_id=company.id, reason=reason.strip(),
                 old={"status": "verified"}, new={"status": "suspended"})


def reactivate_company(db: Session, actor: Actor, company: Company) -> None:
    if company.status != "suspended":
        raise conflict("INVALID_TRANSITION")
    company.status = "verified"
    audit.record(db, actor.user, "reactivate", "company", company.id, company_id=company.id,
                 old={"status": "suspended"}, new={"status": "verified"})


# ---------------------------------------------------------------- verification requests
def can_review(actor: Actor, req: VerificationRequest) -> bool:
    if req.kind == "student":
        return actor.code == "co" and actor.user.college_id == req.college_id
    return actor.code == "pa"


def request_out(db: Session, req: VerificationRequest) -> dict:
    user = db.get(User, req.user_id)
    college = db.get(College, req.college_id) if req.college_id else None
    uni = db.get(University, college.university_id) if college else None
    company = db.get(Company, req.company_id) if req.company_id else None
    domain = user.email.rsplit("@", 1)[-1].lower()
    matches = None
    if uni is not None:
        matches = any(domain == d or domain.endswith("." + d) for d in uni.email_domains) if uni.email_domains \
            else None
    docs = []
    for d in db.scalars(select(VerificationDocument).where(VerificationDocument.request_id == req.id)):
        f = db.get(StoredFile, d.file_id) if d.file_id else None
        docs.append({"kind": d.kind, "file_id": d.file_id, "original_name": f.original_name if f else None,
                     "purged": d.purged_at is not None})
    earlier = [{"id": r.id, "status": r.status, "reason": r.reason, "decided_at": r.decided_at}
               for r in db.scalars(select(VerificationRequest).where(VerificationRequest.user_id == req.user_id,
                                                                    VerificationRequest.id != req.id,
                                                                    VerificationRequest.created_at < req.created_at)
                                   .order_by(VerificationRequest.created_at.desc()))]
    no_open_cycle = False
    if req.kind == "student" and req.status == "pending":
        no_open_cycle = db.scalar(select(TrainingCycle.id).where(TrainingCycle.college_id == req.college_id,
                                                                 TrainingCycle.status == "open")) is None
    return {"id": req.id, "kind": req.kind, "status": req.status, "submitted_at": req.created_at,
            "applicant": {"id": user.id, "name_en": user.name_en, "name_ar": user.name_ar, "email": user.email,
                          "email_confirmed": user.email_confirmed_at is not None,
                          "email_matches_university_domain": matches},
            "submitted_data": req.submitted_data,
            "college": {"id": college.id, "name_en": college.name_en, "name_ar": college.name_ar,
                        "is_active": college.is_active} if college else None,
            "university_en": uni.name_en if uni else None, "university_ar": uni.name_ar if uni else None,
            "company": {"id": company.id, "name": company.name, "commercial_reg_no": company.commercial_reg_no,
                        "city": company.city, "website": company.website, "status": company.status}
            if company else None,
            "documents": docs, "earlier_decisions": earlier, "reason": req.reason, "decided_at": req.decided_at,
            "cycle_id": req.cycle_id, "no_open_cycle": no_open_cycle}


def approve(db: Session, actor: Actor, req: VerificationRequest, cycle_id: uuid.UUID | None) -> None:
    if not can_review(actor, req):
        raise forbidden()
    if req.status != "pending":
        raise conflict("INVALID_TRANSITION")
    user = db.get(User, req.user_id)
    now = clock.now()
    if req.kind == "coordinator":
        if db.scalar(select(User.id).where(User.college_id == req.college_id, User.role == "coordinator",
                                           User.verification_status == "verified", User.is_active,
                                           User.id != user.id)):
            raise conflict("COLLEGE_HAS_COORDINATOR")
    elif req.kind == "company":
        company = db.get(Company, req.company_id)
        company.status, company.verified_at = "verified", now
        user.is_company_admin = True
    else:
        cycle = db.get(TrainingCycle, cycle_id) if cycle_id else None
        if cycle is None or cycle.college_id != req.college_id or cycle.status != "open":
            raise conflict("CYCLE_NOT_OPEN")
        req.cycle_id = cycle.id
        if db.get(Enrollment, (cycle.id, user.id)) is None:
            db.add(Enrollment(cycle_id=cycle.id, student_id=user.id, verification_request_id=req.id,
                              created_by=actor.id))
    user.verification_status = "verified"
    req.status, req.reviewer_id, req.decided_at = "approved", actor.id, now
    audit.record(db, actor.user, "approve", "verification_request", req.id,
                 student_id=user.id if req.kind == "student" else None, college_id=req.college_id,
                 company_id=req.company_id, cycle_id=req.cycle_id, old={"status": "pending"},
                 new={"status": "approved"})


def reject(db: Session, actor: Actor, req: VerificationRequest, reason: str) -> None:
    if not can_review(actor, req):
        raise forbidden()
    if req.status != "pending":
        raise conflict("INVALID_TRANSITION")
    if not reason.strip():
        raise ApiError(422, "REASON_REQUIRED")
    user = db.get(User, req.user_id)
    user.verification_status = "rejected"
    if req.kind == "company":
        db.get(Company, req.company_id).status = "rejected"
    req.status, req.reviewer_id, req.decided_at, req.reason = "rejected", actor.id, clock.now(), reason.strip()
    audit.record(db, actor.user, "reject", "verification_request", req.id,
                 student_id=user.id if req.kind == "student" else None, college_id=req.college_id,
                 company_id=req.company_id, reason=req.reason, old={"status": "pending"},
                 new={"status": "rejected"})


def requests_query(actor: Actor, status: str | None, kind: str | None):
    stmt = select(VerificationRequest).order_by(VerificationRequest.created_at)
    if actor.code == "co":
        stmt = stmt.where(VerificationRequest.kind == "student",
                          VerificationRequest.college_id == actor.user.college_id)
    else:
        stmt = stmt.where(VerificationRequest.kind.in_(("coordinator", "company")))
    if status:
        stmt = stmt.where(VerificationRequest.status == status)
    if kind:
        stmt = stmt.where(VerificationRequest.kind == kind)
    return stmt


# ---------------------------------------------------------------- accounts
def user_out(u: User) -> dict:
    return {"id": u.id, "email": u.email, "role": u.role, "name_en": u.name_en, "name_ar": u.name_ar,
            "is_active": u.is_active, "verification_status": u.verification_status,
            "is_company_admin": u.is_company_admin, "email_confirmed": u.email_confirmed_at is not None,
            "invitation_pending": u.password_hash is None, "college_id": u.college_id, "company_id": u.company_id,
            "created_at": u.created_at, "last_login_at": u.last_login_at}


def users_query(actor: Actor, role: str | None, q: str | None, is_active: bool | None, verification: str | None):
    stmt = select(User).order_by(User.created_at.desc())
    if actor.code == "co":
        stmt = stmt.where(User.college_id == actor.user.college_id,
                          User.role.in_(("student", "academic_supervisor")))
    elif actor.code == "cs":
        stmt = stmt.where(User.company_id == actor.user.company_id)
    if role:
        stmt = stmt.where(User.role == role)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.name_en.ilike(like), User.name_ar.ilike(like), User.email.ilike(like)))
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    if verification:
        stmt = stmt.where(User.verification_status == verification)
    return stmt


def can_manage(actor: Actor, target: User) -> bool:
    if target.id == actor.id:
        return False
    if actor.code == "pa":
        return True
    if actor.code == "co":
        return target.college_id == actor.user.college_id and target.role in ("student", "academic_supervisor")
    if actor.is_ca:
        return target.company_id == actor.user.company_id and target.role == "company_supervisor"
    return False


def can_view_user(actor: Actor, target: User) -> bool:
    return target.id == actor.id or can_manage(actor, target) or (
        actor.code == "pa") or (actor.is_ca and target.company_id == actor.user.company_id)


def set_active(db: Session, actor: Actor, target: User, active: bool) -> None:
    if not can_manage(actor, target):
        raise forbidden()
    if target.is_active == active:
        return
    target.is_active = active
    if not active:
        revoke_sessions(db, target.id, "deactivated")
    audit.record(db, actor.user, "reactivate" if active else "deactivate", "user", target.id,
                 student_id=target.id if target.role == "student" else None, college_id=target.college_id,
                 company_id=target.company_id, old={"is_active": not active}, new={"is_active": active})


def get_user(db: Session, user_id: uuid.UUID) -> User:
    u = db.get(User, user_id)
    if u is None:
        raise not_found()
    return u
