"""Universities, colleges, companies, verification, invitations (AT-ORG-01 – 06, AT-ORG-08, AT-ORG-09)."""
from datetime import timedelta

from app.core import clock
from app.core.db import SessionLocal
from app.jobs import jobs
from app.models import Enrollment, User, VerificationDocument, VerificationRequest
from tests.conftest import last_link
from tests.factories import PNG, pdf
from tests.test_auth import register_student

API = "/api/v1"


def register_coordinator(client, college, email="coord@iau.edu.sa"):
    return client.post(f"{API}/auth/register",
                       data={"kind": "coordinator", "email": email, "password": "Strong-pass-1", "name_en": "Coord",
                             "name_ar": "منسق", "college_id": str(college.id)},
                       files={"appointment_letter": ("letter.png", PNG, "image/png")})


def register_company(client, reg_no="4030111111", email="hr@acme.example.org"):
    return client.post(f"{API}/auth/register",
                       data={"kind": "company", "email": email, "password": "Strong-pass-1", "name_en": "HR",
                             "name_ar": "الموارد", "company_name": "Acme", "commercial_reg_no": reg_no,
                             "city": "Riyadh"},
                       files={"commercial_registration": ("cr.pdf", pdf("CR"), "application/pdf"),
                              "authorization_letter": ("auth.pdf", pdf("Auth"), "application/pdf")})


# ---------------------------------------------------------------- AT-ORG-01
def test_at_org_01_new_college_appears_and_deactivated_does_not(client, w, f):
    pa = f.headers(w.pa)
    r = client.post(f"{API}/universities/{w.uniA.id}/colleges", headers=pa,
                    json={"name_en": "College of Business", "name_ar": "كلية إدارة الأعمال"})
    assert r.status_code == 201, r.text
    new_id = r.json()["id"]
    names = [c["id"] for u in client.get(f"{API}/universities").json() for c in u["colleges"]]
    assert new_id in names
    assert client.post(f"{API}/universities/{w.uniA.id}/colleges", headers=pa,
                       json={"name_en": "college of business", "name_ar": "مكرر"}).json()["code"] == "DUPLICATE_NAME"
    assert client.patch(f"{API}/colleges/{new_id}", headers=pa, json={"is_active": False}).status_code == 200
    names = [c["id"] for u in client.get(f"{API}/universities").json() for c in u["colleges"]]
    assert new_id not in names
    admin_view = client.get(f"{API}/admin/universities", headers=pa).json()
    assert new_id in [c["id"] for u in admin_view for c in u["colleges"]]


def test_university_crud_and_scale(client, w, f):
    pa = f.headers(w.pa)
    r = client.post(f"{API}/universities", headers=pa, json={"name_en": "Qassim University",
                                                              "name_ar": "جامعة القصيم", "gpa_scale": "4.00",
                                                              "email_domains": ["qu.edu.sa"]})
    assert r.status_code == 201 and r.json()["gpa_scale"] == "4.00"
    bad = client.post(f"{API}/universities", headers=pa, json={"name_en": "X Uni", "name_ar": "س",
                                                                "gpa_scale": "10"})
    assert bad.status_code == 422
    uid = r.json()["id"]
    assert client.patch(f"{API}/universities/{uid}", headers=pa, json={"is_active": False}).json()["is_active"] is False
    assert uid not in [u["id"] for u in client.get(f"{API}/universities").json()]


def test_registration_refused_for_inactive_college(client, w, f, db):
    w.A2.is_active = False
    db.commit()
    r = register_coordinator(client, w.A2, "c2@iau.edu.sa")
    assert r.status_code == 422 and r.json()["errors"][0]["field"] == "college_id"


