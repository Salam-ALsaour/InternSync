"""The M4 demo scenario end to end through the HTTP API (Increment 2 requirements, Section 7). Step 10, the AI
evaluation script, runs outside the test suite; its numbers are in the test report."""
from datetime import UTC, datetime, timedelta

import pytest

from app.ai import embeddings
from app.core import clock
from app.models import AuditEntry, Placement
from tests.factories import HashEmbedder

API = "/api/v1"
WEEK1_END = datetime(2026, 10, 31, 20, 59, 59, tzinfo=UTC)


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json()


def count(client, h, type_):
    return next(i["count"] for i in ok(client.get(f"{API}/dashboard", headers=h))["items"] if i["type"] == type_)


@pytest.fixture
def model():
    embeddings.set_embedder(HashEmbedder())
    yield
    embeddings.set_embedder(None)


def test_m4_demo_scenario(model, client, w, f, db):
    f.rubric(w.cycle)
    comps = f.components(w.cycle)
    data = f.vacancy(w.cs1, [w.cs_major], required=(w.sql,), title="Data Analyst Trainee")
    f.commit()
    st, cs, ac, co = (f.headers(u) for u in (w.stA, w.cs1, w.asA1, w.coA1))

    # 1. The student's dashboard and recommended vacancies; applies to one
    assert {"reports_due", "applications_submitted"} <= {i["type"] for i in ok(client.get(f"{API}/dashboard",
                                                                                          headers=st))["items"]}
    ok(client.put(f"{API}/students/me/skills", headers=st,
                  json={"skills": [{"skill_id": str(w.python.id), "source": "manual"}]}))
    ranked = ok(client.get(f"{API}/students/me/matches", headers=st))
    assert ranked["mode"] == "semantic" and ranked["advisory"] is True and ranked["total"] == 2
    top = ranked["items"][0]
    assert top["vacancy"]["id"] == str(w.vac.id) and [s["name_en"] for s in top["matched_skills"]] == ["Python"]
    assert [s["name_en"] for s in ranked["items"][1]["missing_skills"]] == ["SQL"]
    plan = ok(client.get(f"{API}/students/me/matches/{data.id}/plan", headers=st))
    assert [m["skill"]["name_en"] for m in plan["missing_skills"]] == ["SQL"]
    application = ok(client.post(f"{API}/vacancies/{w.vac.id}/applications", headers=st), 201)

    # 2. With the model off, the same list is labelled basic
    embeddings.set_embedder(None)
    assert ok(client.get(f"{API}/students/me/matches", headers=st))["mode"] == "basic"
    embeddings.set_embedder(HashEmbedder())

    # 3. The company sees the applicant with the fit snapshot; the placement is confirmed; attendance is recorded
    assert count(client, cs, "applicants_to_review") == 1
    applicants = ok(client.get(f"{API}/vacancies/{w.vac.id}/applications", headers=cs))
    assert applicants[0]["fit_score"] is not None and applicants[0]["match_mode"] == "semantic"
    ok(client.post(f"{API}/applications/{application['id']}/accept", headers=cs))
    placement = ok(client.post(f"{API}/placements", headers=co, json={
        "application_id": application["id"], "academic_supervisor_id": str(w.asA1.id),
        "company_supervisor_id": str(w.cs1.id)}), 201)
    pid = placement["id"]
    p2 = f.placement(w.stA2, w.vac, w.cs1, w.coA1, w.asA1)  # a second trainee, for the bulk approval in step 7
    f.commit()
    ok(client.put(f"{API}/placements/{pid}/attendance/1", headers=cs, json={"full": True}))
    clock.freeze(WEEK1_END + timedelta(days=11))  # week 2 ended 4 days ago: overdue; week 1 is locked
    st, cs, ac, co = (f.headers(u) for u in (w.stA, w.cs1, w.asA1, w.coA1))  # sessions ended; sign in again
    assert count(client, cs, "attendance_to_record") == 3  # week 2 here, weeks 1 and 2 of the second trainee
    ok(client.put(f"{API}/placements/{pid}/attendance/2", headers=cs,
                  json={"attended_days": 4, "note": "One day of sick leave", "full": False}))
    assert count(client, cs, "attendance_to_record") == 2

    # 4. Week 1 is locked; the coordinator unlocks it and the supervisor corrects it
    r = client.put(f"{API}/placements/{pid}/attendance/1", headers=cs, json={"attended_days": 4, "full": False})
    assert r.status_code == 409 and r.json()["code"] == "WEEK_LOCKED"
    ok(client.post(f"{API}/placements/{pid}/attendance/1/unlock", headers=co, json={"reason": "Supervisor away"}))
    weeks = ok(client.put(f"{API}/placements/{pid}/attendance/1", headers=cs,
                          json={"attended_days": 4, "note": "Public holiday", "full": False}))
    assert weeks["percent"] == 80.0

    # 5. The periodic evaluation is visible to the student at once; the final one only with the Final grade
    criteria = ok(client.get(f"{API}/placements/{pid}/evaluations", headers=cs))["rubric"]

    def evaluate(type_, score):
        ok(client.put(f"{API}/placements/{pid}/evaluations/{type_}", headers=cs, json={
            "scores": [{"criterion_id": c["id"], "score": score} for c in criteria], "overall_comment": "Reliable"}))
        ok(client.post(f"{API}/placements/{pid}/evaluations/{type_}/submit", headers=cs))

    evaluate("periodic", 4)
    seen = ok(client.get(f"{API}/placements/{pid}/evaluations", headers=st))["items"]
    assert [i["evaluation"] is not None for i in seen] == [True, False]
    evaluate("final", 4)
    assert ok(client.get(f"{API}/placements/{pid}/evaluations", headers=st))["items"][1]["evaluation"] is None

    # 6. A submission with missing items is refused with the list; then the grade is entered and submitted
    gid = ok(client.get(f"{API}/placements/{pid}/grade", headers=ac))["id"]
    scores = {"component_scores": [{"component_id": str(c.id), "score": "90"} for c in comps[1:]]}
    ok(client.put(f"{API}/placements/{pid}/grade", headers=ac, json=scores))
    r = client.post(f"{API}/grades/{gid}/submit", headers=ac)
    assert r.status_code == 409 and {m["item"] for m in r.json()["missing"]} == {"final_report", "weekly_report"}
    f.finish_reports(db.get(Placement, pid))  # the remaining reports accepted (seeded for the demo)
    f.commit()
    graded = ok(client.post(f"{API}/grades/{gid}/submit", headers=ac))
    company = next(c for c in graded["components"] if c["computed"])
    assert company["score"] == "80.00" and graded["total"] == "86.00"  # 0.4 × 80 + 0.3 × 90 + 0.3 × 90

    # The second trainee's grade, so the coordinator can approve in bulk
    f.finish_reports(p2)
    f.evaluation(p2, w.cs1, "final", [5, 5, 5])
    f.commit()
    gid2 = ok(client.get(f"{API}/placements/{p2.id}/grade", headers=ac))["id"]
    ok(client.put(f"{API}/placements/{p2.id}/grade", headers=ac, json=scores))
    ok(client.post(f"{API}/grades/{gid2}/submit", headers=ac))
    assert count(client, co, "grades_to_approve") == 2

    # 7. One grade returned with a comment and resubmitted; both approved in bulk; the student sees them
    ok(client.post(f"{API}/grades/{gid}/return", headers=co, json={"comment": "Check the report score"}))
    assert count(client, ac, "grades_returned") == 1
    ok(client.post(f"{API}/grades/{gid}/submit", headers=ac))
    results = ok(client.post(f"{API}/grades/bulk-approve", headers=co, json={"grade_ids": [gid, gid2]}))
    assert [r["ok"] for r in results] == [True, True]
    mine = ok(client.get(f"{API}/placements/{pid}/grade", headers=st))
    assert mine["visible"] is True and mine["status"] == "final" and mine["total"] == "86.00"
    assert ok(client.get(f"{API}/placements/{pid}/evaluations", headers=st))["items"][1]["evaluation"] is not None
    assert ok(client.get(f"{API}/placements/{pid}", headers=st))["status"] == "completed"

    # 8. A Final grade reopened with a reason; the audit log shows it
    ok(client.post(f"{API}/grades/{gid}/reopen", headers=co, json={"reason": "Late attendance correction"}))
    assert ok(client.get(f"{API}/placements/{pid}", headers=co))["status"] == "active"
    entry = db.query(AuditEntry).filter_by(entity_type="grade", action="reopen").one()
    assert entry.reason == "Late attendance correction"
    actions = {(e.entity_type, e.action) for e in db.query(AuditEntry)}
    assert {("attendance_week", "record_attendance"), ("attendance_week", "unlock_attendance"),
            ("evaluation", "submit"), ("grade", "submit"), ("grade", "return"), ("grade", "approve")} <= actions

    # 9. The coordinator's cycle statistics and the Platform Admin's figures
    stats = ok(client.get(f"{API}/cycles/{w.cycle.id}/stats", headers=co))["overall"]
    assert stats["placed"] == 2 and stats["enrolled"] == 2 and stats["unplaced"] == 0
    assert stats["attended_days"] == 8 and stats["attendance_rate"] == 80.0
    figures = ok(client.get(f"{API}/platform/stats", headers=f.headers(w.pa)))
    assert figures["universities"] == 2 and figures["published_vacancies"] == 1  # the full one closed itself
    assert set(figures) == {"universities", "colleges", "colleges_with_coordinator", "colleges_without_coordinator",
                            "verified_companies", "users_by_role", "pending_verifications", "oldest_pending_days",
                            "published_vacancies"}  # counts only, no academic records (FR-DSH-05)
