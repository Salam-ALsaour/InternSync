"""Grade sheet, term summary, and training record (FR-EXP-01 – 03; Design 5.6; Increment 3 design, Section 7).

The values come from the same service functions as the screens, so an export always equals what the coordinator
and the supervisor see. The caller's language decides the labels and the direction."""
import io
from decimal import Decimal

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.attendance import service as attendance
from app.dashboard.service import cycle_stats
from app.exports.pdf import Document, stamp_text
from app.grades import service as grades
from app.models import (
    College,
    Company,
    Evaluation,
    Grade,
    GradeComponent,
    Placement,
    ReportSlot,
    StudentProfile,
    TrainingCycle,
    User,
    Vacancy,
)

L = {
    "en": {
        "grade_sheet": "Grade sheet", "term_summary": "Term summary", "training_record": "Training record",
        "student_number": "Student number", "student": "Student", "company": "Company",
        "academic_supervisor": "Academic supervisor", "company_supervisor": "Company supervisor", "total": "Total",
        "status": "Status", "cycle": "Training cycle", "dates": "Dates", "college": "College", "vacancy": "Vacancy",
        "placement_status": "Placement status", "reports": "Weekly and final reports", "report": "Report",
        "due": "Deadline", "late": "Late", "missing": "Missing", "yes": "Yes", "no": "No",
        "attendance": "Attendance", "week": "Week", "days": "Days attended", "percent": "Attendance rate",
        "evaluations": "Evaluations", "mean": "Average", "submitted_at": "Submitted", "grade": "Final grade",
        "component": "Component", "weight": "Weight %", "score": "Score", "overall": "Whole cycle",
        "by_company": "By company", "figure": "Figure", "value": "Value", "enrolled": "Enrolled students",
        "placed": "Placed", "unplaced": "Not placed", "reports_due": "Reports due so far",
        "submission_rate": "Reports submitted", "late_rate": "Submitted late",
        "attendance_rate": "Attendance", "evaluation_completion": "Evaluations completed",
        "final_report": "Final report",
        "not_recorded": "Not recorded", "no_rows": "No placements in this cycle.",
    },
    "ar": {
        "grade_sheet": "كشف الدرجات", "term_summary": "ملخص الفصل التدريبي", "training_record": "سجل التدريب",
        "student_number": "الرقم الجامعي", "student": "الطالب", "company": "جهة التدريب",
        "academic_supervisor": "المشرف الأكاديمي", "company_supervisor": "مشرف الجهة", "total": "المجموع",
        "status": "الحالة", "cycle": "دورة التدريب", "dates": "الفترة", "college": "الكلية", "vacancy": "الفرصة",
        "placement_status": "حالة التوزيع", "reports": "التقارير الأسبوعية والنهائية", "report": "التقرير",
        "due": "الموعد", "late": "متأخر", "missing": "لم يُسلَّم", "yes": "نعم", "no": "لا",
        "attendance": "الحضور", "week": "الأسبوع", "days": "أيام الحضور", "percent": "نسبة الحضور",
        "evaluations": "التقييمات", "mean": "المتوسط", "submitted_at": "تاريخ الإرسال", "grade": "الدرجة النهائية",
        "component": "المكوّن", "weight": "الوزن ٪", "score": "الدرجة", "overall": "الدورة كاملة",
        "by_company": "حسب جهة التدريب", "figure": "المؤشر", "value": "القيمة", "enrolled": "الطلاب المسجلون",
        "placed": "تم توزيعهم", "unplaced": "لم يُوزّعوا", "reports_due": "التقارير المستحقة حتى الآن",
        "submission_rate": "التقارير المُسلّمة", "late_rate": "سُلّمت متأخرة",
        "attendance_rate": "الحضور", "evaluation_completion": "التقييمات المكتملة", "final_report": "التقرير النهائي",
        "not_recorded": "لم يُسجَّل", "no_rows": "لا توزيعات في هذه الدورة.",
    },
}
STATUS = {
    "en": {"draft": "Draft", "submitted": "Submitted", "final": "Final", "revision_requested": "Revision requested",
           "accepted": "Accepted", "closed_missing": "Closed – missing", "active": "Active", "completed": "Completed",
           "cancelled": "Cancelled", "none": "Not started"},
    "ar": {"draft": "مسودة", "submitted": "مُسلَّم", "final": "نهائية", "revision_requested": "مطلوب تعديله",
           "accepted": "مقبول", "closed_missing": "مغلق – لم يُسلَّم", "active": "نشط", "completed": "مكتمل",
           "cancelled": "ملغى", "none": "لم يبدأ"},
}
EVAL_NAME = {"en": {"periodic": "Periodic evaluation", "final": "Final evaluation"},
             "ar": {"periodic": "التقييم الدوري", "final": "التقييم النهائي"}}


def _lang(lang: str) -> str:
    return "ar" if lang == "ar" else "en"


def _name(obj, lang: str) -> str:
    return (obj.name_ar if lang == "ar" else obj.name_en) or obj.name_en


