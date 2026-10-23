"""Weekly and final reports (AT-REP-01 – 07, AT-WFL-01)."""
from datetime import UTC, datetime, timedelta

import pytest

from app.core import clock
from app.core.db import SessionLocal
from app.core.errors import ApiError
from app.jobs import jobs
from app.models import ReportSlot
from app.reports.service import TRANSITIONS, is_late, next_state
from tests.factories import PNG, docx, pdf

API = "/api/v1"
WEEK1_DUE = datetime(2026, 10, 29, 20, 59, tzinfo=UTC)  # Thursday 23:59 in Riyadh
FULL = {"tasks_performed": "Built the login API", "learning": "FastAPI dependencies",
        "challenges": "Time zones", "next_week_plan": "Write tests"}


@pytest.fixture
def placed(w, f, db):
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.commit()
    slots = {(s.kind, s.week_no): s for s in db.query(ReportSlot).filter_by(placement_id=p.id)}
    return p, slots


def slot_url(slot, suffix=""):
    return f"{API}/report-slots/{slot.id}{suffix}"


# ---------------------------------------------------------------- AT-WFL-01 (unit)
STATES = ("draft", "submitted", "revision_requested", "accepted", "closed_missing")
ACTIONS = ("submit", "accept", "request_revision", "close_missing")


def test_at_wfl_01_every_allowed_transition_passes():
    for (state, action), target in TRANSITIONS.items():
        assert next_state(state, action) == target


def test_at_wfl_01_disallowed_transitions_from_each_state_are_rejected():
    for state in STATES:
        refused = [a for a in ACTIONS if (state, a) not in TRANSITIONS]
        assert refused, state
        for action in refused:
            with pytest.raises(ApiError) as exc:
                next_state(state, action)
            assert exc.value.status == 409
    with pytest.raises(ApiError) as exc:
        next_state("closed_missing", "submit")
    assert exc.value.code == "SLOT_CLOSED"


def test_at_rep_04_unit_deadline_minute_is_inclusive():
    assert not is_late(WEEK1_DUE - timedelta(minutes=1), WEEK1_DUE)
    assert not is_late(WEEK1_DUE + timedelta(seconds=59), WEEK1_DUE)
    assert is_late(WEEK1_DUE + timedelta(minutes=1), WEEK1_DUE)


# ---------------------------------------------------------------- AT-REP-01
def test_at_rep_01_slots_and_deadlines(client, w, f, placed):
    p, _ = placed
    rows = client.get(f"{API}/placements/{p.id}/report-slots", headers=f.headers(w.stA)).json()
    weekly = [r for r in rows if r["kind"] == "weekly"]
    assert len(weekly) == 12 and len([r for r in rows if r["kind"] == "final"]) == 1
    assert [r["week_no"] for r in weekly] == list(range(1, 13))
    assert weekly[0]["due_at"].startswith("2026-10-29T20:59")
    assert weekly[11]["due_at"].startswith("2027-01-14T20:59")
    assert client.get(f"{API}/placements/{p.id}/report-slots", headers=f.headers(w.stA2)).status_code == 403


# ---------------------------------------------------------------- AT-REP-02
def test_at_rep_02_attachment_limits(client, w, f, placed):
    _, slots = placed
    s1 = slots[("weekly", 1)]
    h = f.headers(w.stA)
    big = PNG + b"0" * (11 * 1024 * 1024)
    r = client.post(slot_url(s1, "/draft/attachments"), headers=h, files={"file": ("big.png", big, "image/png")})
    assert r.status_code == 413
    for i in range(3):
        r = client.post(slot_url(s1, "/draft/attachments"), headers=h,
                        files={"file": (f"shot{i}.png", PNG, "image/png")})
        assert r.status_code == 201, r.text
    r = client.post(slot_url(s1, "/draft/attachments"), headers=h, files={"file": ("shot4.png", PNG, "image/png")})
    assert r.status_code == 409 and r.json()["code"] == "TOO_MANY_ATTACHMENTS"
    client.put(slot_url(s1, "/draft"), headers=h, json=FULL)
    r = client.post(slot_url(s1, "/submit"), headers=h)
    assert r.status_code == 200 and r.json()["status"] == "submitted"
    assert len(r.json()["submitted"][0]["attachments"]) == 3
    att = r.json()["submitted"][0]["attachments"][0]
    assert client.get(f"{API}/files/{att['file_id']}", headers=f.headers(w.asA1)).status_code == 200
    assert client.get(f"{API}/files/{att['file_id']}", headers=f.headers(w.asA2)).status_code == 403


def test_weekly_report_needs_all_fields(client, w, f, placed):
    _, slots = placed
    s1 = slots[("weekly", 1)]
    h = f.headers(w.stA)
    assert client.post(slot_url(s1, "/submit"), headers=h).json()["code"] == "NOTHING_TO_SUBMIT"
    client.put(slot_url(s1, "/draft"), headers=h, json={"tasks_performed": "Something"})
    r = client.post(slot_url(s1, "/submit"), headers=h)
    assert r.status_code == 422 and {e["field"] for e in r.json()["errors"]} == {"learning", "challenges",
                                                                                 "next_week_plan"}


