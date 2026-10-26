"""Factories for test data (Increment 1 design, Section 11). They write straight to the database or call the
services, never the HTTP API, so each test exercises only the endpoint it is about."""
import io
import zipfile
from datetime import date, time, timedelta
from decimal import Decimal
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.catalog.router import match_terms
from app.core import clock
from app.core.deps import Actor
from app.core.security import create_access_token, hash_password
from app.cycles import service as cycles
from app.models import (
    College,
    Company,
    Enrollment,
    Major,
    Skill,
    StudentProfile,
    TrainingCycle,
    University,
    User,
    UserSession,
    Vacancy,
)
from app.vacancies import service as vacancies

PW = "Passw0rd-test"
CYCLE_START = date(2026, 10, 25)  # a Sunday


# ---------------------------------------------------------------- files
def pdf(*lines: str) -> bytes:
    """A one-page PDF with the given text lines (Helvetica); no lines gives a page without text."""
    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    body = "".join(f"BT /F1 11 Tf 72 {740 - 16 * i} Td ({esc(line)}) Tj ET\n" for i, line in enumerate(lines))
    content = body.encode("latin-1")
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            b"/Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offsets = b"%PDF-1.4\n", []
    for i, obj in enumerate(objs, start=1):
        offsets.append(len(out))
        out += str(i).encode() + b" 0 obj\n" + obj + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{off:010d} 00000 n \n".encode() for off in offsets)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return out


def docx(*paragraphs: str) -> bytes:
    from docx import Document

    document = Document()
    for p in paragraphs:
        document.add_paragraph(p)
    buf = io.BytesIO()
    document.save(buf)
    return buf.getvalue()


PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
       b"\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7\x35\x81\x84\x00\x00\x00\x00IEND\xaeB`\x82")


def zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("readme.txt", "not a document")
    return buf.getvalue()


