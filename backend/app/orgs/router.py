"""API 3.2 – Organizations, verification, and accounts (FR-ORG-07 transfers are in Increment 3)."""
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.service import issue_token
from app.core import audit
from app.core.common import Page, PageParams, get_or_404, paginate
from app.core.db import get_db
from app.core.deps import Actor, auth
from app.core.errors import conflict, forbidden
from app.models import College, Company, University, VerificationRequest
from app.orgs import schemas as s
from app.orgs import service

router = APIRouter(tags=["organizations"])


# ---------------------------------------------------------------- universities and colleges
@router.get("/universities", response_model=list[s.UniversityOut])
def list_universities(db: Session = Depends(get_db)):
    """Public: active universities with their active colleges (registration form)."""
    unis = db.scalars(select(University).where(University.is_active).order_by(University.name_en))
    return [service.university_out(db, u, active_colleges_only=True) for u in unis]


@router.get("/admin/universities", response_model=list[s.UniversityOut])
def list_all_universities(actor: Actor = Depends(auth("pa")), db: Session = Depends(get_db)):
    """Platform Admin: every university with every college, active or not."""
    return [service.university_out(db, u, active_colleges_only=False)
            for u in db.scalars(select(University).order_by(University.name_en))]


@router.post("/universities", status_code=201, response_model=s.UniversityOut)
def create_university(body: s.UniversityIn, actor: Actor = Depends(auth("pa")), db: Session = Depends(get_db)):
    uni = service.create_university(db, actor, body.model_dump())
    db.commit()
    return service.university_out(db, uni, active_colleges_only=False)


@router.patch("/universities/{university_id}", response_model=s.UniversityOut)
def patch_university(university_id: uuid.UUID, body: s.UniversityPatch, actor: Actor = Depends(auth("pa")),
                     db: Session = Depends(get_db)):
    uni = get_or_404(db, University, university_id)
    service.patch_university(db, actor, uni, body.model_dump(exclude_unset=True))
    db.commit()
    return service.university_out(db, uni, active_colleges_only=False)


@router.post("/universities/{university_id}/colleges", status_code=201, response_model=s.CollegeOut)
def create_college(university_id: uuid.UUID, body: s.CollegeIn, actor: Actor = Depends(auth("pa")),
                   db: Session = Depends(get_db)):
    uni = get_or_404(db, University, university_id)
    college = service.create_college(db, actor, uni, body.model_dump())
    db.commit()
    return {"id": college.id, "name_en": college.name_en, "name_ar": college.name_ar, "is_active": college.is_active}


@router.get("/colleges/{college_id}", response_model=s.CollegeDetail)
def get_college(college_id: uuid.UUID, actor: Actor = Depends(auth("pa", "co")), db: Session = Depends(get_db)):
    service.ensure_college_access(actor, college_id)
    return service.college_detail(db, get_or_404(db, College, college_id))


@router.patch("/colleges/{college_id}", response_model=s.CollegeDetail)
def patch_college(college_id: uuid.UUID, body: s.CollegePatch, actor: Actor = Depends(auth("pa")),
                  db: Session = Depends(get_db)):
    college = get_or_404(db, College, college_id)
    service.patch_college(db, actor, college, body.model_dump(exclude_unset=True))
    db.commit()
    return service.college_detail(db, college)


@router.get("/colleges/{college_id}/academic-supervisors", response_model=list[s.MemberOut])
def college_supervisors(college_id: uuid.UUID, actor: Actor = Depends(auth("co", "pa")),
                        db: Session = Depends(get_db)):
    service.ensure_college_access(actor, college_id)
    get_or_404(db, College, college_id)
    return service.members(db, "academic_supervisor", college_id=college_id)


