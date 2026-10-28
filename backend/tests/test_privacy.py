"""Retention period and anonymization of a closed cycle (AT-PRV-04)."""
from datetime import UTC, datetime

from sqlalchemy import select

from app.core import clock, files
from app.models import AuditEntry, Cv, Notification, ReportSlot, ReportVersion, StoredFile, StudentProfile, User
from app.privacy.service import add_months
from tests.factories import PW, pdf
from tests.increment4 import API, final_grade, ok, prepare

WEEKLY = {"tasks_performed": "Ahmed built the payroll API with Sara.", "learning": "Testing with pytest.",
          "challenges": "Slow database at the client site.", "next_week_plan": "Deploy to staging."}


def test_unit_add_months_keeps_the_end_of_the_month():
    assert add_months(datetime(2026, 1, 31, tzinfo=UTC), 1) == datetime(2026, 2, 28, tzinfo=UTC)
    assert add_months(datetime(2026, 11, 15, tzinfo=UTC), 14) == datetime(2028, 1, 15, tzinfo=UTC)
    assert add_months(datetime(2026, 11, 15, tzinfo=UTC), 0) == datetime(2026, 11, 15, tzinfo=UTC)


def _world(client, w, f, db):
    """stA: a Final grade, a certificate, a submitted report with a comment, a CV, feedback, and a survey answer.
    stA2: enrolled in this cycle and in another open one, so skipped."""
    prepare(f, w.cycle)
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    other = f.cycle(w.coA1, name="Summer 2027")
    f.enroll(other, w.stA2, w.coA1)
    stored = files.store(db, pdf("Ahmed Alqahtani CV", "Python"), "ahmed-cv.pdf", "cv", {files.PDF}, w.stA)
    db.add(Cv(student_id=w.stA.id, version_no=1, file_id=stored.id, extracted_text="Ahmed Alqahtani Python",
              text_status="ok", language="en", uploaded_at=clock.now()))
    f.commit()
    st, co = f.headers(w.stA), f.headers(w.coA1)
    slot = db.scalar(select(ReportSlot).where(ReportSlot.placement_id == p.id, ReportSlot.week_no == 1))
    ok(client.put(f"{API}/report-slots/{slot.id}/draft", headers=st, json=WEEKLY))
    ok(client.post(f"{API}/report-slots/{slot.id}/submit", headers=st))
    ok(client.post(f"{API}/report-slots/{slot.id}/comments", headers=st, json={"body": "My phone is 0551234567"}), 201)
    final_grade(f, db, w, p)
    cert = ok(client.post(f"{API}/placements/{p.id}/certificate", headers=co), 201).json()["certificate"]
    ok(client.put(f"{API}/placements/{p.id}/company-evaluation", headers=st, json={
        "learning_opportunities": 4, "supervision_quality": 4, "work_environment": 5, "relevance_to_major": 4,
        "would_recommend": True, "comment": "Thanks to Eng. Khalid"}))
    ok(client.put(f"{API}/placements/{p.id}/outcome-survey", headers=st, json={"job_offer": "yes"}))
    return p, slot, cert, stored


def _figures(client, co, cycle_id):
    return [ok(client.get(f"{API}/cycles/{cycle_id}/{path}", headers=co)).json()
            for path in ("stats", "outcomes", "company-evaluations", "leniency-alerts")]


