"""Vacancies, applications, placements (AT-VAC-01 – 08) and eligibility, including CR-06."""
from datetime import timedelta

from app.core import clock
from app.models import Application, AuditEntry, ReportSlot, SystemSetting, Vacancy
from app.vacancies.service import eligibility

API = "/api/v1"


def vacancy_body(w, **extra):
    return {"title": "Frontend Trainee", "city": "Khobar", "description": "Build React screens with the team.",
            "training_type": "coop", "training_start": "2026-11-01", "training_end": "2027-01-21",
            "min_gpa": "3.00", "seats": 2, "application_deadline": "2026-11-15T20:59:00Z",
            "required_skill_ids": [str(w.js.id)], "preferred_skill_ids": [str(w.sql.id)],
            "major_ids": [str(w.cs_major.id)], "target_university_ids": [], **extra}


# ---------------------------------------------------------------- unit: eligibility
def test_unit_eligibility_reasons(w, f, db):
    assert eligibility(db, w.stA, w.vac) is None
    ee = f.student(w.A1, w.ee_major)
    f.enroll(w.cycle, ee, w.coA1)
    assert eligibility(db, ee, w.vac) == "major_not_eligible"
    picky = f.vacancy(w.cs1, [w.cs_major, w.cis_major], min_gpa="3.50")
    assert eligibility(db, w.stA2, picky) == "gpa_below_minimum"
    summer = f.vacancy(w.cs1, [w.cs_major], training_type="summer")
    assert eligibility(db, w.stA, summer) == "training_type_mismatch"
    lone = f.student(w.A1, w.cs_major)
    assert eligibility(db, lone, w.vac) == "not_enrolled"
    clock.advance(timedelta(days=15))
    assert eligibility(db, w.stA, w.vac) == "deadline_passed"


# ---------------------------------------------------------------- AT-VAC-01
def test_at_vac_01_create_and_validate(client, w, f):
    h = f.headers(w.cs1)
    body = vacancy_body(w)
    del body["title"]
    r = client.post(f"{API}/vacancies", headers=h, json=body)
    assert r.status_code == 422 and r.json()["errors"][0]["field"] == "title"
    r = client.post(f"{API}/vacancies", headers=h, json=vacancy_body(w, major_ids=[]))
    assert r.status_code == 422
    r = client.post(f"{API}/vacancies", headers=h, json=vacancy_body(w, training_end="2026-10-01"))
    assert r.status_code == 422 and r.json()["errors"][0]["field"] == "training_end"
    r = client.post(f"{API}/vacancies", headers=h, json=vacancy_body(w))
    assert r.status_code == 201, r.text
    v = r.json()
    assert v["status"] == "draft" and v["company_supervisor"]["id"] == str(w.cs1.id)
    assert [s["name_en"] for s in v["required_skills"]] == ["JavaScript"]
    assert [s["name_en"] for s in v["preferred_skills"]] == ["SQL"]
    assert v["majors"][0]["name_en"] == "Computer Science" and v["min_gpa"] == "3.00"
    pending = f.company(status="pending")
    pending_user = f.user("company_supervisor", company=pending, status="pending")
    f.commit()
    r = client.post(f"{API}/vacancies", headers=f.headers(pending_user), json=vacancy_body(w))
    assert r.status_code == 403


def test_publish_close_and_edit(client, w, f):
    h = f.headers(w.cs1)
    vid = client.post(f"{API}/vacancies", headers=h, json=vacancy_body(w)).json()["id"]
    assert client.patch(f"{API}/vacancies/{vid}", headers=h, json={"seats": 3}).json()["seats"] == 3
    assert client.post(f"{API}/vacancies/{vid}/publish", headers=h).json()["status"] == "published"
    assert client.post(f"{API}/vacancies/{vid}/publish", headers=h).json()["code"] == "INVALID_TRANSITION"
    r = client.patch(f"{API}/vacancies/{vid}", headers=h, json={"application_deadline": "2026-10-01T00:00:00Z"})
    assert r.json()["code"] == "DEADLINE_PASSED"
    assert client.post(f"{API}/vacancies/{vid}/close", headers=h).json()["status"] == "closed"
    assert client.patch(f"{API}/vacancies/{vid}", headers=h, json={"seats": 4}).json()["code"] == "INVALID_TRANSITION"
    assert client.patch(f"{API}/vacancies/{vid}", headers=f.headers(w.ca2), json={"seats": 4}).status_code == 403


