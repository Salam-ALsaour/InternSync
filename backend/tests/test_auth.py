"""Authentication, registration, sessions, and consent (AT-AUT-01 – 04, AT-AUT-06, NFR-SEC-02/03)."""
from datetime import timedelta

from app.core import clock
from app.core.i18n import MESSAGES
from app.models import AuditEntry, User, VerificationRequest
from tests.conftest import last_link
from tests.factories import PNG, PW, pdf

API = "/api/v1"


def login(client, email, password=PW):
    return client.post(f"{API}/auth/login", json={"email": email, "password": password})


def register_student(client, w, email="new.student@iau.edu.sa", number="2299001", **extra):
    data = {"kind": "student", "email": email, "password": "Strong-pass-1", "name_en": "New Student",
            "name_ar": "طالب جديد", "college_id": str(w.A1.id), "student_number": number,
            "major_id": str(w.cs_major.id), "gpa": "4.10", "level": "7", **extra}
    return client.post(f"{API}/auth/register", data=data,
                       files={"course_registration": ("schedule.pdf", pdf("Course registration"), "application/pdf")})


# ---------------------------------------------------------------- AT-AUT-01
def test_at_aut_01_each_role_logs_in_with_its_role(client, w):
    for user, role, is_ca in [(w.pa, "platform_admin", False), (w.coA1, "coordinator", False),
                              (w.asA1, "academic_supervisor", False), (w.ca1, "company_supervisor", True),
                              (w.cs1, "company_supervisor", False), (w.stA, "student", False)]:
        r = login(client, user.email)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["user"]["role"] == role and body["user"]["is_company_admin"] is is_ca
        assert body["idle_timeout_minutes"] == 30
        me = client.get(f"{API}/me", headers={"Authorization": f"Bearer {body['access_token']}"})
        assert me.json().get("id") == str(user.id), me.text


def test_wrong_password_and_unknown_email_get_the_same_answer(client, w):
    a, b = login(client, w.stA.email, "wrong-pass-1"), login(client, "nobody@iau.edu.sa", "wrong-pass-1")
    assert a.status_code == b.status_code == 401
    assert a.json()["code"] == b.json()["code"] == "INVALID_CREDENTIALS"


def test_lockout_after_five_failures(client, w):
    for _ in range(5):
        login(client, w.stA.email, "wrong-pass-1")
    r = login(client, w.stA.email)
    assert r.status_code == 423 and r.json()["code"] == "ACCOUNT_LOCKED"
    clock.advance(timedelta(minutes=16))
    assert login(client, w.stA.email).status_code == 200


# ---------------------------------------------------------------- AT-AUT-02
def test_at_aut_02_registration_kinds_and_single_use_confirmation(client, w, db):
    r = client.post(f"{API}/auth/register", data={"kind": "academic_supervisor", "email": "x@iau.edu.sa",
                                                  "password": "Strong-pass-1", "name_en": "X", "name_ar": "س"})
    assert r.status_code == 422
    r = register_student(client, w)
    assert r.status_code == 201, r.text
    assert r.json()["verification"]["reviewer"] == "coordinator"
    assert login(client, "new.student@iau.edu.sa", "Strong-pass-1").json()["code"] == "EMAIL_NOT_CONFIRMED"
    token = last_link("new.student@iau.edu.sa")
    assert client.get(f"{API}/auth/tokens/{token}").json() == {"purpose": "email_confirmation", "valid": True,
                                                                "reason": None, "email": None, "name_en": None,
                                                                "name_ar": None}
    assert client.post(f"{API}/auth/email/confirm", json={"token": token}).status_code == 200
    again = client.post(f"{API}/auth/email/confirm", json={"token": token})
    assert again.status_code == 410 and again.json()["code"] == "TOKEN_USED"
    assert client.post(f"{API}/auth/email/confirm", json={"token": "x" * 40}).status_code == 400
    r = login(client, "new.student@iau.edu.sa", "Strong-pass-1")
    assert r.status_code == 200 and r.json()["user"]["verification_status"] == "pending"