def test_at_prv_04_anonymize_after_the_retention_period(client, w, f, db):
    email = w.stA.email
    p, slot, cert, cv_file = _world(client, w, f, db)
    co = f.headers(w.coA1)
    preview = ok(client.get(f"{API}/cycles/{w.cycle.id}/anonymization", headers=co)).json()
    assert preview["status"] == "open" and preview["eligible_at"] is None
    r = client.post(f"{API}/cycles/{w.cycle.id}/anonymize", headers=co, json={"confirm": True})
    assert r.status_code == 409 and r.json()["code"] == "CYCLE_NOT_CLOSED"

    ok(client.post(f"{API}/cycles/{w.cycle.id}/close", headers=co))
    preview = ok(client.get(f"{API}/cycles/{w.cycle.id}/anonymization", headers=co)).json()
    assert preview["status"] == "waiting" and preview["retention_months"] == 12
    assert preview["students"] == 1 and preview["skipped"] == 1
    r = client.post(f"{API}/cycles/{w.cycle.id}/anonymize", headers=co, json={"confirm": True})
    assert r.status_code == 409 and r.json()["code"] == "RETENTION_NOT_OVER" and "eligible_at" in r.json()

    clock.freeze(add_months(clock.now(), 12))
    co = f.headers(w.coA1)
    assert ok(client.get(f"{API}/cycles/{w.cycle.id}/anonymization", headers=co)).json()["status"] == "ready"
    r = client.post(f"{API}/cycles/{w.cycle.id}/anonymize", headers=co, json={})
    assert r.status_code == 422 and r.json()["code"] == "CONFIRM_REQUIRED"
    before = _figures(client, co, w.cycle.id)
    out = ok(client.post(f"{API}/cycles/{w.cycle.id}/anonymize", headers=co, json={"confirm": True})).json()
    assert out["status"] == "done" and out["students"] == 0 and out["skipped"] == 1
    assert _figures(client, co, w.cycle.id) == before  # statistics unchanged

    db.expire_all()
    student = db.get(User, w.stA.id)
    assert student.name_en.startswith("Student ") and "@invalid" in student.email and not student.is_active
    assert db.get(StudentProfile, w.stA.id).student_number.startswith("A")
    assert client.post(f"{API}/auth/login", json={"email": email, "password": PW}).status_code == 401
    assert db.get(StoredFile, cv_file.id).purged_at is not None
    assert not files.storage().exists(cv_file.storage_key)
    assert db.scalar(select(Cv).where(Cv.student_id == w.stA.id)).extracted_text is None
    assert client.get(f"{API}/files/{cv_file.id}", headers=co).status_code == 410
    assert client.get(f"{API}/files/{cert['file_id']}", headers=co).status_code == 410

    seen = ok(client.get(f"{API}/report-slots/{slot.id}", headers=co)).json()
    version = seen["submitted"][0]
    assert all(version[k] is None for k in WEEKLY) and "Ahmed" not in str(seen)
    comments = ok(client.get(f"{API}/report-slots/{slot.id}/comments", headers=co)).json()
    assert [c["body"] for c in comments] == ["—"]
    assert db.scalars(select(ReportVersion.body_text).where(ReportVersion.slot_id == slot.id)).all() == [None]
    assert ok(client.get(f"{API}/placements/{p.id}/company-evaluation", headers=co)).json()["comment"] is None
    public = ok(client.get(f"{API}/public/certificates/{cert['code']}")).json()
    assert public["status"] == "valid" and public["name_removed"] is True and public["student_name"] is None
    assert db.scalar(select(Notification).where(Notification.user_id == w.stA.id)) is None

    log = ok(client.get(f"{API}/audit-log?student_id={w.stA.id}&page_size=100", headers=co)).json()["items"]
    assert log and all(e["old_value"] is None and e["new_value"] is None and e["reason"] is None for e in log)
    assert "Ahmed" not in str(log) and "0551234567" not in str(log)
    entry = db.scalar(select(AuditEntry).where(AuditEntry.action == "anonymize"))
    assert entry.new_value == {"students": 1, "skipped": 1} and entry.entity_type == "training_cycle"

    kept = db.get(User, w.stA2.id)
    assert kept.anonymized_at is None and kept.is_active and not kept.email.endswith("@invalid")
    r = client.post(f"{API}/cycles/{w.cycle.id}/anonymize", headers=co, json={"confirm": True})
    assert r.status_code == 409 and r.json()["code"] == "ALREADY_ANONYMIZED"
    r = client.post(f"{API}/cycles/{w.cycle.id}/reopen", headers=co, json={"reason": "late grade"})
    assert r.status_code == 409 and r.json()["code"] == "ALREADY_ANONYMIZED"


def test_retention_period_is_set_by_the_college_coordinator(client, w, f, db):
    co = f.headers(w.coA1)
    assert ok(client.get(f"{API}/colleges/{w.A1.id}/retention", headers=co)).json() == {"retention_months": 12}
    assert ok(client.put(f"{API}/colleges/{w.A1.id}/retention", headers=co,
                         json={"retention_months": 0})).json() == {"retention_months": 0}
    assert client.put(f"{API}/colleges/{w.A1.id}/retention", headers=co,
                      json={"retention_months": 121}).status_code == 422
    for user in (w.coA2, w.asA1, w.stA, w.pa, w.cs1):
        h = f.headers(user)
        assert client.get(f"{API}/colleges/{w.A1.id}/retention", headers=h).status_code == 403
        assert client.get(f"{API}/cycles/{w.cycle.id}/anonymization", headers=h).status_code == 403
    entry = db.scalar(select(AuditEntry).where(AuditEntry.entity_type == "college", AuditEntry.action == "update"))
    assert entry.old_value == {"retention_months": 12} and entry.new_value == {"retention_months": 0}
    ok(client.post(f"{API}/cycles/{w.cycle.id}/close", headers=co))
    assert ok(client.get(f"{API}/cycles/{w.cycle.id}/anonymization", headers=co)).json()["status"] == "ready"