def _num(x) -> str:
    return "—" if x is None else f"{Decimal(x):.2f}"


def _pct(x, lang: str = "en") -> str:
    if x is None:
        return "—"
    return f"{x:.1f}٪" if lang == "ar" else f"{x:.1f}%"  # the Arabic percent sign keeps its place after the digits


def _weight(c, lang: str) -> str:
    w = f"{Decimal(c.weight).normalize():f}"
    return f"{_name(c, lang)} {w}٪" if lang == "ar" else f"{_name(c, lang)} ({w}%)"


def _safe(value):
    """Text that a spreadsheet would read as a formula gets a leading quote (Design 5.6)."""
    if isinstance(value, str) and value[:1] in ("=", "+", "-", "@"):
        return "'" + value
    return value


# ---------------------------------------------------------------- grade sheet (FR-EXP-01)
def grade_rows(db: Session, cycle: TrainingCycle, lang: str) -> tuple[list[GradeComponent], list[dict]]:
    comps = list(db.scalars(select(GradeComponent).where(GradeComponent.cycle_id == cycle.id)
                            .order_by(GradeComponent.position)))
    rows = []
    for grade, p, student in db.execute(
            select(Grade, Placement, User).join(Placement, Placement.id == Grade.placement_id)
            .join(User, User.id == Placement.student_id)
            .where(Placement.cycle_id == cycle.id, Placement.status != "cancelled")):
        parts = {c["id"]: c["score"] for c in grades.components(db, grade, p)}
        v = db.get(Vacancy, p.vacancy_id)
        profile = db.get(StudentProfile, student.id)
        rows.append({"student_number": profile.student_number if profile else "", "name": _name(student, lang),
                     "company": db.get(Company, v.company_id).name,
                     "academic_supervisor": _name(db.get(User, p.academic_supervisor_id), lang),
                     "scores": [parts.get(c.id) for c in comps],
                     "total": grade.total if grade.status != "draft" else grades.total(grades.components(db, grade, p)),
                     "status": grade.status})
    rows.sort(key=lambda r: r["name"])
    return comps, rows


def grade_sheet_xlsx(db: Session, cycle: TrainingCycle, lang: str) -> bytes:
    lang = _lang(lang)
    t = L[lang]
    comps, rows = grade_rows(db, cycle, lang)
    wb = Workbook()
    ws = wb.active
    ws.title = t["grade_sheet"][:31]
    ws.sheet_view.rightToLeft = lang == "ar"
    ws.append([_safe(f"{t['grade_sheet']} – {cycle.name}")])
    ws["A1"].font = Font(bold=True, size=13)
    headers = [t["student_number"], t["student"], t["company"], t["academic_supervisor"],
               *[_weight(c, lang) for c in comps], t["total"], t["status"]]
    ws.append(headers)
    for cell in ws[2]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="E6F0EC")
        cell.alignment = Alignment(wrap_text=True, vertical="center")
    for r in rows:
        ws.append([_safe(r["student_number"]), _safe(r["name"]), _safe(r["company"]), _safe(r["academic_supervisor"]),
                   *[float(s) if s is not None else None for s in r["scores"]],
                   float(r["total"]) if r["total"] is not None else None, STATUS[lang].get(r["status"], r["status"])])
    for i, width in enumerate([14, 28, 26, 24, *[16] * len(comps), 10, 12], start=1):
        ws.column_dimensions[ws.cell(row=2, column=i).column_letter].width = width
    ws.freeze_panes = "A3"
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def grade_sheet_pdf(db: Session, cycle: TrainingCycle, lang: str) -> bytes:
    lang = _lang(lang)
    t = L[lang]
    comps, rows = grade_rows(db, cycle, lang)
    college = db.get(College, cycle.college_id)
    doc = Document(lang, f"{t['grade_sheet']} – {cycle.name}", _name(college, lang), landscape=True)
    headers = [t["student_number"], t["student"], t["company"], t["academic_supervisor"],
               *[_weight(c, lang) for c in comps], t["total"], t["status"]]
    fixed = 22 + 46 + 44 + 40 + 18 + 22
    widths = [22, 46, 44, 40, *[max(16.0, (269 - fixed) / max(len(comps), 1))] * len(comps), 18, 22]
    numeric = {0, *range(4, 4 + len(comps) + 1)}
    body = [[r["student_number"], r["name"], r["company"], r["academic_supervisor"], *[_num(s) for s in r["scores"]],
             _num(r["total"]), STATUS[lang].get(r["status"], r["status"])] for r in rows]
    if body:
        doc.grid(headers, body, widths, numeric, size=8)
    else:
        doc.paragraph(t["no_rows"])
    return doc.render()


# ---------------------------------------------------------------- term summary (FR-EXP-02)
FIGURES = ("enrolled", "placed", "unplaced", "reports_due", "submission_rate", "late_rate", "attendance_rate",
           "evaluation_completion")


def _figure(name: str, figures: dict, lang: str) -> str:
    value = figures.get(name)
    if name.endswith("_rate") or name == "evaluation_completion":
        return _pct(value, lang)
    return "—" if value is None else str(value)


