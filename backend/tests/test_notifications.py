"""Notifications, web push, and escalations (AT-NOT-01 – 06, AT-PWA-02, AT-REL-03)."""
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core import clock, mail
from app.core.db import SessionLocal
from app.jobs import jobs
from app.models import Notification, PushSubscription, ReportSlot
from app.notifications import delivery
from tests.test_auth import register_student

API = "/api/v1"
WEEK1_DUE = datetime(2026, 10, 29, 20, 59, tzinfo=UTC)  # Thursday 23:59 in Riyadh
WEEK1_END = datetime(2026, 10, 31, 20, 59, 59, tzinfo=UTC)
FULL = {"tasks_performed": "Built the login API", "learning": "FastAPI dependencies",
        "challenges": "Time zones", "next_week_plan": "Write tests"}


def events(db, user) -> list[str]:
    db.expire_all()
    rows = db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at))
    return [n.event + (f".{n.params['variant']}" if n.params.get("variant") else "") for n in rows]


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json() if r.content else None


@pytest.fixture
def push(monkeypatch):
    """Web push configured, with a stand-in sender that records what would go to the push service."""
    sent = []
    monkeypatch.setattr(delivery, "push_configured", lambda: True)
    delivery.set_sender(lambda subscription, data: sent.append((subscription["endpoint"], data)))
    yield sent
    delivery.set_sender(None)


# ---------------------------------------------------------------- AT-NOT-05: events and recipients
def test_at_not_05_application_and_placement_events(client, w, f, db):
    st, cs, co = f.headers(w.stA), f.headers(w.cs1), f.headers(w.coA1)
    application = ok(client.post(f"{API}/vacancies/{w.vac.id}/applications", headers=st), 201)
    assert events(db, w.cs1) == ["application.received"]
    ok(client.post(f"{API}/applications/{application['id']}/accept", headers=cs))
    assert events(db, w.stA) == ["application.decided.accepted"]
    assert events(db, w.coA1) == ["application.accepted"]
    other = f.vacancy(w.cs1, [w.cs_major], title="Second vacancy")
    f.commit()
    ok(client.post(f"{API}/vacancies/{other.id}/applications", headers=st), 201)
    ok(client.post(f"{API}/placements", headers=co, json={"application_id": application["id"],
                                                         "academic_supervisor_id": str(w.asA1.id)}), 201)
    assert events(db, w.stA)[-2:] == ["application.withdrawn_auto", "placement.confirmed"]
    assert events(db, w.asA1) == ["placement.confirmed"]
    assert events(db, w.cs1)[-1] == "placement.confirmed"


