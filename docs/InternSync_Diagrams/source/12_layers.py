"""Layered architecture as built (component view of the code): client, API, services, data access, core.
Used in the SDD, Sections 2.4 and 4.3."""
import sys
sys.path.insert(0, ".")
from blocks import Canvas, AI_EDGE, NAVY, EXT_EDGE

W, H = 7.3, 8.15
c = Canvas(W, H)
LX, LW = 1.25, 5.9


def layer_label(y, h, n, name, note):
    c.ax.text(0.17, y + 0.06, f"Layer {n}", fontsize=6.6, color="#595959", va="top")
    c.ax.text(0.17, y + 0.22, name, fontsize=8.0, fontweight="bold", color=NAVY, va="top", linespacing=1.15)
    c.ax.text(0.17, y + h - 0.06, note, fontsize=6.0, color="#595959", va="bottom", linespacing=1.15)


# ---------------------------------------------------------------- users
c.box("BR", LX, 0.12, LW, 0.34, "Users' browsers or the installed PWA (Student, Company Supervisor, Academic Supervisor, "
      "Coordinator, Platform Admin, public verifier)", kind="ext", fs=6.5)

# ---------------------------------------------------------------- layer 1: presentation (client)
y1, h1 = 0.72, 1.28
layer_label(y1, h1, 1, "Presentation\n(client)", "React 18 PWA\nfrontend/src")
c.frame(LX, y1, LW, h1, "React PWA (Vite, TypeScript): one page component per screen, grouped by role")
bw = (LW - 0.20 - 3 * 0.10) / 4
for i, (k, t) in enumerate([("PG", "pages/\nstudent · company · academic\ncoordinator · platform\nshared · public"),
                            ("CMP", "components/\nLayout (menu by role,\nfolds on phones)\nui (status chips, forms)"),
                            ("LIB", "lib/ and i18n/\nauth (token, idle limit)\noffline copy and drafts\npush · ar.json / en.json"),
                            ("CLI", "api/client\nopenapi-fetch with types\ngenerated from the\nserver's OpenAPI document")]):
    c.box(k, LX + 0.10 + i * (bw + 0.10), y1 + 0.34, bw, 0.82, t, fs=6.2, bold_first=True)

# ---------------------------------------------------------------- layer 2: API (routers + pipeline)
y2, h2 = 2.30, 1.42
layer_label(y2, h2, 2, "Interface\n(REST API)", "FastAPI\napp/<module>/router.py")
c.frame(LX, y2, LW, h2, "Routers under /api/v1 (21 routers, 163 endpoints) behind one request pipeline")
c.box("PIPE", LX + 0.10, y2 + 0.33, LW - 0.20, 0.36,
      "Pipeline (core/deps.py):  token and session  →  consent gate  →  verification gate  →  role check  →  "
      "body validation (Pydantic)", kind="white", fs=6.4)
c.box("RT", LX + 0.10, y2 + 0.79, LW - 0.20, 0.50,
      "auth · orgs · cycles · catalog · profiles · vacancies · matching · reports · similarity · attendance · evaluations\n"
      "grades · dashboard · exports · certificates · notifications · files · history · audit · privacy · system",
      fs=6.3)

# ---------------------------------------------------------------- layer 3: services (business logic + AI)
y3, h3 = 4.02, 1.25
layer_label(y3, h3, 3, "Business\nlogic", "app/<module>/service.py\napp/ai")
c.frame(LX, y3, LW, h3, "Services: business rules, record scope, state transitions (one transaction each)")
c.box("SVC", LX + 0.10, y3 + 0.34, 3.55, 0.78,
      "Workflow services\nregistration and verification · cycles · applications and placement\nreport review · "
      "attendance · evaluations · grade approval\ncertificates · exports · dashboards · anonymization",
      fs=6.2, bold_first=True)
c.box("AI", LX + 3.75, y3 + 0.34, LW - 3.85, 0.78,
      "AI services (advisory)\ntext and skill extraction\nfit score (matching/scoring.py)\nsimilarity (passages.py)",
      kind="ai", fs=6.2, bold_first=True)

# ---------------------------------------------------------------- layer 4: data access
y4, h4 = 5.57, 0.92
layer_label(y4, h4, 4, "Data access", "app/models\nalembic/versions")
c.frame(LX, y4, LW, h4, "SQLAlchemy 2.0 models (49 tables) and Alembic migrations")
c.box("ORM", LX + 0.10, y4 + 0.32, LW - 0.20, 0.47,
      "orgs · cycles · catalog · profiles · vacancies · reports · tracking · notices · platform\n"
      "Every query on academic records joins the caller's college, and on company records the caller's company",
      fs=6.3)

# ---------------------------------------------------------------- layer 5: core / infrastructure
y5, h5 = 6.79, 0.88
layer_label(y5, h5, 5, "Core and\ninfrastructure", "app/core, app/jobs,\napp/notifications")
c.frame(LX, y5, LW, h5, "Shared services used by the layers above")
c.box("CORE", LX + 0.10, y5 + 0.31, LW - 0.20, 0.46,
      "database session · settings · clock (UTC, Asia/Riyadh) · errors (problem+json) · i18n · audit helper · scope · "
      "security\nfile checks and storage adapter · mail · web push · scheduler (APScheduler, advisory locks) · "
      "notification outbox", kind="white", fs=6.1)

# ---------------------------------------------------------------- external services
ye = 7.80
ew = (LW - 3 * 0.12) / 4
for i, t in enumerate(["PostgreSQL + pgvector", "File storage (bucket or volume)", "Email (SMTP over TLS)",
                       "Browser push (VAPID)"]):
    x = LX + i * (ew + 0.12)
    c.box(f"E{i}", x, ye, ew, 0.28, t, kind="ext", fs=6.1)
    c.arrow([(x + ew / 2, y5 + h5), (x + ew / 2, ye)], dashed=True, color=EXT_EDGE)
c.ax.text(0.17, ye + 0.14, "External\nservices", fontsize=7.4, fontweight="bold", color=EXT_EDGE, va="center",
          linespacing=1.1)

# ---------------------------------------------------------------- calls between layers (downward only)
mid = LX + 0.55
c.arrow([(mid, 0.46), (mid, y1)], "HTTPS", lpos=(mid + 0.06, (0.46 + y1) / 2), fs=6.3)
for ya, yb, lab in ((y1 + h1, y2, "HTTPS, JSON, JWT bearer token"), (y2 + h2, y3, "calls"),
                    (y3 + h3, y4, "reads and writes records"), (y4 + h4, y5, "session, helpers")):
    c.arrow([(mid, ya), (mid, yb)], lab, lpos=(mid + 0.06, (ya + yb) / 2), fs=6.3)
c.ax.text(LX + LW, (y1 + h1 + y2) / 2, "Rule: each layer calls only the layer below it.\n"
          "AI results are advisory: they never change a status.", fontsize=6.3, color=AI_EDGE, ha="right", va="center",
          linespacing=1.15)

c.save("../png/12_layers")
print("ok")
