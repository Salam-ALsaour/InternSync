"""Student profile, CV upload, skill extraction (AT-PRF-02 – 05, AT-CYC-04) and the skill catalog."""
from sqlalchemy import select

from app.ai import skills as extractor
from app.ai.text import detect_language, extract_text, normalize, tokens
from app.core.files import DOCX, PDF
from app.models import Cv, Skill, StudentSkill
from app.seed import seed_reference
from tests.factories import PNG, docx, pdf, zip_bytes

API = "/api/v1"
EN_CV = ("Abdullah Al-Shehri - Computer Science student", "Skills: Python, JS, PostgreSQL, Docker and Git",
         "Projects: REST APIs with FastAPI; machine learning model for course grades",
         "Languages: Arabic and English. Teamwork and problem solving.")
AR_CV = ("عبدالله الشهري - طالب علوم الحاسب",
         "المهارات: بايثون، قواعد البيانات، تعلم الآلة، الأمن السيبراني",
         "خبرة في تحليل البيانات باستخدام باور بي آي وإكسل",
         "اللغات: العربية والإنجليزية")


def upload(client, h, data, name="cv.pdf", mime="application/pdf"):
    return client.post(f"{API}/students/me/cvs", headers=h, files={"file": (name, data, mime)})


# ---------------------------------------------------------------- unit: normalization and extraction
def test_unit_arabic_normalization():
    assert normalize("الإحصاء") == normalize("الاحصاء") == "الاحصاء"
    assert normalize("مُبَرْمِجة") == "مبرمجه"
    assert tokens("C++, C# and Node.js.") == ["c++", "c#", "and", "node.js"]


def test_unit_text_extraction_and_language():
    text, status = extract_text(pdf(*EN_CV), PDF)
    assert status == "ok" and "PostgreSQL" in text
    text, status = extract_text(docx(*AR_CV), DOCX)
    assert status == "ok" and detect_language(text) == "ar"
    assert extract_text(pdf(), PDF)[1] == "no_text"
    assert extract_text(b"%PDF-1.4 broken", PDF)[1] == "failed"


def test_at_cyc_04_unit_synonym_matches_and_shows_canonical_name(f, db):
    js = f.skill("JavaScript", "جافاسكربت", ("JS", "ECMAScript"))
    f.skill("Java", "جافا")
    db.commit()
    found = extractor.extract(db, "I wrote JS for the front end and some Java services.")
    ids = {m.skill_id for m in found}
    assert js.id in ids and len(ids) == 2
    evidence = next(m.evidence for m in found if m.skill_id == js.id)
    assert "JS" in evidence


def test_at_prf_04_unit_full_dictionary_on_sample_cvs(db):
    seed_reference(db)
    db.commit()
    ids = [m.skill_id for m in extractor.extract(db, "\n".join(EN_CV))]
    en = set(db.scalars(select(Skill.name_en).where(Skill.id.in_(ids))))
    assert {"Python", "JavaScript", "PostgreSQL", "Docker", "Git", "REST APIs", "FastAPI", "Machine Learning",
            "Teamwork", "Problem Solving"} <= en
    ar_ids = {m.skill_id for m in extractor.extract(db, "\n".join(AR_CV))}
    assert len(ar_ids) >= 5


def test_unit_longest_match_wins(f, db):
    f.skill("Machine Learning", "تعلم الآلة")
    f.skill("Learning Management", "إدارة التعلم")
    db.commit()
    found = extractor.extract(db, "machine learning management")
    assert len(found) == 1


# ---------------------------------------------------------------- AT-PRF-02
def test_at_prf_02_verified_student_cannot_edit_academic_fields(client, w, f):
    h = f.headers(w.stA)
    r = client.patch(f"{API}/students/me/profile", headers=h, json={"interests": ["Backend", "Data"],
                                                                     "languages": ["Arabic", "English"]})
    assert r.status_code == 200 and r.json()["interests"] == ["Backend", "Data"]
    assert r.json()["academic_read_only"] is True
    for field, value in (("student_number", "99999999"), ("major_id", str(w.cis_major.id)), ("gpa", "4.9")):
        r = client.patch(f"{API}/students/me/profile", headers=h, json={field: value})
        assert r.status_code == 422 and r.json()["errors"][0]["code"] == "READ_ONLY_FIELD", field


