"""Attendance (AT-ATT-01 – 04) and evaluations (AT-EVL-01 – 04)."""
from datetime import UTC, datetime, timedelta

import pytest

from app.core import clock
from app.models import AuditEntry, Evaluation, Grade, TrainingCycle

API = "/api/v1"
WEEK1_END = datetime(2026, 10, 31, 20, 59, 59, tzinfo=UTC)  # Saturday 23:59:59 in Riyadh


@pytest.fixture
def placed(w, f):
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.rubric(w.cycle)
    f.commit()
    return p


def att(client, h, p, week, **body):
    return client.put(f"{API}/placements/{p.id}/attendance/{week}", headers=h, json=body)


# ---------------------------------------------------------------- attendance
def test_at_att_01_full_attendance_in_one_action(client, w, f, placed):
    h = f.headers(w.cs1)
    r = att(client, h, placed, 1, full=True)
    assert r.status_code == 200, r.text
    week1 = r.json()["weeks"][0]
    assert week1["attended_days"] == week1["scheduled_days"] == 5 and week1["state"] == "recorded"
    r = att(client, h, placed, 1, attended_days=6)
    assert r.status_code == 422 and r.json()["code"] == "ATTENDED_EXCEEDS_SCHEDULED"
    r = att(client, h, placed, 1, attended_days=3, note="Two days sick leave")
    assert r.json()["weeks"][0]["attended_days"] == 3 and r.json()["weeks"][0]["note"] == "Two days sick leave"
    assert att(client, h, placed, 2, full=True).json()["code"] == "WEEK_NOT_STARTED"
    assert att(client, f.headers(w.ca1), placed, 1, full=True).status_code == 403  # admin, not the assigned one
    assert att(client, f.headers(w.ca2), placed, 1, full=True).status_code == 403


def test_at_att_02_locked_after_seven_days_until_unlocked(client, w, f, placed, db):
    clock.freeze(WEEK1_END + timedelta(days=8))
    h, co = f.headers(w.cs1), f.headers(w.coA1)
    r = att(client, h, placed, 1, full=True)
    assert r.status_code == 409 and r.json()["code"] == "WEEK_LOCKED"
    url = f"{API}/placements/{placed.id}/attendance/1/unlock"
    assert client.post(url, headers=co, json={"reason": ""}).json()["code"] == "REASON_REQUIRED"
    assert client.post(url, headers=f.headers(w.coB1), json={"reason": "x"}).status_code == 403
    r = client.post(url, headers=co, json={"reason": "Supervisor was travelling"})
    assert r.status_code == 200 and r.json()["weeks"][0]["locked"] is False
    assert att(client, h, placed, 1, attended_days=4).status_code == 200
    entry = db.query(AuditEntry).filter_by(action="unlock_attendance").one()
    assert entry.reason == "Supervisor was travelling"
    clock.advance(timedelta(days=8))
    assert att(client, f.headers(w.cs1), placed, 1, full=True).json()["code"] == "WEEK_LOCKED"


def test_at_att_03_percentage_and_visibility(client, w, f, placed):
    clock.freeze(WEEK1_END + timedelta(days=1))  # inside week 2, week 1 still editable
    h = f.headers(w.cs1)
    att(client, h, placed, 1, full=True)
    r = att(client, h, placed, 2, attended_days=3)
    assert r.json()["percent"] == 80.0 and r.json()["attended_days"] == 8 and r.json()["scheduled_days"] == 10
    for user in (w.stA, w.asA1, w.coA1, w.ca1):
        assert client.get(f"{API}/placements/{placed.id}/attendance", headers=f.headers(user)).json()["percent"] \
            == 80.0
    for user in (w.stA2, w.asA1b, w.coB1, w.ca2):
        assert client.get(f"{API}/placements/{placed.id}/attendance", headers=f.headers(user)).status_code == 403
    assert client.get(f"{API}/placements/{placed.id}", headers=f.headers(w.stA)).json()["attendance_percent"] == 80.0


def test_at_att_04_unrecorded_week_on_the_company_dashboard_on_day_4(client, w, f, placed):
    def count(user):
        items = client.get(f"{API}/dashboard", headers=f.headers(user)).json()["items"]
        return next(i["count"] for i in items if i["type"] == "attendance_to_record")
    clock.freeze(WEEK1_END + timedelta(days=3) - timedelta(hours=1))
    assert count(w.cs1) == 0
    clock.freeze(WEEK1_END + timedelta(days=3, hours=12))
    assert count(w.cs1) == 1 and count(w.ca1) == 1 and count(w.ca2) == 0
    weeks = client.get(f"{API}/placements/{placed.id}/attendance", headers=f.headers(w.cs1)).json()["weeks"]
    assert weeks[0]["state"] == "overdue"
    att(client, f.headers(w.cs1), placed, 1, full=True)
    assert count(w.cs1) == 0


# ---------------------------------------------------------------- evaluations
def ev_url(p, type_, submit=False):
    return f"{API}/placements/{p.id}/evaluations/{type_}" + ("/submit" if submit else "")


def rubric_ids(client, h, p):
    return [c["id"] for c in client.get(f"{API}/placements/{p.id}/evaluations", headers=h).json()["rubric"]]