# ---------------------------------------------------------------- AT-ORG-02
def test_at_org_02_unverified_accounts_are_limited(client, w, f, db):
    pending_student = f.student(w.A1, w.cs_major, status="pending")
    pending_coord = f.user("coordinator", college=f.college(w.uniA), status="pending")
    pending_company = f.company(status="pending")
    pending_cs = f.user("company_supervisor", company=pending_company, status="pending")
    db.commit()
    r = client.post(f"{API}/vacancies/{w.vac.id}/applications", headers=f.headers(pending_student))
    assert r.status_code == 403 and r.json()["code"] == "VERIFICATION_REQUIRED"
    r = client.get(f"{API}/verification-requests", headers=f.headers(pending_coord))
    assert r.status_code == 403 and r.json()["code"] == "VERIFICATION_REQUIRED"
    r = client.post(f"{API}/vacancies", headers=f.headers(pending_cs), json={})
    assert r.status_code == 403 and r.json()["code"] == "VERIFICATION_REQUIRED"
    # the pending student can still read the profile, see the status, and browse
    h = f.headers(pending_student)
    assert client.get(f"{API}/me/verification", headers=h).status_code == 200
    assert client.get(f"{API}/students/me/profile", headers=h).status_code == 200
    assert client.get(f"{API}/vacancies", headers=h).status_code == 200


# ---------------------------------------------------------------- AT-ORG-03
def test_at_org_03_one_coordinator_per_college(client, w, f, db):
    r = register_coordinator(client, w.A1, "second@iau.edu.sa")
    assert r.status_code == 409 and r.json()["code"] == "COLLEGE_HAS_COORDINATOR"
    college = f.college(w.uniA, "College of Law")
    db.commit()
    first, second = register_coordinator(client, college, "c1@iau.edu.sa"), register_coordinator(client, college,
                                                                                                "c2@iau.edu.sa")
    assert first.status_code == second.status_code == 201
    pa = f.headers(w.pa)
    r1, r2 = first.json()["verification"]["request_id"], second.json()["verification"]["request_id"]
    assert client.post(f"{API}/verification-requests/{r1}/reject", headers=pa, json={"reason": " "}).json()["code"] \
        == "REASON_REQUIRED"
    assert client.post(f"{API}/verification-requests/{r1}/approve", headers=pa, json={}).status_code == 200
    r = client.post(f"{API}/verification-requests/{r2}/approve", headers=pa, json={})
    assert r.status_code == 409 and r.json()["code"] == "COLLEGE_HAS_COORDINATOR"
    assert client.post(f"{API}/verification-requests/{r2}/reject", headers=pa,
                       json={"reason": "The college already has a coordinator"}).status_code == 200


# ---------------------------------------------------------------- AT-ORG-04
def test_at_org_04_company_verification(client, w, f, db):
    r = register_company(client)
    assert r.status_code == 201, r.text
    assert register_company(client, email="other@acme.example.org").json()["code"] == "DUPLICATE_COMMERCIAL_REG"
    user = db.query(User).filter_by(email="hr@acme.example.org").one()
    client.post(f"{API}/auth/email/confirm", json={"token": last_link("hr@acme.example.org")})
    h = f.headers(user)
    client.post(f"{API}/me/consent", headers=h)
    assert client.post(f"{API}/vacancies", headers=h, json={}).status_code == 403
    assert client.post(f"{API}/companies/{user.company_id}/invitations", headers=h,
                       json={"email": "a@acme.example.org", "name_en": "Ali", "name_ar": "علي"}).status_code == 403
    req = r.json()["verification"]["request_id"]
    detail = client.get(f"{API}/verification-requests/{req}", headers=f.headers(w.pa)).json()
    assert detail["company"]["commercial_reg_no"] == "4030111111" and len(detail["documents"]) == 2
    assert client.post(f"{API}/verification-requests/{req}/approve", headers=f.headers(w.pa), json={}).status_code \
        == 200
    db.expire_all()
    me = client.get(f"{API}/me", headers=h).json()
    assert me["is_company_admin"] is True and me["organization"]["company_status"] == "verified"
    r = client.post(f"{API}/companies/{user.company_id}/invitations", headers=h,
                    json={"email": "a@acme.example.org", "name_en": "Ali", "name_ar": "علي"})
    assert r.status_code == 201 and r.json()["invitation_pending"] is True


