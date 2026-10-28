"""Similarity detection (AT-SIM-01 – 03, AT-PER-04) and the passage functions."""
import time

import pytest
from sqlalchemy import select, text

from app.ai import embeddings
from app.core.db import SessionLocal
from app.jobs import jobs
from app.models import AuditEntry, ReportSlot, ReportVersion, SimilarityCheck
from app.similarity.passages import MIN_WORDS, containment, covered, split
from tests.factories import HashEmbedder

API = "/api/v1"
COPIED = ("This week I designed the database schema for the inventory module and wrote the migration scripts. "
          "I added indexes on the product and warehouse tables, because the stock report was slow with large "
          "data. Then I built REST endpoints for creating, updating, and listing items, with validation of every "
          "field and clear error messages. My supervisor reviewed the pull request and asked me to split one large "
          "function into smaller ones, which made the code easier to test. I also wrote unit tests for the stock "
          "calculation and fixed two bugs they revealed in the rounding of quantities.")
OTHER_SOURCE = ("I spent the week on the mobile application of the delivery team. I fixed the crash that happened "
                "when the driver opened the map without a network, and I added a retry button that loads the route "
                "again. Later I measured the start time of the app on old phones and removed two libraries that were "
                "not needed, which made the first screen appear about one second faster. On Thursday I presented "
                "the changes to the team and wrote notes for the next release.")
OWN = ("I attended the security awareness session of the company and learned how phishing emails are recognised. "
       "With the network team I visited the server room and saw how backups are rotated every night. I asked many "
       "questions about the monitoring dashboard and wrote a short summary for my academic supervisor.")
OWN_OTHER = ("On Monday I joined the planning meeting and estimated my tasks for the sprint. In the afternoons I "
             "paired with a tester to understand how they write test cases, and I read the coding guidelines of the "
             "company so my next pull requests follow them.")
ORIGINAL_SAME_TOPIC = ("My main task was the inventory module again. Together with a senior developer I planned how "
                       "products move between warehouses and drew the tables on the whiteboard before writing any "
                       "code. We agreed to keep a history table for every stock change so that audits are possible. "
                       "I implemented the transfer endpoint and tested it with sample data from two warehouses, and "
                       "next week I will add permissions so that only managers approve large transfers.")


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r.json() if r.content else None


@pytest.fixture
def model():
    embeddings.set_embedder(HashEmbedder())
    yield
    embeddings.set_embedder(None)


def week(db, placement, n=1) -> ReportSlot:
    return db.scalars(select(ReportSlot).where(ReportSlot.placement_id == placement.id, ReportSlot.week_no == n)).one()


def submit(client, f, student, slot, tasks, learning=OWN):
    h = f.headers(student)
    ok(client.put(f"{API}/report-slots/{slot.id}/draft", headers=h, json={
        "tasks_performed": tasks, "learning": learning, "challenges": "Time management.",
        "next_week_plan": "Continue the module."}))
    ok(client.post(f"{API}/report-slots/{slot.id}/submit", headers=h))


def latest(db, slot) -> ReportVersion:
    db.expire_all()
    return db.scalars(select(ReportVersion).where(ReportVersion.slot_id == slot.id)
                      .order_by(ReportVersion.version_no.desc())).first()


@pytest.fixture
def world(model, w, f, db):
    """stA (college A1) copies from stA2 (A1) and from stX (A2, same university); stB (another university) holds
    the same text as stA2."""
    vac = f.vacancy(w.cs1, [w.cs_major, w.cis_major], seats=10, title="Software Trainee")
    w.stX = f.student(w.A2, w.cs_major, "3.80")
    w.cycleA2 = f.cycle(w.coA2, name="Co-op A2")
    f.enroll(w.cycleA2, w.stX, w.coA2)
    w.asB1 = f.user("academic_supervisor", college=w.B1)
    f.commit()
    w.pA = f.placement(w.stA, vac, w.cs1, w.coA1, w.asA1)
    w.pA2 = f.placement(w.stA2, vac, w.cs1, w.coA1, w.asA1)
    w.pX = f.placement(w.stX, vac, w.cs1, w.coA2, w.asA2)
    w.pB = f.placement(w.stB, vac, w.cs1, w.coB1, w.asB1)
    f.commit()
    return w


# ---------------------------------------------------------------- unit
def test_unit_passages_keep_their_place_in_the_text():
    parts = split(COPIED + "\n" + OWN)
    assert len(parts) >= 2
    for p in parts:
        assert (COPIED + "\n" + OWN)[p.start:p.end] == p.text
        assert len(p.text.split()) >= MIN_WORDS // 2
    assert split("") == [] and len(split("Short report. Only two sentences.")) == 1
    long = " ".join(["word"] * 200)
    assert [len(p.text.split()) for p in split(long)] == [25] * 8


