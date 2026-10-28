"""The M5 demo scenario through the HTTP API (Increment 3 requirements, Section 7). Step 6 (install and offline) is
checked in the browser and step 10 (the evaluation script) outside the test suite; both are in the test report."""
import io
import json
from datetime import date, timedelta

import pytest
from openpyxl import load_workbook
from sqlalchemy import select

from app.ai import embeddings
from app.core import clock, mail
from app.core.db import SessionLocal
from app.jobs import jobs
from app.models import AuditEntry, Notification, ReportSlot, ReportVersion, User
from app.notifications import delivery
from tests.factories import HashEmbedder
from tests.test_similarity import COPIED, OTHER_SOURCE, OWN, OWN_OTHER

API = "/api/v1"


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json() if r.content and r.headers.get("content-type", "").startswith("application/json") else r


def week(db, placement, n):
    return db.scalars(select(ReportSlot).where(ReportSlot.placement_id == placement.id, ReportSlot.week_no == n)).one()


def submit(client, h, slot, tasks, learning):
    ok(client.put(f"{API}/report-slots/{slot.id}/draft", headers=h, json={
        "tasks_performed": tasks, "learning": learning, "challenges": "Time management.",
        "next_week_plan": "Continue the module."}))
    ok(client.post(f"{API}/report-slots/{slot.id}/submit", headers=h))


def kinds(db, user):
    db.expire_all()
    return [n.event for n in db.scalars(select(Notification).where(Notification.user_id == user.id)
                                        .order_by(Notification.created_at))]


@pytest.fixture
def setup(w, f, db, monkeypatch):
    embeddings.set_embedder(HashEmbedder())
    pushed = []
    monkeypatch.setattr(delivery, "push_configured", lambda: True)
    delivery.set_sender(lambda subscription, data: pushed.append(json.loads(data)))
    vac = f.vacancy(w.cs1, [w.cs_major, w.cis_major], seats=10, title="Software Trainee")
    earlier = f.cycle(w.coA1, start=date(2026, 2, 1), name="Co-op Spring 2026")
    former = f.student(w.A1, w.cs_major, "4.00")
    f.enroll(earlier, former, w.coA1)
    w.asB1 = f.user("academic_supervisor", college=w.B1)
    f.rubric(w.cycle)
    comps = f.components(w.cycle)
    f.commit()
    # the earlier cycle's report, and the same text at another university
    old = f.placement(former, vac, w.cs1, w.coA1, w.asA1)
    other_uni = f.placement(w.stB, vac, w.cs1, w.coB1, w.asB1)
    f.commit()
    yield {"vac": vac, "former": former, "old": old, "other_uni": other_uni, "comps": comps, "pushed": pushed}
    embeddings.set_embedder(None)
    delivery.set_sender(None)