def test_company_suspend_and_reactivate(client, w, f):
    pa = f.headers(w.pa)
    assert client.post(f"{API}/companies/{w.co1.id}/suspend", headers=pa, json={"reason": ""}).status_code == 422
    r = client.post(f"{API}/companies/{w.co1.id}/suspend", headers=pa, json={"reason": "Expired registration"})
    assert r.json()["status"] == "suspended"
    assert client.post(f"{API}/vacancies", headers=f.headers(w.cs1), json={
        "title": "Trainee", "city": "Dammam", "description": "A useful vacancy text", "training_type": "coop",
        "training_start": "2026-11-01", "training_end": "2027-01-01", "seats": 1,
        "application_deadline": "2026-10-30T00:00:00Z", "major_ids": [str(w.cs_major.id)]}).json()["code"] \
        == "COMPANY_NOT_VERIFIED"
    assert client.post(f"{API}/companies/{w.co1.id}/reactivate", headers=pa).json()["status"] == "verified"


def test_company_admin_edits_own_company_only(client, w, f):
    assert client.patch(f"{API}/companies/{w.co1.id}", headers=f.headers(w.ca1),
                        json={"city": "Khobar"}).json()["city"] == "Khobar"
    assert client.patch(f"{API}/companies/{w.co2.id}", headers=f.headers(w.ca1),
                        json={"city": "Khobar"}).status_code == 403
    assert client.patch(f"{API}/companies/{w.co1.id}", headers=f.headers(w.cs1),
                        json={"city": "Khobar"}).status_code == 403


# ---------------------------------------------------------------- AT-ORG-05
def test_at_org_05_student_verification_enrols(client, w, f, db):
    r = register_student(client, w)
    req = r.json()["verification"]["request_id"]
    student = db.query(User).filter_by(email="new.student@iau.edu.sa").one()
    client.post(f"{API}/auth/email/confirm", json={"token": last_link()})
    co = f.headers(w.coA1)
    listed = client.get(f"{API}/verification-requests?status=pending", headers=co).json()
    assert [x["id"] for x in listed["items"]] == [req]
    assert listed["items"][0]["applicant"]["email_matches_university_domain"] is True
    assert client.get(f"{API}/verification-requests", headers=f.headers(w.coA2)).json()["items"] == []
    assert client.get(f"{API}/verification-requests/{req}", headers=f.headers(w.coA2)).status_code == 403
    assert client.post(f"{API}/verification-requests/{req}/approve", headers=f.headers(w.coA2),
                       json={"cycle_id": str(w.cycle.id)}).status_code == 403
    assert client.post(f"{API}/verification-requests/{req}/reject", headers=co, json={"reason": ""}).status_code \
        == 422
    assert client.post(f"{API}/verification-requests/{req}/approve", headers=co, json={}).json()["code"] \
        == "CYCLE_NOT_OPEN"
    r = client.post(f"{API}/verification-requests/{req}/approve", headers=co, json={"cycle_id": str(w.cycle.id)})
    assert r.status_code == 200 and r.json()["status"] == "approved"
    assert db.get(Enrollment, (w.cycle.id, student.id)) is not None
    h = f.headers(student)
    client.post(f"{API}/me/consent", headers=h)
    assert client.post(f"{API}/vacancies/{w.vac.id}/applications", headers=h).status_code == 201


def test_student_request_waits_without_open_cycle(client, w, f, db):
    """RQ-2: with no open cycle the request stays pending and is flagged."""
    college = f.college(w.uniA, "College of Science")
    f.user("coordinator", college=college)
    db.commit()
    r = register_student(client, w, college_id=str(college.id))
    req = r.json()["verification"]["request_id"]
    co = db.query(User).filter_by(college_id=college.id, role="coordinator").one()
    detail = client.get(f"{API}/verification-requests/{req}", headers=f.headers(co)).json()
    assert detail["status"] == "pending" and detail["no_open_cycle"] is True