def test_unit_containment_and_coverage():
    assert containment(COPIED, COPIED, 5) == 1.0
    assert containment(ORIGINAL_SAME_TOPIC, COPIED, 5) < 0.1
    arabic = "عملت هذا الأسبوع على تصميم قاعدة البيانات لوحدة المخزون وكتبت سكربتات الترحيل"
    assert containment(arabic, "مقدمة. " + arabic.replace("أ", "ا"), 5) == 1.0  # normalized Arabic
    assert covered([(0, 10), (5, 15), (20, 25), (21, 22)]) == 20


# ---------------------------------------------------------------- AT-SIM-01 and AT-SIM-02
def test_at_sim_01_02_copied_report_flagged_within_the_university_only(client, world, f, db):
    w = world
    submit(client, f, w.stA2, week(db, w.pA2), COPIED)
    submit(client, f, w.stX, week(db, w.pX), OTHER_SOURCE)
    submit(client, f, w.stB, week(db, w.pB), COPIED + " " + OTHER_SOURCE)  # another university: never a source
    slot = week(db, w.pA)
    submit(client, f, w.stA, slot, COPIED + " " + OTHER_SOURCE)
    version = latest(db, slot)
    result = ok(client.get(f"{API}/report-versions/{version.id}/similarity", headers=f.headers(w.asA1)))
    assert result["status"] == "done" and result["is_flagged"] is True and result["advisory"] is True
    assert result["model_version"] == "test-hash@1"
    sources = {s["version_id"]: s for s in result["sources"]}
    assert set(sources) == {str(latest(db, week(db, w.pA2)).id), str(latest(db, week(db, w.pX)).id)}
    assert all(s["author"] is None for s in result["sources"])  # not for the academic supervisor
    first = result["sources"][0]
    assert first["week_no"] == 1 and first["cycle_name"] and float(first["score"]) >= 0.3
    pair = first["passages"][0]
    assert pair["report_text"] and pair["source_text"] and pair["cosine"] >= 0.9
    as_co = ok(client.get(f"{API}/report-versions/{version.id}/similarity", headers=f.headers(w.coA1)))
    authors = {s["version_id"]: s["author"] for s in as_co["sources"]}
    assert authors[str(latest(db, week(db, w.pA2)).id)]["name_en"] == w.stA2.name_en  # the author's coordinator
    assert authors[str(latest(db, week(db, w.pX)).id)] is None  # author of another college
    for user in (w.stA, w.cs1, w.coA2, w.asA2):
        assert client.get(f"{API}/report-versions/{version.id}/similarity", headers=f.headers(user)).status_code \
            == 403
    flagged = ok(client.get(f"{API}/similarity-checks?flagged=true&decided=false", headers=f.headers(w.asA1)))
    assert [c["version_id"] for c in flagged] == [str(version.id)]
    items = ok(client.get(f"{API}/dashboard", headers=f.headers(w.asA1)))["items"]
    assert next(i for i in items if i["type"] == "similarity_flags")["count"] == 1


def test_at_sim_01_earlier_versions_of_the_same_report_are_not_sources(client, world, f, db):
    w = world
    slot = week(db, w.pA)
    submit(client, f, w.stA, slot, COPIED)
    ok(client.post(f"{API}/report-slots/{slot.id}/request-revision", headers=f.headers(w.asA1),
                   json={"comment": "Add more details"}))
    submit(client, f, w.stA, slot, COPIED + " I also documented the endpoints.")
    result = ok(client.get(f"{API}/report-versions/{latest(db, slot).id}/similarity", headers=f.headers(w.asA1)))
    assert result["status"] == "done" and result["is_flagged"] is False and result["sources"] == []


def test_original_report_on_the_same_topic_is_not_flagged(client, world, f, db):
    w = world
    submit(client, f, w.stA2, week(db, w.pA2), COPIED)
    slot = week(db, w.pA)
    submit(client, f, w.stA, slot, ORIGINAL_SAME_TOPIC, learning=OWN_OTHER)
    check = db.scalars(select(SimilarityCheck).where(SimilarityCheck.version_id == latest(db, slot).id)).one()
    assert check.status == "done" and check.is_flagged is False and float(check.max_score) < 0.3


