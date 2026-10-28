import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class OrganizationOut(BaseModel):
    university_id: uuid.UUID | None = None
    university_en: str | None = None
    university_ar: str | None = None
    college_id: uuid.UUID | None = None
    college_en: str | None = None
    college_ar: str | None = None
    company_id: uuid.UUID | None = None
    company: str | None = None
    company_status: str | None = None


class MeOut(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    name_en: str
    name_ar: str
    language: str
    consent_required: bool
    verification_status: str
    is_company_admin: bool
    idle_timeout_minutes: int = 30
    organization: OrganizationOut


class LoginIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=200)


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: datetime
    idle_timeout_minutes: int
    user: MeOut


class TokenIn(BaseModel):
    token: str = Field(min_length=10, max_length=200)


class TokenPasswordIn(TokenIn):
    password: str = Field(min_length=1, max_length=200)


class EmailIn(BaseModel):
    email: EmailStr


class TokenCheckOut(BaseModel):
    purpose: str | None
    valid: bool
    reason: str | None = None
    email: str | None = None
    name_en: str | None = None
    name_ar: str | None = None


class MePatch(BaseModel):
    language: str = Field(pattern="^(ar|en)$")


class RegistrationVerification(BaseModel):
    request_id: uuid.UUID
    status: str
    reviewer: str


class RegisterOut(BaseModel):
    user_id: uuid.UUID
    kind: str
    email_confirmation_sent: bool
    verification: RegistrationVerification


class DocumentOut(BaseModel):
    kind: str
    file_id: uuid.UUID | None
    original_name: str | None
    purged: bool


class MyRequestOut(BaseModel):
    id: uuid.UUID
    kind: str
    status: str
    submitted_at: datetime
    submitted_data: dict
    reason: str | None
    decided_at: datetime | None
    documents: list[DocumentOut]