def test_m5_demo_scenario(client, w, f, db, setup):
    s = setup
    submit(client, f.headers(s["former"]), week(db, s["old"], 1), COPIED, OWN_OTHER)
    submit(client, f.headers(w.stB), week(db, s["other_uni"], 1), COPIED + " " + OTHER_SOURCE, OWN_OTHER)
    p = f.placement(w.stA, s["vac"], w.cs1, w.coA1, w.asA1)
    f.commit()
    st, cs, ac, co = (f.headers(u) for u in (w.stA, w.cs1, w.asA1, w.coA1))

    # 1. A copied report is flagged; the supervisor sees score, source cycle and week, and passages
    slot = week(db, p, 1)
    submit(client, st, slot, COPIED, OWN)
    items = ok(client.get(f"{API}/dashboard", headers=ac))["items"]
    assert next(i for i in items if i["type"] == "similarity_flags")["count"] == 1
    version = db.scalars(select(ReportVersion).where(ReportVersion.slot_id == slot.id)).one()
    result = ok(client.get(f"{API}/report-versions/{version.id}/similarity", headers=ac))
    assert result["is_flagged"] and result["advisory"] and len(result["sources"]) == 1
    source = result["sources"][0]
    assert source["cycle_name"] == "Co-op Spring 2026" and source["week_no"] == 1 and source["passages"]
    assert source["author"] is None

    # 2. The decision is recorded; the report status does not change; the coordinator sees the author
    ok(client.post(f"{API}/report-versions/{version.id}/similarity/decision", headers=ac,
                   json={"decision": "overlap_confirmed", "comment": "The tasks section is copied."}))
    assert ok(client.get(f"{API}/report-slots/{slot.id}", headers=st))["status"] == "submitted"
    author = ok(client.get(f"{API}/report-versions/{version.id}/similarity", headers=co))["sources"][0]["author"]
    assert author["name_en"] == s["former"].name_en

    # 3. The report of another university is never a source (checked in step 1: one source only)
    assert all(src["cycle_name"] != "Co-op B" for src in result["sources"])

    # 4. Reminder, Missing notice, escalation; emails in each recipient's language
    week2 = week(db, p, 2)
    clock.freeze(week2.due_at - timedelta(hours=23))
    jobs.run(SessionLocal, "send_reminders")
    clock.freeze(week2.due_at + timedelta(minutes=5))
    jobs.run(SessionLocal, "flag_missing")
    clock.freeze(week2.due_at + timedelta(days=3, minutes=5))
    jobs.run(SessionLocal, "escalate_overdue")
    assert {"report.reminder", "report.missing"} <= set(kinds(db, w.stA))
    assert "report.missing" in kinds(db, w.asA1) and "escalation.overdue" in kinds(db, w.coA1)
    w.asA1.language = "en"
    db.commit()
    mail.outbox.clear()
    jobs.run(SessionLocal, "deliver_notifications")
    subjects = {(m["to"], m["subject"]) for m in mail.outbox}
    assert (w.stA.email, "تقرير لم يُسلَّم") in subjects and (w.asA1.email, "Report missing") in subjects

    # 5. A Final grade: in-app, email, and push for the student
    st, cs, ac, co = (f.headers(u) for u in (w.stA, w.cs1, w.asA1, w.coA1))
    ok(client.post(f"{API}/push/subscriptions", headers=st, json={
        "endpoint": "https://push.example.org/demo", "keys": {"p256dh": "k", "auth": "a"}}), 204)
    f.finish_reports(p)
    f.evaluation(p, w.cs1, "final", [4, 4, 4])
    f.commit()
    gid = ok(client.get(f"{API}/placements/{p.id}/grade", headers=ac))["id"]
    ok(client.put(f"{API}/placements/{p.id}/grade", headers=ac, json={"component_scores": [
        {"component_id": str(c.id), "score": "90"} for c in s["comps"][1:]]}))
    ok(client.post(f"{API}/grades/{gid}/submit", headers=ac))
    ok(client.post(f"{API}/grades/{gid}/approve", headers=co))
    jobs.run(SessionLocal, "deliver_notifications")
    assert s["pushed"][-1] == {"title": "اعتُمدت الدرجة", "link": "/student/reports?tab=grade"}
    assert "grade.final" in kinds(db, w.stA)

    # 7. Exports: grade sheet (Excel and PDF) with Arabic names, term summary, training record
    ws = load_workbook(io.BytesIO(ok(client.get(f"{API}/cycles/{w.cycle.id}/exports/grade-sheet",
                                                headers=co)).content)).active
    assert w.stA.name_ar in [row[1] for row in ws.iter_rows(min_row=3, values_only=True)]
    assert ok(client.get(f"{API}/cycles/{w.cycle.id}/exports/grade-sheet?format=pdf",
                         headers=co)).content.startswith(b"%PDF")
    assert ok(client.get(f"{API}/cycles/{w.cycle.id}/exports/term-summary", headers=co)).content.startswith(b"%PDF")
    assert ok(client.get(f"{API}/placements/{p.id}/exports/training-record",
                         headers=ac)).content.startswith(b"%PDF")

    # 8. History of a report, an evaluation, and a grade
    assert [e["action"] for e in ok(client.get(f"{API}/history/report_slot/{slot.id}", headers=ac))] \
        == ["submit", "similarity_decision"]
    evaluation = ok(client.get(f"{API}/placements/{p.id}/evaluations", headers=st))["items"][1]["evaluation"]
    assert [e["action"] for e in ok(client.get(f"{API}/history/evaluation/{evaluation['id']}", headers=st))] \
        == ["submit"]
    assert [e["action"] for e in ok(client.get(f"{API}/history/grade/{gid}", headers=st))] \
        == ["update", "submit", "approve"]

    # 9. The Platform Admin transfers the coordinator role; the previous coordinator loses access
    ok(client.post(f"{API}/colleges/{w.A1.id}/coordinator/transfer", headers=f.headers(w.pa),
                   json={"user_id": str(w.asA1b.id), "reason": "The coordinator moved to another college"}))
    assert client.get(f"{API}/cycles/{w.cycle.id}/stats", headers=co).status_code == 403
    db.expire_all()
    assert db.get(User, w.coA1.id).role == "academic_supervisor"
    assert db.scalars(select(AuditEntry).where(AuditEntry.action == "transfer_role")).one().reason \
        == "The coordinator moved to another college"