# ---------------------------------------------------------------- AT-SIM-03
def test_at_sim_03_advisory_decision_changes_nothing_else(client, world, f, db):
    w = world
    submit(client, f, w.stA2, week(db, w.pA2), COPIED)
    slot = week(db, w.pA)
    submit(client, f, w.stA, slot, COPIED)
    version = latest(db, slot)
    url = f"{API}/report-versions/{version.id}/similarity/decision"
    ah = f.headers(w.asA1)
    assert client.post(url, headers=ah, json={"decision": "overlap_confirmed", "comment": " "}).json()["code"] \
        == "COMMENT_REQUIRED"
    assert client.post(url, headers=f.headers(w.coA1), json={"decision": "no_issue", "comment": "x"}) \
        .status_code == 403
    result = ok(client.post(url, headers=ah, json={"decision": "overlap_confirmed",
                                                   "comment": "Most of the tasks section is copied."}))
    assert result["decision"] == "overlap_confirmed" and result["decided_by_en"] == w.asA1.name_en
    db.expire_all()
    assert db.get(ReportSlot, slot.id).status == "submitted"  # FR-SIM-03: the status is untouched
    entry = db.scalars(select(AuditEntry).where(AuditEntry.action == "similarity_decision")).one()
    assert entry.reason == "Most of the tasks section is copied."
    other = latest(db, week(db, w.pA2))
    assert client.post(f"{API}/report-versions/{other.id}/similarity/decision", headers=ah,
                       json={"decision": "no_issue", "comment": "ok"}).json()["code"] == "NOT_FLAGGED"
    history = ok(client.get(f"{API}/history/report_slot/{slot.id}", headers=f.headers(w.stA)))
    assert "similarity_decision" not in [e["action"] for e in history]  # the student does not see the check
    assert "similarity_decision" in [e["action"] for e in ok(client.get(f"{API}/history/report_slot/{slot.id}",
                                                                        headers=ah))]


def test_without_the_model_the_check_waits_for_the_retry_job(client, world, f, db):
    w = world
    submit(client, f, w.stA2, week(db, w.pA2), COPIED)
    embeddings.set_embedder(None)
    slot = week(db, w.pA)
    submit(client, f, w.stA, slot, COPIED)
    version = latest(db, slot)
    check = db.scalars(select(SimilarityCheck).where(SimilarityCheck.version_id == version.id)).one()
    assert check.status == "failed" and check.error == "embedding model not available" and check.attempts == 1
    embeddings.set_embedder(HashEmbedder())
    jobs.run(SessionLocal, "similarity_retry")
    db.expire_all()
    check = db.get(SimilarityCheck, check.id)
    assert check.status == "done" and check.is_flagged is True and check.attempts == 2


# ---------------------------------------------------------------- AT-PER-04
def test_at_per_04_result_within_2_minutes_with_10000_stored_reports(client, world, f, db):
    """10,000 stored report versions with 2 passages each at the student's university, made inside the database
    (random vectors), then one submission and its check."""
    w = world
    source_slot = week(db, w.pA2, 2)
    university = db.execute(text("SELECT university_id FROM colleges WHERE id = :c"), {"c": w.A1.id}).scalar()
    db.execute(text("DROP INDEX ix_report_passages_embedding"))
    db.execute(text("""
        INSERT INTO report_versions (id, slot_id, version_no, body_text, submitted_at)
        SELECT gen_random_uuid(), :slot, g, 'stored report ' || g, now() FROM generate_series(1, 10000) AS g"""),
               {"slot": source_slot.id})
    db.execute(text("""
        INSERT INTO report_passages (version_id, slot_id, university_id, idx, char_start, char_end, text, embedding)
        SELECT v.id, v.slot_id, :uni, i, 0, 10, 'passage ' || i,
               (SELECT array_agg(random() - 0.5)::real[] FROM generate_series(1, 384)
                WHERE v.id IS NOT NULL)::vector(384)::halfvec(384)
        FROM report_versions AS v CROSS JOIN generate_series(0, 1) AS i WHERE v.slot_id = :slot"""),
               {"uni": university, "slot": source_slot.id})
    db.execute(text("CREATE INDEX ix_report_passages_embedding ON report_passages "
                    "USING hnsw (embedding halfvec_cosine_ops)"))
    db.commit()
    assert db.scalar(text("SELECT count(*) FROM report_passages")) == 20_000
    slot = week(db, w.pA)
    started = time.perf_counter()
    submit(client, f, w.stA, slot, COPIED)
    elapsed = time.perf_counter() - started
    check = db.scalars(select(SimilarityCheck).where(SimilarityCheck.version_id == latest(db, slot).id)).one()
    print(f"NFR-PER-04: submission and check with 10,000 stored reports in {elapsed:.2f} s")  # for the test report
    assert check.status == "done" and elapsed < 120
