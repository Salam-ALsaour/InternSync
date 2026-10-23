"""The M3 demo scenario end to end through the HTTP API (01_Requirements Section 7) and AT-AUD-01: every step
leaves exactly one matching audit entry."""
from collections import Counter
from datetime import datetime, timedelta

from app.core import clock
from app.models import AuditEntry
from tests.conftest import last_link
from tests.factories import PNG, PW, docx, pdf

API = "/api/v1"
PASS = "Demo-pass-2026"


def sign_in(client, email, password=PASS):
    r = client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    if r.json()["user"]["consent_required"]:
        client.post(f"{API}/me/consent", headers=h)
    return h


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json()


def test_m3_demo_scenario_and_at_aud_01(client, f, db):
    uni = f.university("Imam Abdulrahman Bin Faisal University", ("iau.edu.sa",))
    major = f.major("Computer Science")
    python, sql = f.skill("Python", "بايثون"), f.skill("SQL", "إس كيو إل")
    pa_user = f.user("platform_admin", email="admin@internsync.example.org")
    f.commit()

    # 1. Platform Admin adds a college and a skill
    pa = sign_in(client, pa_user.email, PW)
    college = ok(client.post(f"{API}/universities/{uni.id}/colleges", headers=pa,
                             json={"name_en": "College of Computing", "name_ar": "كلية الحاسب"}), 201)
    ok(client.post(f"{API}/skills", headers=pa, json={"name_en": "FastAPI", "name_ar": "فاست إيه بي آي"}), 201)

    # 2. A coordinator registers with an appointment letter; the Platform Admin approves
    r = ok(client.post(f"{API}/auth/register", data={
        "kind": "coordinator", "email": "huda@iau.edu.sa", "password": PASS, "name_en": "Dr. Huda",
        "name_ar": "د. هدى", "college_id": college["id"]},
        files={"appointment_letter": ("letter.png", PNG, "image/png")}), 201)
    ok(client.post(f"{API}/auth/email/confirm", json={"token": last_link("huda@iau.edu.sa")}))
    ok(client.post(f"{API}/verification-requests/{r['verification']['request_id']}/approve", headers=pa, json={}))

    # 3. The coordinator opens a 12-week Co-op cycle with weights and a rubric and invites a supervisor
    co = sign_in(client, "huda@iau.edu.sa")
    start = clock.today_riyadh() - timedelta(days=clock.today_riyadh().isoweekday() % 7)
    end = start + timedelta(days=83)
    cycle = ok(client.post(f"{API}/cycles", headers=co, json={
        "name": "Co-op Fall 2026", "type": "coop", "start_date": str(start), "end_date": str(end), "weeks": 12,
        "report_weekday": 4, "report_time": "23:59:00",
        "periodic_eval_due_at": f"{start + timedelta(weeks=6)}T20:59:00Z",
        "final_eval_due_at": f"{end + timedelta(days=5)}T20:59:00Z",
        "final_report_due_at": f"{end + timedelta(days=5)}T20:59:00Z"}), 201)
    assert len(cycle["week_list"]) == 12
    ok(client.put(f"{API}/cycles/{cycle['id']}/grade-components", headers=co, json={"components": [
        {"name_en": "Company evaluation", "name_ar": "تقييم الجهة", "weight": 40, "source": "company_final_evaluation"},
        {"name_en": "Weekly reports", "name_ar": "التقارير", "weight": 30, "source": "academic_supervisor"},
        {"name_en": "Final report", "name_ar": "التقرير النهائي", "weight": 30, "source": "academic_supervisor"}]}))
    levels = {str(n): {"en": f"Level {n}", "ar": f"مستوى {n}"} for n in range(1, 6)}
    ok(client.put(f"{API}/cycles/{cycle['id']}/rubric", headers=co, json={"criteria": [
        {"name_en": "Technical skills", "name_ar": "المهارات التقنية", "levels": levels}]}))
    ok(client.post(f"{API}/colleges/{college['id']}/invitations", headers=co,
                   json={"email": "faisal@iau.edu.sa", "name_en": "Dr. Faisal", "name_ar": "د. فيصل"}), 201)
    ok(client.post(f"{API}/auth/invitations/accept", json={"token": last_link("faisal@iau.edu.sa"),
                                                           "password": PASS}))

    # 4. A company registers; the Platform Admin approves; the Company Admin invites a colleague and publishes
    r = ok(client.post(f"{API}/auth/register", data={
        "kind": "company", "email": "sara@nakheel.example.org", "password": PASS, "name_en": "Sara",
        "name_ar": "سارة", "company_name": "Nakheel Digital", "commercial_reg_no": "2050123456", "city": "Dammam"},
        files={"commercial_registration": ("cr.pdf", pdf("CR"), "application/pdf"),
               "authorization_letter": ("auth.pdf", pdf("Authorization"), "application/pdf")}), 201)
    ok(client.post(f"{API}/auth/email/confirm", json={"token": last_link("sara@nakheel.example.org")}))
    ok(client.post(f"{API}/verification-requests/{r['verification']['request_id']}/approve", headers=pa, json={}))
    ca = sign_in(client, "sara@nakheel.example.org")
    company_id = ok(client.get(f"{API}/me", headers=ca))["organization"]["company_id"]
    ok(client.post(f"{API}/companies/{company_id}/invitations", headers=ca,
                   json={"email": "omar@nakheel.example.org", "name_en": "Omar", "name_ar": "عمر"}), 201)
    ok(client.post(f"{API}/auth/invitations/accept", json={"token": last_link("omar@nakheel.example.org"),
                                                           "password": PASS}))
    vacancy = ok(client.post(f"{API}/vacancies", headers=ca, json={
        "title": "Backend Trainee", "city": "Dammam", "description": "Python services with code review.",
        "training_type": "coop", "training_start": str(start), "training_end": str(end), "seats": 2,
        "application_deadline": (clock.now() + timedelta(days=14)).isoformat(), "required_skill_ids": [str(python.id)],
        "preferred_skill_ids": [str(sql.id)], "major_ids": [str(major.id)], "target_university_ids": [str(uni.id)],
        "publish": True}), 201)
    assert vacancy["status"] == "published"

    # 5. A student registers, confirms the email, sees the pending status, completes the profile, uploads a CV
    r = ok(client.post(f"{API}/auth/register", data={
        "kind": "student", "email": "abdullah@iau.edu.sa", "password": PASS, "name_en": "Abdullah",
        "name_ar": "عبدالله", "college_id": college["id"], "student_number": "2210001", "major_id": str(major.id),
        "gpa": "4.20"}, files={"course_registration": ("schedule.pdf", pdf("Schedule"), "application/pdf")}), 201)
    student_request = r["verification"]["request_id"]
    ok(client.post(f"{API}/auth/email/confirm", json={"token": last_link("abdullah@iau.edu.sa")}))
    st = sign_in(client, "abdullah@iau.edu.sa")
    assert ok(client.get(f"{API}/me", headers=st))["verification_status"] == "pending"
    ok(client.patch(f"{API}/students/me/profile", headers=st, json={"interests": ["Backend"], "level": 8}))
    cv = ok(client.post(f"{API}/students/me/cvs", headers=st, files={"file": (
        "cv.docx", docx("Computer science student at the College of Computing.", "Skills: Python, SQL and FastAPI."),
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}), 201)
    extracted = cv["extracted_skills"]
    assert {s["name_en"] for s in extracted} == {"Python", "SQL", "FastAPI"}
    ok(client.put(f"{API}/students/me/skills", headers=st,
                  json={"skills": [{"skill_id": s["id"], "source": "extracted"} for s in extracted]}))

    # 6. The coordinator approves and enrols the student; the student browses, filters, and applies
    ok(client.post(f"{API}/verification-requests/{student_request}/approve", headers=co,
                   json={"cycle_id": cycle["id"]}))
    found = ok(client.get(f"{API}/vacancies?city=Dammam&training_type=coop", headers=st))["items"]
    assert [v["id"] for v in found] == [vacancy["id"]] and found[0]["eligible"] is True
    application = ok(client.post(f"{API}/vacancies/{vacancy['id']}/applications", headers=st), 201)

    # 7. The company accepts; the coordinator confirms the placement; report slots appear
    ok(client.post(f"{API}/applications/{application['id']}/accept", headers=ca))
    candidate = ok(client.get(f"{API}/placements/candidates", headers=co))[0]
    faisal = next(s for s in ok(client.get(f"{API}/colleges/{college['id']}/academic-supervisors", headers=co))
                  if s["email"] == "faisal@iau.edu.sa")
    placement = ok(client.post(f"{API}/placements", headers=co, json={
        "application_id": candidate["application_id"], "academic_supervisor_id": faisal["id"]}), 201)
    slots = ok(client.get(f"{API}/placements/{placement['id']}/report-slots", headers=st))
    assert len(slots) == 13
    week1, week2 = slots[0], slots[1]

    # 8. Week 1 late (clock moved), revision, resubmission, acceptance; week 2 closed as Missing
    report = {"tasks_performed": "Login API", "learning": "Dependencies", "challenges": "Time zones",
              "next_week_plan": "Tests"}
    ok(client.put(f"{API}/report-slots/{week1['id']}/draft", headers=st, json=report))
    clock.freeze(datetime.fromisoformat(week2["due_at"]) + timedelta(hours=1))  # both deadlines have passed
    st, sup, co = sign_in(client, "abdullah@iau.edu.sa"), sign_in(client, "faisal@iau.edu.sa"), \
        sign_in(client, "huda@iau.edu.sa")
    submitted = ok(client.post(f"{API}/report-slots/{week1['id']}/submit", headers=st))
    assert submitted["is_late"] is True
    ok(client.post(f"{API}/report-slots/{week1['id']}/request-revision", headers=sup,
                   json={"comment": "Add the test results"}))
    ok(client.put(f"{API}/report-slots/{week1['id']}/draft", headers=st,
                  json={"challenges": "Time zones; tests now pass"}))
    ok(client.post(f"{API}/report-slots/{week1['id']}/submit", headers=st))
    accepted = ok(client.post(f"{API}/report-slots/{week1['id']}/accept", headers=sup))
    assert accepted["status"] == "accepted" and len(accepted["submitted"]) == 2
    closed = ok(client.post(f"{API}/report-slots/{week2['id']}/close-missing", headers=sup))
    assert closed["status"] == "closed_missing"

    # 9. Language switch is saved per user
    assert ok(client.patch(f"{API}/me", headers=st, json={"language": "en"}))["language"] == "en"
    assert ok(client.patch(f"{API}/me", headers=st, json={"language": "ar"}))["language"] == "ar"

    # 10. The coordinator finds every step for the student in the audit log
    student_id = ok(client.get(f"{API}/me", headers=st))["id"]
    trail = ok(client.get(f"{API}/audit-log?page_size=100&student_id={student_id}", headers=co))["items"]
    actions = Counter((e["entity_type"], e["action"]) for e in trail)
    for step in [("user", "register"), ("verification_request", "submit"), ("student_profile", "update"),
                 ("cv", "upload_cv"), ("student_profile", "confirm_skills"), ("verification_request", "approve"),
                 ("application", "apply"), ("application", "accept"), ("placement", "confirm"),
                 ("report_slot", "request_revision"), ("report_slot", "accept"), ("report_slot", "close_missing")]:
        assert actions[step] == 1, step
    assert actions[("report_slot", "submit")] == 2

    # AT-AUD-01: platform-level steps are recorded once each
    def count(action, entity_type):
        return db.query(AuditEntry).filter_by(action=action, entity_type=entity_type).count()
    assert count("create", "college") == 1 and count("create", "skill") == 1
    assert count("approve", "verification_request") == 3
    assert count("create", "training_cycle") == 1 and count("replace_components", "training_cycle") == 1
    assert count("replace_rubric", "training_cycle") == 1 and count("accept_invitation", "user") == 2
    assert count("create", "vacancy") == 1 and count("publish", "vacancy") == 1