# ---------------------------------------------------------------- AT-ORG-06
def test_at_org_06_invited_supervisor_joins_the_college(client, w, f, db):
    co = f.headers(w.coA1)
    r = client.post(f"{API}/colleges/{w.A1.id}/invitations", headers=co,
                    json={"email": "new.as@iau.edu.sa", "name_en": "Dr. New", "name_ar": "د. جديد"})
    assert r.status_code == 201, r.text
    assert client.post(f"{API}/colleges/{w.A2.id}/invitations", headers=co,
                       json={"email": "x@iau.edu.sa", "name_en": "Dr. X", "name_ar": "د. س"}).status_code == 403
    token = last_link("new.as@iau.edu.sa")
    check = client.get(f"{API}/auth/tokens/{token}").json()
    assert check["purpose"] == "invitation" and check["email"] == "new.as@iau.edu.sa"
    assert client.post(f"{API}/auth/invitations/accept", json={"token": token, "password": "Strong-pass-1"}) \
        .status_code == 200
    assert client.post(f"{API}/auth/invitations/accept", json={"token": token, "password": "Strong-pass-2"}) \
        .status_code == 410
    user = db.query(User).filter_by(email="new.as@iau.edu.sa").one()
    assert user.role == "academic_supervisor" and user.college_id == w.A1.id
    sups = client.get(f"{API}/colleges/{w.A1.id}/academic-supervisors", headers=co).json()
    assert "new.as@iau.edu.sa" in [s["email"] for s in sups]


def test_at_org_06_expired_invitation_and_resend(client, w, f, db):
    co = f.headers(w.coA1)
    r = client.post(f"{API}/colleges/{w.A1.id}/invitations", headers=co,
                    json={"email": "late.as@iau.edu.sa", "name_en": "Dr. Late", "name_ar": "د. متأخر"})
    uid = r.json()["id"]
    old = last_link("late.as@iau.edu.sa")
    clock.advance(timedelta(hours=73))
    assert client.post(f"{API}/auth/invitations/accept", json={"token": old, "password": "Strong-pass-1"}) \
        .json()["code"] == "TOKEN_EXPIRED"
    assert client.post(f"{API}/users/{uid}/invitation/resend", headers=f.headers(w.coA1)).status_code == 200
    new = last_link("late.as@iau.edu.sa")
    assert client.post(f"{API}/auth/invitations/accept", json={"token": new, "password": "Strong-pass-1"}) \
        .status_code == 200


def test_company_admin_invites_colleague(client, w, f, db):
    r = client.post(f"{API}/companies/{w.co1.id}/invitations", headers=f.headers(w.ca1),
                    json={"email": "mona@nakheel.example.org", "name_en": "Mona", "name_ar": "منى"})
    assert r.status_code == 201
    assert client.post(f"{API}/companies/{w.co2.id}/invitations", headers=f.headers(w.ca1),
                       json={"email": "y@x.example.org", "name_en": "Yasir", "name_ar": "ياسر"}).status_code == 403
    assert client.post(f"{API}/companies/{w.co1.id}/invitations", headers=f.headers(w.cs1),
                       json={"email": "z@x.example.org", "name_en": "Zaid", "name_ar": "زيد"}).status_code == 403
    team = client.get(f"{API}/companies/{w.co1.id}/supervisors", headers=f.headers(w.ca1)).json()
    assert {m["email"] for m in team} >= {w.ca1.email, w.cs1.email, "mona@nakheel.example.org"}


def test_invitation_to_existing_email_refused(client, w, f):
    r = client.post(f"{API}/colleges/{w.A1.id}/invitations", headers=f.headers(w.coA1),
                    json={"email": w.stA.email, "name_en": "Dup", "name_ar": "مكرر"})
    assert r.status_code == 409 and r.json()["code"] == "EMAIL_TAKEN"