def test_at_not_05_report_evaluation_and_grade_events(client, w, f, db):
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.rubric(w.cycle)
    comps = f.components(w.cycle)
    f.commit()
    db.query(Notification).delete()
    db.commit()
    st, cs, ac, co = (f.headers(u) for u in (w.stA, w.cs1, w.asA1, w.coA1))
    slot = db.scalars(select(ReportSlot).where(ReportSlot.placement_id == p.id, ReportSlot.week_no == 1)).one()
    ok(client.put(f"{API}/report-slots/{slot.id}/draft", headers=st, json=FULL))
    ok(client.post(f"{API}/report-slots/{slot.id}/submit", headers=st))
    assert events(db, w.asA1) == ["report.submitted"]
    ok(client.post(f"{API}/report-slots/{slot.id}/request-revision", headers=ac, json={"comment": "Add details"}))
    ok(client.put(f"{API}/report-slots/{slot.id}/draft", headers=st, json={**FULL, "learning": "More details"}))
    ok(client.post(f"{API}/report-slots/{slot.id}/submit", headers=st))
    ok(client.post(f"{API}/report-slots/{slot.id}/accept", headers=ac))
    assert events(db, w.stA) == ["report.revision_requested", "report.accepted"]

    criteria = ok(client.get(f"{API}/placements/{p.id}/evaluations", headers=cs))["rubric"]
    for type_ in ("periodic", "final"):
        ok(client.put(f"{API}/placements/{p.id}/evaluations/{type_}", headers=cs, json={
            "scores": [{"criterion_id": c["id"], "score": 4} for c in criteria], "overall_comment": "Good"}))
        ok(client.post(f"{API}/placements/{p.id}/evaluations/{type_}/submit", headers=cs))
    assert events(db, w.asA1).count("evaluation.submitted") == 2
    assert events(db, w.stA).count("evaluation.submitted") == 1  # the final one stays hidden (FR-EVL-03)

    f.finish_reports(p)
    f.commit()
    gid = ok(client.get(f"{API}/placements/{p.id}/grade", headers=ac))["id"]
    ok(client.put(f"{API}/placements/{p.id}/grade", headers=ac, json={"component_scores": [
        {"component_id": str(c.id), "score": "90"} for c in comps[1:]]}))
    ok(client.post(f"{API}/grades/{gid}/submit", headers=ac))
    assert events(db, w.coA1) == ["grade.submitted"]
    ok(client.post(f"{API}/grades/{gid}/return", headers=co, json={"comment": "Check the weekly score"}))
    ok(client.post(f"{API}/grades/{gid}/submit", headers=ac))
    ok(client.post(f"{API}/grades/{gid}/approve", headers=co))
    ok(client.post(f"{API}/grades/{gid}/reopen", headers=co, json={"reason": "Correction"}))
    assert events(db, w.asA1)[-3:] == ["grade.returned", "grade.final", "grade.reopened"]
    assert events(db, w.stA)[-2:] == ["grade.final", "grade.reopened"]
    assert "grade.submitted" not in events(db, w.stA)


def test_at_not_05_verification_events(client, w, f, db):
    r = register_student(client, w)
    req = r.json()["verification"]["request_id"]
    assert events(db, w.coA1) == ["verification.submitted"]
    ok(client.post(f"{API}/verification-requests/{req}/reject", headers=f.headers(w.coA1),
                   json={"reason": "The schedule is unreadable"}))
    from app.models import User
    student = db.scalars(select(User).where(User.email == "new.student@iau.edu.sa")).one()
    assert events(db, student) == ["verification.rejected"]
    n = db.scalars(select(Notification).where(Notification.user_id == student.id)).one()
    assert n.params["reason"] == "The schedule is unreadable" and n.link == "/verification"


# ---------------------------------------------------------------- AT-NOT-01 and AT-NOT-06
def test_at_not_01_list_unread_count_and_one_email_each(client, w, f, db):
    w.stA.language = "en"
    db.commit()
    st = f.headers(w.stA)
    application = ok(client.post(f"{API}/vacancies/{w.vac.id}/applications", headers=st), 201)
    ok(client.post(f"{API}/applications/{application['id']}/accept", headers=f.headers(w.cs1)))
    page = ok(client.get(f"{API}/notifications", headers=st))
    assert page["unread_count"] == 1 and page["items"][0]["title"] == "Application accepted"
    assert "accepted your application to Backend Trainee" in page["items"][0]["body"]
    mail.outbox.clear()
    jobs.run(SessionLocal, "deliver_notifications")
    sent = {m["to"]: m for m in mail.outbox}
    assert len(mail.outbox) == 3 and set(sent) == {w.stA.email, w.cs1.email, w.coA1.email}  # one email each
    assert sent[w.stA.email]["subject"] == "Application accepted"
    assert sent[w.cs1.email]["subject"] == "متقدم جديد"  # the supervisor's language is Arabic (AT-NOT-06)
    assert "مرحباً" in sent[w.cs1.email]["body"] and f"/company/vacancies/{w.vac.id}/applicants" in \
        sent[w.cs1.email]["body"]
    jobs.run(SessionLocal, "deliver_notifications")
    assert len(mail.outbox) == 3  # delivered once
    item = page["items"][0]["id"]
    assert client.post(f"{API}/notifications/{item}/read", headers=f.headers(w.cs1)).status_code == 404
    ok(client.post(f"{API}/notifications/{item}/read", headers=st))
    assert ok(client.get(f"{API}/notifications?unread_only=true", headers=st))["items"] == []
    assert ok(client.post(f"{API}/notifications/read-all", headers=f.headers(w.coA1)))["unread_count"] == 0
    assert ok(client.get(f"{API}/notifications", headers=f.headers(w.coA1)))["unread_count"] == 0