def test_at_aut_02_expired_confirmation_link(client, w):
    register_student(client, w)
    token = last_link()
    clock.advance(timedelta(hours=73))
    r = client.post(f"{API}/auth/email/confirm", json={"token": token})
    assert r.status_code == 410 and r.json()["code"] == "TOKEN_EXPIRED"
    assert client.get(f"{API}/auth/tokens/{token}").json()["reason"] == "expired"


def test_registration_checks(client, w):
    assert register_student(client, w, email="bad").json()["errors"][0]["field"] == "email"
    assert register_student(client, w).status_code == 201
    r = register_student(client, w, number="2299002")
    assert r.status_code == 409 and r.json()["code"] == "EMAIL_TAKEN"
    r = register_student(client, w, email="other@iau.edu.sa", number="2299001")
    assert r.status_code == 409 and r.json()["code"] == "STUDENT_NUMBER_TAKEN"
    r = register_student(client, w, email="third@iau.edu.sa", number="2299003", gpa="5.50")
    assert r.status_code == 422 and r.json()["code"] == "GPA_ABOVE_SCALE"
    r = client.post(f"{API}/auth/register", data={"kind": "student", "email": "nodoc@iau.edu.sa",
                                                  "password": "Strong-pass-1", "name_en": "N", "name_ar": "ن",
                                                  "college_id": str(w.A1.id), "student_number": "2299009",
                                                  "major_id": str(w.cs_major.id), "gpa": "3"})
    assert r.json()["errors"][0]["code"] == "DOCUMENT_REQUIRED"


def test_weak_password_refused(client, w):
    r = client.post(f"{API}/auth/register", data={"kind": "coordinator", "email": "c@iau.edu.sa",
                                                  "password": "onlyletters", "name_en": "C", "name_ar": "ج",
                                                  "college_id": str(w.A2.id)},
                    files={"appointment_letter": ("letter.png", PNG, "image/png")})
    assert r.status_code == 422 and r.json()["errors"][0]["code"] == "WEAK_PASSWORD"


def test_registration_rate_limit(client, w, db):
    codes = [register_student(client, w, email=f"s{i}@iau.edu.sa", number=f"22990{i:02d}").status_code
             for i in range(6)]
    assert codes[:5] == [201] * 5 and codes[5] == 429


def test_company_registration_creates_pending_company(client, w, db):
    r = client.post(f"{API}/auth/register", data={"kind": "company", "email": "hr@newco.example.org",
                                                  "password": "Strong-pass-1", "name_en": "HR", "name_ar": "موارد",
                                                  "company_name": "NewCo", "commercial_reg_no": "4030999999",
                                                  "city": "Riyadh"},
                    files={"commercial_registration": ("cr.pdf", pdf("CR"), "application/pdf"),
                           "authorization_letter": ("auth.pdf", pdf("Auth"), "application/pdf")})
    assert r.status_code == 201, r.text
    assert r.json()["verification"]["reviewer"] == "platform_admin"
    user = db.query(User).filter_by(email="hr@newco.example.org").one()
    assert user.role == "company_supervisor" and not user.is_company_admin


# ---------------------------------------------------------------- AT-AUT-03
def test_at_aut_03_idle_timeout_and_logout(client, w, f):
    h = f.headers(w.stA)
    assert client.get(f"{API}/me", headers=h).status_code == 200
    clock.advance(timedelta(minutes=31))
    r = client.get(f"{API}/me", headers=h)
    assert r.status_code == 401 and r.json()["code"] == "SESSION_EXPIRED"
    h2 = f.headers(w.stA)
    clock.advance(timedelta(minutes=20))
    assert client.get(f"{API}/me", headers=h2).status_code == 200  # activity extends the session
    clock.advance(timedelta(minutes=20))
    assert client.get(f"{API}/me", headers=h2).status_code == 200
    assert client.post(f"{API}/auth/logout", headers=h2).status_code == 204
    assert client.get(f"{API}/me", headers=h2).status_code == 401


def test_session_max_lifetime(client, w, f):
    h = f.headers(w.stA)
    for _ in range(25):
        clock.advance(timedelta(minutes=29))
        r = client.get(f"{API}/me", headers=h)
    assert r.status_code == 401


def test_missing_and_garbage_tokens(client, w):
    assert client.get(f"{API}/me").json()["code"] == "UNAUTHENTICATED"
    assert client.get(f"{API}/me", headers={"Authorization": "Bearer abc"}).status_code == 401


