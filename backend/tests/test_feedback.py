"""The student's evaluation of the company and the survey (AT-EVL-05, AT-DSH-03) and the leniency alert
(AT-DSH-04)."""
from datetime import UTC, datetime

from sqlalchemy import select

from app.core import clock
from app.models import AuditEntry, User
from tests.increment4 import API, final_grade, ok, placed_students, prepare

RATING = {"learning_opportunities": 5, "supervision_quality": 4, "work_environment": 4, "relevance_to_major": 3,
          "would_recommend": True, "comment": "Real projects every week."}
AFTER_TRAINING = datetime(2027, 1, 18, 6, 0, tzinfo=UTC)  # the vacancies end on 17 January 2027


def test_at_evl_05_evaluation_of_the_company_once_after_the_end_and_never_for_the_company(client, w, f, db):
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.commit()
    st, co = f.headers(w.stA), f.headers(w.coA1)
    view = ok(client.get(f"{API}/placements/{p.id}/feedback", headers=st)).json()
    assert view["is_open"] is False and view["open_from"] == "2027-01-17" and view["can_evaluate"] is False
    r = client.put(f"{API}/placements/{p.id}/company-evaluation", headers=st, json=RATING)
    assert r.status_code == 409 and r.json()["code"] == "FEEDBACK_NOT_OPEN"
    assert ok(client.get(f"{API}/dashboard", headers=st)).json()["items"][-1] == {
        "type": "feedback_due", "count": 0, "link": "/student/feedback", "status": None, "oldest_days": None}

    clock.freeze(AFTER_TRAINING)
    st, co = f.headers(w.stA), f.headers(w.coA1)
    assert ok(client.get(f"{API}/dashboard", headers=st)).json()["items"][-1]["count"] == 1
    out = ok(client.put(f"{API}/placements/{p.id}/company-evaluation", headers=st, json=RATING)).json()
    assert out["evaluation"]["supervision_quality"] == 4 and out["can_evaluate"] is False and out["can_answer"]
    r = client.put(f"{API}/placements/{p.id}/company-evaluation", headers=st, json={**RATING, "work_environment": 1})
    assert r.status_code == 409 and r.json()["code"] == "ALREADY_SUBMITTED"
    assert client.put(f"{API}/placements/{p.id}/company-evaluation", headers=st,
                      json={**RATING, "learning_opportunities": 6}).status_code == 422

    seen = ok(client.get(f"{API}/placements/{p.id}/company-evaluation", headers=co)).json()
    assert seen["comment"] == "Real projects every week." and seen["would_recommend"] is True
    for user in (w.cs1, w.ca1, w.asA1, w.coA2, w.stA2, w.pa):
        h = f.headers(user)
        for path in ("feedback", "company-evaluation", "outcome-survey"):
            assert client.get(f"{API}/placements/{p.id}/{path}", headers=h).status_code == 403, (user.role, path)
        assert client.get(f"{API}/cycles/{w.cycle.id}/company-evaluations", headers=h).status_code == 403
    assert client.put(f"{API}/placements/{p.id}/company-evaluation", headers=co, json=RATING).status_code == 403
    entry = db.scalar(select(AuditEntry).where(AuditEntry.entity_type == "company_evaluation"))
    assert entry.action == "submit" and "comment" not in entry.new_value

    summary = ok(client.get(f"{API}/cycles/{w.cycle.id}/company-evaluations", headers=co)).json()
    assert summary["overall"]["answers"] == 1 and summary["overall"]["supervision_quality"] == "4.00"
    assert summary["companies"][0]["company_name"] == "Nakheel" and summary["companies"][0]["recommend_rate"] == 100.0


def test_feedback_opens_with_the_final_grade_before_the_end_date(client, w, f, db):
    prepare(f, w.cycle)
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.commit()
    final_grade(f, db, w, p)
    view = ok(client.get(f"{API}/placements/{p.id}/feedback", headers=f.headers(w.stA))).json()
    assert view["is_open"] is True and view["can_evaluate"] is True