def test_only_company_admin_reassigns_vacancy_owner(client, w, f):
    other = f.user("company_supervisor", company=w.co1)
    f.commit()
    r = client.patch(f"{API}/vacancies/{w.vac.id}", headers=f.headers(w.cs1),
                     json={"company_supervisor_id": str(other.id)})
    assert r.status_code == 403
    r = client.patch(f"{API}/vacancies/{w.vac.id}", headers=f.headers(w.ca1),
                     json={"company_supervisor_id": str(other.id)})
    assert r.status_code == 200 and r.json()["company_supervisor"]["id"] == str(other.id)
    r = client.patch(f"{API}/vacancies/{w.vac.id}", headers=f.headers(w.ca1),
                     json={"company_supervisor_id": str(w.ca2.id)})
    assert r.json()["code"] == "COMPANY_SUPERVISOR_INVALID"


# ---------------------------------------------------------------- AT-VAC-02
def test_at_vac_02_visibility(client, w, f):
    draft = f.vacancy(w.cs1, [w.cs_major], publish=False, title="Hidden draft")
    only_b = f.vacancy(w.ca2, [w.cs_major], universities=(w.uniB,), title="Only KFUPM")
    f.commit()
    titles_a = {v["title"] for v in client.get(f"{API}/vacancies", headers=f.headers(w.stA)).json()["items"]}
    titles_b = {v["title"] for v in client.get(f"{API}/vacancies", headers=f.headers(w.stB)).json()["items"]}
    assert "Hidden draft" not in titles_a and "Only KFUPM" not in titles_a and "Backend Trainee" in titles_a
    assert "Only KFUPM" in titles_b
    assert client.get(f"{API}/vacancies/{draft.id}", headers=f.headers(w.stA)).status_code == 403
    assert client.get(f"{API}/vacancies/{only_b.id}", headers=f.headers(w.stA)).status_code == 403
    assert client.get(f"{API}/vacancies/{only_b.id}", headers=f.headers(w.coA1)).status_code == 403
    assert client.get(f"{API}/vacancies/{draft.id}", headers=f.headers(w.cs1)).status_code == 200
    assert client.get(f"{API}/vacancies/{draft.id}", headers=f.headers(w.ca2)).status_code == 403
    own = {v["title"] for v in client.get(f"{API}/vacancies", headers=f.headers(w.ca1)).json()["items"]}
    assert own == {"Backend Trainee", "Hidden draft"}
    assert client.get(f"{API}/vacancies", headers=f.headers(w.asA1)).status_code == 403


# ---------------------------------------------------------------- AT-VAC-03
def test_at_vac_03_filters(client, w, f):
    f.vacancy(w.ca2, [w.cis_major], title="Data Analyst", city="Riyadh", required=(w.sql,))
    f.vacancy(w.ca2, [w.cs_major], title="Summer Intern", training_type="summer", city="Jeddah")
    f.commit()
    h = f.headers(w.stA)

    def titles(query):
        return {v["title"] for v in client.get(f"{API}/vacancies?{query}", headers=h).json()["items"]}

    assert titles("city=riyadh") == {"Data Analyst"}
    assert titles(f"company_id={w.co1.id}") == {"Backend Trainee"}
    assert titles(f"major_id={w.cis_major.id}") == {"Backend Trainee", "Data Analyst"}
    assert titles(f"skill_id={w.sql.id}") == {"Data Analyst"}
    assert titles("training_type=summer") == {"Summer Intern"}
    assert titles("q=backend") == {"Backend Trainee"}
    items = client.get(f"{API}/vacancies?training_type=summer", headers=h).json()["items"]
    assert items[0]["eligible"] is False and items[0]["ineligible_reason"] == "training_type_mismatch"