def test_failed_email_is_retried_then_marked_failed(w, f, db, monkeypatch):
    from app.notifications.service import notify
    notify(db, [w.stA], "report.accepted", {"report_en": "week 1 report", "report_ar": "تقرير الأسبوع 1"}, "/")
    db.commit()
    monkeypatch.setattr(mail, "deliver", lambda *a, **k: False)
    for _ in range(5):
        jobs.run(SessionLocal, "deliver_notifications")
    db.expire_all()
    n = db.scalars(select(Notification)).one()
    assert n.email_status == "failed" and n.email_attempts == 5


# ---------------------------------------------------------------- AT-NOT-02, AT-NOT-03, AT-REL-03
@pytest.fixture
def placed(w, f, db):
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.commit()
    db.query(Notification).delete()
    db.commit()
    return p


def test_at_not_02_reminder_once_between_24_and_23_hours(client, w, f, db, placed):
    clock.freeze(WEEK1_DUE - timedelta(hours=24, minutes=1))
    jobs.run(SessionLocal, "send_reminders")
    assert events(db, w.stA) == []
    clock.freeze(WEEK1_DUE - timedelta(hours=23, minutes=30))
    jobs.run(SessionLocal, "send_reminders")
    jobs.run(SessionLocal, "send_reminders")
    assert events(db, w.stA) == ["report.reminder"]
    n = db.scalars(select(Notification)).one()
    assert n.params["due"] == "29/10/2026 23:59" and n.params["report_en"] == "week 1 report"
    slot2 = db.scalars(select(ReportSlot).where(ReportSlot.placement_id == placed.id, ReportSlot.week_no == 2)).one()
    st = f.headers(w.stA)
    ok(client.put(f"{API}/report-slots/{slot2.id}/draft", headers=st, json=FULL))
    ok(client.post(f"{API}/report-slots/{slot2.id}/submit", headers=st))
    clock.freeze(slot2.due_at - timedelta(hours=2))
    jobs.run(SessionLocal, "send_reminders")
    assert events(db, w.stA).count("report.reminder") == 1  # week 2 was submitted: no reminder


def test_at_not_03_missing_notice_to_student_and_supervisor(w, f, db, placed):
    clock.freeze(WEEK1_DUE + timedelta(minutes=10))
    jobs.run(SessionLocal, "flag_missing")
    jobs.run(SessionLocal, "flag_missing")
    assert events(db, w.stA) == ["report.missing"] and events(db, w.asA1) == ["report.missing"]


def test_at_not_04_escalation_on_day_4_never_twice(client, w, f, db, placed):
    co = f.headers(w.coA1)
    clock.freeze(WEEK1_DUE + timedelta(days=2, hours=23))
    jobs.run(SessionLocal, "escalate_overdue")
    assert events(db, w.coA1) == []
    clock.freeze(WEEK1_DUE + timedelta(days=3, minutes=1))
    jobs.run(SessionLocal, "escalate_overdue")
    jobs.run(SessionLocal, "escalate_overdue")
    assert events(db, w.coA1) == ["escalation.overdue"]
    clock.freeze(WEEK1_END + timedelta(days=3, minutes=1))  # the first attendance week is now 3 days overdue too
    co = f.headers(w.coA1)
    jobs.run(SessionLocal, "escalate_overdue")
    kinds = {e["kind"] for e in ok(client.get(f"{API}/escalations", headers=co))}
    assert kinds == {"report", "attendance"} and events(db, w.coA1).count("escalation.overdue") == 2
    items = ok(client.get(f"{API}/dashboard", headers=co))["items"]
    assert next(i for i in items if i["type"] == "escalations")["count"] == 2
    ok(client.put(f"{API}/placements/{placed.id}/attendance/1", headers=f.headers(w.cs1), json={"full": True}))
    assert {e["kind"] for e in ok(client.get(f"{API}/escalations", headers=co))} == {"report"}
    clock.freeze(w.cycle.periodic_eval_due_at + timedelta(days=3, minutes=1))
    co = f.headers(w.coA1)
    jobs.run(SessionLocal, "escalate_overdue")
    assert "evaluation" in {e["kind"] for e in ok(client.get(f"{API}/escalations", headers=co))}
    body = db.scalars(select(Notification).where(Notification.user_id == w.coA1.id)
                      .order_by(Notification.created_at.desc())).first()
    assert body.params["days"] == 3 and body.link == f"/placements/{placed.id}"


