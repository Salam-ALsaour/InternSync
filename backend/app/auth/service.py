"""Accounts: registration with verification request, email links, login, sessions, consent
(FR-AUT-02 – 04, FR-ORG-02 – 05, FR-ORG-09, NFR-SEC-02/03, NFR-PRV-01)."""
import time as _time
import uuid
from collections import defaultdict, deque
from datetime import timedelta
from decimal import Decimal, InvalidOperation

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import audit, clock, files, mail, settings
from app.core.config import get_settings
from app.core.errors import ApiError, conflict, field_error
from app.core.security import (
    create_access_token,
    hash_password,
    hash_token,
    new_link_token,
    password_is_strong,
    verify_password,
)
from app.models import (
    AccountToken,
    College,
    Company,
    Major,
    StoredFile,
    StudentProfile,
    University,
    User,
    UserSession,
    VerificationDocument,
    VerificationRequest,
)
from app.notifications import events

KIND_DOCUMENTS = {
    "student": ["course_registration"],
    "coordinator": ["appointment_letter"],
    "company": ["commercial_registration", "authorization_letter"],
}
DUMMY_HASH = hash_password("timing-equalizer-0")


# ---------------------------------------------------------------- helpers
def find_user_by_email(db: Session, email: str) -> User | None:
    return db.scalar(select(User).where(func.lower(User.email) == email.strip().lower()))


def check_password(db: Session, password: str) -> None:
    if not password_is_strong(password, settings.get(db, "auth.password_min_length")):
        raise field_error("password", "WEAK_PASSWORD")


def issue_token(db: Session, user: User, purpose: str) -> str:
    now = clock.now()
    for old in db.scalars(select(AccountToken).where(AccountToken.user_id == user.id, AccountToken.purpose == purpose,
                                                     AccountToken.used_at.is_(None),
                                                     AccountToken.revoked_at.is_(None))):
        old.revoked_at = now
    raw, hashed = new_link_token()
    if purpose == "password_reset":
        expires = now + timedelta(minutes=settings.get(db, "auth.reset_link_minutes"))
    else:
        expires = now + timedelta(hours=settings.get(db, "auth.email_link_hours"))
    db.add(AccountToken(user_id=user.id, purpose=purpose, token_hash=hashed, expires_at=expires))
    return raw


def link(path: str, raw: str) -> str:
    return f"{get_settings().frontend_base_url.rstrip('/')}/{path}/{raw}"


def check_token(db: Session, raw: str, purpose: str | None = None) -> tuple[AccountToken | None, str | None]:
    token = db.scalar(select(AccountToken).where(AccountToken.token_hash == hash_token(raw)))
    if token is None or (purpose and token.purpose != purpose):
        return None, "TOKEN_INVALID"
    if token.used_at is not None or token.revoked_at is not None:
        return token, "TOKEN_USED"
    if token.expires_at <= clock.now():
        return token, "TOKEN_EXPIRED"
    return token, None


def use_token(db: Session, raw: str, purpose: str) -> AccountToken:
    token, problem = check_token(db, raw, purpose)
    if problem == "TOKEN_INVALID":
        raise ApiError(400, problem)
    if problem:
        raise ApiError(410, problem)
    token.used_at = clock.now()
    return token


def send_confirmation(db: Session, user: User) -> str:
    return issue_token(db, user, "email_confirmation")


def mail_confirmation(user: User, raw: str, hours: int) -> None:
    mail.send("email_confirmation", user.email, user.language, name=user.name_ar if user.language == "ar"
              else user.name_en, link=link("confirm", raw), hours=hours)


# ---------------------------------------------------------------- registration rate limit (Design 7.1)
_registrations: dict[str, deque] = defaultdict(deque)


def rate_limit(db: Session, ip: str) -> None:
    limit = settings.get(db, "auth.registrations_per_ip_hour")
    window, now = 3600, _time.monotonic()
    q = _registrations[ip]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        raise ApiError(429, "RATE_LIMITED")
    q.append(now)


