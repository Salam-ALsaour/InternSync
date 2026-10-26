import uuid
from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class WeekOut(BaseModel):
    week_no: int
    starts_on: date
    ends_on: date
    report_due_at: datetime
    scheduled_days: int


class CycleIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    type: Literal["coop", "summer"]
    start_date: date
    end_date: date
    weeks: int = Field(ge=1, le=30)
    working_days: list[int] = [7, 1, 2, 3, 4]
    report_weekday: int = Field(ge=1, le=7)
    report_time: time
    periodic_eval_due_at: datetime
    final_eval_due_at: datetime
    final_report_due_at: datetime

    @field_validator("working_days")
    @classmethod
    def _days(cls, v: list[int]) -> list[int]:
        if not v or len(set(v)) != len(v) or any(d < 1 or d > 7 for d in v):
            raise ValueError("working days are distinct ISO weekdays 1–7")
        return v


class CyclePatch(BaseModel):
    name: str | None = Field(None, min_length=2, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    weeks: int | None = Field(None, ge=1, le=30)
    working_days: list[int] | None = None
    report_weekday: int | None = Field(None, ge=1, le=7)
    report_time: time | None = None
    periodic_eval_due_at: datetime | None = None
    final_eval_due_at: datetime | None = None
    final_report_due_at: datetime | None = None


class CycleOut(BaseModel):
    id: uuid.UUID
    college_id: uuid.UUID
    name: str
    type: str
    start_date: date
    end_date: date
    weeks: int
    working_days: list[int]
    report_weekday: int
    report_time: time
    periodic_eval_due_at: datetime
    final_eval_due_at: datetime
    final_report_due_at: datetime
    status: str
    rubric_locked_at: datetime | None
    closed_at: datetime | None
    schedule_locked: bool
    enrolled_students: int


class CycleWithWeeks(CycleOut):
    week_list: list[WeekOut]


class WeekPatch(BaseModel):
    report_due_at: datetime
    reason: str = Field("", max_length=1000)


class ReasonIn(BaseModel):
    reason: str = Field("", max_length=1000)


class ComponentIO(BaseModel):
    id: uuid.UUID | None = None
    name_en: str = Field(min_length=2, max_length=120)
    name_ar: str = Field(min_length=2, max_length=120)
    weight: Decimal = Field(gt=0, le=100)
    source: Literal["company_final_evaluation", "academic_supervisor"]


class ComponentsIn(BaseModel):
    components: list[ComponentIO] = Field(min_length=1, max_length=10)


class LevelText(BaseModel):
    en: str = Field(min_length=1, max_length=500)
    ar: str = Field(min_length=1, max_length=500)


class CriterionIO(BaseModel):
    id: uuid.UUID | None = None
    name_en: str = Field(min_length=2, max_length=120)
    name_ar: str = Field(min_length=2, max_length=120)
    levels: dict[Literal["1", "2", "3", "4", "5"], LevelText]

    @field_validator("levels")
    @classmethod
    def _five(cls, v: dict) -> dict:
        if set(v) != {"1", "2", "3", "4", "5"}:
            raise ValueError("all five levels are required")
        return v


class RubricIn(BaseModel):
    criteria: list[CriterionIO] = Field(min_length=1, max_length=15)


class RubricOut(BaseModel):
    locked: bool
    criteria: list[CriterionIO]


class EnrollmentOut(BaseModel):
    student_id: uuid.UUID
    name_en: str
    name_ar: str
    email: str
    student_number: str
    major_en: str
    major_ar: str
    gpa: Decimal
    is_active: bool
    placed: bool
    enrolled_at: datetime
