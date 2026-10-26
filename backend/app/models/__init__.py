"""All Increment 1 tables (35 of the 49 in Design 4.3)."""
from app.models.catalog import Major, Skill, SkillResource, SystemSetting
from app.models.cycles import CycleWeek, Enrollment, GradeComponent, RubricCriterion, TrainingCycle
from app.models.orgs import (
                             AccountToken,
                             College,
                             Company,
                             University,
                             User,
                             UserSession,
                             VerificationDocument,
                             VerificationRequest,
)
from app.models.platform import AuditEntry, JobRun, StoredFile
from app.models.profiles import Cv, CvExtractedSkill, StudentProfile, StudentSkill
from app.models.reports import ReportAttachment, ReportComment, ReportReview, ReportSlot, ReportVersion
from app.models.vacancies import Application, Placement, Vacancy, VacancyMajor, VacancySkill, VacancyUniversity

__all__ = [
    "AccountToken", "Application", "AuditEntry", "College", "Company", "Cv", "CvExtractedSkill", "CycleWeek",
    "Enrollment", "GradeComponent", "JobRun", "Major", "Placement", "ReportAttachment", "ReportComment",
    "ReportReview", "ReportSlot", "ReportVersion", "RubricCriterion", "Skill", "SkillResource", "StoredFile",
    "StudentProfile", "StudentSkill", "SystemSetting", "TrainingCycle", "University", "User", "UserSession",
    "Vacancy", "VacancyMajor", "VacancySkill", "VacancyUniversity", "VerificationDocument", "VerificationRequest",
]