def test_at_dsh_03_job_offer_rate_is_yes_over_answers(client, w, f, db):
    nakheel = placed_students(f, w, 4, w.cs1)
    sahil = placed_students(f, w, 2, w.ca2)
    clock.freeze(AFTER_TRAINING)
    answers = {nakheel[0]: "yes", nakheel[1]: "no", nakheel[2]: "pending", sahil[0]: "yes"}  # two skipped
    for p, answer in answers.items():
        st = f.headers(db.get(User, p.student_id))
        ok(client.put(f"{API}/placements/{p.id}/outcome-survey", headers=st, json={"job_offer": answer}))
    st = f.headers(db.get(User, nakheel[2].student_id))
    out = ok(client.put(f"{API}/placements/{nakheel[2].id}/outcome-survey", headers=st, json={"job_offer": "yes"}))
    assert out.json()["survey"]["job_offer"] == "yes"  # Pending may become Yes later
    r = ok(client.get(f"{API}/cycles/{w.cycle.id}/outcomes", headers=f.headers(w.coA1))).json()
    assert r["overall"] == {"answers": 4, "yes": 3, "no": 1, "pending": 0, "job_offer_rate": 75.0}
    by_name = {c["company_name"]: c for c in r["companies"]}
    assert by_name["Nakheel"]["job_offer_rate"] == round(100 * 2 / 3, 1) and by_name["Sahil"]["answers"] == 1
    assert client.put(f"{API}/placements/{sahil[1].id}/outcome-survey", headers=st,
                      json={"job_offer": "yes"}).status_code == 403  # another student's placement
    for user in (w.cs1, w.ca1, w.asA1, w.coA2, w.stA):
        assert client.get(f"{API}/cycles/{w.cycle.id}/outcomes", headers=f.headers(user)).status_code == 403
    actions = [e.action for e in db.scalars(select(AuditEntry).where(AuditEntry.entity_type == "outcome_survey"))]
    assert actions.count("submit") == 4 and actions.count("update") == 1


def _evaluate_all(f, placements, owner, means):
    for p, m in zip(placements, means, strict=True):
        f.evaluation(p, owner, "final", [m, m, m])
    f.commit()


def test_at_dsh_04_leniency_alert_from_five_final_evaluations(client, w, f, db):
    prepare(f, w.cycle)
    generous, strict = placed_students(f, w, 5, w.cs1), placed_students(f, w, 5, w.ca2)
    _evaluate_all(f, generous, w.cs1, [5, 5, 5, 5, 4])  # mean 4.8
    _evaluate_all(f, strict, w.ca2, [2, 2, 2, 3, 3])  # mean 2.4, so the cycle mean is 3.6
    co = f.headers(w.coA1)
    r = ok(client.get(f"{API}/cycles/{w.cycle.id}/leniency-alerts", headers=co)).json()
    assert r["cycle_mean"] == "3.600" and r["evaluations"] == 10 and r["min_evaluations"] == 5
    top = r["companies"][0]
    assert top["company_name"] == "Nakheel" and top["mean"] == "4.800" and top["difference"] == "1.200"
    assert top["alert"] is True and r["companies"][1]["alert"] is False
    items = {i["type"]: i for i in ok(client.get(f"{API}/dashboard", headers=co)).json()["items"]}
    assert items["leniency_alerts"]["count"] == 1 and items["leniency_alerts"]["link"] == "/coordinator/cycles"
    for user in (w.cs1, w.asA1, w.coA2, w.stA, w.pa):
        assert client.get(f"{API}/cycles/{w.cycle.id}/leniency-alerts", headers=f.headers(user)).status_code == 403


def test_at_dsh_04_four_evaluations_raise_no_alert(client, w, f, db):
    prepare(f, w.cycle)
    generous, strict = placed_students(f, w, 4, w.cs1), placed_students(f, w, 4, w.ca2)
    _evaluate_all(f, generous, w.cs1, [5, 5, 5, 5])
    _evaluate_all(f, strict, w.ca2, [2, 2, 2, 2])
    r = ok(client.get(f"{API}/cycles/{w.cycle.id}/leniency-alerts", headers=f.headers(w.coA1))).json()
    assert r["companies"][0]["difference"] == "1.500" and not any(c["alert"] for c in r["companies"])