# ---------------------------------------------------------------- AT-AUT-04
def test_at_aut_04_password_reset(client, w, f):
    h = f.headers(w.stA)
    assert client.post(f"{API}/auth/password/forgot", json={"email": w.stA.email}).status_code == 202
    assert client.post(f"{API}/auth/password/forgot", json={"email": "ghost@iau.edu.sa"}).status_code == 202
    token = last_link(w.stA.email)
    assert client.post(f"{API}/auth/password/reset", json={"token": token, "password": "New-pass-123"}).status_code \
        == 200
    assert client.post(f"{API}/auth/password/reset", json={"token": token, "password": "New-pass-456"}).status_code \
        == 410
    assert login(client, w.stA.email).status_code == 401
    assert login(client, w.stA.email, "New-pass-123").status_code == 200
    assert client.get(f"{API}/me", headers=h).status_code == 401  # sessions ended by the reset


def test_at_aut_04_expired_reset_link(client, w):
    client.post(f"{API}/auth/password/forgot", json={"email": w.stA.email})
    token = last_link(w.stA.email)
    clock.advance(timedelta(minutes=61))
    r = client.post(f"{API}/auth/password/reset", json={"token": token, "password": "New-pass-123"})
    assert r.status_code == 410 and r.json()["code"] == "TOKEN_EXPIRED"


# ---------------------------------------------------------------- AT-AUT-06
def test_at_aut_06_deactivation(client, w, f, db):
    h = f.headers(w.coA1)
    r = client.post(f"{API}/users/{w.stA.id}/deactivate", headers=h, json={"reason": "Left the university"})
    assert r.status_code == 200, r.text
    assert login(client, w.stA.email).json()["code"] == "ACCOUNT_INACTIVE"
    assert client.get(f"{API}/users/{w.stA.id}", headers=h).status_code == 200  # record still visible
    r = client.post(f"{API}/users/{w.stB.id}/deactivate", headers=h, json={"reason": "x"})
    assert r.status_code == 403
    assert client.post(f"{API}/users/{w.stA.id}/reactivate", headers=h).status_code == 200
    assert login(client, w.stA.email).status_code == 200


def test_deactivated_user_session_ends(client, w, f):
    h_student = f.headers(w.stA)
    client.post(f"{API}/users/{w.stA.id}/deactivate", headers=f.headers(w.coA1), json={"reason": "Graduated"})
    assert client.get(f"{API}/me", headers=h_student).status_code == 401


# ---------------------------------------------------------------- consent and language
def test_consent_gate(client, w, f, db):
    user = f.user("student", college=w.A1, consent=False)
    db.commit()
    h = f.headers(user)
    assert client.get(f"{API}/me", headers=h).json()["consent_required"] is True
    r = client.get(f"{API}/cycles", headers=h)
    assert r.status_code == 403 and r.json()["code"] == "CONSENT_REQUIRED"
    assert client.post(f"{API}/me/consent", headers=h).json()["consent_required"] is False
    assert client.get(f"{API}/cycles", headers=h).status_code == 200
    assert db.query(AuditEntry).filter_by(action="consent").count() == 1


def test_language_is_saved_and_used_for_errors(client, w, f):
    h = f.headers(w.stA)
    assert client.patch(f"{API}/me", headers=h, json={"language": "en"}).json()["language"] == "en"
    r = client.post(f"{API}/vacancies", headers=h, json={})
    assert r.status_code == 403 and r.json()["detail"] == MESSAGES["FORBIDDEN"][0]
    client.patch(f"{API}/me", headers=h, json={"language": "ar"})
    r = client.post(f"{API}/vacancies", headers=h, json={})
    assert r.json()["detail"] == MESSAGES["FORBIDDEN"][1]


def test_resend_confirmation(client, w, db):
    register_student(client, w)
    first = last_link()
    assert client.post(f"{API}/auth/email/resend", json={"email": "new.student@iau.edu.sa"}).status_code == 202
    second = last_link()
    assert first != second
    assert client.post(f"{API}/auth/email/confirm", json={"token": first}).status_code == 410  # revoked
    assert client.post(f"{API}/auth/email/confirm", json={"token": second}).status_code == 200
    assert db.query(VerificationRequest).count() == 1