# ---------------------------------------------------------------- AT-ORG-08
def test_at_org_08_document_access_and_purge(client, w, f, db):
    r = register_student(client, w)
    req_id = r.json()["verification"]["request_id"]
    student = db.query(User).filter_by(email="new.student@iau.edu.sa").one()
    doc = db.query(VerificationDocument).filter_by(request_id=req_id).one()
    assert client.get(f"{API}/files/{doc.file_id}", headers=f.headers(w.coA1)).status_code == 200
    assert client.get(f"{API}/files/{doc.file_id}", headers=f.headers(w.coA2)).status_code == 403
    assert client.get(f"{API}/files/{doc.file_id}", headers=f.headers(w.ca1)).status_code == 403
    client.post(f"{API}/verification-requests/{req_id}/approve", headers=f.headers(w.coA1),
                json={"cycle_id": str(w.cycle.id)})
    clock.advance(timedelta(days=29))
    jobs.run(SessionLocal, "purge_verification_documents")
    assert client.get(f"{API}/files/{doc.file_id}", headers=f.headers(w.coA1)).status_code == 200
    clock.advance(timedelta(days=2))
    jobs.run(SessionLocal, "purge_verification_documents")
    r = client.get(f"{API}/files/{doc.file_id}", headers=f.headers(w.coA1))
    assert r.status_code == 410 and r.json()["code"] == "FILE_PURGED"
    db.expire_all()
    assert db.get(VerificationRequest, req_id).status == "approved"
    detail = client.get(f"{API}/verification-requests/{req_id}", headers=f.headers(w.coA1)).json()
    assert detail["documents"][0]["purged"] is True
    h = f.headers(student)
    client.post(f"{API}/me/consent", headers=h)
    assert client.get(f"{API}/me/verification", headers=h).json()[0]["status"] == "approved"


# ---------------------------------------------------------------- AT-ORG-09
def test_at_org_09_resubmission_after_rejection(client, w, f, db):
    r = register_student(client, w)
    req = r.json()["verification"]["request_id"]
    student = db.query(User).filter_by(email="new.student@iau.edu.sa").one()
    h = f.headers(student)
    client.post(f"{API}/me/consent", headers=h)
    assert client.post(f"{API}/me/verification", headers=h, data={}).json()["code"] == "INVALID_TRANSITION"
    client.post(f"{API}/verification-requests/{req}/reject", headers=f.headers(w.coA1),
                json={"reason": "The schedule is unreadable"})
    mine = client.get(f"{API}/me/verification", headers=h).json()
    assert mine[0]["status"] == "rejected" and mine[0]["reason"] == "The schedule is unreadable"
    clock.advance(timedelta(days=1))
    h = f.headers(student)
    r = client.post(f"{API}/me/verification", headers=h, data={"gpa": "4.30"},
                    files={"course_registration": ("schedule2.pdf", pdf("Clear schedule"), "application/pdf")})
    assert r.status_code == 201, r.text
    assert r.json()[0]["status"] == "pending" and r.json()[0]["submitted_data"]["gpa"] == "4.30"
    pending = client.get(f"{API}/verification-requests?status=pending", headers=f.headers(w.coA1)).json()["items"]
    assert pending[0]["earlier_decisions"][0]["reason"] == "The schedule is unreadable"


# ---------------------------------------------------------------- accounts
def test_users_list_is_scoped(client, w, f):
    emails = {u["email"] for u in client.get(f"{API}/users?page_size=100", headers=f.headers(w.coA1)).json()["items"]}
    assert w.stA.email in emails and w.asA1.email in emails and w.stB.email not in emails
    emails = {u["email"] for u in client.get(f"{API}/users", headers=f.headers(w.ca1)).json()["items"]}
    assert emails == {w.ca1.email, w.cs1.email}
    assert client.get(f"{API}/users/{w.stA.id}", headers=f.headers(w.ca1)).status_code == 403


def test_company_admin_cannot_deactivate_self_or_other_company(client, w, f):
    assert client.post(f"{API}/users/{w.ca1.id}/deactivate", headers=f.headers(w.ca1)).status_code in (403, 409)
    assert client.post(f"{API}/users/{w.ca2.id}/deactivate", headers=f.headers(w.ca1)).status_code == 403
    assert client.post(f"{API}/users/{w.cs1.id}/deactivate", headers=f.headers(w.ca1)).status_code == 200


def test_college_detail(client, w, f):
    r = client.get(f"{API}/colleges/{w.A1.id}", headers=f.headers(w.coA1)).json()
    assert r["coordinator"]["email"] == w.coA1.email and r["verified_students"] == 2
    assert client.get(f"{API}/colleges/{w.A2.id}", headers=f.headers(w.coA1)).status_code == 403
