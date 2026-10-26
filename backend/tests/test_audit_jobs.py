"""Audit log (AT-AUD-02) and scheduled jobs (Increment 1 design, Section 7)."""
from datetime import timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core import clock
from app.core.db import SessionLocal, engine
from app.jobs import jobs
from app.models import AccountToken, AuditEntry, JobRun, UserSession
from tests.permissions.test_matrix import MATRIX

API = "/api/v1"


# ---------------------------------------------------------------- AT-AUD-02
def test_at_aud_02_no_endpoint_changes_audit_entries():
    audit_routes = [k for k in MATRIX if "/audit" in k]
    assert audit_routes == ["GET /api/v1/audit-log"]


def test_at_aud_02_database_refuses_update_and_delete(w, db):
    db.add(AuditEntry(role="system", action="test", entity_type="user", entity_id="x"))
    db.commit()
    for sql in ("UPDATE audit_log SET action = 'changed'", "DELETE FROM audit_log"):
        with pytest.raises(DBAPIError), engine.begin() as conn:
            conn.execute(text(sql))


def test_at_aud_02_filters_and_scope(client, w, f):
    f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.application(w.stB, f.vacancy(w.ca2, [w.cs_major]))
    f.commit()
    co = f.headers(w.coA1)
    entries = client.get(f"{API}/audit-log?page_size=100", headers=co).json()["items"]
    assert entries and all(e["student_id"] in (None, str(w.stA.id), str(w.stA2.id)) for e in entries)
    actions = {e["action"] for e in entries}
    assert {"apply", "accept", "confirm"} <= actions
    mine = client.get(f"{API}/audit-log?student_id={w.stA.id}", headers=co).json()["items"]
    assert mine and {e["student_id"] for e in mine} == {str(w.stA.id)}
    placements = client.get(f"{API}/audit-log?entity_type=placement", headers=co).json()["items"]
    assert [e["action"] for e in placements] == ["confirm"]
    by_user = client.get(f"{API}/audit-log?user_id={w.cs1.id}", headers=co).json()["items"]
    assert {e["action"] for e in by_user} == {"accept"}
    future = (clock.now() + timedelta(days=1)).isoformat().replace("+00:00", "Z")
    assert client.get(f"{API}/audit-log", headers=co, params={"date_from": future}).json()["items"] == []
    other = client.get(f"{API}/audit-log?page_size=100", headers=f.headers(w.coB1)).json()["items"]
    assert {e["student_id"] for e in other} <= {None, str(w.stB.id)}
    platform = client.get(f"{API}/audit-log?page_size=100", headers=f.headers(w.pa)).json()["items"]
    assert all(e["entity_type"] not in ("placement", "application", "report_slot") for e in platform)


# ---------------------------------------------------------------- jobs
def test_jobs_record_runs_and_skip_when_locked(w, db):
    jobs.run(SessionLocal, "flag_missing")
    row = db.query(JobRun).one()
    assert row.status == "ok" and row.items == 0
    with engine.connect() as conn:
        conn.execute(text("SELECT pg_advisory_lock(7101)"))
        jobs.run(SessionLocal, "flag_missing")  # another instance holds the lock: nothing happens
        conn.execute(text("SELECT pg_advisory_unlock(7101)"))
        conn.commit()
    assert db.query(JobRun).count() == 1


def test_job_failure_is_recorded_and_releases_the_lock(w, db, monkeypatch):
    def boom(_db):
        raise RuntimeError("disk full")
    with SessionLocal() as other:  # a second pooled connection, so a leaked lock would show
        other.execute(text("SELECT 1"))
        monkeypatch.setitem(jobs.JOBS, "cleanup", boom)
        jobs.run(SessionLocal, "cleanup")
    row = db.query(JobRun).one()
    assert row.status == "error" and "disk full" in row.error
    with engine.connect() as conn:
        held = conn.execute(text("SELECT count(*) FROM pg_locks WHERE locktype = 'advisory'")).scalar()
    assert held == 0


def test_missing_flag_ignores_cancelled_placements(client, w, f, db):
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.commit()
    client.post(f"{API}/placements/{p.id}/cancel", headers=f.headers(w.coA1), json={"reason": "Moved city"})
    clock.advance(timedelta(days=30))
    jobs.run(SessionLocal, "flag_missing")
    assert db.query(JobRun).one().items == 0


def test_cleanup_removes_old_sessions_and_tokens(w, f, db):
    f.headers(w.stA)
    db.add(AccountToken(user_id=w.stA.id, purpose="password_reset", token_hash="h" * 64,
                        expires_at=clock.now() + timedelta(hours=1)))
    db.commit()
    clock.advance(timedelta(days=40))
    jobs.run(SessionLocal, "cleanup")
    db.expire_all()
    run = db.query(JobRun).one()
    assert run.status == "ok", run.error
    assert db.query(UserSession).count() == 0 and db.query(AccountToken).count() == 0
