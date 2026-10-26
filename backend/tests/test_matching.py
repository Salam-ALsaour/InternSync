"""Matching (AT-MAT-01 – 05, AT-MAT-07, AT-AI-02, AT-PER-02; FR-MAT-06 plan)."""
import statistics
import time
from datetime import timedelta
from decimal import Decimal

import pytest

from app.ai import embeddings
from app.core import clock
from app.core.db import SessionLocal
from app.jobs import jobs
from app.matching.scoring import Weights, score
from app.models import Application, MatchScore, SkillResource, StudentProfile, StudentSkill, Vacancy, VacancyMajor
from tests.factories import HashEmbedder

API = "/api/v1"


def confirm(db, student, *skills):
    for k in skills:
        db.add(StudentSkill(student_id=student.id, skill_id=k.id, source="manual", confirmed_at=clock.now()))
    db.get(StudentProfile, student.id).skills_confirmed_at = clock.now()
    db.commit()


@pytest.fixture
def model():
    embeddings.set_embedder(HashEmbedder())
    yield
    embeddings.set_embedder(None)


# ---------------------------------------------------------------- unit
def test_at_mat_02_unit_required_skills_raise_the_score():
    w = Weights()
    has = score({"python", "sql"}, {"python", "sql"}, set(), 0.85, w)
    lacks = score({"python", "sql"}, {"react", "docker"}, set(), 0.85, w)
    assert has.score > lacks.score
    assert has.required == 1.0 and lacks.required == 0.0


def test_at_mat_05_unit_matched_and_missing_are_the_set_comparison():
    fit = score({"a", "b", "x"}, {"a", "b", "c"}, {"x", "y"}, None, Weights())
    assert fit.matched == ["a", "b"] and fit.missing == ["c"]
    assert fit.preferred == 0.5


def test_at_mat_04_unit_basic_mode_without_a_vector():
    w = Weights()
    fit = score({"a"}, {"a", "b"}, set(), None, w)
    assert fit.mode == "basic" and fit.semantic is None and fit.score == 50.0
    semantic = score({"a"}, {"a", "b"}, set(), 0.95, w)
    assert semantic.mode == "semantic" and semantic.semantic == 1.0 and semantic.score == 75.0


def test_unit_semantic_part_is_clamped():
    w = Weights(floor=0.7, ceiling=0.9)
    assert score(set(), set(), set(), 0.5, w).semantic == 0.0
    assert score(set(), set(), set(), 0.99, w).semantic == 1.0
    assert score(set(), set(), set(), 0.8, w).semantic == pytest.approx(0.5)


# ---------------------------------------------------------------- API
def test_ranking_needs_verification_and_confirmed_skills(client, w, f, db):
    pending = f.student(w.A1, w.cs_major, status="pending")
    db.commit()
    assert client.get(f"{API}/students/me/matches", headers=f.headers(pending)).json()["code"] \
        == "VERIFICATION_REQUIRED"
    r = client.get(f"{API}/students/me/matches", headers=f.headers(w.stA))
    assert r.status_code == 409 and r.json()["code"] == "SKILLS_NOT_CONFIRMED"


def test_at_mat_01_ranking_holds_eligible_vacancies_in_descending_fit(model, client, w, f, db):
    strong = f.vacancy(w.ca2, [w.cs_major], required=(w.python, w.sql), title="Python and SQL developer")
    weak = f.vacancy(w.ca2, [w.cs_major], required=(w.js,), title="Frontend trainee")
    f.vacancy(w.ca2, [w.ee_major], title="Not for CS")
    f.vacancy(w.ca2, [w.cs_major], training_type="summer", title="Summer only")
    f.vacancy(w.ca2, [w.cs_major], universities=(w.uniB,), title="Other university")
    f.commit()
    confirm(db, w.stA, w.python, w.sql)
    client.patch(f"{API}/students/me/profile", headers=f.headers(w.stA), json={"interests": ["Python", "SQL"]})
    body = client.get(f"{API}/students/me/matches", headers=f.headers(w.stA)).json()
    titles = [i["vacancy"]["title"] for i in body["items"]]
    assert set(titles) == {"Python and SQL developer", "Frontend trainee", "Backend Trainee"}
    scores = [i["fit_score"] for i in body["items"]]
    assert scores == sorted(scores, reverse=True)
    assert titles.index("Python and SQL developer") < titles.index("Frontend trainee")
    assert body["advisory"] is True and body["mode"] == "semantic" and body["model_version"] == "test-hash@1"
    top = next(i for i in body["items"] if i["vacancy"]["title"] == "Python and SQL developer")
    assert {s["name_en"] for s in top["matched_skills"]} == {"Python", "SQL"} and top["missing_skills"] == []
    stored = db.query(MatchScore).filter_by(student_id=w.stA.id).all()
    assert len(stored) == 3 and all(m.model_version == "test-hash@1" for m in stored)  # AT-AI-02
    assert {strong.id, weak.id} <= {m.vacancy_id for m in stored}


