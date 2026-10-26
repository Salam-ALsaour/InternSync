"""API 3.1 – Authentication and session."""
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, Request, Response, UploadFile
from pydantic import EmailStr, TypeAdapter
from sqlalchemy.orm import Session

from app.auth import schemas as s
from app.auth import service
from app.core import audit, clock, mail, settings
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import field_error
from app.core.i18n import get_language
from app.core.security import hash_password
from app.models import User

router = APIRouter(tags=["auth"])


@router.post("/auth/register", status_code=201, response_model=s.RegisterOut)
def register(request: Request, db: Session = Depends(get_db),
             kind: Literal["student", "coordinator", "company"] = Form(...),
             email: str = Form(..., max_length=200), password: str = Form(..., max_length=200),
             name_en: str = Form(..., max_length=120), name_ar: str = Form(..., max_length=120),
             college_id: uuid.UUID | None = Form(None), student_number: str | None = Form(None),
             major_id: uuid.UUID | None = Form(None), gpa: str | None = Form(None), level: str | None = Form(None),
             company_name: str | None = Form(None), commercial_reg_no: str | None = Form(None),
             city: str | None = Form(None), website: str | None = Form(None),
             course_registration: UploadFile | None = File(None), appointment_letter: UploadFile | None = File(None),
             commercial_registration: UploadFile | None = File(None),
             authorization_letter: UploadFile | None = File(None)):
    try:
        TypeAdapter(EmailStr).validate_python(email)
    except ValueError as exc:
        raise field_error("email", "VALIDATION_ERROR") from exc
    service.rate_limit(db, request.client.host if request.client else "unknown")
    form = dict(kind=kind, email=email, password=password, name_en=name_en, name_ar=name_ar, college_id=college_id,
                student_number=student_number, major_id=major_id, gpa=gpa, level=level, company_name=company_name,
                commercial_reg_no=commercial_reg_no, city=city, website=website)
    docs = dict(course_registration=course_registration, appointment_letter=appointment_letter,
                commercial_registration=commercial_registration, authorization_letter=authorization_letter)
    user, req, raw = service.register(db, form, docs, get_language())
    db.commit()
    service.mail_confirmation(user, raw, settings.get(db, "auth.email_link_hours"))
    return {"user_id": user.id, "kind": kind, "email_confirmation_sent": True,
            "verification": {"request_id": req.id, "status": req.status,
                             "reviewer": "coordinator" if kind == "student" else "platform_admin"}}


@router.post("/auth/email/confirm")
def confirm_email(body: s.TokenIn, db: Session = Depends(get_db)) -> dict:
    token = service.use_token(db, body.token, "email_confirmation")
    user = db.get(User, token.user_id)
    user.email_confirmed_at = user.email_confirmed_at or clock.now()
    audit.record(db, user, "confirm_email", "user", user.id, college_id=user.college_id, company_id=user.company_id)
    db.commit()
    return {"confirmed": True}


@router.post("/auth/email/resend", status_code=202)
def resend_confirmation(body: s.EmailIn, db: Session = Depends(get_db)) -> dict:
    user = service.find_user_by_email(db, body.email)
    if user and user.email_confirmed_at is None and user.password_hash and user.is_active:
        raw = service.send_confirmation(db, user)
        db.commit()
        service.mail_confirmation(user, raw, settings.get(db, "auth.email_link_hours"))
    return {"accepted": True}


@router.post("/auth/login", response_model=s.LoginOut)
def login(body: s.LoginIn, request: Request, db: Session = Depends(get_db)):
    user, session, token = service.login(db, body.email, body.password, request.headers.get("user-agent"))
    db.commit()
    return {"access_token": token, "expires_at": session.expires_at,
            "idle_timeout_minutes": settings.get(db, "auth.idle_timeout_minutes"), "user": service.me(db, user)}


@router.post("/auth/logout", status_code=204)
def logout(actor: Actor = Depends(auth(unverified=True, consent=False)), db: Session = Depends(get_db)):
    session = db.merge(actor.session)
    session.revoked_at, session.revoke_reason = clock.now(), "logout"
    db.commit()
    return Response(status_code=204)


@router.get("/auth/tokens/{token}", response_model=s.TokenCheckOut)
def check_link(token: str, db: Session = Depends(get_db)):
    row, problem = service.check_token(db, token)
    if row is None:
        return {"purpose": None, "valid": False, "reason": "invalid"}
    user = db.get(User, row.user_id)
    reason = {"TOKEN_USED": "used", "TOKEN_EXPIRED": "expired"}.get(problem or "")
    out = {"purpose": row.purpose, "valid": problem is None, "reason": reason}
    if row.purpose == "invitation":
        out.update(email=user.email, name_en=user.name_en, name_ar=user.name_ar)
    return out


