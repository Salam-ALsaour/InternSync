"""The M6 demo scenario on the demo data (Increment 4 requirements, Section 8). Step 6 (offline) is checked in the
browser tests and step 7 is the results file; both are in the test report."""
from sqlalchemy import select

from app.models import TrainingCycle, User
from app.seed import seed_demo, seed_reference
from tests.increment4 import API, ok

RATING = {"learning_opportunities": 4, "supervision_quality": 5, "work_environment": 4, "relevance_to_major": 5,
          "would_recommend": True, "comment": None}


def _user(db, email):
    return db.scalar(select(User).where(User.email == email))


def test_m6_demo_scenario(client, f, db):
    seed_reference(db)
    seed_demo(db)
    db.commit()
    seed_demo(db)  # idempotent
    db.commit()
    summer = db.scalar(select(TrainingCycle).where(TrainingCycle.name == "Summer 2025 (demo)"))
    assert len(db.scalars(select(TrainingCycle).where(TrainingCycle.name == "Summer 2025 (demo)")).all()) == 1
    co = f.headers(_user(db, "coordinator@iau.edu.sa"))
    s10 = _user(db, "s10@iau.edu.sa")
    st = f.headers(s10)

    # 1 – 2: a certificate issued live, checked publicly, revoked; the one issued with the demo data stays valid
    placements = ok(client.get(f"{API}/placements?cycle_id={summer.id}&page_size=50", headers=co)).json()["items"]
    p10 = next(p for p in placements if p["student"]["id"] == str(s10.id))
    view = ok(client.get(f"{API}/placements/{p10['id']}/certificate", headers=co)).json()
    assert view == {"certificate": None, "can_issue": True}
    cert = ok(client.post(f"{API}/placements/{p10['id']}/certificate", headers=co), 201).json()["certificate"]
    public = ok(client.get(f"{API}/public/certificates/{cert['code']}")).json()
    assert public["status"] == "valid" and public["student_name"]["en"] == "Fahad Al-Dosari"
    ok(client.post(f"{API}/certificates/{cert['id']}/revoke", headers=co, json={"reason": "Demo"}))
    assert ok(client.get(f"{API}/public/certificates/{cert['code']}")).json()["status"] == "revoked"
    issued = ok(client.get(f"{API}/certificates?status=valid", headers=co)).json()
    assert [c["student"]["name_en"] for c in issued] == ["Lama Al-Harbi"]

    # 3: the student answers; the coordinator sees the averages and the job-offer rate, the company does not
    ok(client.put(f"{API}/placements/{p10['id']}/company-evaluation", headers=st, json=RATING))
    ok(client.put(f"{API}/placements/{p10['id']}/outcome-survey", headers=st, json={"job_offer": "yes"}))
    outcomes = ok(client.get(f"{API}/cycles/{summer.id}/outcomes", headers=co)).json()
    assert outcomes["overall"] == {"answers": 7, "yes": 4, "no": 2, "pending": 1, "job_offer_rate": round(400 / 7, 1)}
    ratings = ok(client.get(f"{API}/cycles/{summer.id}/company-evaluations", headers=co)).json()
    assert ratings["overall"]["answers"] == 8
    company = f.headers(_user(db, "sara@nakheel.example"))
    assert client.get(f"{API}/placements/{p10['id']}/company-evaluation", headers=company).status_code == 403

    # 4: the generous company is marked
    leniency = ok(client.get(f"{API}/cycles/{summer.id}/leniency-alerts", headers=co)).json()
    alerts = [c["company_name"] for c in leniency["companies"] if c["alert"]]
    assert alerts == ["Nakheel Digital Solutions"] and leniency["cycle_mean"] == "3.875"

    # 5: anonymization of the closed cycle; its statistics stay the same
    before = [ok(client.get(f"{API}/cycles/{summer.id}/{p}", headers=co)).json()
              for p in ("stats", "outcomes", "company-evaluations", "leniency-alerts")]
    state = ok(client.get(f"{API}/cycles/{summer.id}/anonymization", headers=co)).json()
    assert state["status"] == "ready" and state["students"] == 8 and state["skipped"] == 0
    ok(client.post(f"{API}/cycles/{summer.id}/anonymize", headers=co, json={"confirm": True}))
    after = [ok(client.get(f"{API}/cycles/{summer.id}/{p}", headers=co)).json()
             for p in ("stats", "outcomes", "company-evaluations", "leniency-alerts")]
    assert after == before
    db.expire_all()
    assert db.get(User, s10.id).anonymized_at is not None
    assert _user(db, "s0@iau.edu.sa").anonymized_at is None  # the spring cycle is still within its period
    assert ok(client.get(f"{API}/public/certificates/{issued[0]['code']}")).json()["name_removed"] is True