# ---------------------------------------------------------------- AT-VAC-04
def test_at_vac_04_application_rules(client, w, f, db):
    h = f.headers(w.stA)
    assert client.post(f"{API}/vacancies/{w.vac.id}/applications", headers=h).status_code == 201
    r = client.post(f"{API}/vacancies/{w.vac.id}/applications", headers=h)
    assert r.status_code == 409 and r.json()["code"] == "DUPLICATE_APPLICATION"
    summer = f.vacancy(w.ca2, [w.cs_major], training_type="summer")
    f.commit()
    r = client.post(f"{API}/vacancies/{summer.id}/applications", headers=h)
    assert r.status_code == 409 and r.json()["code"] == "NOT_ELIGIBLE"
    assert r.json()["reason"] == "training_type_mismatch"
    late = f.vacancy(w.ca2, [w.cs_major], deadline_days=1)
    others = [f.vacancy(w.ca2, [w.cs_major]) for _ in range(4)]
    f.commit()
    clock.advance(timedelta(days=2))
    h = f.headers(w.stA)
    r = client.post(f"{API}/vacancies/{late.id}/applications", headers=h)
    assert r.status_code == 409 and r.json()["code"] == "DEADLINE_PASSED"
    for v in others:
        assert client.post(f"{API}/vacancies/{v.id}/applications", headers=h).status_code == 201
    sixth = f.vacancy(w.ca2, [w.cs_major])
    f.commit()
    r = client.post(f"{API}/vacancies/{sixth.id}/applications", headers=h)
    assert r.status_code == 409 and r.json()["code"] == "APPLICATION_LIMIT_REACHED"


def test_cannot_apply_to_other_universities_vacancy(client, w, f):
    only_b = f.vacancy(w.ca2, [w.cs_major], universities=(w.uniB,))
    f.commit()
    assert client.post(f"{API}/vacancies/{only_b.id}/applications", headers=f.headers(w.stA)).status_code == 403


# ---------------------------------------------------------------- AT-VAC-05
def test_at_vac_05_withdraw_frees_a_slot(client, w, f, db):
    db.merge(SystemSetting(key="applications.max_active", value=1))
    db.commit()
    h = f.headers(w.stA)
    aid = client.post(f"{API}/vacancies/{w.vac.id}/applications", headers=h).json()["id"]
    other = f.vacancy(w.ca2, [w.cs_major])
    f.commit()
    assert client.post(f"{API}/vacancies/{other.id}/applications", headers=h).json()["code"] \
        == "APPLICATION_LIMIT_REACHED"
    assert client.post(f"{API}/applications/{aid}/withdraw", headers=h).json()["status"] == "withdrawn"
    assert client.post(f"{API}/vacancies/{other.id}/applications", headers=h).status_code == 201
    mine = client.get(f"{API}/applications?status=submitted", headers=h).json()["items"]
    assert [a["vacancy_id"] for a in mine] == [str(other.id)]


