"""M3 demo dry run against the running stack (`docker compose up`): the ten steps of 01_Requirements Section 7
through the HTTP API, with the email links read from Mailpit and the demo clock moved for the late report.

    python scripts/demo_dry_run.py [--api http://localhost:8000] [--mail http://localhost:8025]

Needs the seeded Platform Admin (`python -m app.seed --demo`). Every run uses new names, so it can be repeated;
the registration limit per address is raised for the run and restored afterwards. It prints one line per step and
exits with status 1 at the first failure."""
import argparse
import re
import sys
import time
from datetime import UTC, date, datetime, timedelta

import httpx

PASS = "Demo-pass-2026"
PA = ("admin@internsync.example", "Demo-2026-pass")


class Run:
    def __init__(self, api: str, mail: str):
        self.api = httpx.Client(base_url=f"{api.rstrip('/')}/api/v1", timeout=30)
        self.mail = httpx.Client(base_url=mail.rstrip("/"), timeout=10)
        self.tag = datetime.now().strftime("%H%M%S")

    def call(self, method: str, path: str, token: str | None = None, expect: int = 200, **kw):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        r = self.api.request(method, path, headers=headers, **kw)
        if r.status_code != expect:
            raise SystemExit(f"FAILED {method} {path}: {r.status_code} {r.text[:300]}")
        return r.json() if r.content else None

    def login(self, email: str, password: str = PASS) -> str:
        out = self.call("POST", "/auth/login", json={"email": email, "password": password})
        if out["user"]["consent_required"]:
            self.call("POST", "/me/consent", out["access_token"])
        return out["access_token"]

    def link(self, to: str) -> str:
        """The token in the newest email to `to` (Mailpit search API)."""
        for _ in range(20):
            found = self.mail.get("/api/v1/search", params={"query": f"to:{to}", "limit": 1}).json()
            if found["messages"]:
                text = self.mail.get(f"/api/v1/message/{found['messages'][0]['ID']}").json()["Text"]
                return re.search(r"/(?:confirm|invite|reset)/([\w-]+)", text).group(1)
            time.sleep(0.5)
        raise SystemExit(f"FAILED no email to {to}")


def pdf(text: str) -> bytes:
    content = f"BT /F1 11 Tf 72 720 Td ({text}) Tj ET".encode()
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
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
    return out + f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()


