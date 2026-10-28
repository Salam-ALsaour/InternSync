"""Grades (AT-WFL-02 – 07) and dashboards (AT-DSH-01, AT-DSH-02, AT-DSH-05)."""
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.core import clock
from app.grades.service import round2, total
from app.models import (
    AttendanceWeek,
    AuditEntry,
    Grade,
    Placement,
    ReportSlot,
    ReportVersion,
    VerificationRequest,
)
from app.notifications.scheduled import overdue_items

API = "/api/v1"


@pytest.fixture
def ready(w, f):
    """A placement with the rubric, components 40/30/30, every report accepted, and the final evaluation (mean 4)."""
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.rubric(w.cycle)
    comps = f.components(w.cycle)
    f.finish_reports(p)
    f.evaluation(p, w.cs1, "final", [4, 5, 3])
    f.commit()
    return p, comps


def grade(client, h, p):
    return client.get(f"{API}/placements/{p.id}/grade", headers=h).json()


def scores(client, h, p, comps, *values):
    return client.put(f"{API}/placements/{p.id}/grade", headers=h, json={"component_scores": [
        {"component_id": str(c.id), "score": v} for c, v in zip(comps[1:], values, strict=True)]})


# ---------------------------------------------------------------- AT-WFL-02
def test_at_wfl_02_unit_total_rounds_half_up():
    parts = [{"weight": Decimal(40), "score": Decimal("80.00")}, {"weight": Decimal(30), "score": Decimal("85.50")},
             {"weight": Decimal(30), "score": Decimal("72.25")}]
    assert total(parts) == Decimal("79.33")  # 32 + 25.65 + 21.675 = 79.325
    assert total(parts[:2] + [{"weight": Decimal(30), "score": None}]) is None
    assert round2(Decimal("1.005")) == Decimal("1.01")


def test_at_wfl_02_grade_equals_the_hand_calculation(client, w, f, ready):
    p, comps = ready
    h = f.headers(w.asA1)
    g = grade(client, h, p)
    company = next(c for c in g["components"] if c["computed"])
    assert company["score"] == "80.00"  # mean 4.000 ÷ 5 × 100
    assert g["total"] is None
    r = scores(client, h, p, comps, "85.50", "72.25")
    assert r.status_code == 200 and r.json()["total"] == "79.33"
    bad = client.put(f"{API}/placements/{p.id}/grade", headers=h, json={"component_scores": [
        {"component_id": str(comps[0].id), "score": 90}]})
    assert bad.status_code == 422  # the company component is computed, not entered


# ---------------------------------------------------------------- AT-WFL-03
def test_at_wfl_03_submit_refused_with_the_missing_items(client, w, f):
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.rubric(w.cycle)
    f.components(w.cycle)
    f.commit()
    h = f.headers(w.asA1)
    gid = grade(client, h, p)["id"]
    r = client.post(f"{API}/grades/{gid}/submit", headers=h)
    assert r.status_code == 409 and r.json()["code"] == "PRECONDITIONS_UNMET"
    items = [m["item"] for m in r.json()["missing"]]
    assert items.count("weekly_report") == 12 and "final_report" in items and "final_evaluation" in items
    assert items.count("component") == 2
    checks = client.get(f"{API}/placements/{p.id}/grade/preconditions", headers=f.headers(w.coA1)).json()
    assert len(checks) == 16 and not any(c["ok"] for c in checks)


# ---------------------------------------------------------------- AT-WFL-04, AT-WFL-06
def test_at_wfl_04_and_06_return_approve_and_what_the_student_sees(client, w, f, ready, db):
    p, comps = ready
    h_as, h_co, h_st = f.headers(w.asA1), f.headers(w.coA1), f.headers(w.stA)
    scores(client, h_as, p, comps, 90, 70)
    assert grade(client, h_st, p) == {**grade(client, h_st, p), "visible": False}
    gid = grade(client, h_as, p)["id"]
    assert client.post(f"{API}/grades/{gid}/submit", headers=h_as).json()["status"] == "submitted"
    assert grade(client, h_st, p)["visible"] is False
    assert client.post(f"{API}/grades/{gid}/return", headers=h_co, json={"comment": " "}).json()["code"] \
        == "COMMENT_REQUIRED"
    r = client.post(f"{API}/grades/{gid}/return", headers=h_co, json={"comment": "Check the final report mark"})
    assert r.json()["status"] == "draft" and r.json()["return_comment"] == "Check the final report mark"
    client.post(f"{API}/grades/{gid}/submit", headers=h_as)
    assert client.post(f"{API}/grades/{gid}/approve", headers=f.headers(w.coB1)).status_code == 403
    r = client.post(f"{API}/grades/{gid}/approve", headers=h_co)
    assert r.json()["status"] == "final" and r.json()["approved_at"] is not None and r.json()["total"] == "80.00"
    db.expire_all()
    assert db.get(Placement, p.id).status == "completed"
    seen = grade(client, h_st, p)
    assert seen["visible"] is True and seen["total"] == "80.00" and seen["preconditions"] == []


