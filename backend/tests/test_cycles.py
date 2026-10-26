"""Training cycles, weeks, grade components, rubric (AT-CYC-01 – 03, AT-CYC-05)."""
from datetime import UTC, date, datetime, time, timedelta

from app.core import clock
from app.cycles.service import build_weeks
from app.models import ReportSlot

API = "/api/v1"


def cycle_body(**extra):
    return {"name": "Co-op Spring 2027", "type": "coop", "start_date": "2027-01-17", "end_date": "2027-04-10",
            "weeks": 12, "working_days": [7, 1, 2, 3, 4], "report_weekday": 4, "report_time": "23:59:00",
            "periodic_eval_due_at": "2027-02-25T20:59:00Z", "final_eval_due_at": "2027-04-15T20:59:00Z",
            "final_report_due_at": "2027-04-15T20:59:00Z", **extra}


# ---------------------------------------------------------------- AT-CYC-01
def test_at_cyc_01_unit_weeks_follow_weekday_and_time():
    weeks = build_weeks(date(2026, 10, 25), date(2027, 1, 16), 12, [7, 1, 2, 3, 4], 4, time(23, 59))
    assert len(weeks) == 12
    for k, wk in enumerate(weeks, start=1):
        assert wk["week_no"] == k
        due_local = wk["report_due_at"].astimezone(clock.RIYADH)
        assert due_local.isoweekday() == 4 and due_local.time() == time(23, 59)
        assert wk["scheduled_days"] == 5
    assert weeks[0]["report_due_at"] == datetime(2026, 10, 29, 20, 59, tzinfo=UTC)
    assert weeks[0]["starts_on"] == date(2026, 10, 25) and weeks[0]["ends_on"] == date(2026, 10, 31)


def test_unit_partial_last_week_counts_only_days_in_the_cycle():
    weeks = build_weeks(date(2026, 10, 25), date(2026, 11, 3), 2, [7, 1, 2, 3, 4], 4, time(12, 0))
    assert [wk["scheduled_days"] for wk in weeks] == [5, 3]


def test_at_cyc_01_api_creates_twelve_weeks(client, w, f):
    r = client.post(f"{API}/cycles", headers=f.headers(w.coA1), json=cycle_body())
    assert r.status_code == 201, r.text
    body = r.json()
    assert len(body["week_list"]) == 12 and body["status"] == "open"
    assert {wk["scheduled_days"] for wk in body["week_list"]} == {5}
    assert client.post(f"{API}/cycles", headers=f.headers(w.coA1), json=cycle_body()).json()["code"] \
        == "DUPLICATE_NAME"


def test_cycle_schedule_validation(client, w, f):
    h = f.headers(w.coA1)
    r = client.post(f"{API}/cycles", headers=h, json=cycle_body(name="Too short", end_date="2027-02-01"))
    assert r.status_code == 422 and r.json()["errors"][0]["field"] == "weeks"
    r = client.post(f"{API}/cycles", headers=h, json=cycle_body(name="Bad days", working_days=[1, 1]))
    assert r.status_code == 422


def test_cycles_are_scoped_to_the_college(client, w, f):
    ids = [c["id"] for c in client.get(f"{API}/cycles", headers=f.headers(w.coA1)).json()]
    assert ids == [str(w.cycle.id)]
    assert client.get(f"{API}/cycles/{w.cycle.id}", headers=f.headers(w.coB1)).status_code == 403
    assert [c["id"] for c in client.get(f"{API}/cycles", headers=f.headers(w.stA)).json()] == [str(w.cycle.id)]
    assert client.get(f"{API}/cycles", headers=f.headers(w.cs1)).json() == []


def test_schedule_edit_regenerates_weeks_until_a_placement_exists(client, w, f):
    h = f.headers(w.coA1)
    r = client.patch(f"{API}/cycles/{w.cycle.id}", headers=h, json={"report_weekday": 3})
    assert r.status_code == 200
    assert r.json()["week_list"][0]["report_due_at"].startswith("2026-10-28")
    f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.commit()
    r = client.patch(f"{API}/cycles/{w.cycle.id}", headers=h, json={"report_weekday": 4})
    assert r.status_code == 409 and r.json()["code"] == "SCHEDULE_LOCKED"
    assert client.patch(f"{API}/cycles/{w.cycle.id}", headers=h, json={"name": "Renamed"}).json()["name"] == "Renamed"


def test_move_one_week_deadline_moves_open_slots(client, w, f, db):
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.commit()
    h = f.headers(w.coA1)
    new_due = "2026-11-01T20:59:00Z"
    assert client.patch(f"{API}/cycles/{w.cycle.id}/weeks/1", headers=h,
                        json={"report_due_at": new_due}).json()["code"] == "REASON_REQUIRED"
    r = client.patch(f"{API}/cycles/{w.cycle.id}/weeks/1", headers=h,
                     json={"report_due_at": new_due, "reason": "National holiday"})
    assert r.status_code == 200
    slot = db.query(ReportSlot).filter_by(placement_id=p.id, week_no=1).one()
    db.refresh(slot)
    assert slot.due_at == datetime(2026, 11, 1, 20, 59, tzinfo=UTC)


