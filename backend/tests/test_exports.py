"""Exports (AT-EXP-01 – 03, AT-PER-05, AT-L10N-03), history (AT-AUD-03), and role transfers (AT-ORG-07)."""
import io
import time

import pytest
from openpyxl import load_workbook
from pypdf import PdfReader
from sqlalchemy import select

from app.exports.service import _safe, grade_rows
from app.models import AuditEntry, Grade, Notification, StudentProfile, User

API = "/api/v1"


def ok(r, status=200):
    assert r.status_code == status, r.text
    return r


def pdf_text(data: bytes) -> str:
    return "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(data)).pages)


def pdf_fonts(data: bytes) -> set[str]:
    fonts = set()
    for page in PdfReader(io.BytesIO(data)).pages:
        for font in (page["/Resources"].get("/Font") or {}).values():
            fonts.add(str(font.get_object()["/BaseFont"]))
    return fonts


@pytest.fixture
def graded(w, f, db):
    """Two placements of the cycle: one Final grade with every score, one draft with the company part only."""
    w.stA.name_ar = "عبدالله الشهري"
    p1 = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    p2 = f.placement(w.stA2, w.vac, w.cs1, w.coA1, w.asA1)
    f.rubric(w.cycle)
    comps = f.components(w.cycle)
    f.finish_reports(p1)
    f.evaluation(p1, w.cs1, "final", [4, 5, 3])
    f.evaluation(p2, w.cs1, "final", [5, 5, 5])
    g1 = db.scalar(select(Grade).where(Grade.placement_id == p1.id))
    f.commit()
    return p1, p2, comps, g1


# ---------------------------------------------------------------- AT-EXP-01
def test_at_exp_01_grade_sheet_values_equal_stored_values(client, w, f, db, graded):
    p1, p2, comps, g1 = graded
    ah, co = f.headers(w.asA1), f.headers(w.coA1)
    ok(client.put(f"{API}/placements/{p1.id}/grade", headers=ah, json={"component_scores": [
        {"component_id": str(c.id), "score": "85.5"} for c in comps[1:]]}))
    ok(client.post(f"{API}/grades/{g1.id}/submit", headers=ah))
    ok(client.post(f"{API}/grades/{g1.id}/approve", headers=co))
    db.expire_all()
    w.coA1.language = "en"
    db.commit()
    r = ok(client.get(f"{API}/cycles/{w.cycle.id}/exports/grade-sheet?format=xlsx", headers=co))
    assert r.headers["content-type"].startswith("application/vnd.openxmlformats")
    assert "attachment" in r.headers["content-disposition"] and r.headers["cache-control"] == "private, no-store"
    ws = load_workbook(io.BytesIO(r.content)).active
    rows = list(ws.iter_rows(min_row=3, values_only=True))
    assert len(rows) == 2 and ws.sheet_view.rightToLeft is not True
    by_number = {row[0]: row for row in rows}
    number = db.get(StudentProfile, w.stA.id).student_number
    first = by_number[number]
    assert first[1] == w.stA.name_en and first[2] == "Nakheel" and first[3] == w.asA1.name_en
    assert first[4:7] == (80.0, 85.5, 85.5)  # company part 4.000 ÷ 5 × 100, then the two entered scores
    assert first[7] == float(db.get(Grade, g1.id).total) == 83.3 and first[8] == "Final"
    second = by_number[db.get(StudentProfile, w.stA2.id).student_number]
    assert second[4] == 100.0 and second[5] is None and second[7] is None and second[8] == "Draft"
    w.coA1.language = "ar"
    db.commit()
    ws = load_workbook(io.BytesIO(ok(client.get(f"{API}/cycles/{w.cycle.id}/exports/grade-sheet",
                                                headers=co)).content)).active
    assert ws.sheet_view.rightToLeft is True
    assert "عبدالله الشهري" in [row[1] for row in ws.iter_rows(min_row=3, values_only=True)]
    data = ok(client.get(f"{API}/cycles/{w.cycle.id}/exports/grade-sheet?format=pdf", headers=co)).content
    assert data.startswith(b"%PDF")
    text = pdf_text(data)
    assert number in text and "83.30" in text and "85.50" in text and "Nakheel" in text
    assert entries(db, "export") == 3
    for user in (w.asA1, w.coA2, w.cs1, w.stA, w.pa):
        assert client.get(f"{API}/cycles/{w.cycle.id}/exports/grade-sheet",
                          headers=f.headers(user)).status_code == 403


def entries(db, action: str) -> int:
    return len(db.scalars(select(AuditEntry).where(AuditEntry.action == action)).all())