def term_summary_pdf(db: Session, cycle: TrainingCycle, lang: str) -> bytes:
    lang = _lang(lang)
    t = L[lang]
    stats = cycle_stats(db, cycle, None)
    college = db.get(College, cycle.college_id)
    dates = f"{cycle.start_date:%d/%m/%Y} – {cycle.end_date:%d/%m/%Y}"
    doc = Document(lang, f"{t['term_summary']} – {cycle.name}", f"{_name(college, lang)} · {dates}")
    doc.heading(t["overall"])
    doc.grid([t["figure"], t["value"]], [[t[f], _figure(f, stats["overall"], lang)] for f in FIGURES], [120, 60],
             {1})
    if stats["companies"]:
        doc.heading(t["by_company"])
        names = [f for f in FIGURES if f not in ("enrolled", "unplaced")]
        doc.grid([t["company"], *[t[f] for f in names]],
                 [[c["company_name"], *[_figure(f, c, lang) for f in names]] for c in stats["companies"]],
                 [52, *[(182 - 52) / len(names)] * len(names)], set(range(1, len(names) + 1)), size=8)
    return doc.render()


# ---------------------------------------------------------------- training record (FR-EXP-03)
def training_record_pdf(db: Session, placement: Placement, lang: str) -> bytes:
    lang = _lang(lang)
    t = L[lang]
    student = db.get(User, placement.student_id)
    profile = db.get(StudentProfile, student.id)
    cycle = db.get(TrainingCycle, placement.cycle_id)
    v = db.get(Vacancy, placement.vacancy_id)
    doc = Document(lang, f"{t['training_record']} – {_name(student, lang)}", cycle.name)
    doc.facts([
        (t["student_number"], profile.student_number if profile else "—"),
        (t["college"], _name(db.get(College, student.college_id), lang)),
        (t["cycle"], cycle.name),
        (t["dates"], f"{cycle.start_date:%d/%m/%Y} – {cycle.end_date:%d/%m/%Y}"),
        (t["company"], f"{db.get(Company, v.company_id).name} – {v.title}"),
        (t["company_supervisor"], _name(db.get(User, placement.company_supervisor_id), lang)),
        (t["academic_supervisor"], _name(db.get(User, placement.academic_supervisor_id), lang)),
        (t["placement_status"], STATUS[lang].get(placement.status, placement.status)),
    ])
    doc.heading(t["reports"])
    slots = db.scalars(select(ReportSlot).where(ReportSlot.placement_id == placement.id)
                       .order_by(ReportSlot.kind.desc(), ReportSlot.week_no)).all()
    doc.grid([t["report"], t["due"], t["status"], t["late"], t["missing"]],
             [[f"{t['week']} {s.week_no}" if s.week_no else t["final_report"], stamp_text(s.due_at),
               STATUS[lang].get(s.status, s.status), t["yes"] if s.is_late else t["no"],
               t["yes"] if s.is_missing else t["no"]] for s in slots], [40, 40, 50, 26, 26], {1, 3, 4})
    summary = attendance.summary(db, placement)
    doc.heading(f"{t['attendance']} – {t['percent']}: {_pct(summary['percent'], lang)}")
    doc.grid([t["week"], t["dates"], t["days"]],
             [[str(w["week_no"]), f"{w['starts_on']:%d/%m/%Y} – {w['ends_on']:%d/%m/%Y}",
               f"{w['attended_days']} / {w['scheduled_days']}" if w["attended_days"] is not None else t["not_recorded"]]
              for w in summary["weeks"]], [30, 90, 62], {0, 2})
    doc.heading(t["evaluations"])
    rows = []
    for type_ in ("periodic", "final"):
        e = db.scalar(select(Evaluation).where(Evaluation.placement_id == placement.id, Evaluation.type == type_))
        status = STATUS[lang]["none"] if e is None else STATUS[lang].get(e.status, e.status)
        rows.append([EVAL_NAME[lang][type_], status,
                     _num(e.mean_score) if e is not None and e.status == "submitted" else "—",
                     stamp_text(e.submitted_at) if e is not None and e.submitted_at else "—"])
    doc.grid([t["evaluations"], t["status"], t["mean"], t["submitted_at"]], rows, [60, 40, 30, 52], {2, 3})
    grade = grades.grade_for(db, placement)
    parts = grades.components(db, grade, placement)
    doc.heading(f"{t['grade']}: {STATUS[lang].get(grade.status, grade.status)}")
    doc.grid([t["component"], t["weight"], t["score"]],
             [[_name_dict(c, lang), f"{c['weight']:g}", _num(c["score"])] for c in parts]
             + [[t["total"], "100", _num(grade.total if grade.status != "draft" else grades.total(parts))]],
             [110, 32, 40], {1, 2})
    return doc.render()


def _name_dict(c: dict, lang: str) -> str:
    return (c["name_ar"] if lang == "ar" else c["name_en"]) or c["name_en"]
