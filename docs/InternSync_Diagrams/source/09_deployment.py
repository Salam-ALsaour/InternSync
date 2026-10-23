"""Deployment: zero-cost reference deployment (CR-01) and the self-hosted Docker Compose option."""
import sys
sys.path.insert(0, ".")
from blocks import Canvas

W, H = 7.3, 5.75
c = Canvas(W, H)

# ======================================================== Option A (chosen)
xa = 0.12
c.frame(xa, 0.12, 3.5, 5.5, "A — Reference deployment, zero cost (chosen)", fill="#F7FBF4", kind="green", fs=8.2)
c.box("BRA", xa + 0.2, 0.5, 3.1, 0.38, "Users' browsers / installed PWA", kind="white")
c.box("VER", xa + 0.2, 1.2, 1.45, 0.78, "Vercel (Hobby, free)\nReact PWA static build\nHTTPS + CDN,\npreview per pull request",
      bold_first=True)
c.box("HF", xa + 1.85, 1.2, 1.45, 1.05, "Hugging Face Spaces\nCPU Basic (free), Docker:\nFastAPI + e5-small model\n+ scheduler\n2 vCPU · 16 GB RAM",
      bold_first=True)
c.box("SUP", xa + 1.85, 2.75, 1.45, 0.82, "Supabase (Free)\nPostgreSQL + pgvector;\nprivate Storage bucket;\n500 MB DB · 1 GB files",
      bold_first=True)
c.box("GH", xa + 0.2, 2.75, 1.45, 0.82, "GitHub Actions\nCI, deploy on merge,\nnightly encrypted backup,\nkeep-alive every 6 h",
      bold_first=True, kind="white")
c.box("MA", xa + 0.2, 4.15, 1.45, 0.62, "Email\nGmail SMTP\n(app password)", bold_first=True, kind="ext")
c.box("PA", xa + 1.85, 4.15, 1.45, 0.62, "Browser push\nservices (VAPID)", kind="ext")
c.arrow([c.at("BRA", "bottom", 0.24), c.at("VER", "top")], "HTTPS", lpos=(c.at("VER", "top")[0] + 0.05, 1.04))
c.arrow([c.at("BRA", "bottom", 0.76), c.at("HF", "top")], "API calls (JWT)", lpos=(c.at("HF", "top")[0] + 0.05, 1.04))
c.arrow([c.at("HF", "bottom"), c.at("SUP", "top")], "SQL (TLS) +\nStorage API", lpos=(c.at("SUP", "top")[0] + 0.05, 2.5))
c.arrow([c.at("GH", "top", 0.5), c.at("VER", "bottom", 0.5)], "auto-deploy\non merge", lpos=(xa + 0.98, 2.37))
c.arrow([c.at("GH", "right", 0.25), (xa + 1.75, c.at("GH", "right", 0.25)[1]), (xa + 1.75, 1.75),
         c.at("HF", "left", 0.5)], None)
c.arrow([c.at("GH", "right", 0.75), c.at("SUP", "left", 0.75)])
c.text(xa + 1.75, 3.68, "nightly backup", ha="center", va="center", fontsize=6.4, color="#333333")
c.arrow([c.at("HF", "right", 0.85), (xa + 3.4, c.at("HF", "right", 0.85)[1]), (xa + 3.4, 3.95),
         (c.at("MA", "top")[0], 3.95), c.at("MA", "top")], None)
c.arrow([(c.at("PA", "top")[0], 3.95), c.at("PA", "top")], None)
c.text(xa + 2.62, 3.88, "notifications", ha="center", va="bottom", fontsize=6.6, color="#333333")
c.text(xa + 0.2, 5.0, "Cost: US$0, no card needed. Spaces sleeps after 48 h\nwithout visits and Supabase pauses after 7 idle days;\n"
       "the keep-alive job prevents both (SRS D-05).", fontsize=6.7, va="top", color="#333333", linespacing=1.25)

# ======================================================== Option B (self-hosted)
xb = 3.7
c.frame(xb, 0.12, 3.48, 5.5, "B — Self-hosted with Docker Compose (NFR-PRT-02)", fs=8.2)
c.box("BRB", xb + 0.2, 0.5, 3.08, 0.38, "Users' browsers / installed PWA", kind="white")
c.frame(xb + 0.2, 1.12, 3.08, 2.82, "Linux server or laptop + Docker Compose", fill="white", fs=7.6, z=1)
c.text(xb + 0.3, 1.38, "At least 2 vCPU and 4 GB RAM", fontsize=6.6, va="top", color="#595959")
c.box("CAD", xb + 0.35, 1.68, 2.78, 0.42, "caddy: automatic HTTPS, serves the PWA, proxies /api")
c.box("API", xb + 0.35, 2.28, 2.78, 0.42, "api: FastAPI + AI model + scheduler (same image)")
c.box("DBB", xb + 0.35, 2.88, 1.32, 0.48, "db: PostgreSQL\n+ pgvector")
c.box("VOL", xb + 1.81, 2.88, 1.32, 0.48, "volume: files\n+ nightly pg_dump")
c.arrow([c.at("BRB", "bottom", 0.85), c.at("CAD", "top", 0.83)], "HTTPS", lpos=(c.at("BRB", "bottom", 0.85)[0] + 0.05, 1.0))
c.arrow([c.at("CAD", "bottom"), c.at("API", "top")])
c.arrow([c.at("API", "bottom", 0.24), c.at("DBB", "top")])
c.arrow([c.at("API", "bottom", 0.76), c.at("VOL", "top")])
c.box("GHB", xb + 0.2, 4.15, 1.45, 0.62, "Local development\nsame Compose file\n+ Mailpit for email",
      bold_first=True, kind="white")
c.box("EXB", xb + 1.83, 4.15, 1.45, 0.62, "Email (SMTP) and\nbrowser push", kind="ext")
c.arrow([(c.at("EXB", "top")[0], 3.94), c.at("EXB", "top")], None)
c.text(xb + 0.2, 5.0, "Fallback for UAT and the final demo if a free tier is\nunavailable: run the same images on a laptop.",
       fontsize=6.7, va="top", color="#333333", linespacing=1.25)

c.save("../png/09_deployment")
print("ok")