# ---------------------------------------------------------------- registration
def _active_college(db: Session, college_id: uuid.UUID | None) -> College:
    college = db.get(College, college_id) if college_id else None
    if college is None or not college.is_active or not db.get(University, college.university_id).is_active:
        raise field_error("college_id", "VALIDATION_ERROR")
    return college


def _gpa(db: Session, raw: str | None, college: College) -> Decimal:
    try:
        gpa = Decimal(str(raw)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError) as exc:
        raise field_error("gpa", "VALIDATION_ERROR") from exc
    if gpa < 0:
        raise field_error("gpa", "VALIDATION_ERROR")
    if gpa > db.get(University, college.university_id).gpa_scale:
        raise field_error("gpa", "GPA_ABOVE_SCALE")
    return gpa


def _student_number_taken(db: Session, number: str, college: College, exclude_user: uuid.UUID | None = None) -> bool:
    stmt = (select(StudentProfile.user_id).join(User, User.id == StudentProfile.user_id)
            .join(College, College.id == User.college_id)
            .where(College.university_id == college.university_id, StudentProfile.student_number == number))
    if exclude_user:
        stmt = stmt.where(StudentProfile.user_id != exclude_user)
    return db.scalar(stmt) is not None


def _college_has_coordinator(db: Session, college_id: uuid.UUID) -> bool:
    return db.scalar(select(User.id).where(User.college_id == college_id, User.role == "coordinator",
                                           User.verification_status == "verified", User.is_active)) is not None


def _student_data(db: Session, form: dict, college: College, exclude_user=None) -> dict:
    number = (form.get("student_number") or "").strip()
    if not 4 <= len(number) <= 20:
        raise field_error("student_number", "VALIDATION_ERROR")
    if _student_number_taken(db, number, college, exclude_user):
        raise conflict("STUDENT_NUMBER_TAKEN")
    major = db.get(Major, form.get("major_id")) if form.get("major_id") else None
    if major is None:
        raise field_error("major_id", "VALIDATION_ERROR")
    level = form.get("level")
    try:
        level = int(level) if level not in (None, "") else None
    except ValueError as exc:
        raise field_error("level", "VALIDATION_ERROR") from exc
    return {"student_number": number, "major_id": str(major.id), "major_en": major.name_en, "major_ar": major.name_ar,
            "gpa": str(_gpa(db, form.get("gpa"), college)), "level": level}


def _company_data(db: Session, form: dict, exclude_company: uuid.UUID | None = None) -> dict:
    name, reg_no, city = ((form.get(k) or "").strip() for k in ("company_name", "commercial_reg_no", "city"))
    for field, value in (("company_name", name), ("commercial_reg_no", reg_no), ("city", city)):
        if not value:
            raise field_error(field, "VALIDATION_ERROR")
    stmt = select(Company.id).where(Company.commercial_reg_no == reg_no)
    if exclude_company:
        stmt = stmt.where(Company.id != exclude_company)
    if db.scalar(stmt):
        raise conflict("DUPLICATE_COMMERCIAL_REG")
    return {"company_name": name, "commercial_reg_no": reg_no, "city": city,
            "website": (form.get("website") or "").strip() or None}


def _store_documents(db: Session, kind: str, docs: dict[str, UploadFile | None], request: VerificationRequest,
                     uploader: User) -> None:
    max_mb = settings.get(db, "files.cv_max_mb")
    for doc_kind in KIND_DOCUMENTS[kind]:
        upload = docs.get(doc_kind)
        if upload is None or not upload.filename:
            raise field_error(doc_kind, "DOCUMENT_REQUIRED")
        data = files.read_upload(upload, max_mb)
        stored = files.store(db, data, upload.filename, "verification_document", files.VERIFICATION_TYPES, uploader)
        db.add(VerificationDocument(request_id=request.id, kind=doc_kind, file_id=stored.id))