def test_pending_student_can_correct_academic_fields(client, w, f, db):
    s = f.student(w.A1, w.cs_major, status="pending")
    db.commit()
    h = f.headers(s)
    r = client.patch(f"{API}/students/me/profile", headers=h, json={"gpa": "3.75", "major_id": str(w.cis_major.id)})
    assert r.status_code == 200 and r.json()["gpa"] == "3.75" and r.json()["major"]["id"] == str(w.cis_major.id)
    assert client.patch(f"{API}/students/me/profile", headers=h, json={"gpa": "5.5"}).json()["code"] \
        == "GPA_ABOVE_SCALE"


# ---------------------------------------------------------------- AT-PRF-03
def test_at_prf_03_size_and_type_limits_and_versions(client, w, f, db):
    h = f.headers(w.stA)
    big = pdf(*EN_CV) + b"0" * (6 * 1024 * 1024)
    r = upload(client, h, big)
    assert r.status_code == 413 and r.json()["code"] == "FILE_TOO_LARGE"
    for data, name in ((PNG, "cv.pdf"), (zip_bytes(), "cv.docx"), (b"hello", "cv.txt")):
        r = upload(client, h, data, name)
        assert r.status_code == 415 and r.json()["code"] == "UNSUPPORTED_FILE_TYPE", name
    first = upload(client, h, pdf(*EN_CV))
    second = upload(client, h, docx(*AR_CV), "cv.docx", DOCX)
    assert first.status_code == second.status_code == 201
    versions = client.get(f"{API}/students/me/cvs", headers=h).json()
    assert [v["version_no"] for v in versions] == [2, 1]
    assert client.get(f"{API}/files/{versions[1]['file_id']}", headers=h).status_code == 200
    assert db.query(Cv).count() == 2


# ---------------------------------------------------------------- AT-PRF-04
def test_at_prf_04_extracted_skills_are_only_candidates(client, w, f, db):
    h = f.headers(w.stA)
    r = upload(client, h, pdf("Computer science student at the College of Computing.", "Skills: Python, JS and SQL"))
    body = r.json()
    assert body["text_status"] == "ok" and body["advisory"] is True
    assert {s["name_en"] for s in body["extracted_skills"]} == {"Python", "JavaScript", "SQL"}
    assert db.query(StudentSkill).filter_by(student_id=w.stA.id).count() == 0
    chosen = [{"skill_id": str(w.python.id), "source": "extracted"}, {"skill_id": str(w.js.id), "source": "manual"}]
    r = client.put(f"{API}/students/me/skills", headers=h, json={"skills": chosen})
    assert {s["name_en"] for s in r.json()} == {"Python", "JavaScript"}
    assert client.get(f"{API}/students/me/profile", headers=h).json()["skills_confirmed_at"] is not None


def test_arabic_docx_cv_extraction(client, w, f):
    h = f.headers(w.stA)
    r = upload(client, h, docx("طالب في كلية علوم الحاسب وتقنية المعلومات", "خبرة في بايثون و جافاسكربت"), "cv.docx",
               DOCX)
    assert r.json()["language"] == "ar"
    assert {s["name_en"] for s in r.json()["extracted_skills"]} == {"Python", "JavaScript"}


# ---------------------------------------------------------------- AT-PRF-05
def test_at_prf_05_image_only_pdf(client, w, f):
    r = upload(client, f.headers(w.stA), pdf())
    assert r.status_code == 201
    assert r.json()["text_status"] == "no_text" and r.json()["extracted_skills"] == []