# ---------------------------------------------------------------- AT-PWA-02
def test_at_pwa_02_push_has_title_and_link_only(client, w, f, db, push):
    st = f.headers(w.stA)
    ok(client.post(f"{API}/push/subscriptions", headers=st, json={
        "endpoint": "https://push.example.org/sub/1", "keys": {"p256dh": "BPk", "auth": "a1"}}), 204)
    ok(client.post(f"{API}/vacancies/{w.vac.id}/applications", headers=st), 201)
    jobs.run(SessionLocal, "deliver_notifications")
    assert push == []  # the supervisor has no subscription: email only
    db.expire_all()
    n = db.scalars(select(Notification)).one()
    assert n.push_status == "skipped" and n.email_status == "sent"
    from app.notifications.service import notify
    notify(db, [w.stA], "grade.final", {"student_en": "Abdullah", "student_ar": "عبدالله"}, "/student/reports")
    db.commit()
    jobs.run(SessionLocal, "deliver_notifications")
    import json
    endpoint, data = push[0]
    assert endpoint == "https://push.example.org/sub/1" and json.loads(data) == {
        "title": "اعتُمدت الدرجة", "link": "/student/reports"}  # NFR-PRV-03: no name, no grade


def test_gone_subscription_is_deleted(w, f, db, monkeypatch):
    from app.notifications.service import notify
    monkeypatch.setattr(delivery, "push_configured", lambda: True)

    def gone(subscription, data):
        raise delivery.Gone()
    delivery.set_sender(gone)
    try:
        db.add(PushSubscription(user_id=w.stA.id, endpoint="https://push.example.org/old", p256dh="k", auth="a"))
        notify(db, [w.stA], "report.accepted", {}, "/")
        db.commit()
        jobs.run(SessionLocal, "deliver_notifications")
        db.expire_all()
        assert db.scalars(select(PushSubscription)).all() == []
        assert db.scalars(select(Notification)).one().push_status == "failed"
    finally:
        delivery.set_sender(None)


def test_push_subscription_endpoints(client, w, f, db):
    st = f.headers(w.stA)
    assert ok(client.get(f"{API}/push/vapid-public-key", headers=st))["key"] is None
    body = {"endpoint": "https://push.example.org/sub/2", "keys": {"p256dh": "k", "auth": "a"}}
    assert client.post(f"{API}/push/subscriptions", headers=st, json={**body, "endpoint": "http://x.org/y"}) \
        .status_code == 422
    ok(client.post(f"{API}/push/subscriptions", headers=st, json=body), 204)
    ok(client.post(f"{API}/push/subscriptions", headers=f.headers(w.stA2), json=body), 204)  # same browser
    assert db.scalars(select(PushSubscription)).one().user_id == w.stA2.id
    ok(client.request("DELETE", f"{API}/push/subscriptions", headers=st, json={"endpoint": body["endpoint"]}), 204)
    assert db.scalars(select(PushSubscription)).one() is not None  # not the caller's
    ok(client.request("DELETE", f"{API}/push/subscriptions", headers=f.headers(w.stA2),
                      json={"endpoint": body["endpoint"]}), 204)
    assert db.scalars(select(PushSubscription)).all() == []