# ---------------------------------------------------------------- AT-WFL-05
def test_at_wfl_05_final_grade_locked_and_reopened_with_a_reason(client, w, f, ready, db):
    p, comps = ready
    h_as, h_co = f.headers(w.asA1), f.headers(w.coA1)
    scores(client, h_as, p, comps, 90, 70)
    gid = grade(client, h_as, p)["id"]
    client.post(f"{API}/grades/{gid}/submit", headers=h_as)
    client.post(f"{API}/grades/{gid}/approve", headers=h_co)
    r = scores(client, h_as, p, comps, 95, 70)
    assert r.status_code == 409 and r.json()["code"] == "GRADE_LOCKED"
    assert client.post(f"{API}/grades/{gid}/reopen", headers=h_co, json={"reason": ""}).json()["code"] \
        == "REASON_REQUIRED"
    r = client.post(f"{API}/grades/{gid}/reopen", headers=h_co, json={"reason": "Appeal accepted"})
    assert r.json()["status"] == "draft"
    db.expire_all()
    assert db.get(Placement, p.id).status == "active"
    entry = db.query(AuditEntry).filter_by(entity_type="grade", action="reopen").one()
    assert entry.reason == "Appeal accepted"
    assert scores(client, f.headers(w.asA1), p, comps, 95, 70).status_code == 200


def test_grade_visibility(client, w, f, ready):
    p, _ = ready
    for user, status in ((w.cs1, 403), (w.ca1, 403), (w.asA1b, 403), (w.coB1, 403), (w.pa, 403), (w.stA2, 403)):
        assert client.get(f"{API}/placements/{p.id}/grade", headers=f.headers(user)).status_code == status


def test_weights_fixed_once_a_grade_is_submitted(client, w, f, ready, db):
    p, _ = ready
    db.query(Grade).filter_by(placement_id=p.id).one().status = "submitted"
    db.commit()
    r = client.put(f"{API}/cycles/{w.cycle.id}/grade-components", headers=f.headers(w.coA1), json={"components": [
        {"name_en": "All", "name_ar": "الكل", "weight": 100, "source": "academic_supervisor"}]})
    assert r.status_code == 409 and r.json()["code"] == "GRADES_EXIST"


# ---------------------------------------------------------------- AT-WFL-07
def test_at_wfl_07_bulk_approval_one_audit_entry_each(client, w, f, db):
    v = f.vacancy(w.cs1, [w.cs_major], seats=20)
    ids = []
    for _ in range(10):
        s = f.student(w.A1, w.cs_major)
        f.enroll(w.cycle, s, w.coA1)
        p = f.placement(s, v, w.cs1, w.coA1, w.asA1)
        g = db.query(Grade).filter_by(placement_id=p.id).one()
        g.status = "submitted"
        ids.append(str(g.id))
    f.commit()
    r = client.post(f"{API}/grades/bulk-approve", headers=f.headers(w.coA1), json={"grade_ids": ids})
    assert [x["ok"] for x in r.json()] == [True] * 10
    assert db.query(AuditEntry).filter_by(entity_type="grade", action="approve").count() == 10
    again = client.post(f"{API}/grades/bulk-approve", headers=f.headers(w.coA1), json={"grade_ids": ids[:1]})
    assert again.json()[0] == {"grade_id": ids[0], "ok": False, "code": "INVALID_TRANSITION"}
    listed = client.get(f"{API}/grades?status=final", headers=f.headers(w.coA1)).json()
    assert len(listed) == 10 and client.get(f"{API}/grades", headers=f.headers(w.coB1)).json() == []


# ---------------------------------------------------------------- AT-DSH-01
def counts(client, f, user) -> dict:
    return {i["type"]: i["count"] for i in client.get(f"{API}/dashboard", headers=f.headers(user)).json()["items"]}