def step(n: int, text: str) -> None:
    print(f"step {n:>2} ok  {text}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default="http://localhost:8000")
    parser.add_argument("--mail", default="http://localhost:8025")
    args = parser.parse_args()
    r = Run(args.api, args.mail)
    r.call("POST", "/dev/clock/reset")
    pa = r.login(*PA)
    limit = "auth.registrations_per_ip_hour"
    before = r.call("GET", "/settings", pa)[limit]
    r.call("PATCH", "/settings", pa, json={limit: max(before, 100)})
    try:
        return scenario(r, pa)
    finally:
        r.call("PATCH", "/settings", r.login(*PA), json={limit: before})
        r.call("POST", "/dev/clock/reset")


def scenario(r: Run, pa: str) -> int:
    tag = r.tag

    # 1. The Platform Admin adds a college and a skill
    uni = next(u for u in r.call("GET", "/universities") if u["name_en"].startswith("Imam"))
    college = r.call("POST", f"/universities/{uni['id']}/colleges", pa, 201,
                     json={"name_en": f"College of Applied Computing {tag}",
                           "name_ar": f"كلية الحوسبة التطبيقية {tag}"})
    r.call("POST", "/skills", pa, 201, json={"name_en": f"Dry Run Skill {tag}", "name_ar": f"مهارة تجريبية {tag}"})
    step(1, "Platform Admin added a college and a skill")

    # 2. A coordinator registers; the Platform Admin approves
    co_email = f"coord.{tag}@iau.edu.sa"
    reg = r.call("POST", "/auth/register", None, 201, data={
        "kind": "coordinator", "email": co_email, "password": PASS, "name_en": "Dr. Dry Run", "name_ar": "د. تجربة",
        "college_id": college["id"]},
        files={"appointment_letter": ("letter.pdf", pdf("Appointment"), "application/pdf")})
    r.call("POST", "/auth/email/confirm", json={"token": r.link(co_email)})
    r.call("POST", f"/verification-requests/{reg['verification']['request_id']}/approve", pa, json={})
    step(2, "coordinator registered, confirmed the email, and was approved")

    # 3. The coordinator opens a 12-week Co-op cycle with weights and a rubric and invites a supervisor
    co = r.login(co_email)
    today = date.today()
    start = today - timedelta(days=today.isoweekday() % 7)
    end = start + timedelta(days=83)
    cycle = r.call("POST", "/cycles", co, 201, json={
        "name": f"Co-op {tag}", "type": "coop", "start_date": str(start), "end_date": str(end), "weeks": 12,
        "report_weekday": 4, "report_time": "23:59:00",
        "periodic_eval_due_at": f"{start + timedelta(weeks=6)}T20:59:00Z",
        "final_eval_due_at": f"{end + timedelta(days=5)}T20:59:00Z",
        "final_report_due_at": f"{end + timedelta(days=5)}T20:59:00Z"})
    r.call("PUT", f"/cycles/{cycle['id']}/grade-components", co, json={"components": [
        {"name_en": "Company evaluation", "name_ar": "تقييم الجهة", "weight": 40, "source": "company_final_evaluation"},
        {"name_en": "Weekly reports", "name_ar": "التقارير", "weight": 30, "source": "academic_supervisor"},
        {"name_en": "Final report", "name_ar": "التقرير النهائي", "weight": 30, "source": "academic_supervisor"}]})
    levels = {str(n): {"en": f"Level {n}", "ar": f"مستوى {n}"} for n in range(1, 6)}
    r.call("PUT", f"/cycles/{cycle['id']}/rubric", co, json={"criteria": [
        {"name_en": "Technical skills", "name_ar": "المهارات التقنية", "levels": levels}]})
    as_email = f"as.{tag}@iau.edu.sa"
    r.call("POST", f"/colleges/{college['id']}/invitations", co, 201,
           json={"email": as_email, "name_en": "Dr. Reviewer", "name_ar": "د. مراجع"})
    r.call("POST", "/auth/invitations/accept", json={"token": r.link(as_email), "password": PASS})
    step(3, f"12-week cycle with {len(cycle['week_list'])} deadlines, weights 40/30/30, rubric; supervisor joined")

    # 4. A company registers and is approved; the Company Admin invites a colleague and publishes a vacancy
    ca_email = f"hr.{tag}@company.example.org"
    reg = r.call("POST", "/auth/register", None, 201, data={
        "kind": "company", "email": ca_email, "password": PASS, "name_en": "HR", "name_ar": "الموارد",
        "company_name": f"Dry Run Co {tag}", "commercial_reg_no": f"70{tag}0001", "city": "Dammam"},
        files={"commercial_registration": ("cr.pdf", pdf("CR"), "application/pdf"),
               "authorization_letter": ("auth.pdf", pdf("Authorization"), "application/pdf")})
    r.call("POST", "/auth/email/confirm", json={"token": r.link(ca_email)})
    r.call("POST", f"/verification-requests/{reg['verification']['request_id']}/approve", pa, json={})
    ca = r.login(ca_email)
    company_id = r.call("GET", "/me", ca)["organization"]["company_id"]
    mate = f"mate.{tag}@company.example.org"
    r.call("POST", f"/companies/{company_id}/invitations", ca, 201,
           json={"email": mate, "name_en": "Mate", "name_ar": "زميل"})
    r.call("POST", "/auth/invitations/accept", json={"token": r.link(mate), "password": PASS})
    major = next(m for m in r.call("GET", "/majors") if m["name_en"] == "Computer Science")
    python = r.call("GET", "/skills", ca, params={"q": "python"})["items"][0]
    vacancy = r.call("POST", "/vacancies", ca, 201, json={
        "title": f"Backend Trainee {tag}", "city": "Dammam", "description": "Python services with code review.",
        "training_type": "coop", "training_start": str(start), "training_end": str(end), "seats": 2,
        "application_deadline": (datetime.now(UTC) + timedelta(days=14)).isoformat(),
        "required_skill_ids": [python["id"]], "major_ids": [major["id"]], "target_university_ids": [uni["id"]],
        "publish": True})
    step(4, "company approved, colleague joined, vacancy published for the university")

    # 5. A student registers, confirms, sees pending, completes the profile, uploads a CV, confirms skills
    st_email = f"student.{tag}@iau.edu.sa"
    reg = r.call("POST", "/auth/register", None, 201, data={
        "kind": "student", "email": st_email, "password": PASS, "name_en": "Dry Run Student", "name_ar": "طالب تجربة",
        "college_id": college["id"], "student_number": f"9{tag}", "major_id": major["id"], "gpa": "4.20"},
        files={"course_registration": ("schedule.pdf", pdf("Schedule"), "application/pdf")})
    r.call("POST", "/auth/email/confirm", json={"token": r.link(st_email)})
    st = r.login(st_email)
    assert r.call("GET", "/me", st)["verification_status"] == "pending"
    r.call("PATCH", "/students/me/profile", st, json={"interests": ["Backend"], "level": 8})
    cv = r.call("POST", "/students/me/cvs", st, 201, files={"file": ("cv.pdf", pdf(
        "Computer science student. Skills: Python, SQL, Docker, Git and REST APIs with FastAPI."), "application/pdf")})
    found = cv["extracted_skills"]
    r.call("PUT", "/students/me/skills", st,
           json={"skills": [{"skill_id": s["id"], "source": "extracted"} for s in found]})
    step(5, f"student pending; CV read ({cv['text_status']}), {len(found)} skills suggested and confirmed")

    # 6. The coordinator approves and enrols; the student browses, filters, and applies
    r.call("POST", f"/verification-requests/{reg['verification']['request_id']}/approve", co,
           json={"cycle_id": cycle["id"]})
    listed = r.call("GET", "/vacancies", st, params={"q": tag, "training_type": "coop"})["items"]
    assert [v["id"] for v in listed] == [vacancy["id"]] and listed[0]["eligible"]
    application = r.call("POST", f"/vacancies/{vacancy['id']}/applications", st, 201)
    step(6, "student approved and enrolled; filtered list shows the vacancy; applied")

    # 7. The company accepts; the coordinator confirms the placement; report slots appear
    r.call("POST", f"/applications/{application['id']}/accept", ca)
    supervisors = r.call("GET", f"/colleges/{college['id']}/academic-supervisors", co)
    supervisor = next(s for s in supervisors if s["email"] == as_email)
    placement = r.call("POST", "/placements", co, 201, json={"application_id": application["id"],
                                                              "academic_supervisor_id": supervisor["id"]})
    slots = r.call("GET", f"/placements/{placement['id']}/report-slots", st)
    step(7, f"placement confirmed; {len(slots)} report slots")

    # 8. Week 1 late (clock moved), revision, resubmission, acceptance; week 2 closed as Missing
    week1, week2 = slots[0], slots[1]
    report = {"tasks_performed": "Login API", "learning": "Dependencies", "challenges": "Time zones",
              "next_week_plan": "Tests"}
    r.call("PUT", f"/report-slots/{week1['id']}/draft", st, json=report)
    due2 = datetime.fromisoformat(week2["due_at"])
    now = datetime.fromisoformat(r.call("GET", "/dev/clock")["now"])
    hours = max(0.0, (due2 - now).total_seconds() / 3600) + 1
    r.call("POST", "/dev/clock/advance", json={"hours": round(hours, 2)})
    st, sup = r.login(st_email), r.login(as_email)
    late = r.call("POST", f"/report-slots/{week1['id']}/submit", st)
    r.call("POST", f"/report-slots/{week1['id']}/request-revision", sup, json={"comment": "Add the test results"})
    r.call("PUT", f"/report-slots/{week1['id']}/draft", st, json={"challenges": "Time zones; tests pass now"})
    r.call("POST", f"/report-slots/{week1['id']}/submit", st)
    accepted = r.call("POST", f"/report-slots/{week1['id']}/accept", sup)
    closed = r.call("POST", f"/report-slots/{week2['id']}/close-missing", sup)
    r.call("POST", "/dev/clock/reset")
    assert late["is_late"] and accepted["status"] == "accepted" and len(accepted["submitted"]) == 2
    assert closed["status"] == "closed_missing"
    step(8, "week 1 late, revised, resubmitted (2 versions), accepted; week 2 closed as Missing")

    # 9. Language switch is saved per user
    st = r.login(st_email)
    assert r.call("PATCH", "/me", st, json={"language": "en"})["language"] == "en"
    assert r.call("PATCH", "/me", st, json={"language": "ar"})["language"] == "ar"
    step(9, "language switched to English and back, saved on the account")

    # 10. The coordinator finds every step in the audit log
    co = r.login(co_email)
    student_id = r.call("GET", "/me", st)["id"]
    trail = r.call("GET", "/audit-log", co, params={"student_id": student_id, "page_size": 100})["items"]
    actions = sorted({f"{e['entity_type']}:{e['action']}" for e in trail})
    step(10, f"audit log has {len(trail)} entries for the student: {', '.join(actions)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
