"""Certificates (AT-CER-01 – 03): issue only for a Final grade, the PDF with its QR code, the public check, revoke."""
import io
import re

import zxingcpp
from pypdf import PdfReader
from sqlalchemy import select

from app.certificates import service
from app.core import files
from app.models import AuditEntry, Certificate, Notification, StoredFile
from tests.increment4 import API, final_grade, ok, prepare


def pdf_text(data: bytes) -> str:
    return "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(data)).pages)


def qr_texts(data: bytes) -> list[str]:
    out = []
    for page in PdfReader(io.BytesIO(data)).pages:
        for image in page.images:
            out += [b.text for b in zxingcpp.read_barcodes(image.image)]
    return out


def issued(client, w, f, db):
    prepare(f, w.cycle)
    p = f.placement(w.stA, w.vac, w.cs1, w.coA1, w.asA1)
    f.commit()
    return p


def test_unit_code_is_26_characters_of_base32_and_unguessable():
    codes = {service.new_code() for _ in range(200)}
    assert len(codes) == 200
    assert all(re.fullmatch(r"[A-Z2-7]{26}", c) for c in codes)
    assert service.normalize(" abcd-efgh ijkl ") == "ABCDEFGHIJKL"


def test_at_cer_01_only_a_final_grade_gets_a_certificate(client, w, f, db):
    p = issued(client, w, f, db)
    co = f.headers(w.coA1)
    r = client.post(f"{API}/placements/{p.id}/certificate", headers=co)
    assert r.status_code == 409 and r.json()["code"] == "GRADE_NOT_FINAL"
    assert ok(client.get(f"{API}/placements/{p.id}/certificate", headers=co)).json() == {
        "certificate": None, "can_issue": False}

    final_grade(f, db, w, p)
    assert ok(client.get(f"{API}/placements/{p.id}/certificate", headers=co)).json()["can_issue"] is True
    out = ok(client.post(f"{API}/placements/{p.id}/certificate", headers=co), 201).json()
    cert = out["certificate"]
    assert cert["status"] == "valid" and len(cert["code"]) == 26 and out["can_issue"] is False
    assert cert["verify_url"].endswith(f"/verify/{cert['code']}") and cert["can_revoke"] is True
    r = client.post(f"{API}/placements/{p.id}/certificate", headers=co)
    assert r.status_code == 409 and r.json()["code"] == "CERTIFICATE_EXISTS"

    stored = db.get(StoredFile, cert["file_id"])
    assert stored.purpose == "certificate" and stored.mime_type == "application/pdf"
    data = files.storage().read(stored.storage_key)
    text = pdf_text(data)
    grouped = "-".join(cert["code"][i:i + 4] for i in range(0, 26, 4))
    assert grouped in text and w.stA.name_en in text and "Nakheel" in text and "Certificate of Completion" in text
    assert "90" not in text.replace(grouped, "")  # no grade on the page
    assert qr_texts(data) == [cert["verify_url"]]

    student = f.headers(w.stA)
    mine = ok(client.get(f"{API}/placements/{p.id}/certificate", headers=student)).json()
    assert mine["certificate"]["code"] == cert["code"] and mine["certificate"]["can_revoke"] is False
    assert ok(client.get(f"{API}/files/{cert['file_id']}", headers=student)).content == data
    for user in (w.cs1, w.ca1, w.asA1, w.coA2, w.stA2, w.pa):
        h = f.headers(user)
        assert client.get(f"{API}/files/{cert['file_id']}", headers=h).status_code == 403
        assert client.get(f"{API}/certificates/{cert['id']}", headers=h).status_code == 403
    assert db.scalar(select(Notification).where(Notification.event == "certificate.issued",
                                                Notification.user_id == w.stA.id)) is not None
    assert db.scalar(select(AuditEntry).where(AuditEntry.action == "issue",
                                              AuditEntry.entity_type == "certificate")) is not None