def test_final_report_needs_a_main_document(client, w, f, placed):
    _, slots = placed
    final = slots[("final", None)]
    h = f.headers(w.stA)
    client.put(slot_url(final, "/draft"), headers=h, json={"summary": "Twelve weeks on the backend team"})
    assert client.post(slot_url(final, "/submit"), headers=h).json()["code"] == "MAIN_DOCUMENT_REQUIRED"
    r = client.post(slot_url(final, "/draft/attachments"), headers=h, data={"role": "main"},
                    files={"file": ("final.png", PNG, "image/png")})
    assert r.status_code == 415
    r = client.post(slot_url(final, "/draft/attachments"), headers=h, data={"role": "main"},
                    files={"file": ("final.docx", docx("Final report of the training period"), "application/"
                                    "vnd.openxmlformats-officedocument.wordprocessingml.document")})
    assert r.status_code == 201
    r = client.post(slot_url(final, "/submit"), headers=h)
    assert r.status_code == 200 and r.json()["submitted"][0]["attachments"][0]["role"] == "main"
    weekly = slots[("weekly", 2)]
    r = client.post(slot_url(weekly, "/draft/attachments"), headers=h, data={"role": "main"},
                    files={"file": ("x.pdf", pdf("text"), "application/pdf")})
    assert r.status_code == 422


# ---------------------------------------------------------------- AT-REP-03
def test_at_rep_03_drafts_private_and_submission_final(client, w, f, placed):
    _, slots = placed
    s1 = slots[("weekly", 1)]
    h = f.headers(w.stA)
    client.put(slot_url(s1, "/draft"), headers=h, json=FULL)
    view = client.get(slot_url(s1), headers=f.headers(w.asA1)).json()
    assert view["draft"] is None and view["submitted"] == [] and view["has_draft"] is True
    assert client.get(slot_url(s1), headers=h).json()["draft"]["tasks_performed"] == "Built the login API"
    draft_id = client.get(slot_url(s1), headers=h).json()["draft"]["id"]
    assert client.get(f"{API}/report-versions/{draft_id}", headers=f.headers(w.asA1)).status_code == 404
    client.post(slot_url(s1, "/submit"), headers=h)
    r = client.put(slot_url(s1, "/draft"), headers=h, json={"learning": "changed"})
    assert r.status_code == 409 and r.json()["code"] == "INVALID_TRANSITION"
    assert client.put(slot_url(s1, "/draft"), headers=f.headers(w.asA1), json=FULL).status_code == 403
    assert client.get(slot_url(s1), headers=f.headers(w.stA2)).status_code == 403


# ---------------------------------------------------------------- AT-REP-04
def test_at_rep_04_on_time_late_and_missing(client, w, f, placed, db):
    _, slots = placed
    s1, s2, s3 = slots[("weekly", 1)], slots[("weekly", 2)], slots[("weekly", 3)]
    h = f.headers(w.stA)
    for s in (s1, s2):
        client.put(slot_url(s, "/draft"), headers=h, json=FULL)
    clock.freeze(WEEK1_DUE - timedelta(minutes=1))
    h = f.headers(w.stA)
    r = client.post(slot_url(s1, "/submit"), headers=h).json()
    assert r["is_late"] is False and r["submitted"][0]["is_late"] is False
    clock.freeze(s2.due_at + timedelta(minutes=1))
    h = f.headers(w.stA)
    r = client.post(slot_url(s2, "/submit"), headers=h).json()
    assert r["is_late"] is True and r["submitted"][0]["submitted_at"].startswith("2026-11-05T21:00")
    clock.freeze(s3.due_at + timedelta(minutes=10))
    jobs.run(SessionLocal, "flag_missing")
    db.expire_all()
    flagged = {s.week_no for s in db.query(ReportSlot).filter_by(is_missing=True)}
    assert flagged == {3}
    jobs.run(SessionLocal, "flag_missing")  # idempotent
    assert db.query(ReportSlot).filter_by(is_missing=True).count() == 1
    h = f.headers(w.stA)
    client.put(slot_url(s3, "/draft"), headers=h, json=FULL)
    r = client.post(slot_url(s3, "/submit"), headers=h).json()
    assert r["status"] == "submitted" and r["is_late"] is True and r["is_missing"] is True  # both flags stay


