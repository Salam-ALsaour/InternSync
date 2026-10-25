import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class Ref(BaseModel):
    id: uuid.UUID
    name_en: str
    name_ar: str


class VacancyIn(BaseModel):
    title: str = Field(min_length=3, max_length=150)
    city: str = Field(min_length=2, max_length=80)
    description: str = Field(min_length=10, max_length=5000)
    training_type: Literal["coop", "summer"]
    training_start: date
    training_end: date
    min_gpa: Decimal | None = Field(None, ge=0, le=5)
    seats: int = Field(ge=1, le=100)
    application_deadline: datetime
    required_skill_ids: list[uuid.UUID] = Field(default_factory=list, max_length=30)
    preferred_skill_ids: list[uuid.UUID] = Field(default_factory=list, max_length=30)
    major_ids: list[uuid.UUID] = Field(min_length=1, max_length=30)
    target_university_ids: list[uuid.UUID] = Field(default_factory=list, max_length=30)
    publish: bool = False


class VacancyPatch(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=150)
    city: str | None = Field(None, min_length=2, max_length=80)
    description: str | None = Field(None, min_length=10, max_length=5000)
    training_type: Literal["coop", "summer"] | None = None
    training_start: date | None = None
    training_end: date | None = None
    min_gpa: Decimal | None = Field(None, ge=0, le=5)
    seats: int | None = Field(None, ge=1, le=100)
    application_deadline: datetime | None = None
    required_skill_ids: list[uuid.UUID] | None = Field(None, max_length=30)
    preferred_skill_ids: list[uuid.UUID] | None = Field(None, max_length=30)
    major_ids: list[uuid.UUID] | None = Field(None, min_length=1, max_length=30)
    target_university_ids: list[uuid.UUID] | None = Field(None, max_length=30)
    company_supervisor_id: uuid.UUID | None = None


class VacancyOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    company_supervisor: Ref
    title: str
    city: str
    description: str
    training_type: str
    training_start: date
    training_end: date
    min_gpa: Decimal | None
    seats: int
    seats_taken: int
    application_deadline: datetime
    status: str
    published_at: datetime | None
    closed_at: datetime | None
    required_skills: list[Ref]
    preferred_skills: list[Ref]
    majors: list[Ref]
    target_universities: list[Ref]
    applicants: int | None = None
    eligible: bool | None = None
    ineligible_reason: str | None = None
    already_applied: bool | None = None


class ApplicationOut(BaseModel):
    id: uuid.UUID
    status: str
    withdraw_reason: str | None
    created_at: datetime
    decided_at: datetime | None
    vacancy_id: uuid.UUID
    vacancy_title: str
    company_name: str
    student_id: uuid.UUID
    student_name_en: str
    student_name_ar: str
    placement_id: uuid.UUID | None = None


class ApplicantOut(ApplicationOut):
    university_en: str
    university_ar: str
    college_en: str
    college_ar: str
    major_en: str
    major_ar: str
    gpa: Decimal
    skills: list[Ref]
    cv_file_id: uuid.UUID | None
    fit_score: Decimal | None = None
    match_mode: str | None = None


class PlacementIn(BaseModel):
    application_id: uuid.UUID
    academic_supervisor_id: uuid.UUID
    company_supervisor_id: uuid.UUID | None = None


class SupervisorChange(BaseModel):
    academic_supervisor_id: uuid.UUID
    reason: str = Field("", max_length=1000)


class ReasonIn(BaseModel):
    reason: str = Field("", max_length=1000)


class SlotSummary(BaseModel):
    total: int
    submitted: int
    accepted: int
    revision_requested: int
    late: int
    missing: int


class PlacementOut(BaseModel):
    id: uuid.UUID
    status: str
    cycle_id: uuid.UUID
    cycle_name: str
    student: Ref
    student_email: str
    vacancy_id: uuid.UUID
    vacancy_title: str
    company_name: str
    company_supervisor: Ref
    academic_supervisor: Ref
    confirmed_at: datetime
    cancel_reason: str | None
    reports: SlotSummary
    attendance_percent: float | None = None
    grade_status: str | None = None


class AcceptedApplicant(BaseModel):
    application_id: uuid.UUID
    student: Ref
    student_number: str
    vacancy_id: uuid.UUID
    vacancy_title: str
    company_id: uuid.UUID
    company_name: str
    vacancy_owner: Ref
    company_supervisors: list[Ref]
    decided_at: datetime | None
    cycle_id: uuid.UUID | None
    cycle_name: str | None