# ---------------------------------------------------------------- factory
class Factory:
    def __init__(self, db: Session):
        self.db = db
        self.n = 0

    def seq(self) -> int:
        self.n += 1
        return self.n

    def commit(self):
        self.db.commit()

    # organizations and catalog
    def university(self, name: str | None = None, domains=("iau.edu.sa",), scale: str = "5.00") -> University:
        n = self.seq()
        uni = University(name_en=name or f"University {n}", name_ar=f"جامعة {n}", email_domains=list(domains),
                         gpa_scale=Decimal(scale))
        self.db.add(uni)
        self.db.flush()
        return uni

    def college(self, uni: University, name: str | None = None, active: bool = True) -> College:
        n = self.seq()
        college = College(university_id=uni.id, name_en=name or f"College {n}", name_ar=f"كلية {n}",
                          is_active=active)
        self.db.add(college)
        self.db.flush()
        return college

    def major(self, name: str | None = None) -> Major:
        n = self.seq()
        major = Major(name_en=name or f"Major {n}", name_ar=f"تخصص {n}")
        self.db.add(major)
        self.db.flush()
        return major

    def skill(self, name_en: str, name_ar: str | None = None, synonyms: tuple = ()) -> Skill:
        name_ar = name_ar or f"مهارة {self.seq()}"
        skill = Skill(name_en=name_en, name_ar=name_ar, synonyms=list(synonyms),
                      match_terms=match_terms(name_en, name_ar, list(synonyms)))
        self.db.add(skill)
        self.db.flush()
        return skill

    def company(self, status: str = "verified", name: str | None = None) -> Company:
        n = self.seq()
        company = Company(name=name or f"Company {n}", commercial_reg_no=f"10{n:08d}", city="Dammam",
                          status=status, verified_at=clock.now() if status == "verified" else None)
        self.db.add(company)
        self.db.flush()
        return company

    # people
    def user(self, role: str, *, college: College | None = None, company: Company | None = None,
             is_ca: bool = False, status: str | None = None, email: str | None = None, active: bool = True,
             consent: bool = True, confirmed: bool = True, password: str | None = PW, lang: str = "ar") -> User:
        n = self.seq()
        if status is None:
            status = "verified" if role in ("student", "coordinator") or is_ca else "not_required"
        domain = "iau.edu.sa" if college else "example.org"
        now = clock.now()
        user = User(email=email or f"{role}{n}@{domain}", password_hash=hash_password(password) if password else None,
                    role=role, name_en=f"{role.title()} {n}", name_ar=f"مستخدم {n}", language=lang,
                    college_id=college.id if college else None, company_id=company.id if company else None,
                    is_company_admin=is_ca, verification_status=status, is_active=active,
                    email_confirmed_at=now if confirmed else None, consent_at=now if consent else None)
        self.db.add(user)
        self.db.flush()
        return user

    def student(self, college: College, major: Major, gpa: str = "4.00", number: str | None = None,
                **kw) -> User:
        user = self.user("student", college=college, **kw)
        self.db.add(StudentProfile(user_id=user.id, student_number=number or f"22{self.seq():06d}",
                                   major_id=major.id, gpa=Decimal(gpa), level=8))
        self.db.flush()
        return user

    def headers(self, user: User, lang: str | None = None) -> dict:
        now = clock.now()
        session = UserSession(user_id=user.id, last_seen_at=now, expires_at=now + timedelta(hours=12))
        self.db.add(session)
        self.db.commit()
        token = create_access_token(user.id, user.role, session.id, now, session.expires_at)
        out = {"Authorization": f"Bearer {token}"}
        if lang:
            out["Accept-Language"] = lang
        return out

    # cycles and vacancies
    def cycle(self, coordinator: User, type_: str = "coop", start: date = CYCLE_START, weeks: int = 12,
              name: str | None = None) -> TrainingCycle:
        end = start + timedelta(days=7 * weeks - 1)
        final = clock.riyadh_to_utc(end + timedelta(days=7), time(23, 59))
        cycle = cycles.create(self.db, Actor(coordinator, None), {
            "name": name or f"Cycle {self.seq()}", "type": type_, "start_date": start, "end_date": end,
            "weeks": weeks, "working_days": [7, 1, 2, 3, 4], "report_weekday": 4, "report_time": time(23, 59),
            "periodic_eval_due_at": clock.riyadh_to_utc(start + timedelta(weeks=weeks // 2), time(23, 59)),
            "final_eval_due_at": final, "final_report_due_at": final})
        self.db.flush()
        return cycle

    def enroll(self, cycle: TrainingCycle, student: User, by: User) -> None:
        self.db.add(Enrollment(cycle_id=cycle.id, student_id=student.id, created_by=by.id))
        self.db.flush()

    def vacancy(self, owner: User, majors: list[Major], *, training_type: str = "coop", seats: int = 2,
                deadline_days: int = 14, min_gpa: str | None = None, universities: tuple = (),
                required: tuple = (), preferred: tuple = (), publish: bool = True, title: str | None = None,
                city: str = "Dammam") -> Vacancy:
        v = vacancies.create(self.db, Actor(owner, None), {
            "title": title or f"Trainee {self.seq()}", "city": city,
            "description": "Training on real projects with a mentor.", "training_type": training_type,
            "training_start": CYCLE_START, "training_end": CYCLE_START + timedelta(weeks=12),
            "min_gpa": Decimal(min_gpa) if min_gpa else None, "seats": seats,
            "application_deadline": clock.now() + timedelta(days=deadline_days),
            "required_skill_ids": [s.id for s in required], "preferred_skill_ids": [s.id for s in preferred],
            "major_ids": [m.id for m in majors], "target_university_ids": [u.id for u in universities],
            "publish": publish})
        self.db.flush()
        return v

    def application(self, student: User, v: Vacancy, accept_by: User | None = None):
        a = vacancies.apply(self.db, Actor(student, None), v)
        if accept_by is not None:
            vacancies.decide(self.db, Actor(accept_by, None), a, accept=True)
        self.db.flush()
        return a

    def placement(self, student: User, v: Vacancy, company_user: User, coordinator: User, academic: User):
        a = self.application(student, v, accept_by=company_user)
        p = vacancies.confirm_placement(self.db, Actor(coordinator, None), a.id, academic.id, None)
        self.db.flush()
        return p

    # the standard world
    def world(self) -> SimpleNamespace:
        w = SimpleNamespace()
        w.uniA = self.university("Imam Abdulrahman Bin Faisal University", ("iau.edu.sa",), "5.00")
        w.uniB = self.university("King Fahd University", ("kfupm.edu.sa",), "4.00")
        w.A1 = self.college(w.uniA, "College of Computing")
        w.A2 = self.college(w.uniA, "College of Engineering")
        w.B1 = self.college(w.uniB, "College of Computing and Mathematics")
        w.cs_major, w.cis_major, w.ee_major = self.major("Computer Science"), self.major("Information Systems"), \
            self.major("Electrical Engineering")
        w.python, w.sql, w.js = self.skill("Python", "بايثون"), self.skill("SQL", "إس كيو إل"), \
            self.skill("JavaScript", "جافاسكربت", ("JS",))
        w.pa = self.user("platform_admin")
        w.coA1, w.coA2, w.coB1 = (self.user("coordinator", college=c) for c in (w.A1, w.A2, w.B1))
        w.asA1, w.asA1b = self.user("academic_supervisor", college=w.A1), self.user("academic_supervisor",
                                                                                 college=w.A1)
        w.asA2 = self.user("academic_supervisor", college=w.A2)
        w.co1, w.co2 = self.company(name="Nakheel"), self.company(name="Sahil")
        w.ca1 = self.user("company_supervisor", company=w.co1, is_ca=True)
        w.cs1 = self.user("company_supervisor", company=w.co1)
        w.ca2 = self.user("company_supervisor", company=w.co2, is_ca=True)
        w.cycle = self.cycle(w.coA1, name="Co-op Fall 2026")
        w.stA = self.student(w.A1, w.cs_major, "4.20")
        w.stA2 = self.student(w.A1, w.cis_major, "3.00")
        w.stB = self.student(w.B1, w.cs_major, "3.50")
        w.cycleB = self.cycle(w.coB1, name="Co-op B")
        for s in (w.stA, w.stA2):
            self.enroll(w.cycle, s, w.coA1)
        self.enroll(w.cycleB, w.stB, w.coB1)
        w.vac = self.vacancy(w.cs1, [w.cs_major, w.cis_major], required=(w.python,), title="Backend Trainee")
        self.commit()
        w.h = self.headers
        return w
