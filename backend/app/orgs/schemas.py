import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class CollegeOut(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str
    is_active: bool


class UniversityOut(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str
    email_domains: list[str]
    gpa_scale: Decimal
    is_active: bool
    colleges: list[CollegeOut]


class UniversityIn(BaseModel):
    name_en: str = Field(min_length=2, max_length=200)
    name_ar: str = Field(min_length=2, max_length=200)
    email_domains: list[str] = []
    gpa_scale: Decimal = Decimal("5.00")


class UniversityPatch(BaseModel):
    name_en: str | None = Field(None, min_length=2, max_length=200)
    name_ar: str | None = Field(None, min_length=2, max_length=200)
    email_domains: list[str] | None = None
    gpa_scale: Decimal | None = None
    is_active: bool | None = None


class CollegeIn(BaseModel):
    name_en: str = Field(min_length=2, max_length=200)
    name_ar: str = Field(min_length=2, max_length=200)


class CollegePatch(BaseModel):
    name_en: str | None = Field(None, min_length=2, max_length=200)
    name_ar: str | None = Field(None, min_length=2, max_length=200)
    is_active: bool | None = None


class PersonOut(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str
    email: str


class CollegeDetail(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str
    is_active: bool
    university_id: uuid.UUID
    university_en: str
    university_ar: str
    coordinator: PersonOut | None
    verified_students: int
    academic_supervisors: int


class MemberOut(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str
    email: str
    is_active: bool
    is_company_admin: bool = False
    invitation_pending: bool
    active_students: int


class InviteIn(BaseModel):
    email: EmailStr
    name_en: str = Field(min_length=2, max_length=120)
    name_ar: str = Field(min_length=2, max_length=120)


class CompanyOut(BaseModel):
    id: uuid.UUID
    name: str
    commercial_reg_no: str
    city: str
    website: str | None
    status: str
    verified_at: datetime | None
    admin: PersonOut | None
    supervisors: int


class CompanyPatch(BaseModel):
    city: str | None = Field(None, min_length=2, max_length=100)
    website: str | None = Field(None, max_length=200)


class ReasonIn(BaseModel):
    reason: str = Field("", max_length=1000)


class TransferIn(BaseModel):
    user_id: uuid.UUID
    reason: str = Field("", max_length=1000)


class ApproveIn(BaseModel):
    cycle_id: uuid.UUID | None = None


class ApplicantOut(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str
    email: str
    email_confirmed: bool
    email_matches_university_domain: bool | None


class RequestDocOut(BaseModel):
    kind: str
    file_id: uuid.UUID | None
    original_name: str | None
    purged: bool


class EarlierDecision(BaseModel):
    id: uuid.UUID
    status: str
    reason: str | None
    decided_at: datetime | None


class VerificationRequestOut(BaseModel):
    id: uuid.UUID
    kind: str
    status: str
    submitted_at: datetime
    applicant: ApplicantOut
    submitted_data: dict
    college: CollegeOut | None
    university_en: str | None
    university_ar: str | None
    company: dict | None
    documents: list[RequestDocOut]
    earlier_decisions: list[EarlierDecision]
    reason: str | None
    decided_at: datetime | None
    cycle_id: uuid.UUID | None
    no_open_cycle: bool = False


class UserOut(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    name_en: str
    name_ar: str
    is_active: bool
    verification_status: str
    is_company_admin: bool
    email_confirmed: bool
    invitation_pending: bool
    college_id: uuid.UUID | None
    company_id: uuid.UUID | None
    created_at: datetime
    last_login_at: datetime | None