# ---------------------------------------------------------------- AT-VAC-06
def test_at_vac_06_applicants_and_decisions(client, w, f, db):
    a = f.application(w.stA, w.vac)
    own_vac = f.vacancy(w.ca1, [w.cs_major, w.cis_major], title="Admin's own")
    b = f.application(w.stA2, own_vac)
    other_sup = f.user("company_supervisor", company=w.co1)
    f.commit()
    assert [x["id"] for x in client.get(f"{API}/vacancies/{w.vac.id}/applications",
                                         headers=f.headers(w.cs1)).json()] == [str(a.id)]
    assert client.get(f"{API}/vacancies/{own_vac.id}/applications", headers=f.headers(w.cs1)).status_code == 403
    assert client.get(f"{API}/vacancies/{w.vac.id}/applications", headers=f.headers(w.ca1)).status_code == 200
    assert client.get(f"{API}/vacancies/{w.vac.id}/applications", headers=f.headers(other_sup)).status_code == 403
    assert client.get(f"{API}/vacancies/{w.vac.id}/applications", headers=f.headers(w.ca2)).status_code == 403
    applicant = client.get(f"{API}/vacancies/{w.vac.id}/applications", headers=f.headers(w.cs1)).json()[0]
    assert applicant["gpa"] == "4.20" and applicant["major_en"] == "Computer Science"
    assert client.post(f"{API}/applications/{a.id}/accept", headers=f.headers(other_sup)).status_code == 403
    assert client.post(f"{API}/applications/{a.id}/accept", headers=f.headers(w.cs1)).json()["status"] == "accepted"
    assert client.post(f"{API}/applications/{a.id}/decline", headers=f.headers(w.cs1)).json()["code"] \
        == "INVALID_TRANSITION"
    assert client.post(f"{API}/applications/{b.id}/decline", headers=f.headers(w.ca1)).json()["status"] == "declined"
    assert client.get(f"{API}/applications/{a.id}", headers=f.headers(w.stA)).json()["status"] == "accepted"
    assert client.get(f"{API}/applications/{a.id}", headers=f.headers(w.coA1)).json()["status"] == "accepted"
    assert client.get(f"{API}/applications/{a.id}", headers=f.headers(w.coB1)).status_code == 403
    assert client.get(f"{API}/applications/{a.id}", headers=f.headers(w.stA2)).status_code == 403
    college_view = client.get(f"{API}/applications", headers=f.headers(w.coA1)).json()["items"]
    assert {x["id"] for x in college_view} == {str(a.id), str(b.id)}


# ---------------------------------------------------------------- AT-VAC-07
def test_at_vac_07_placement_rules(client, w, f, db):
    second_vac = f.vacancy(w.ca2, [w.cs_major, w.cis_major], seats=1)
    a1 = f.application(w.stA, w.vac, accept_by=w.cs1)
    a2 = f.application(w.stA, second_vac, accept_by=w.ca2)
    b = f.application(w.stA2, second_vac, accept_by=w.ca2)
    f.commit()
    co = f.headers(w.coA1)
    candidates = client.get(f"{API}/placements/candidates", headers=co).json()
    assert {c["application_id"] for c in candidates} == {str(a1.id), str(a2.id), str(b.id)}
    r = client.post(f"{API}/placements", headers=co, json={"application_id": str(a1.id),
                                                           "academic_supervisor_id": str(w.asA2.id)})
    assert r.json()["code"] == "ACADEMIC_SUPERVISOR_INVALID"
    r = client.post(f"{API}/placements", headers=co, json={"application_id": str(a1.id),
                                                           "academic_supervisor_id": str(w.asA1.id)})
    assert r.status_code == 201, r.text
    p = r.json()
    assert p["company_supervisor"]["id"] == str(w.cs1.id)  # RQ-5: defaults to the vacancy owner
    db.expire_all()
    assert db.get(Application, a2.id).status == "withdrawn" and db.get(Application, a2.id).withdraw_reason \
        == "placed_elsewhere"
    r = client.post(f"{API}/placements", headers=co, json={"application_id": str(a2.id),
                                                           "academic_supervisor_id": str(w.asA1.id)})
    assert r.status_code == 409
    r = client.post(f"{API}/placements", headers=co, json={"application_id": str(b.id),
                                                           "academic_supervisor_id": str(w.asA1b.id)})
    assert r.status_code == 201
    db.expire_all()
    assert db.get(Vacancy, second_vac.id).status == "closed"  # the last seat closes the vacancy
    assert client.post(f"{API}/placements", headers=f.headers(w.coB1),
                       json={"application_id": str(a1.id), "academic_supervisor_id": str(w.asA1.id)}).status_code \
        == 403