@router.post("/auth/invitations/accept")
def accept_invitation(body: s.TokenPasswordIn, db: Session = Depends(get_db)) -> dict:
    token = service.use_token(db, body.token, "invitation")
    user = db.get(User, token.user_id)
    service.check_password(db, body.password)
    user.password_hash = hash_password(body.password)
    user.email_confirmed_at = user.email_confirmed_at or clock.now()
    audit.record(db, user, "accept_invitation", "user", user.id, college_id=user.college_id,
                 company_id=user.company_id)
    db.commit()
    return {"accepted": True}


@router.post("/auth/password/forgot", status_code=202)
def forgot_password(body: s.EmailIn, db: Session = Depends(get_db)) -> dict:
    user = service.find_user_by_email(db, body.email)
    if user and user.is_active and user.password_hash:
        raw = service.issue_token(db, user, "password_reset")
        db.commit()
        mail.send("password_reset", user.email, user.language,
                  name=user.name_ar if user.language == "ar" else user.name_en,
                  link=service.link("reset", raw), minutes=settings.get(db, "auth.reset_link_minutes"))
    return {"accepted": True}


@router.post("/auth/password/reset")
def reset_password(body: s.TokenPasswordIn, db: Session = Depends(get_db)) -> dict:
    token = service.use_token(db, body.token, "password_reset")
    user = db.get(User, token.user_id)
    service.check_password(db, body.password)
    user.password_hash = hash_password(body.password)
    user.failed_logins, user.locked_until = 0, None
    service.revoke_sessions(db, user.id, "password_reset")
    audit.record(db, user, "reset_password", "user", user.id, college_id=user.college_id,
                 company_id=user.company_id)
    db.commit()
    return {"reset": True}


@router.get("/me", response_model=s.MeOut)
def get_me(actor: Actor = Depends(auth(unverified=True, consent=False)), db: Session = Depends(get_db)):
    return service.me(db, actor.user)


@router.patch("/me", response_model=s.MeOut)
def patch_me(body: s.MePatch, actor: Actor = Depends(auth(unverified=True, consent=False)),
             db: Session = Depends(get_db)):
    user = db.merge(actor.user)
    user.language = body.language
    db.commit()
    return service.me(db, user)


@router.post("/me/consent", response_model=s.MeOut)
def give_consent(actor: Actor = Depends(auth(unverified=True, consent=False)), db: Session = Depends(get_db)):
    user = db.merge(actor.user)
    if user.consent_at is None:
        user.consent_at = clock.now()
        audit.record(db, user, "consent", "user", user.id, college_id=user.college_id, company_id=user.company_id)
        db.commit()
    return service.me(db, user)


@router.get("/me/verification", response_model=list[s.MyRequestOut])
def my_verification(actor: Actor = Depends(auth(unverified=True)), db: Session = Depends(get_db)):
    return service.my_requests(db, actor.user)


@router.post("/me/verification", status_code=201, response_model=list[s.MyRequestOut])
def resubmit_verification(actor: Actor = Depends(auth("st", "co", "cs", unverified=True)),
                          db: Session = Depends(get_db), college_id: uuid.UUID | None = Form(None),
                          student_number: str | None = Form(None), major_id: uuid.UUID | None = Form(None),
                          gpa: str | None = Form(None), level: str | None = Form(None),
                          company_name: str | None = Form(None), commercial_reg_no: str | None = Form(None),
                          city: str | None = Form(None), website: str | None = Form(None),
                          course_registration: UploadFile | None = File(None),
                          appointment_letter: UploadFile | None = File(None),
                          commercial_registration: UploadFile | None = File(None),
                          authorization_letter: UploadFile | None = File(None)):
    user = db.merge(actor.user)
    form = dict(college_id=college_id, student_number=student_number, major_id=major_id, gpa=gpa, level=level,
                company_name=company_name, commercial_reg_no=commercial_reg_no, city=city, website=website)
    docs = dict(course_registration=course_registration, appointment_letter=appointment_letter,
                commercial_registration=commercial_registration, authorization_letter=authorization_letter)
    service.resubmit(db, user, form, docs)
    db.commit()
    return service.my_requests(db, user)