def test_at_l10n_03_arabic_pdf_embeds_the_arabic_font(client, w, f, db, graded):
    data = ok(client.get(f"{API}/cycles/{w.cycle.id}/exports/grade-sheet?format=pdf", headers=f.headers(w.coA1)))
    fonts = pdf_fonts(data.content)
    assert any("NotoNaskhArabic" in name for name in fonts) and any("NotoSans" in name for name in fonts)
    text = pdf_text(data.content)
    arabic = [c for c in text if "\u0600" <= c <= "\u06ff"]
    assert len(arabic) > 20 and "Grade sheet" not in text  # the Arabic page, its text readable back


def test_unit_formula_injection_guard():
    assert _safe("=HYPERLINK(1)") == "'=HYPERLINK(1)" and _safe("+1") == "'+1" and _safe("@x") == "'@x"
    assert _safe("Nakheel") == "Nakheel" and _safe(85.5) == 85.5


# ---------------------------------------------------------------- AT-EXP-02 and AT-EXP-03
def test_at_exp_02_term_summary_equals_the_dashboard(client, w, f, db, graded):
    co = f.headers(w.coA1)
    w.coA1.language = "en"
    db.commit()
    stats = ok(client.get(f"{API}/cycles/{w.cycle.id}/stats", headers=co)).json()["overall"]
    text = pdf_text(ok(client.get(f"{API}/cycles/{w.cycle.id}/exports/term-summary", headers=co)).content)
    assert f"Enrolled students {stats['enrolled']}" in text and f"Placed {stats['placed']}" in text
    assert f"Reports due so far {stats['reports_due']}" in text and "Nakheel" in text


def test_at_exp_03_training_record_for_the_assigned_supervisor(client, w, f, db, graded):
    p1 = graded[0]
    w.asA1.language = "en"
    db.commit()
    data = ok(client.get(f"{API}/placements/{p1.id}/exports/training-record", headers=f.headers(w.asA1))).content
    text = pdf_text(data)
    assert db.get(StudentProfile, w.stA.id).student_number in text and "Nakheel" in text
    assert "Week 1" in text and "Final report" in text and "Accepted" in text  # every report accepted
    assert "Final evaluation" in text and "4.00" in text and "Final grade: Draft" in text
    assert client.get(f"{API}/placements/{p1.id}/exports/training-record",
                      headers=f.headers(w.asA1b)).status_code == 403
    assert client.get(f"{API}/placements/{p1.id}/exports/training-record",
                      headers=f.headers(w.coA1)).status_code == 200
    assert client.get(f"{API}/placements/{p1.id}/exports/training-record",
                      headers=f.headers(w.stA)).status_code == 403


# ---------------------------------------------------------------- AT-PER-05
def test_at_per_05_grade_sheet_of_100_students_under_60_seconds(client, w, f, db):
    vac = f.vacancy(w.cs1, [w.cs_major, w.cis_major], seats=100, title="Cohort Trainee")
    f.components(w.cycle)
    for i in range(100):
        s = f.student(w.A1, w.cs_major, "3.50")
        s.name_ar = f"طالب رقم {i}"
        f.enroll(w.cycle, s, w.coA1)
        f.placement(s, vac, w.cs1, w.coA1, w.asA1)
    f.commit()
    co = f.headers(w.coA1)
    assert len(grade_rows(db, w.cycle, "ar")[1]) == 100
    for fmt in ("xlsx", "pdf"):
        started = time.perf_counter()
        r = ok(client.get(f"{API}/cycles/{w.cycle.id}/exports/grade-sheet?format={fmt}", headers=co))
        elapsed = time.perf_counter() - started
        print(f"NFR-PER-05 {fmt}: 100 students in {elapsed:.2f} s")  # for the test report
        assert elapsed < 60 and len(r.content) > 1000


