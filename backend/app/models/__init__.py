"""The tables built so far (Increments 1 – 4) of the 49 in Design 4.3."""
from app.models.catalog import Major, Skill, SkillResource, SystemSetting
from app.models.cycles import CycleWeek, Enrollment, GradeComponent, RubricCriterion, TrainingCycle
from app.models.notices import (
                             Notification,
                             PushSubscription,
                             ReportPassage,
                             SimilarityCheck,
                             SimilarityMatch,
)
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
from app.models.tracking import (
                             AttendanceWeek,
                             Certificate,
                             CompanyEvaluation,
                             Evaluation,
                             EvaluationScore,
                             Grade,
                             GradeComponentScore,
                             OutcomeSurvey,
)
from app.models.vacancies import (
                             Application,
                             MatchScore,
                             Placement,
                             Vacancy,
                             VacancyMajor,
                             VacancySkill,
                             VacancyUniversity,
)

__all__ = [
    "AccountToken", "Application", "AttendanceWeek", "AuditEntry", "Certificate", "College", "Company",
    "CompanyEvaluation", "Cv", "CvExtractedSkill", "CycleWeek", "Enrollment", "Evaluation", "EvaluationScore", "Grade",
    "GradeComponent", "GradeComponentScore", "JobRun", "Major", "MatchScore", "Notification", "OutcomeSurvey",
    "Placement", "PushSubscription", "ReportAttachment",
    "ReportComment", "ReportPassage", "SimilarityCheck", "SimilarityMatch",
    "ReportReview", "ReportSlot", "ReportVersion", "RubricCriterion", "Skill", "SkillResource", "StoredFile",
    "StudentProfile", "StudentSkill", "SystemSetting", "TrainingCycle", "University", "User", "UserSession",
    "Vacancy", "VacancyMajor", "VacancySkill", "VacancyUniversity", "VerificationDocument", "VerificationRequest",
]