def test_at_cer_02_public_check_valid_revoked_and_altered(client, w, f, db):
    p = issued(client, w, f, db)
    final_grade(f, db, w, p)
    cert = ok(client.post(f"{API}/placements/{p.id}/certificate", headers=f.headers(w.coA1)), 201).json()["certificate"]
    code = cert["code"]
    r = ok(client.get(f"{API}/public/certificates/{code}"))  # no login
    body = r.json()
    assert body["status"] == "valid" and body["student_name"] == {"en": w.stA.name_en, "ar": w.stA.name_ar}
    assert body["company"] == "Nakheel" and body["cycle"] == "Co-op Fall 2026"
    assert body["university"]["en"] == w.uniA.name_en and body["college"]["en"] == w.A1.name_en
    assert body["training_start"] == "2026-10-25" and body["training_end"] == "2027-01-17"
    assert set(body) == {"status", "name_removed", "student_name", "university", "college", "cycle", "company",
                         "training_start", "training_end"}  # never the grade
    spaced = "-".join(code[i:i + 4] for i in range(0, 26, 4)).lower()
    assert ok(client.get(f"{API}/public/certificates/{spaced}")).json()["status"] == "valid"
    altered = ("B" if code[0] != "B" else "C") + code[1:]
    assert ok(client.get(f"{API}/public/certificates/{altered}")).json() == {
        "status": "not_found", "name_removed": False, "student_name": None, "university": None, "college": None,
        "cycle": None, "company": None, "training_start": None, "training_end": None}
    assert ok(client.get(f"{API}/public/certificates/short")).json()["status"] == "not_found"


def test_at_cer_03_revoke_needs_a_reason_then_a_new_one_can_be_issued(client, w, f, db):
    p = issued(client, w, f, db)
    final_grade(f, db, w, p)
    co = f.headers(w.coA1)
    cert = ok(client.post(f"{API}/placements/{p.id}/certificate", headers=co), 201).json()["certificate"]
    r = client.post(f"{API}/certificates/{cert['id']}/revoke", headers=co, json={"reason": "  "})
    assert r.status_code == 422 and r.json()["code"] == "REASON_REQUIRED"
    for user in (w.stA, w.coA2, w.asA1):
        assert client.post(f"{API}/certificates/{cert['id']}/revoke", headers=f.headers(user),
                           json={"reason": "x"}).status_code == 403
    out = ok(client.post(f"{API}/certificates/{cert['id']}/revoke", headers=co,
                         json={"reason": "Issued with the wrong company name"})).json()
    assert out["status"] == "revoked" and out["revoke_reason"] == "Issued with the wrong company name"
    assert ok(client.get(f"{API}/public/certificates/{cert['code']}")).json()["status"] == "revoked"
    r = client.post(f"{API}/certificates/{cert['id']}/revoke", headers=co, json={"reason": "again"})
    assert r.status_code == 409 and r.json()["code"] == "CERTIFICATE_REVOKED"
    entry = db.scalar(select(AuditEntry).where(AuditEntry.action == "revoke"))
    assert entry.reason == "Issued with the wrong company name" and entry.new_value == {"status": "revoked"}
    assert db.scalar(select(Notification).where(Notification.event == "certificate.revoked")) is not None

    view = ok(client.get(f"{API}/placements/{p.id}/certificate", headers=co)).json()
    assert view["certificate"]["status"] == "revoked" and view["can_issue"] is True
    again = ok(client.post(f"{API}/placements/{p.id}/certificate", headers=co), 201).json()["certificate"]
    assert again["code"] != cert["code"] and again["status"] == "valid"
    listed = ok(client.get(f"{API}/certificates?cycle_id={w.cycle.id}", headers=co)).json()
    assert [c["status"] for c in listed] == ["valid", "revoked"]
    assert [c["status"] for c in ok(client.get(f"{API}/certificates?status=revoked", headers=co)).json()] == ["revoked"]
    assert ok(client.get(f"{API}/certificates", headers=f.headers(w.coA2))).json() == []
    assert len(db.scalars(select(Certificate)).all()) == 2