def test_at_mat_03_gpa_below_minimum_is_left_out_and_explained(client, w, f, db):
    picky = f.vacancy(w.ca2, [w.cs_major, w.cis_major], min_gpa="3.50", title="Picky")
    f.commit()
    confirm(db, w.stA2, w.sql)  # GPA 3.00
    ranked = client.get(f"{API}/students/me/matches", headers=f.headers(w.stA2)).json()
    assert "Picky" not in [i["vacancy"]["title"] for i in ranked["items"]]
    browse = client.get(f"{API}/vacancies/{picky.id}", headers=f.headers(w.stA2)).json()
    assert browse["eligible"] is False and browse["ineligible_reason"] == "gpa_below_minimum"
    r = client.get(f"{API}/students/me/matches/{picky.id}", headers=f.headers(w.stA2))
    assert r.status_code == 409 and r.json()["reason"] == "gpa_below_minimum"


def test_at_mat_04_basic_mode_without_the_model(client, w, f, db):
    confirm(db, w.stA, w.python)
    start = time.perf_counter()
    body = client.get(f"{API}/students/me/matches", headers=f.headers(w.stA)).json()
    assert time.perf_counter() - start < 5
    assert body["mode"] == "basic" and body["model_version"] is None
    assert body["items"][0]["mode"] == "basic" and body["items"][0]["parts"]["semantic"] is None


def test_vacancy_without_embedding_is_scored_by_the_rules(model, client, w, f, db):
    confirm(db, w.stA, w.python)
    client.put(f"{API}/students/me/skills", headers=f.headers(w.stA),
               json={"skills": [{"skill_id": str(w.python.id), "source": "manual"}]})
    db.get(Vacancy, w.vac.id).embedding = None
    db.commit()
    other = f.vacancy(w.ca2, [w.cs_major], required=(w.python,), title="Embedded")
    f.commit()
    body = client.get(f"{API}/students/me/matches", headers=f.headers(w.stA)).json()
    modes = {i["vacancy"]["title"]: i["mode"] for i in body["items"]}
    assert modes == {"Backend Trainee": "basic", "Embedded": "semantic"} and body["mode"] == "mixed"
    assert other.embedding is not None


def test_at_mat_07_ranking_is_advisory_and_any_eligible_vacancy_can_be_applied_to(model, client, w, f, db):
    for i in range(3):
        f.vacancy(w.ca2, [w.cs_major], required=(w.js,), title=f"Other {i}")
    f.commit()
    confirm(db, w.stA, w.python)
    before = {a.id: a.status for a in db.query(Application)}
    items = client.get(f"{API}/students/me/matches", headers=f.headers(w.stA)).json()["items"]
    db.expire_all()
    assert {a.id: a.status for a in db.query(Application)} == before
    lowest = items[-1]["vacancy"]["id"]
    r = client.post(f"{API}/vacancies/{lowest}/applications", headers=f.headers(w.stA))
    assert r.status_code == 201


def test_application_keeps_the_fit_snapshot(model, client, w, f, db):
    confirm(db, w.stA, w.python)
    client.put(f"{API}/students/me/skills", headers=f.headers(w.stA),
               json={"skills": [{"skill_id": str(w.python.id), "source": "manual"}]})
    client.post(f"{API}/vacancies/{w.vac.id}/applications", headers=f.headers(w.stA))
    a = db.query(Application).filter_by(student_id=w.stA.id).one()
    assert a.fit_score is not None and a.match_mode == "semantic" and a.model_version == "test-hash@1"
    applicant = client.get(f"{API}/vacancies/{w.vac.id}/applications", headers=f.headers(w.cs1)).json()[0]
    assert Decimal(str(applicant["fit_score"])) == a.fit_score and applicant["match_mode"] == "semantic"


