"""Seed data (Increment 1 design, Section 9).

    python -m app.seed           reference data: majors, skills with resources, universities and colleges
    python -m app.seed --demo    reference data plus demo accounts and a running cycle (local use only)

Rows are matched by their English name (or email) and left alone when they already exist, so the command
can run again safely. Demo accounts share DEMO_PASSWORD and are refused when ENV is production."""
import argparse
import json
import sys
from datetime import date, time, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.attendance.service import week_end
from app.catalog.router import match_terms
from app.core import clock, files
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.deps import Actor
from app.core.security import hash_password
from app.cycles import service as cycles
from app.evaluations import service as evaluations
from app.matching import service as matching
from app.models import (
    Application,
    AttendanceWeek,
    College,
    Company,
    CycleWeek,
    Enrollment,
    Major,
    Placement,
    ReportSlot,
    ReportVersion,
    Skill,
    SkillResource,
    StudentProfile,
    StudentSkill,
    TrainingCycle,
    University,
    User,
    Vacancy,
)
from app.similarity import service as similarity
from app.vacancies import service as vacancies

DATA = Path(__file__).parent / "seed_data"
DEMO_PASSWORD = "Demo-2026-pass"
CCSIT = "College of Computer Science and Information Technology"
IAU = "Imam Abdulrahman Bin Faisal University"