# ---------------------------------------------------------------- AT-REP-05
def test_at_rep_05_revision_cycle_keeps_versions(client, w, f, placed):
    _, slots = placed
    s1 = slots[("weekly", 1)]
    st, sup = f.headers(w.stA), f.headers(w.asA1)
    client.put(slot_url(s1, "/draft"), headers=st, json=FULL)
    client.post(slot_url(s1, "/submit"), headers=st)
    r = client.post(slot_url(s1, "/request-revision"), headers=sup, json={"comment": "  "})
    assert r.status_code == 422 and r.json()["code"] == "COMMENT_REQUIRED"
    r = client.post(slot_url(s1, "/request-revision"), headers=sup, json={"comment": "Add the test results"})
    assert r.json()["status"] == "revision_requested"
    assert client.post(slot_url(s1, "/accept"), headers=sup).json()["code"] == "INVALID_TRANSITION"
    draft = client.get(slot_url(s1), headers=st).json()
    assert draft["allowed_actions"] == ["save_draft", "submit"]
    client.put(slot_url(s1, "/draft"), headers=st, json={"learning": "FastAPI dependencies and pytest fixtures"})
    r = client.post(slot_url(s1, "/submit"), headers=st).json()
    assert [v["version_no"] for v in r["submitted"]] == [1, 2]
    assert r["submitted"][1]["tasks_performed"] == "Built the login API"  # copied from version 1
    assert r["submitted"][0]["review"]["decision"] == "revision_requested"
    r = client.post(slot_url(s1, "/accept"), headers=sup).json()
    assert r["status"] == "accepted" and r["allowed_actions"] == []
    first = r["submitted"][0]["id"]
    assert client.get(f"{API}/report-versions/{first}", headers=f.headers(w.cs1)).json()["version_no"] == 1
    assert client.post(slot_url(s1, "/accept"), headers=f.headers(w.asA1b)).status_code == 403


# ---------------------------------------------------------------- AT-REP-06
def test_at_rep_06_comments(client, w, f, placed):
    _, slots = placed
    s1 = slots[("weekly", 1)]
    r = client.post(slot_url(s1, "/comments"), headers=f.headers(w.stA), json={"body": "Is the format right?"})
    assert r.status_code == 201
    clock.advance(timedelta(minutes=5))
    r = client.post(slot_url(s1, "/comments"), headers=f.headers(w.asA1), json={"body": "Yes, keep it short."})
    comments = r.json()
    assert [c["author_role"] for c in comments] == ["student", "academic_supervisor"]
    assert comments[0]["created_at"] and comments[0]["author_en"] == w.stA.name_en
    assert client.get(slot_url(s1, "/comments"), headers=f.headers(w.cs1)).status_code == 200
    assert client.post(slot_url(s1, "/comments"), headers=f.headers(w.cs1), json={"body": "Hi"}).status_code == 403
    assert client.get(slot_url(s1), headers=f.headers(w.cs1)).json()["can_comment"] is False
    assert client.get(slot_url(s1, "/comments"), headers=f.headers(w.ca2)).status_code == 403


# ---------------------------------------------------------------- AT-REP-07
def test_at_rep_07_closed_slot_refuses_submission(client, w, f, placed):
    _, slots = placed
    s2 = slots[("weekly", 2)]
    st, sup = f.headers(w.stA), f.headers(w.asA1)
    client.put(slot_url(s2, "/draft"), headers=st, json=FULL)
    r = client.post(slot_url(s2, "/close-missing"), headers=sup)
    assert r.status_code == 409 and r.json()["code"] == "DEADLINE_NOT_PASSED"
    clock.freeze(s2.due_at + timedelta(hours=1))
    st, sup = f.headers(w.stA), f.headers(w.asA1)
    assert client.get(slot_url(s2), headers=sup).json()["allowed_actions"] == ["close_missing"]
    r = client.post(slot_url(s2, "/close-missing"), headers=sup).json()
    assert r["status"] == "closed_missing" and r["is_missing"] is True
    r = client.post(slot_url(s2, "/submit"), headers=st)
    assert r.status_code == 409 and r.json()["code"] == "SLOT_CLOSED"
    assert client.put(slot_url(s2, "/draft"), headers=st, json=FULL).json()["code"] == "SLOT_CLOSED"


def test_closed_cycle_freezes_reports(client, w, f, placed):
    _, slots = placed
    client.post(f"{API}/cycles/{w.cycle.id}/close", headers=f.headers(w.coA1))
    r = client.put(slot_url(slots[("weekly", 1)], "/draft"), headers=f.headers(w.stA), json=FULL)
    assert r.status_code == 409 and r.json()["code"] == "CYCLE_CLOSED"


def test_remove_draft_attachment(client, w, f, placed):
    _, slots = placed
    s1 = slots[("weekly", 1)]
    h = f.headers(w.stA)
    att = client.post(slot_url(s1, "/draft/attachments"), headers=h,
                      files={"file": ("a.png", PNG, "image/png")}).json()["draft"]["attachments"][0]["id"]
    r = client.delete(slot_url(s1, f"/draft/attachments/{att}"), headers=h)
    assert r.status_code == 200 and r.json()["draft"]["attachments"] == []
    assert client.delete(slot_url(s1, f"/draft/attachments/{att}"), headers=h).status_code == 404