def register(db: Session, form: dict, docs: dict[str, UploadFile | None], lang: str) -> tuple[User, VerificationRequest,
                                                                                               str]:
    kind = form["kind"]
    email = form["email"].strip()
    if find_user_by_email(db, email):
        raise conflict("EMAIL_TAKEN")
    check_password(db, form["password"])
    name_en, name_ar = form["name_en"].strip(), form["name_ar"].strip()
    if not name_en or not name_ar:
        raise field_error("name_en" if not name_en else "name_ar", "VALIDATION_ERROR")

    user = User(email=email, password_hash=hash_password(form["password"]), name_en=name_en, name_ar=name_ar,
                language=lang, verification_status="pending")
    request = VerificationRequest(kind=kind, submitted_data={})
    if kind == "student":
        college = _active_college(db, form.get("college_id"))
        data = _student_data(db, form, college)
        user.role, user.college_id = "student", college.id
        request.college_id, request.submitted_data = college.id, data
    elif kind == "coordinator":
        college = _active_college(db, form.get("college_id"))
        if _college_has_coordinator(db, college.id):
            raise conflict("COLLEGE_HAS_COORDINATOR")
        user.role, user.college_id = "coordinator", college.id
        request.college_id, request.submitted_data = college.id, {}
    else:
        data = _company_data(db, form)
        company = Company(name=data["company_name"], commercial_reg_no=data["commercial_reg_no"], city=data["city"],
                          website=data["website"])
        db.add(company)
        db.flush()
        user.role, user.company_id = "company_supervisor", company.id
        request.company_id, request.submitted_data = company.id, data

    db.add(user)
    db.flush()
    if kind == "student":
        d = request.submitted_data
        db.add(StudentProfile(user_id=user.id, student_number=d["student_number"], major_id=uuid.UUID(d["major_id"]),
                              gpa=Decimal(d["gpa"]), level=d["level"]))
    request.user_id = user.id
    db.add(request)
    db.flush()
    _store_documents(db, kind, docs, request, user)
    raw = send_confirmation(db, user)
    audit.record(db, user, "register", "user", user.id, student_id=user.id if kind == "student" else None,
                 college_id=user.college_id, company_id=user.company_id, new={"kind": kind})  # no contact details
    audit.record(db, user, "submit", "verification_request", request.id, student_id=user.id if kind == "student"
                 else None, college_id=request.college_id, company_id=request.company_id)
    events.verification_submitted(db, user, request)
    return user, request, raw


def resubmit(db: Session, user: User, form: dict, docs: dict[str, UploadFile | None]) -> VerificationRequest:
    """FR-ORG-09: a new request after a rejection, with corrected data and new documents."""
    requests = db.scalars(select(VerificationRequest).where(VerificationRequest.user_id == user.id)
                          .order_by(VerificationRequest.created_at.desc())).all()
    if not requests or requests[0].status != "rejected" or user.verification_status != "rejected":
        raise conflict("INVALID_TRANSITION")
    kind = requests[0].kind
    request = VerificationRequest(user_id=user.id, kind=kind, submitted_data={})
    if kind == "student":
        college = db.get(College, user.college_id)
        data = _student_data(db, {**requests[0].submitted_data, **{k: v for k, v in form.items() if v}}, college,
                             exclude_user=user.id)
        profile = db.get(StudentProfile, user.id)
        profile.student_number, profile.major_id = data["student_number"], uuid.UUID(data["major_id"])
        profile.gpa, profile.level = Decimal(data["gpa"]), data["level"]
        request.college_id, request.submitted_data = college.id, data
    elif kind == "coordinator":
        college = _active_college(db, form.get("college_id") or user.college_id)
        if _college_has_coordinator(db, college.id):
            raise conflict("COLLEGE_HAS_COORDINATOR")
        user.college_id = college.id
        request.college_id = college.id
    else:
        company = db.get(Company, user.company_id)
        data = _company_data(db, {"company_name": company.name, "commercial_reg_no": company.commercial_reg_no,
                                  "city": company.city, "website": company.website,
                                  **{k: v for k, v in form.items() if v}}, exclude_company=company.id)
        company.name, company.commercial_reg_no, company.city = (data["company_name"], data["commercial_reg_no"],
                                                                 data["city"])
        company.website, company.status = data["website"], "pending"
        request.company_id, request.submitted_data = company.id, data
    user.verification_status = "pending"
    db.add(request)
    db.flush()
    _store_documents(db, kind, docs, request, user)
    audit.record(db, user, "resubmit", "verification_request", request.id,
                 student_id=user.id if kind == "student" else None, college_id=request.college_id,
                 company_id=request.company_id)
    events.verification_submitted(db, user, request)
    return request