def test_at_evl_01_all_criteria_and_comment_required(client, w, f, placed, db):
    h = f.headers(w.cs1)
    ids = rubric_ids(client, h, placed)
    client.put(ev_url(placed, "periodic"), headers=h, json={"scores": [{"criterion_id": ids[0], "score": 4},
                                                                       {"criterion_id": ids[1], "score": 5}],
                                                            "overall_comment": "Good start"})
    r = client.post(ev_url(placed, "periodic", True), headers=h)
    assert r.status_code == 422 and r.json()["code"] == "EVALUATION_INCOMPLETE"
    assert len(r.json()["errors"]) == 1
    full = [{"criterion_id": i, "score": s} for i, s in zip(ids, (4, 5, 3), strict=True)]
    client.put(ev_url(placed, "periodic"), headers=h, json={"scores": full, "overall_comment": " "})
    r = client.post(ev_url(placed, "periodic", True), headers=h)
    assert r.status_code == 422 and r.json()["errors"][0]["field"] == "overall_comment"
    client.put(ev_url(placed, "periodic"), headers=h, json={"scores": full, "overall_comment": "Reliable"})
    r = client.post(ev_url(placed, "periodic", True), headers=h)
    assert r.status_code == 200
    periodic = r.json()["items"][0]["evaluation"]
    assert periodic["status"] == "submitted" and periodic["mean_score"] == "4.000"
    db.expire_all()
    assert db.get(TrainingCycle, w.cycle.id).rubric_locked_at is not None  # FR-CYC-03
    assert client.put(ev_url(placed, "periodic"), headers=f.headers(w.ca1), json={}).status_code == 403


def test_at_evl_02_only_the_cycle_rubric(client, w, f, placed, db):
    other = f.rubric(w.cycleB, n=1)[0]
    f.commit()
    r = client.put(ev_url(placed, "final"), headers=f.headers(w.cs1),
                   json={"scores": [{"criterion_id": str(other.id), "score": 5}]})
    assert r.status_code == 422
    assert db.query(Evaluation).filter_by(placement_id=placed.id).count() == 0  # nothing saved


def test_at_evl_03_student_sees_periodic_now_and_final_when_the_grade_is_final(client, w, f, placed, db):
    f.evaluation(placed, w.cs1, "periodic", [4, 4, 4])
    f.evaluation(placed, w.cs1, "final", [5, 4, 3])
    f.commit()
    items = client.get(f"{API}/placements/{placed.id}/evaluations", headers=f.headers(w.stA)).json()["items"]
    assert items[0]["evaluation"]["mean_score"] == "4.000" and items[1]["evaluation"] is None
    assert client.get(f"{API}/placements/{placed.id}/evaluations", headers=f.headers(w.asA1)).json()["items"][1][
        "evaluation"]["mean_score"] == "4.000"
    db.query(Grade).filter_by(placement_id=placed.id).one().status = "final"
    db.commit()
    items = client.get(f"{API}/placements/{placed.id}/evaluations", headers=f.headers(w.stA)).json()["items"]
    assert items[1]["evaluation"]["status"] == "submitted"


def test_drafts_are_private_to_the_company_supervisor(client, w, f, placed):
    ids = rubric_ids(client, f.headers(w.cs1), placed)
    client.put(ev_url(placed, "periodic"), headers=f.headers(w.cs1),
               json={"scores": [{"criterion_id": ids[0], "score": 2}], "overall_comment": "draft"})
    for user in (w.stA, w.asA1, w.coA1):
        items = client.get(f"{API}/placements/{placed.id}/evaluations", headers=f.headers(user)).json()["items"]
        assert items[0]["evaluation"] is None


def test_at_evl_04_read_only_after_submit_and_reopened_once(client, w, f, placed, db):
    f.evaluation(placed, w.cs1, "periodic", [3, 3, 3])
    f.commit()
    h, co = f.headers(w.cs1), f.headers(w.coA1)
    assert client.put(ev_url(placed, "periodic"), headers=h, json={"overall_comment": "changed"}).json()["code"] \
        == "INVALID_TRANSITION"
    eid = db.query(Evaluation).filter_by(placement_id=placed.id, type="periodic").one().id
    assert client.post(f"{API}/evaluations/{eid}/reopen", headers=co, json={"reason": ""}).json()["code"] \
        == "REASON_REQUIRED"
    assert client.post(f"{API}/evaluations/{eid}/reopen", headers=f.headers(w.coB1),
                       json={"reason": "x"}).status_code == 403
    r = client.post(f"{API}/evaluations/{eid}/reopen", headers=co, json={"reason": "Wrong week rated"})
    assert r.status_code == 200 and r.json()["items"][0]["evaluation"] is None  # a draft again, private
    db.expire_all()
    assert db.get(Evaluation, eid).status == "draft" and db.get(Evaluation, eid).reopen_count == 1
    assert db.query(AuditEntry).filter_by(action="reopen", entity_type="evaluation").one().reason == "Wrong week rated"
    assert client.post(ev_url(placed, "periodic", True), headers=h).status_code == 200
    r = client.post(f"{API}/evaluations/{eid}/reopen", headers=co, json={"reason": "Again"})
    assert r.status_code == 409 and r.json()["code"] == "ALREADY_REOPENED"


def test_final_evaluation_cannot_be_reopened_while_the_grade_is_submitted(client, w, f, placed, db):
    f.evaluation(placed, w.cs1, "final", [4, 4, 4])
    db.query(Grade).filter_by(placement_id=placed.id).one().status = "submitted"
    f.commit()
    eid = db.query(Evaluation).filter_by(placement_id=placed.id, type="final").one().id
    r = client.post(f"{API}/evaluations/{eid}/reopen", headers=f.headers(w.coA1), json={"reason": "Fix a score"})
    assert r.status_code == 409 and r.json()["code"] == "INVALID_TRANSITION"