@router.post("/colleges/{college_id}/invitations", status_code=201, response_model=s.MemberOut)
def invite_academic_supervisor(college_id: uuid.UUID, body: s.InviteIn, actor: Actor = Depends(auth("co")),
                               db: Session = Depends(get_db)):
    service.ensure_college_access(actor, college_id)
    college = get_or_404(db, College, college_id)
    user, raw = service.invite(db, actor, "academic_supervisor", body.model_dump(), college=college)
    db.commit()
    service.mail_invitation(db, actor, user, raw)
    return service.member_out(db, user)


# ---------------------------------------------------------------- companies
@router.get("/companies", response_model=Page[s.CompanyOut])
def list_companies(status: str | None = None, q: str | None = None, params: PageParams = Depends(),
                   actor: Actor = Depends(auth("pa", "cs")), db: Session = Depends(get_db)):
    stmt = select(Company).order_by(Company.name)
    if actor.code == "cs":
        stmt = stmt.where(Company.id == actor.user.company_id)
    if status:
        stmt = stmt.where(Company.status == status)
    if q:
        stmt = stmt.where(Company.name.ilike(f"%{q.strip()}%") | Company.commercial_reg_no.ilike(f"%{q.strip()}%"))
    return paginate(db, stmt, params, lambda c: service.company_out(db, c))


@router.get("/companies/{company_id}", response_model=s.CompanyOut)
def get_company(company_id: uuid.UUID, actor: Actor = Depends(auth("pa", "cs")), db: Session = Depends(get_db)):
    service.ensure_company_access(actor, company_id)
    return service.company_out(db, get_or_404(db, Company, company_id))


@router.patch("/companies/{company_id}", response_model=s.CompanyOut)
def patch_company(company_id: uuid.UUID, body: s.CompanyPatch, actor: Actor = Depends(auth("ca")),
                  db: Session = Depends(get_db)):
    service.ensure_company_access(actor, company_id)
    company = get_or_404(db, Company, company_id)
    old, new = audit.changes(company, body.model_dump(exclude_unset=True))
    if new:
        audit.record(db, actor.user, "update", "company", company.id, company_id=company.id, old=old, new=new)
    db.commit()
    return service.company_out(db, company)


@router.post("/companies/{company_id}/suspend", response_model=s.CompanyOut)
def suspend_company(company_id: uuid.UUID, body: s.ReasonIn, actor: Actor = Depends(auth("pa")),
                    db: Session = Depends(get_db)):
    company = get_or_404(db, Company, company_id)
    service.suspend_company(db, actor, company, body.reason)
    db.commit()
    return service.company_out(db, company)


@router.post("/companies/{company_id}/reactivate", response_model=s.CompanyOut)
def reactivate_company(company_id: uuid.UUID, actor: Actor = Depends(auth("pa")), db: Session = Depends(get_db)):
    company = get_or_404(db, Company, company_id)
    service.reactivate_company(db, actor, company)
    db.commit()
    return service.company_out(db, company)


@router.get("/companies/{company_id}/supervisors", response_model=list[s.MemberOut])
def company_supervisors(company_id: uuid.UUID, actor: Actor = Depends(auth("ca", "pa")),
                        db: Session = Depends(get_db)):
    service.ensure_company_access(actor, company_id)
    get_or_404(db, Company, company_id)
    return service.members(db, "company_supervisor", company_id=company_id)


@router.post("/companies/{company_id}/invitations", status_code=201, response_model=s.MemberOut)
def invite_company_supervisor(company_id: uuid.UUID, body: s.InviteIn, actor: Actor = Depends(auth("ca")),
                              db: Session = Depends(get_db)):
    service.ensure_company_access(actor, company_id)
    company = get_or_404(db, Company, company_id)
    if company.status != "verified":
        raise conflict("COMPANY_NOT_VERIFIED")
    user, raw = service.invite(db, actor, "company_supervisor", body.model_dump(), company=company)
    db.commit()
    service.mail_invitation(db, actor, user, raw)
    return service.member_out(db, user)