def _load(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- reference data
def seed_reference(db: Session) -> dict[str, int]:
    ref, added = _load("reference.json"), {"majors": 0, "skills": 0, "resources": 0, "universities": 0,
                                            "colleges": 0}
    for name_en, name_ar in ref["majors"]:
        if db.scalar(select(Major.id).where(Major.name_en == name_en)) is None:
            db.add(Major(name_en=name_en, name_ar=name_ar))
            added["majors"] += 1
    for name_en, name_ar, synonyms in _load("skills.json"):
        if db.scalar(select(Skill.id).where(func.lower(Skill.name_en) == name_en.lower())) is None:
            db.add(Skill(name_en=name_en, name_ar=name_ar, synonyms=synonyms,
                         match_terms=match_terms(name_en, name_ar, synonyms)))
            added["skills"] += 1
    db.flush()
    for skill_name, items in ref["resources"].items():
        skill = db.scalar(select(Skill).where(Skill.name_en == skill_name))
        if skill is None or db.scalar(select(SkillResource.id).where(SkillResource.skill_id == skill.id)):
            continue
        for pos, (title, url, effort, lang) in enumerate(items, start=1):
            db.add(SkillResource(skill_id=skill.id, title=title, url=url, estimated_effort=effort, language=lang,
                                 position=pos))
            added["resources"] += 1
    for u in ref["universities"]:
        uni = db.scalar(select(University).where(University.name_en == u["name_en"]))
        if uni is None:
            uni = University(name_en=u["name_en"], name_ar=u["name_ar"], email_domains=u["email_domains"],
                             gpa_scale=Decimal(u["gpa_scale"]))
            db.add(uni)
            db.flush()
            added["universities"] += 1
        for name_en, name_ar in u["colleges"]:
            if db.scalar(select(College.id).where(College.university_id == uni.id, College.name_en == name_en)):
                continue
            db.add(College(university_id=uni.id, name_en=name_en, name_ar=name_ar))
            added["colleges"] += 1
    db.flush()
    return added


# ---------------------------------------------------------------- demo data
def _user(db: Session, email: str, role: str, name_en: str, name_ar: str, **extra) -> User:
    user = db.scalar(select(User).where(func.lower(User.email) == email.lower()))
    if user is not None:
        return user
    now = clock.now()
    status = "not_required" if role in ("platform_admin", "academic_supervisor") else "verified"
    if role == "company_supervisor" and not extra.get("is_company_admin"):
        status = "not_required"
    user = User(email=email, password_hash=hash_password(DEMO_PASSWORD), role=role, name_en=name_en,
                name_ar=name_ar, language="ar", email_confirmed_at=now, verification_status=status,
                consent_at=now, **extra)
    db.add(user)
    db.flush()
    return user


def _skills(db: Session, names: list[str]) -> list[Skill]:
    return list(db.scalars(select(Skill).where(Skill.name_en.in_(names))))


def _demo_tracking(db: Session, company_user: User, placement) -> None:
    """Attendance for the weeks that have ended and a submitted periodic evaluation (Increment 2 screens)."""
    now = clock.now()
    for w in db.scalars(select(CycleWeek).where(CycleWeek.cycle_id == placement.cycle_id).order_by(CycleWeek.week_no)):
        if week_end(w) >= now:
            break
        attended = w.scheduled_days - (1 if w.week_no == 2 else 0)
        db.add(AttendanceWeek(placement_id=placement.id, week_no=w.week_no, scheduled_days=w.scheduled_days,
                              attended_days=attended, note="Sick leave, one day" if w.week_no == 2 else None,
                              recorded_by=company_user.id, recorded_at=now))
    criteria = evaluations.criteria(db, placement.cycle_id)
    actor = Actor(company_user, None)
    evaluations.save(db, actor, placement, "periodic", [{"criterion_id": c.id, "score": 4} for c in criteria],
                     "Reliable and quick to learn; should ask for code review earlier.")
    evaluations.submit(db, actor, placement, "periodic")


# The accepted week 1 report of a student of an earlier cycle (Increment 3 demo, step 1): submitting a weekly report
# that copies its first half shows a similarity flag. README shows the paragraph to paste.
EARLIER_REPORT = ("This week I worked on the order service of the e-commerce platform. I wrote a new endpoint "
                  "that returns the order history of a customer with pagination and filters by date and status. To "
                  "make the query fast I added a composite index on the customer and created date columns, which "
                  "reduced the response time from two seconds to about two hundred milliseconds. I also wrote "
                  "integration tests that run against a test database in Docker.")


def _demo_earlier_cycle(db: Session, coord: User, as1: User, ca: User, college: College, vacancy: Vacancy) -> None:
    """A closed Co-op cycle of the spring with one former student and an accepted week 1 report."""
    if db.scalar(select(TrainingCycle).where(TrainingCycle.college_id == college.id,
                                             TrainingCycle.name == "Co-op Spring 2026 (demo)")):
        return
    coord_actor = Actor(coord, None)
    start = date(2026, 2, 1)
    end = start + timedelta(weeks=12) - timedelta(days=1)
    final = clock.riyadh_to_utc(end + timedelta(days=7), time(23, 59))
    earlier = cycles.create(db, coord_actor, {
        "name": "Co-op Spring 2026 (demo)", "type": "coop", "start_date": start, "end_date": end, "weeks": 12,
        "working_days": [7, 1, 2, 3, 4], "report_weekday": 4, "report_time": time(23, 59),
        "periodic_eval_due_at": clock.riyadh_to_utc(start + timedelta(weeks=6), time(23, 59)),
        "final_eval_due_at": final, "final_report_due_at": final})
    former = _user(db, "s0@iau.edu.sa", "student", "Yousef Al-Qahtani", "يوسف القحطاني", college_id=college.id)
    if db.get(StudentProfile, former.id) is None:
        db.add(StudentProfile(user_id=former.id, student_number="2190007",
                              major_id=db.scalar(select(Major.id).where(Major.name_en == "Computer Science")),
                              gpa=Decimal("3.90"), level=10, languages=["Arabic", "English"]))
    db.add(Enrollment(cycle_id=earlier.id, student_id=former.id, created_by=coord.id))
    db.flush()
    application = Application(vacancy_id=vacancy.id, student_id=former.id, status="placed", decided_by=ca.id,
                              decided_at=clock.now())
    db.add(application)
    db.flush()
    placement = Placement(application_id=application.id, student_id=former.id, cycle_id=earlier.id,
                          vacancy_id=vacancy.id, company_supervisor_id=ca.id, academic_supervisor_id=as1.id,
                          status="completed", confirmed_by=coord.id, confirmed_at=clock.now())
    db.add(placement)
    db.flush()
    week1 = db.scalar(select(CycleWeek).where(CycleWeek.cycle_id == earlier.id, CycleWeek.week_no == 1))
    slot = ReportSlot(placement_id=placement.id, kind="weekly", week_no=1, due_at=week1.report_due_at,
                      status="accepted", accepted_at=week1.report_due_at)
    db.add(slot)
    db.flush()
    fields = {"tasks_performed": EARLIER_REPORT, "learning": "Thin controllers are easier to maintain.",
              "challenges": "Slow queries on large tables.", "next_week_plan": "Add caching for frequent queries."}
    version = ReportVersion(slot_id=slot.id, version_no=1, submitted_at=week1.report_due_at, is_late=False,
                            body_text="\n\n".join(fields.values()), **fields)
    db.add(version)
    db.flush()
    earlier.status = "closed"
    check = similarity.create_check(db, version)
    similarity.check(db, check.id)  # stores the passages; without the model the retry job does it later


def seed_demo(db: Session) -> list[tuple[str, str]]:
    """Accounts for each role, an open Co-op cycle that started three weeks ago, a published vacancy, one
    placement with report slots, one accepted applicant waiting for a placement, and one student who has
    not applied yet."""
    college = db.scalar(select(College).where(College.name_en == CCSIT))
    uni = db.scalar(select(University).where(University.name_en == IAU))
    majors = {m.name_en: m for m in db.scalars(select(Major))}

    admin = _user(db, "admin@internsync.example", "platform_admin", "Platform Admin", "مشرف المنصة")
    coord = _user(db, "coordinator@iau.edu.sa", "coordinator", "Dr. Huda Al-Qahtani", "د. هدى القحطاني",
                  college_id=college.id)
    as1 = _user(db, "f.alharbi@iau.edu.sa", "academic_supervisor", "Dr. Faisal Al-Harbi", "د. فيصل الحربي",
                college_id=college.id)
    _user(db, "n.aldossary@iau.edu.sa", "academic_supervisor", "Dr. Noura Al-Dossary", "د. نورة الدوسري",
          college_id=college.id)

    company = db.scalar(select(Company).where(Company.commercial_reg_no == "2050123456"))
    if company is None:
        company = Company(name="Nakheel Digital Solutions", commercial_reg_no="2050123456", city="Dammam",
                          website="https://nakheel.example", status="verified", verified_at=clock.now())
        db.add(company)
        db.flush()
    ca = _user(db, "sara@nakheel.example", "company_supervisor", "Sara Al-Zahrani", "سارة الزهراني",
               company_id=company.id, is_company_admin=True)
    _user(db, "omar@nakheel.example", "company_supervisor", "Omar Al-Otaibi", "عمر العتيبي", company_id=company.id)

    students = [
        ("s1@iau.edu.sa", "Abdullah Al-Shehri", "عبدالله الشهري", "2210001", "Computer Science", "4.20",
         ["Python", "SQL", "Git", "React", "REST APIs"]),
        ("s2@iau.edu.sa", "Reem Al-Mutairi", "ريم المطيري", "2210002", "Computer Information Systems", "3.80",
         ["SQL", "Power BI", "Microsoft Excel", "Data Analysis"]),
        ("s3@iau.edu.sa", "Khalid Al-Ghamdi", "خالد الغامدي", "2210003", "Cybersecurity and Digital Forensics",
         "3.10", ["Linux", "Networking", "Cybersecurity"]),
    ]
    student_users = []
    for email, name_en, name_ar, number, major, gpa, skill_names in students:
        s = _user(db, email, "student", name_en, name_ar, college_id=college.id)
        if db.get(StudentProfile, s.id) is None:
            db.add(StudentProfile(user_id=s.id, student_number=number, major_id=majors[major].id, gpa=Decimal(gpa),
                                  level=8, languages=["Arabic", "English"], skills_confirmed_at=clock.now()))
            for skill in _skills(db, skill_names):
                db.add(StudentSkill(student_id=s.id, skill_id=skill.id, source="manual", confirmed_at=clock.now()))
        student_users.append(s)
    db.flush()

    coord_actor, ca_actor = Actor(coord, None), Actor(ca, None)
    cycle = db.scalar(select(TrainingCycle).where(TrainingCycle.college_id == college.id,
                                                  TrainingCycle.name == "Co-op Fall 2026 (demo)"))
    if cycle is None:
        today = clock.today_riyadh()
        start = today - timedelta(days=(today.isoweekday() % 7) + 21)  # a Sunday three weeks ago
        end = start + timedelta(weeks=12) - timedelta(days=1)
        final = clock.riyadh_to_utc(end + timedelta(days=7), time(23, 59))
        cycle = cycles.create(db, coord_actor, {
            "name": "Co-op Fall 2026 (demo)", "type": "coop", "start_date": start, "end_date": end, "weeks": 12,
            "working_days": [7, 1, 2, 3, 4], "report_weekday": 4, "report_time": time(23, 59),
            "periodic_eval_due_at": clock.riyadh_to_utc(start + timedelta(weeks=6), time(23, 59)),
            "final_eval_due_at": final, "final_report_due_at": final})
        cycles.replace_components(db, coord_actor, cycle, [
            {"name_en": "Company final evaluation", "name_ar": "التقييم النهائي من الجهة", "weight": Decimal(40),
             "source": "company_final_evaluation"},
            {"name_en": "Weekly reports", "name_ar": "التقارير الأسبوعية", "weight": Decimal(30),
             "source": "academic_supervisor"},
            {"name_en": "Final report and presentation", "name_ar": "التقرير النهائي والعرض", "weight": Decimal(30),
             "source": "academic_supervisor"}])
        levels = {str(n): {"en": en, "ar": ar} for n, en, ar in [
            (1, "Poor", "ضعيف"), (2, "Fair", "مقبول"), (3, "Good", "جيد"), (4, "Very good", "جيد جدًا"),
            (5, "Excellent", "ممتاز")]}
        cycles.replace_rubric(db, coord_actor, cycle, [
            {"name_en": "Technical skills", "name_ar": "المهارات التقنية", "levels": levels},
            {"name_en": "Professional behaviour", "name_ar": "السلوك المهني", "levels": levels},
            {"name_en": "Communication", "name_ar": "التواصل", "levels": levels}])
        for s in student_users:
            db.add(Enrollment(cycle_id=cycle.id, student_id=s.id, created_by=coord.id))
        db.flush()

    vacancy = db.scalar(select(Vacancy).where(Vacancy.company_id == company.id,
                                              Vacancy.title == "Software Developer Trainee"))
    if vacancy is None:
        vacancy = vacancies.create(db, ca_actor, {
            "title": "Software Developer Trainee", "city": "Dammam",
            "description": "Join our product team and build web services in Python and React with code review "
                           "and weekly mentoring.",
            "training_type": "coop", "training_start": cycle.start_date, "training_end": cycle.end_date,
            "min_gpa": Decimal("3.00"), "seats": 3, "application_deadline": clock.now() + timedelta(days=30),
            "required_skill_ids": [k.id for k in _skills(db, ["Python", "SQL"])],
            "preferred_skill_ids": [k.id for k in _skills(db, ["React", "Git"])],
            "major_ids": [majors[m].id for m in ("Computer Science", "Computer Information Systems",
                                                 "Software Engineering")],
            "target_university_ids": [uni.id], "publish": True})
        vacancies.create(db, ca_actor, {
            "title": "Data Analyst Trainee", "city": "Khobar",
            "description": "Prepare dashboards and reports in Power BI and SQL for the operations team.",
            "training_type": "coop", "training_start": cycle.start_date, "training_end": cycle.end_date,
            "min_gpa": None, "seats": 2, "application_deadline": clock.now() + timedelta(days=21),
            "required_skill_ids": [k.id for k in _skills(db, ["SQL", "Power BI"])],
            "preferred_skill_ids": [k.id for k in _skills(db, ["Microsoft Excel"])],
            "major_ids": [majors[m].id for m in ("Computer Information Systems", "Data Science",
                                                 "Management Information Systems")],
            "target_university_ids": [], "publish": True})
        vacancies.create(db, ca_actor, {
            "title": "Security Operations Trainee", "city": "Dammam",
            "description": "Monitor alerts in the security operations centre, harden Linux servers, and document "
                           "incidents with the network team.",
            "training_type": "coop", "training_start": cycle.start_date, "training_end": cycle.end_date,
            "min_gpa": Decimal("2.75"), "seats": 2, "application_deadline": clock.now() + timedelta(days=25),
            "required_skill_ids": [k.id for k in _skills(db, ["Linux", "Networking"])],
            "preferred_skill_ids": [k.id for k in _skills(db, ["Cybersecurity", "Incident Response"])],
            "major_ids": [majors[m].id for m in ("Cybersecurity and Digital Forensics", "Computer Science",
                                                 "Computer Networks and Communications")],
            "target_university_ids": [uni.id], "publish": True})
        s1, s2 = student_users[0], student_users[1]
        for s in student_users:
            matching.embed_profile(db, s.id)
        a1 = vacancies.apply(db, Actor(s1, None), vacancy)
        vacancies.decide(db, ca_actor, a1, accept=True)
        placement = vacancies.confirm_placement(db, coord_actor, a1.id, as1.id, None)
        a2 = vacancies.apply(db, Actor(s2, None), vacancy)
        vacancies.decide(db, ca_actor, a2, accept=True)
        _demo_tracking(db, ca, placement)
    _demo_earlier_cycle(db, coord, as1, ca, college, vacancy)
    db.flush()
    return [("Platform Admin", admin.email), ("Coordinator", coord.email), ("Academic supervisor", as1.email),
            ("Company Admin", ca.email), ("Company supervisor", "omar@nakheel.example"),
            ("Student (placed)", "s1@iau.edu.sa"), ("Student (accepted, waiting)", "s2@iau.edu.sa"),
            ("Student (not applied)", "s3@iau.edu.sa"), ("Former student (earlier cycle)", "s0@iau.edu.sa")]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Load InternSync seed data")
    parser.add_argument("--demo", action="store_true", help="also create demo accounts (local use only)")
    args = parser.parse_args(argv)
    if args.demo and get_settings().env == "production":
        print("Demo accounts are not allowed when ENV=production.", file=sys.stderr)
        return 2
    files.storage().prepare()
    with SessionLocal() as db:
        added = seed_reference(db)
        print("reference:", ", ".join(f"{k} +{v}" for k, v in added.items()))
        if args.demo:
            accounts = seed_demo(db)
            print(f"demo accounts (password {DEMO_PASSWORD}):")
            for role, email in accounts:
                print(f"  {role:<30} {email}")
        db.commit()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