# ---------------------------------------------------------------- visibility
def test_profile_visibility(client, w, f):
    assert client.get(f"{API}/students/{w.stA.id}/profile", headers=f.headers(w.coA1)).status_code == 200
    assert client.get(f"{API}/students/{w.stA.id}/profile", headers=f.headers(w.coB1)).status_code == 403
    assert client.get(f"{API}/students/{w.stA.id}/profile", headers=f.headers(w.cs1)).status_code == 403
    f.application(w.stA, w.vac)
    f.commit()
    assert client.get(f"{API}/students/{w.stA.id}/profile", headers=f.headers(w.cs1)).status_code == 200
    assert client.get(f"{API}/students/{w.stA.id}/profile", headers=f.headers(w.ca2)).status_code == 403


def test_cv_file_visible_to_company_only_after_application(client, w, f):
    h = f.headers(w.stA)
    file_id = upload(client, h, pdf(*EN_CV)).json()["cv"]["file_id"]
    assert client.get(f"{API}/files/{file_id}", headers=f.headers(w.cs1)).status_code == 403
    f.application(w.stA, w.vac)
    f.commit()
    r = client.get(f"{API}/files/{file_id}", headers=f.headers(w.cs1))
    assert r.status_code == 200 and r.headers["content-type"] == "application/pdf"
    assert r.headers["x-content-type-options"] == "nosniff"


# ---------------------------------------------------------------- catalog
def test_skill_catalog_admin(client, w, f):
    pa = f.headers(w.pa)
    r = client.post(f"{API}/skills", headers=pa, json={"name_en": "Kotlin", "name_ar": "كوتلن",
                                                        "synonyms": ["kt"]})
    assert r.status_code == 201, r.text
    sid = r.json()["id"]
    assert client.post(f"{API}/skills", headers=pa, json={"name_en": "kotlin", "name_ar": "x"}).json()["code"] \
        == "DUPLICATE_NAME"
    found = client.get(f"{API}/skills?q=kt", headers=f.headers(w.stA)).json()["items"]
    assert [s["name_en"] for s in found] == ["Kotlin"]
    r = upload(client, f.headers(w.stA), pdf("Mobile developer. I build Android apps in Kotlin for clients."))
    assert "Kotlin" in {s["name_en"] for s in r.json()["extracted_skills"]}
    assert client.patch(f"{API}/skills/{sid}", headers=pa, json={"is_active": False}).json()["is_active"] is False
    assert client.get(f"{API}/skills?q=kotlin", headers=f.headers(w.stA)).json()["items"] == []
    r = client.put(f"{API}/skills/{sid}/resources", headers=pa,
                   json=[{"title": "Kotlin docs", "url": "https://kotlinlang.org/docs/", "language": "en"}])
    assert r.status_code == 200
    assert client.get(f"{API}/skills/{sid}/resources", headers=f.headers(w.stA)).json()[0]["title"] == "Kotlin docs"
    bad = client.put(f"{API}/skills/{sid}/resources", headers=pa, json=[{"title": "x", "url": "ftp://x"}])
    assert bad.status_code == 422


def test_majors_and_settings(client, w, f):
    pa = f.headers(w.pa)
    assert client.post(f"{API}/majors", headers=pa, json={"name_en": "Data Science", "name_ar": "علم البيانات"}) \
        .status_code == 201
    assert "Data Science" in [m["name_en"] for m in client.get(f"{API}/majors").json()]
    settings = client.get(f"{API}/settings", headers=pa).json()
    assert settings["applications.max_active"] == 5
    r = client.patch(f"{API}/settings", headers=pa, json={"applications.max_active": 3})
    assert r.json()["applications.max_active"] == 3
    r = client.patch(f"{API}/settings", headers=pa, json={"applications.max_active": 999, "nope": 1})
    assert r.status_code == 422 and {e["field"] for e in r.json()["errors"]} == {"applications.max_active", "nope"}
