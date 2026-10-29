"""The events of Design Table 5.6 (FR-NOT-05): who is told, with which params and link. The services call these right
after the change they report, in the same transaction."""
from sqlalchemy.orm import Session

from app.core import clock
from app.models import (
    Application,
    Company,
    Evaluation,
    Grade,
    Placement,
    ReportSlot,
    User,
    Vacancy,
    VerificationRequest,
)
from app.notifications.service import coordinator_of, notify, platform_admins
from app.notifications.texts import names, report_label

KIND = {"student": ("student", "طالب"), "coordinator": ("coordinator", "منسق تدريب"),
        "company": ("training company", "جهة تدريب")}
EVALUATION = {"periodic": ("periodic evaluation", "التقييم الدوري"), "final": ("final evaluation", "التقييم النهائي")}
WHY = {"placed_elsewhere": ("you were placed in another vacancy", "تم توزيعك على فرصة أخرى"),
       "vacancy_closed": ("the vacancy was closed", "الفرصة أُغلقت")}
ROLE = {"coordinator": ("the training coordinator", "منسق التدريب"),
        "company_admin": ("the Company Admin", "مسؤول الجهة")}


def _pair(prefix: str, pair: tuple[str, str]) -> dict:
    return {f"{prefix}_en": pair[0], f"{prefix}_ar": pair[1]}


def _person(prefix: str, user: User | None) -> dict:
    return names(prefix, user.name_en, user.name_ar) if user else names(prefix, "", "")


def due_text(at) -> str:
    return at.astimezone(clock.RIYADH).strftime("%d/%m/%Y %H:%M")


# ---------------------------------------------------------------- verification and roles
def verification_submitted(db: Session, user: User, req: VerificationRequest) -> None:
    if req.kind == "student":
        to, link = [coordinator_of(db, req.college_id)], "/coordinator/students"
    else:
        to, link = platform_admins(db), "/platform/verifications"
    notify(db, to, "verification.submitted", {**_person("name", user), **_pair("kind", KIND[req.kind])}, link)


def verification_decided(db: Session, req: VerificationRequest) -> None:
    approved = req.status == "approved"
    notify(db, [req.user_id], "verification.approved" if approved else "verification.rejected",
           {"reason": req.reason or ""}, "/" if approved else "/verification")


def role_transferred(db: Session, role: str, previous: User | None, new: User, org_en: str, org_ar: str,
                     reason: str) -> None:
    params = {**_pair("role", ROLE[role]), **names("org", org_en, org_ar), "reason": reason,
              **_person("new_holder", new)}
    notify(db, [new], "role.transferred", {**params, "variant": "received"}, "/")
    notify(db, [previous], "role.transferred", {**params, "variant": "removed"}, "/")


# ---------------------------------------------------------------- applications and placements
def _application_params(db: Session, a: Application, v: Vacancy) -> dict:
    student = db.get(User, a.student_id)
    return {**_person("student", student), "vacancy": v.title, "company": db.get(Company, v.company_id).name}


def application_received(db: Session, a: Application, v: Vacancy) -> None:
    notify(db, [v.company_supervisor_id], "application.received", _application_params(db, a, v),
           f"/company/vacancies/{v.id}/applicants")


def application_decided(db: Session, a: Application, v: Vacancy) -> None:
    params = _application_params(db, a, v)
    accepted = a.status == "accepted"
    notify(db, [a.student_id], "application.decided", {**params, "variant": "accepted" if accepted else "declined"},
           "/student/applications")
    if accepted:
        student = db.get(User, a.student_id)
        notify(db, [coordinator_of(db, student.college_id)], "application.accepted", params,
               "/coordinator/placements")


def application_withdrawn(db: Session, a: Application, v: Vacancy, why: str) -> None:
    notify(db, [a.student_id], "application.withdrawn_auto", {"vacancy": v.title, **_pair("why", WHY[why])},
           "/student/applications")


def _placement_params(db: Session, p: Placement) -> dict:
    v = db.get(Vacancy, p.vacancy_id)
    return {**_person("student", db.get(User, p.student_id)), "vacancy": v.title,
            "company": db.get(Company, v.company_id).name}


def placement_event(db: Session, event: str, p: Placement, **extra) -> None:
    params = {**_placement_params(db, p), **extra}
    notify(db, [p.student_id], event, params, "/student/reports")
    notify(db, [p.company_supervisor_id, p.academic_supervisor_id], event, params, f"/placements/{p.id}")


# ---------------------------------------------------------------- reports, evaluations, grades
def report_event(db: Session, event: str, slot: ReportSlot, p: Placement, **extra) -> None:
    params = {**_person("student", db.get(User, p.student_id)), **report_label(slot.week_no), **extra}
    if event == "report.submitted":
        notify(db, [p.academic_supervisor_id], event, params, f"/reports/{slot.id}")
    else:  # revision requested, accepted
        notify(db, [p.student_id], event, params, f"/reports/{slot.id}")


def evaluation_submitted(db: Session, e: Evaluation, p: Placement) -> None:
    v = db.get(Vacancy, p.vacancy_id)
    params = {**_person("student", db.get(User, p.student_id)), "company": db.get(Company, v.company_id).name,
              **_pair("evaluation", EVALUATION[e.type])}
    notify(db, [p.academic_supervisor_id], "evaluation.submitted", params, f"/placements/{p.id}?tab=evaluations")
    if e.type == "periodic":  # the final one stays hidden from the student until the grade is Final (FR-EVL-03)
        notify(db, [p.student_id], "evaluation.submitted", params, "/student/reports?tab=evaluations")


def grade_event(db: Session, event: str, grade: Grade, p: Placement, **extra) -> None:
    student = db.get(User, p.student_id)
    params = {**_person("student", student), **extra}
    link = f"/placements/{p.id}?tab=grade"
    if event == "grade.submitted":
        notify(db, [coordinator_of(db, student.college_id)], event, params, link)
    elif event == "grade.returned":
        notify(db, [p.academic_supervisor_id], event, params, link)
    else:  # final, reopened
        notify(db, [p.student_id], event, params, "/student/reports?tab=grade")
        notify(db, [p.academic_supervisor_id], event, params, link)


def certificate_event(db: Session, event: str, p: Placement, **extra) -> None:
    """`certificate.issued` and `certificate.revoked` (FR-CER-01, FR-CER-03) to the student."""
    v = db.get(Vacancy, p.vacancy_id)
    notify(db, [p.student_id], event, {"company": db.get(Company, v.company_id).name, **extra},
           "/student/reports?tab=grade")