# ---------------------------------------------------------------- verification requests
@router.get("/verification-requests", response_model=Page[s.VerificationRequestOut])
def list_requests(status: str | None = Query(None, pattern="^(pending|approved|rejected)$"),
                  kind: str | None = Query(None, pattern="^(student|coordinator|company)$"),
                  params: PageParams = Depends(), actor: Actor = Depends(auth("pa", "co")),
                  db: Session = Depends(get_db)):
    return paginate(db, service.requests_query(actor, status, kind), params, lambda r: service.request_out(db, r))


@router.get("/verification-requests/{request_id}", response_model=s.VerificationRequestOut)
def get_request(request_id: uuid.UUID, actor: Actor = Depends(auth(unverified=True)),
                db: Session = Depends(get_db)):
    req = get_or_404(db, VerificationRequest, request_id)
    if req.user_id != actor.id and not service.can_review(actor, req):
        raise forbidden()
    return service.request_out(db, req)


@router.post("/verification-requests/{request_id}/approve", response_model=s.VerificationRequestOut)
def approve_request(request_id: uuid.UUID, body: s.ApproveIn, actor: Actor = Depends(auth("pa", "co")),
                    db: Session = Depends(get_db)):
    req = get_or_404(db, VerificationRequest, request_id)
    service.approve(db, actor, req, body.cycle_id)
    db.commit()
    return service.request_out(db, req)


@router.post("/verification-requests/{request_id}/reject", response_model=s.VerificationRequestOut)
def reject_request(request_id: uuid.UUID, body: s.ReasonIn, actor: Actor = Depends(auth("pa", "co")),
                   db: Session = Depends(get_db)):
    req = get_or_404(db, VerificationRequest, request_id)
    service.reject(db, actor, req, body.reason)
    db.commit()
    return service.request_out(db, req)


# ---------------------------------------------------------------- accounts
@router.get("/users", response_model=Page[s.UserOut])
def list_users(role: str | None = None, q: str | None = None, is_active: bool | None = None,
               verification_status: str | None = None, params: PageParams = Depends(),
               actor: Actor = Depends(auth("pa", "co", "ca")), db: Session = Depends(get_db)):
    return paginate(db, service.users_query(actor, role, q, is_active, verification_status), params,
                    service.user_out)


@router.get("/users/{user_id}", response_model=s.UserOut)
def get_user(user_id: uuid.UUID, actor: Actor = Depends(auth("pa", "co", "ca")), db: Session = Depends(get_db)):
    target = service.get_user(db, user_id)
    if not service.can_view_user(actor, target):
        raise forbidden()
    return service.user_out(target)


@router.post("/users/{user_id}/deactivate", response_model=s.UserOut)
def deactivate_user(user_id: uuid.UUID, actor: Actor = Depends(auth("pa", "co", "ca")),
                    db: Session = Depends(get_db)):
    target = service.get_user(db, user_id)
    service.set_active(db, actor, target, False)
    db.commit()
    return service.user_out(target)


@router.post("/users/{user_id}/reactivate", response_model=s.UserOut)
def reactivate_user(user_id: uuid.UUID, actor: Actor = Depends(auth("pa", "co", "ca")),
                    db: Session = Depends(get_db)):
    target = service.get_user(db, user_id)
    service.set_active(db, actor, target, True)
    db.commit()
    return service.user_out(target)


@router.post("/users/{user_id}/invitation/resend", response_model=s.UserOut)
def resend_invitation(user_id: uuid.UUID, actor: Actor = Depends(auth("co", "ca")), db: Session = Depends(get_db)):
    target = service.get_user(db, user_id)
    allowed = (actor.code == "co" and target.role == "academic_supervisor"
               and target.college_id == actor.user.college_id) or \
              (actor.is_ca and target.role == "company_supervisor" and target.company_id == actor.user.company_id)
    if not allowed:
        raise forbidden()
    if target.password_hash is not None:
        raise conflict("INVALID_TRANSITION")
    raw = issue_token(db, target, "invitation")
    db.commit()
    service.mail_invitation(db, actor, target, raw)
    return service.user_out(target)