def test_at_dsh_01_every_count_equals_the_database(client, w, f, db):
    v2 = f.vacancy(w.ca1, [w.cs_major, w.cis_major], seats=5, title="Second")
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)  # stA placed
    f.application(w.stA2, v2, accept_by=w.ca1)  # accepted, waiting for the coordinator
    f.rubric(w.cycle)
    f.components(w.cycle)
    extra = f.student(w.A1, w.cs_major)
    f.enroll(w.cycle, extra, w.coA1)
    f.application(extra, w.vac)  # waiting for the company
    db.add(VerificationRequest(user_id=f.student(w.A1, w.cs_major, status="pending").id, kind="student",
                               college_id=w.A1.id, submitted_data={}))
    db.add(VerificationRequest(user_id=f.user("coordinator", college=f.college(w.uniA), status="pending").id,
                               kind="coordinator", college_id=w.A1.id, submitted_data={}))
    slots = {(s.kind, s.week_no): s for s in db.query(ReportSlot).filter_by(placement_id=p.id)}
    slots[("weekly", 1)].status = "submitted"
    db.add(ReportVersion(slot_id=slots[("weekly", 1)].id, version_no=1, submitted_at=clock.now()))
    slots[("weekly", 2)].status = "revision_requested"
    f.commit()
    clock.freeze(datetime(2026, 11, 5, 9, 0, tzinfo=UTC))  # week 1 ended 4.5 days ago and is not recorded
    st = counts(client, f, w.stA)
    # due within 7 days or overdue: weeks 2 (revision), 3 and the next ones up to Nov 12
    due = db.query(ReportSlot).filter(ReportSlot.placement_id == p.id,
                                      ReportSlot.status.in_(("draft", "revision_requested")),
                                      ReportSlot.due_at <= clock.now() + timedelta(days=7)).count()
    assert st == {"reports_due": due, "revisions_requested": 1, "applications_submitted": 0,
                  "applications_accepted": 0, "grade_final": 0, "feedback_due": 0}
    assert counts(client, f, w.cs1) == {"applicants_to_review": 1, "attendance_to_record": 1, "evaluations_due": 0}
    assert counts(client, f, w.ca1)["applicants_to_review"] == 1  # the company: own and the colleague's vacancies
    assert counts(client, f, w.asA1) == {"reports_to_review": 1, "similarity_flags": 0, "grades_to_submit": 0,
                                         "grades_returned": 0}
    assert counts(client, f, w.coA1) == {"students_to_verify": 1, "placements_to_confirm": 1, "grades_to_approve": 0,
                                         "escalations": len(overdue_items(db, w.A1.id)), "leniency_alerts": 0}
    assert counts(client, f, w.pa) == {"verifications_pending": 1}
    clock.freeze(w.cycle.periodic_eval_due_at - timedelta(days=3))
    assert counts(client, f, w.cs1)["evaluations_due"] == 1


# ---------------------------------------------------------------- AT-DSH-02
def test_at_dsh_02_cycle_figures_overall_and_per_company(client, w, f, db):
    v2 = f.vacancy(w.ca2, [w.cs_major, w.cis_major], title="Sahil trainee")
    p1 = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    p2 = f.placement(w.stA2, v2, w.ca2, w.coA1, w.asA1)
    slots1 = {s.week_no: s for s in db.query(ReportSlot).filter_by(placement_id=p1.id, kind="weekly")}
    slots2 = {s.week_no: s for s in db.query(ReportSlot).filter_by(placement_id=p2.id, kind="weekly")}
    slots1[1].status, slots1[2].status, slots1[2].is_late = "accepted", "submitted", True
    slots2[1].status = "accepted"
    db.add_all([AttendanceWeek(placement_id=p1.id, week_no=1, scheduled_days=5, attended_days=5,
                               recorded_by=w.cs1.id, recorded_at=clock.now()),
                AttendanceWeek(placement_id=p2.id, week_no=1, scheduled_days=5, attended_days=3,
                               recorded_by=w.ca2.id, recorded_at=clock.now())])
    f.commit()
    clock.freeze(datetime(2026, 11, 9, 9, 0, tzinfo=UTC))  # weeks 1 and 2 are due
    r = client.get(f"{API}/cycles/{w.cycle.id}/stats", headers=f.headers(w.coA1)).json()
    o = r["overall"]
    assert (o["enrolled"], o["placed"], o["unplaced"]) == (2, 2, 0)
    assert (o["reports_due"], o["reports_submitted"]) == (4, 3)
    assert o["submission_rate"] == 75.0 and o["late_rate"] == 33.3 and o["attendance_rate"] == 80.0
    assert o["evaluations_expected"] == 0 and o["evaluation_completion"] is None
    by = {c["company_name"]: c for c in r["companies"]}
    assert by["Nakheel"]["submission_rate"] == 100.0 and by["Sahil"]["submission_rate"] == 50.0
    assert by["Sahil"]["attendance_rate"] == 60.0
    only = client.get(f"{API}/cycles/{w.cycle.id}/stats?company_id={w.co2.id}", headers=f.headers(w.coA1)).json()
    assert [c["company_name"] for c in only["companies"]] == ["Sahil"]
    assert client.get(f"{API}/cycles/{w.cycle.id}/stats", headers=f.headers(w.coB1)).status_code == 403


# ---------------------------------------------------------------- AT-DSH-05
def test_at_dsh_05_platform_figures(client, w, f, db):
    f.college(w.uniA, "College without coordinator")
    f.commit()
    s = client.get(f"{API}/platform/stats", headers=f.headers(w.pa)).json()
    assert s["universities"] == 2 and s["colleges"] == 4
    assert s["colleges_with_coordinator"] == 3 and s["colleges_without_coordinator"] == 1
    assert s["verified_companies"] == 2 and s["published_vacancies"] == 1
    assert s["users_by_role"] == {"student": 3, "company_supervisor": 3, "academic_supervisor": 3,
                                  "coordinator": 3, "platform_admin": 1}
    assert s["pending_verifications"] == 0 and s["oldest_pending_days"] is None
    assert client.get(f"{API}/platform/stats", headers=f.headers(w.coA1)).status_code == 403