# ---------------------------------------------------------------- AT-CYC-02
def test_at_cyc_02_weights_must_total_100(client, w, f):
    h = f.headers(w.coA1)
    items = [{"name_en": "Company evaluation", "name_ar": "تقييم الجهة", "weight": 40,
              "source": "company_final_evaluation"},
             {"name_en": "Weekly reports", "name_ar": "التقارير", "weight": 30, "source": "academic_supervisor"},
             {"name_en": "Final report", "name_ar": "التقرير النهائي", "weight": 20, "source": "academic_supervisor"}]
    r = client.put(f"{API}/cycles/{w.cycle.id}/grade-components", headers=h, json={"components": items})
    assert r.status_code == 422 and r.json()["code"] == "WEIGHTS_NOT_100"
    items[2]["weight"] = 30
    r = client.put(f"{API}/cycles/{w.cycle.id}/grade-components", headers=h, json={"components": items})
    assert r.status_code == 200 and [c["weight"] for c in r.json()] == ["40.00", "30.00", "30.00"]
    two_company = [dict(items[0]), {**items[0], "name_en": "Company 2", "weight": 60}]
    two_company[0]["weight"] = 40
    r = client.put(f"{API}/cycles/{w.cycle.id}/grade-components", headers=h, json={"components": two_company})
    assert r.status_code == 422
    assert client.get(f"{API}/cycles/{w.cycle.id}/grade-components", headers=f.headers(w.asA1)).status_code == 403
    f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)  # a supervisor sees the cycles of their students
    f.commit()
    assert len(client.get(f"{API}/cycles/{w.cycle.id}/grade-components", headers=f.headers(w.asA1)).json()) == 3


# ---------------------------------------------------------------- AT-CYC-03
def test_at_cyc_03_locked_rubric_cannot_change(client, w, f, db):
    h = f.headers(w.coA1)
    levels = {str(n): {"en": f"Level {n}", "ar": f"مستوى {n}"} for n in range(1, 6)}
    body = {"criteria": [{"name_en": "Technical skills", "name_ar": "المهارات التقنية", "levels": levels}]}
    assert client.put(f"{API}/cycles/{w.cycle.id}/rubric", headers=h, json=body).status_code == 200
    missing = {"criteria": [{"name_en": "Teamwork", "name_ar": "العمل الجماعي",
                             "levels": {k: v for k, v in levels.items() if k != "5"}}]}
    assert client.put(f"{API}/cycles/{w.cycle.id}/rubric", headers=h, json=missing).status_code == 422
    w.cycle.rubric_locked_at = clock.now()
    db.merge(w.cycle)
    db.commit()
    r = client.put(f"{API}/cycles/{w.cycle.id}/rubric", headers=h, json=body)
    assert r.status_code == 409 and r.json()["code"] == "RUBRIC_LOCKED"
    rubric = client.get(f"{API}/cycles/{w.cycle.id}/rubric", headers=f.headers(w.stA)).json()
    assert rubric["locked"] is True and rubric["criteria"][0]["name_en"] == "Technical skills"


# ---------------------------------------------------------------- AT-CYC-05
def test_at_cyc_05_closed_cycle_is_read_only(client, w, f):
    h = f.headers(w.coA1)
    assert client.post(f"{API}/cycles/{w.cycle.id}/close", headers=h).json()["status"] == "closed"
    r = client.patch(f"{API}/cycles/{w.cycle.id}", headers=h, json={"name": "Edited"})
    assert r.status_code == 409 and r.json()["code"] == "CYCLE_CLOSED"
    assert client.post(f"{API}/cycles/{w.cycle.id}/reopen", headers=h, json={"reason": ""}).json()["code"] \
        == "REASON_REQUIRED"
    r = client.post(f"{API}/cycles/{w.cycle.id}/reopen", headers=h, json={"reason": "Late grade correction"})
    assert r.json()["status"] == "open"


def test_enrollments_list(client, w, f):
    rows = client.get(f"{API}/cycles/{w.cycle.id}/enrollments", headers=f.headers(w.coA1)).json()
    assert {r["email"] for r in rows} == {w.stA.email, w.stA2.email}
    assert client.get(f"{API}/cycles/{w.cycle.id}/enrollments", headers=f.headers(w.coB1)).status_code == 403


def test_weeks_endpoint(client, w, f):
    weeks = client.get(f"{API}/cycles/{w.cycle.id}/weeks", headers=f.headers(w.stA)).json()
    assert len(weeks) == 12 and weeks[-1]["week_no"] == 12
    clock.advance(timedelta(days=1))