# ---------------------------------------------------------------- AT-AUD-03
def test_at_aud_03_history_matches_the_audit_entries(client, w, f, db, graded):
    p1, p2, comps, g1 = graded
    ah, co = f.headers(w.asA1), f.headers(w.coA1)
    ok(client.put(f"{API}/placements/{p1.id}/grade", headers=ah, json={"component_scores": [
        {"component_id": str(c.id), "score": "70"} for c in comps[1:]]}))
    ok(client.post(f"{API}/grades/{g1.id}/submit", headers=ah))
    ok(client.post(f"{API}/grades/{g1.id}/return", headers=co, json={"comment": "Check the report score"}))
    history = ok(client.get(f"{API}/history/grade/{g1.id}", headers=co)).json()
    audit = db.scalars(select(AuditEntry).where(AuditEntry.entity_type == "grade",
                                                AuditEntry.entity_id == str(g1.id)).order_by(AuditEntry.at)).all()
    assert [h["action"] for h in history] == [a.action for a in audit] == ["update", "submit", "return"]
    assert history[-1]["reason"] == "Check the report score" and history[-1]["user_en"] == w.coA1.name_en
    assert history[1]["old"] == {"status": "draft"} and history[1]["new"]["status"] == "submitted"
    assert client.get(f"{API}/history/grade/{g1.id}", headers=f.headers(w.stA)).status_code == 403  # not Final
    assert client.get(f"{API}/history/grade/{g1.id}", headers=f.headers(w.cs1)).status_code == 403
    evaluation = ok(client.get(f"{API}/placements/{p1.id}/evaluations", headers=ah)).json()["items"][1]["evaluation"]
    assert [h["action"] for h in ok(client.get(f"{API}/history/evaluation/{evaluation['id']}",
                                               headers=ah)).json()] == ["submit"]
    assert client.get(f"{API}/history/evaluation/{evaluation['id']}", headers=f.headers(w.stA)).status_code == 403
    assert client.get(f"{API}/history/grade/{g1.id}", headers=f.headers(w.asA1b)).status_code == 403
    assert client.get(f"{API}/history/report_slot/{g1.id}", headers=ah).status_code == 404


# ---------------------------------------------------------------- AT-ORG-07
def test_at_org_07_coordinator_role_transfer(client, w, f, db):
    pa = f.headers(w.pa)
    url = f"{API}/colleges/{w.A1.id}/coordinator/transfer"
    assert client.post(url, headers=pa, json={"user_id": str(w.asA1b.id), "reason": " "}).json()["code"] \
        == "REASON_REQUIRED"
    assert client.post(url, headers=pa, json={"user_id": str(w.asA2.id), "reason": "Leave"}).json()["code"] \
        == "TRANSFER_TARGET_INVALID"  # another college
    assert client.post(url, headers=f.headers(w.coA1), json={"user_id": str(w.asA1b.id), "reason": "x"}) \
        .status_code == 403
    f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.commit()
    assert client.post(url, headers=pa, json={"user_id": str(w.asA1.id), "reason": "Leave"}).json()["code"] \
        == "SUPERVISOR_HAS_STUDENTS"
    old_headers = f.headers(w.coA1)
    detail = ok(client.post(url, headers=pa, json={"user_id": str(w.asA1b.id), "reason": "Sabbatical leave"})).json()
    assert detail["coordinator"]["id"] == str(w.asA1b.id)
    db.expire_all()
    assert db.get(User, w.coA1.id).role == "academic_supervisor" and db.get(User, w.asA1b.id).role == "coordinator"
    assert client.get(f"{API}/coordinator/students", headers=old_headers).status_code in (403, 404)
    assert client.get(f"{API}/cycles/{w.cycle.id}/stats", headers=old_headers).status_code == 403  # rights gone
    assert client.get(f"{API}/cycles/{w.cycle.id}/stats", headers=f.headers(w.asA1b)).status_code == 200
    entry = db.scalars(select(AuditEntry).where(AuditEntry.action == "transfer_role")).one()
    assert entry.reason == "Sabbatical leave" and entry.new_value == {"coordinator_id": str(w.asA1b.id)}
    events = {(n.user_id, n.params.get("variant")) for n in db.scalars(select(Notification).where(
        Notification.event == "role.transferred"))}
    assert events == {(w.asA1b.id, "received"), (w.coA1.id, "removed")}


def test_at_org_07_company_admin_transfer(client, w, f, db):
    pa = f.headers(w.pa)
    url = f"{API}/companies/{w.co1.id}/admin/transfer"
    assert client.post(url, headers=pa, json={"user_id": str(w.ca2.id), "reason": "x"}).json()["code"] \
        == "TRANSFER_TARGET_INVALID"
    members = ok(client.post(url, headers=pa, json={"user_id": str(w.cs1.id), "reason": "Moved team"})).json()
    admins = [m["id"] for m in members if m["is_company_admin"]]
    assert admins == [str(w.cs1.id)]
    assert client.get(f"{API}/companies/{w.co1.id}/supervisors", headers=f.headers(w.ca1)).status_code == 403
    assert client.get(f"{API}/companies/{w.co1.id}/supervisors", headers=f.headers(w.cs1)).status_code == 200