# ---------------------------------------------------------------- login and sessions
def login(db: Session, email: str, password: str, user_agent: str | None) -> tuple[User, UserSession, str]:
    now = clock.now()
    user = find_user_by_email(db, email)
    if user is None:
        verify_password(DUMMY_HASH, password)
        raise ApiError(401, "INVALID_CREDENTIALS")
    if user.locked_until and user.locked_until > now:
        raise ApiError(423, "ACCOUNT_LOCKED", locked_until=user.locked_until.isoformat())
    if not verify_password(user.password_hash, password):
        user.failed_logins += 1
        if user.failed_logins >= settings.get(db, "auth.lockout_attempts"):
            user.locked_until = now + timedelta(minutes=settings.get(db, "auth.lockout_minutes"))
            user.failed_logins = 0
            audit.record(db, None, "lock", "user", user.id, college_id=user.college_id, company_id=user.company_id)
        db.commit()
        raise ApiError(401, "INVALID_CREDENTIALS")
    if not user.is_active:
        raise ApiError(403, "ACCOUNT_INACTIVE")
    if user.email_confirmed_at is None:
        raise ApiError(403, "EMAIL_NOT_CONFIRMED")
    user.failed_logins, user.locked_until, user.last_login_at = 0, None, now
    session = UserSession(user_id=user.id, last_seen_at=now,
                          expires_at=now + timedelta(hours=settings.get(db, "auth.session_max_hours")),
                          user_agent=(user_agent or "")[:300] or None)
    db.add(session)
    db.flush()
    token = create_access_token(user.id, user.role, session.id, now, session.expires_at)
    audit.record(db, user, "login", "user", user.id, college_id=user.college_id, company_id=user.company_id)
    return user, session, token


def revoke_sessions(db: Session, user_id: uuid.UUID, reason: str) -> None:
    now = clock.now()
    for s in db.scalars(select(UserSession).where(UserSession.user_id == user_id, UserSession.revoked_at.is_(None))):
        s.revoked_at, s.revoke_reason = now, reason


def organization(db: Session, user: User) -> dict:
    out: dict = {}
    if user.college_id:
        college = db.get(College, user.college_id)
        uni = db.get(University, college.university_id)
        out.update(college_id=college.id, college_en=college.name_en, college_ar=college.name_ar,
                   university_id=uni.id, university_en=uni.name_en, university_ar=uni.name_ar)
    if user.company_id:
        company = db.get(Company, user.company_id)
        out.update(company_id=company.id, company=company.name, company_status=company.status)
    return out


def me(db: Session, user: User) -> dict:
    return {"id": user.id, "email": user.email, "role": user.role, "name_en": user.name_en, "name_ar": user.name_ar,
            "language": user.language, "consent_required": user.consent_at is None,
            "verification_status": user.verification_status, "is_company_admin": user.is_company_admin,
            "organization": organization(db, user),
            # the app applies the same idle limit while offline (Increment 4, RQ-2)
            "idle_timeout_minutes": settings.get(db, "auth.idle_timeout_minutes")}


def my_requests(db: Session, user: User) -> list[dict]:
    out = []
    for r in db.scalars(select(VerificationRequest).where(VerificationRequest.user_id == user.id)
                        .order_by(VerificationRequest.created_at.desc())):
        docs = []
        for d in db.scalars(select(VerificationDocument).where(VerificationDocument.request_id == r.id)):
            f = db.get(StoredFile, d.file_id) if d.file_id else None
            docs.append({"kind": d.kind, "file_id": d.file_id, "original_name": f.original_name if f else None,
                         "purged": d.purged_at is not None})
        out.append({"id": r.id, "kind": r.kind, "status": r.status, "submitted_at": r.created_at,
                    "submitted_data": r.submitted_data, "reason": r.reason, "decided_at": r.decided_at,
                    "documents": docs})
    return out