def test_embeddings_are_written_when_profile_or_vacancy_change(model, client, w, f, db):
    h = f.headers(w.stA)
    client.put(f"{API}/students/me/skills", headers=h, json={"skills": [{"skill_id": str(w.sql.id),
                                                                        "source": "manual"}]})
    db.expire_all()
    profile = db.get(StudentProfile, w.stA.id)
    assert profile.embedding is not None and profile.embedding_model == "test-hash@1"
    r = client.post(f"{API}/vacancies", headers=f.headers(w.cs1), json={
        "title": "Data trainee", "city": "Dammam", "description": "SQL reports for operations.",
        "training_type": "coop", "training_start": "2026-11-01", "training_end": "2027-01-21", "seats": 1,
        "application_deadline": "2026-11-20T20:59:00Z", "major_ids": [str(w.cs_major.id)]})
    v = db.get(Vacancy, r.json()["id"])
    assert v.embedding is not None and v.embedding_model == "test-hash@1"


def test_embed_missing_job_fills_the_gaps(client, w, f, db):
    confirm(db, w.stA, w.python)
    assert db.get(Vacancy, w.vac.id).embedding is None
    embeddings.set_embedder(HashEmbedder())
    jobs.run(SessionLocal, "embed_missing")
    db.expire_all()
    assert db.get(Vacancy, w.vac.id).embedding is not None
    assert db.get(StudentProfile, w.stA.id).embedding is not None


def test_development_plan_lists_missing_skills_with_resources(client, w, f, db):
    db.add(SkillResource(skill_id=w.sql.id, title="SQL basics", url="https://example.org/sql", position=1))
    v = f.vacancy(w.ca2, [w.cs_major], required=(w.python, w.sql, w.js))
    f.commit()
    confirm(db, w.stA, w.python)
    plan = client.get(f"{API}/students/me/matches/{v.id}/plan", headers=f.headers(w.stA)).json()
    missing = {m["skill"]["name_en"]: m["resources"] for m in plan["missing_skills"]}
    assert set(missing) == {"SQL", "JavaScript"} and missing["SQL"][0]["title"] == "SQL basics"
    assert missing["JavaScript"] == [] and plan["advisory"] is True


def test_at_per_02_ranking_1000_vacancies_within_5_seconds(model, client, w, f, db):
    confirm(db, w.stA, w.python, w.sql)
    client.put(f"{API}/students/me/skills", headers=f.headers(w.stA), json={"skills": [
        {"skill_id": str(w.python.id), "source": "manual"}, {"skill_id": str(w.sql.id), "source": "manual"}]})
    embedder = HashEmbedder()
    vectors = embedder.encode([f"passage: trainee {i} python sql reports" for i in range(1000)])
    deadline = clock.now() + timedelta(days=20)
    rows = [Vacancy(company_id=w.co2.id, company_supervisor_id=w.ca2.id, created_by=w.ca2.id, title=f"Trainee {i}",
                    city="Dammam", description="Python and SQL work", training_type="coop",
                    training_start=w.cycle.start_date, training_end=w.cycle.end_date, seats=2,
                    application_deadline=deadline, status="published", published_at=clock.now(),
                    embedding=vectors[i], embedding_model=embedder.version, embedded_at=clock.now())
            for i in range(1000)]
    db.add_all(rows)
    db.flush()
    db.add_all([VacancyMajor(vacancy_id=v.id, major_id=w.cs_major.id) for v in rows])
    db.commit()
    h = f.headers(w.stA)
    for mode in ("semantic", "basic"):
        if mode == "basic":
            embeddings.set_embedder(None)
        times = []
        for _ in range(20):
            start = time.perf_counter()
            body = client.get(f"{API}/students/me/matches?limit=20", headers=h).json()
            times.append(time.perf_counter() - start)
        assert body["total"] == 1001 and body["mode"] == mode
        p95 = statistics.quantiles(times, n=20)[18]
        print(f"NFR-PER-02 {mode}: median {statistics.median(times):.2f} s, p95 {p95:.2f} s")  # for the test report
        assert p95 < 5, (mode, p95)


def test_version_and_health_name_the_loaded_model(client):
    assert client.get(f"{API}/version").json()["embedding_model"] is None
    health = client.get(f"{API}/health?deep=true").json()
    assert health["database"] == "ok" and health["model"] is None
    embeddings.set_embedder(HashEmbedder())
    assert client.get(f"{API}/version").json()["embedding_model"] == "test-hash@1"
    assert client.get(f"{API}/health?deep=true").json()["model"] == "test-hash@1"
