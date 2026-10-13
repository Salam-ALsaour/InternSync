"""Layered system architecture (component view)."""
import sys
sys.path.insert(0, ".")
from blocks import Canvas, AI_EDGE

W, H = 7.3, 8.3
c = Canvas(W, H)

# ---------------------------------------------------------------- users
c.frame(0.15, 0.12, 7.0, 0.82, "Users — browser or installed PWA", kind="ext")
for i, (k, t) in enumerate([("ST", "Student"), ("CS", "Company\nsupervisor"), ("AS", "Academic\nsupervisor"),
                            ("CO", "Coordinator"), ("PV", "Public verifier\n(QR scan, no login)")]):
    c.box(k, 0.35 + i * 1.36, 0.42, 1.18, 0.42, t, kind="white")

# ---------------------------------------------------------------- client
c.frame(0.15, 1.22, 7.0, 1.05, "Client — React PWA (Vite), served as static files")
for i, (k, t) in enumerate([("UI", "Role dashboards\nand forms"), ("I18N", "i18n: Arabic (RTL)\n/ English (LTR)"),
                            ("SW", "Service worker:\napp-shell cache, push"),
                            ("APIC", "Typed API client\n(generated from OpenAPI)")]):
    c.box(k, 0.35 + i * 1.72, 1.55, 1.55, 0.52, t)
c.arrow([(W / 2, 0.94), (W / 2, 1.22)], "HTTPS", lpos=(W / 2 + 0.06, 1.08))

# ---------------------------------------------------------------- server
c.frame(0.15, 2.62, 7.0, 3.88, "Server — Python 3 / FastAPI, one Docker image (single instance)")
c.frame(0.3, 2.95, 6.7, 1.55, "REST API  /api/v1  —  JWT authentication, role check on every request", fill="white",
        fs=7.8)
mods = [("AUTH", "Auth and RBAC\n(activation, lockout)"), ("USR", "Users, cycles,\nCSV import, rubric"),
        ("WFL", "Evaluations, grades,\napproval workflow"), ("EXP", "Exports (PDF / Excel)\nand certificates"),
        ("PRF", "Profiles, CVs\nand skills"), ("VAC", "Vacancies, applications\nand placements"),
        ("REP", "Reports, comments\nand attendance"), ("NTF", "Notifications\nand audit log")]
for i, (k, t) in enumerate(mods):
    col, row = i % 4, i // 4
    c.box(k, 0.45 + col * 1.63, 3.27 + row * 0.6, 1.5, 0.48, t)
c.arrow([(c.at("APIC", "bottom")[0], 2.07), (c.at("APIC", "bottom")[0], 2.95)],
        "HTTPS / JSON\nJWT bearer", lpos=(c.at("APIC", "bottom")[0] + 0.06, 2.45))

c.frame(0.3, 4.68, 6.7, 1.05, "AI services (in-process, CPU, advisory)", kind="ai", fill="#FFFBF5", fs=7.6,
        align="right")
ai = [("TXT", "Text and skill\nextraction (AR / EN)"), ("MAT", "Matching: hybrid\nscore + rule fallback"),
      ("SIM", "Similarity\ndetection"), ("EMB", "Embedding model\nmultilingual-e5-small")]
for i, (k, t) in enumerate(ai):
    c.box(k, 0.45 + i * 1.63, 5.0, 1.5, 0.5, t, kind="ai")
# API -> AI (straight down)
for src, dst, lab in (("PRF", "TXT", "CV upload"), ("VAC", "MAT", "rank"), ("REP", "SIM", "on submit")):
    p0, p1 = c.at(src, "bottom"), c.at(dst, "top")
    c.arrow([p0, p1], lab, lpos=(p0[0] + 0.05, 4.62), color=AI_EDGE)
# matching and similarity both use the shared embedding model
yb = 5.62
for src, f in (("MAT", 0.3), ("SIM", 0.6)):
    p0 = c.at(src, "bottom")
    p1 = c.at("EMB", "bottom", f)
    c.arrow([p0, (p0[0], yb), (p1[0], yb), p1], color=AI_EDGE)
c.text(c.at("SIM", "bottom")[0] + 0.62, yb + 0.015, "both use the shared model", fontsize=6.4, color=AI_EDGE, ha="left", va="top")

c.box("SCH", 0.3, 5.85, 6.7, 0.45,
      "Scheduler (APScheduler, every 15 min, idempotent jobs):  reminders  ·  Late / Missing flags  ·  escalations",
      kind="white")
nt = c.at("NTF", "right")
c.arrow([c.at("SCH", "right", 0.5), (6.93, c.at("SCH", "right", 0.5)[1]), (6.93, nt[1]), nt])

# ---------------------------------------------------------------- data + external
c.frame(0.15, 6.78, 4.2, 1.35, "Data")
c.cylinder("DB", 0.35, 7.08, 2.05, 0.92, "PostgreSQL 16 + pgvector\nrelational data and\n384-d embeddings")
c.box("FS", 2.6, 7.13, 1.6, 0.82, "Private file storage\nCVs, attachments,\nexports")
c.frame(4.55, 6.78, 2.6, 1.35, "External", kind="ext")
c.box("MAIL", 4.7, 7.13, 1.15, 0.82, "Email provider\n(SMTP, TLS)", kind="ext")
c.box("PUSH", 5.95, 7.13, 1.05, 0.82, "Browser push\nservices", kind="ext")

c.arrow([(1.37, 6.5), c.at("DB", "top")], "SQL (ORM) +\nvector search", lpos=(1.43, 6.64))
c.arrow([(3.4, 6.5), c.at("FS", "top")], "signed URLs after\npermission check", lpos=(3.46, 6.64))
mx = c.at("MAIL", "top", 0.62)[0]
c.arrow([(mx, 6.5), (mx, 7.13)], "email", lpos=(mx + 0.05, 6.64))
c.arrow([(c.at("PUSH", "top")[0], 6.5), c.at("PUSH", "top")], "web push", lpos=(c.at("PUSH", "top")[0] + 0.05, 6.64))
# push back to the service worker (dashed, along the right margin)
sw = c.at("SW", "top", 0.85)
c.arrow([c.at("PUSH", "right"), (7.22, c.at("PUSH", "right")[1]), (7.22, 1.38), (sw[0] + 0.0, 1.38), (sw[0], 1.55)],
        dashed=True)
c.text(6.35, 1.33, "push to devices", ha="center", va="bottom", fontsize=6.6)

c.save("../png/05_architecture")
print("ok")