def test_placement_with_another_company_supervisor(client, w, f):
    a = f.application(w.stA, w.vac, accept_by=w.cs1)
    f.commit()
    r = client.post(f"{API}/placements", headers=f.headers(w.coA1),
                    json={"application_id": str(a.id), "academic_supervisor_id": str(w.asA1.id),
                          "company_supervisor_id": str(w.ca2.id)})
    assert r.json()["code"] == "COMPANY_SUPERVISOR_INVALID"
    r = client.post(f"{API}/placements", headers=f.headers(w.coA1),
                    json={"application_id": str(a.id), "academic_supervisor_id": str(w.asA1.id),
                          "company_supervisor_id": str(w.ca1.id)})
    assert r.status_code == 201 and r.json()["company_supervisor"]["id"] == str(w.ca1.id)


def test_placements_lists_are_scoped(client, w, f):
    f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.commit()
    for user, count in ((w.stA, 1), (w.stA2, 0), (w.asA1, 1), (w.asA1b, 0), (w.coA1, 1), (w.coB1, 0),
                        (w.ca1, 1), (w.cs1, 1), (w.ca2, 0)):
        assert client.get(f"{API}/placements", headers=f.headers(user)).json()["total"] == count, user.email
    co = f.headers(w.coA1)
    assert client.get(f"{API}/placements?company_id={w.co1.id}", headers=co).json()["total"] == 1
    assert client.get(f"{API}/placements?company_id={w.co2.id}", headers=co).json()["total"] == 0


# ---------------------------------------------------------------- AT-VAC-08
def test_at_vac_08_change_supervisor_and_cancel(client, w, f, db):
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.commit()
    co = f.headers(w.coA1)
    url = f"{API}/placements/{p.id}"
    assert client.patch(f"{url}/academic-supervisor", headers=co,
                        json={"academic_supervisor_id": str(w.asA1b.id)}).json()["code"] == "REASON_REQUIRED"
    r = client.patch(f"{url}/academic-supervisor", headers=co,
                     json={"academic_supervisor_id": str(w.asA1b.id), "reason": "Workload balance"})
    assert r.json()["academic_supervisor"]["id"] == str(w.asA1b.id)
    entry = db.query(AuditEntry).filter_by(action="change_supervisor").one()
    assert entry.reason == "Workload balance"
    assert client.get(url, headers=f.headers(w.asA1)).status_code == 403
    assert client.get(url, headers=f.headers(w.asA1b)).status_code == 200
    assert client.post(f"{url}/cancel", headers=co, json={"reason": ""}).json()["code"] == "REASON_REQUIRED"
    r = client.post(f"{url}/cancel", headers=co, json={"reason": "Company closed the branch"})
    assert r.json()["status"] == "cancelled"
    assert client.post(f"{API}/vacancies/{w.vac.id}/applications", headers=f.headers(w.stA)).json()["code"] \
        == "DUPLICATE_APPLICATION"
    other = f.vacancy(w.ca2, [w.cs_major])
    f.commit()
    assert client.post(f"{API}/vacancies/{other.id}/applications", headers=f.headers(w.stA)).status_code == 201


def test_close_vacancy_withdraws_active_applications(client, w, f, db):
    a = f.application(w.stA, w.vac)
    f.commit()
    client.post(f"{API}/vacancies/{w.vac.id}/close", headers=f.headers(w.cs1))
    db.expire_all()
    assert db.get(Application, a.id).withdraw_reason == "vacancy_closed"


def test_report_slots_created_with_placement(w, f, db):
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.commit()
    slots = db.query(ReportSlot).filter_by(placement_id=p.id).all()
    assert len([s for s in slots if s.kind == "weekly"]) == 12 and len([s for s in slots if s.kind == "final"]) == 1
