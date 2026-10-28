# InternSync

One platform for cooperative and summer training: universities and their colleges, training companies, and students. Students register and are verified, build a profile from their CV, apply to vacancies, and submit weekly and final reports; companies publish vacancies and review applicants; academic supervisors review reports; coordinators run the training cycles and placements. The interface is in Arabic (right to left) and English.

CSC 305 – Software Engineering, Imam Abdulrahman Bin Faisal University, Semester 1 – 2026/2027, Group 3. The project documents (SPMP, SRS, design, API specification, increment reports) are in [docs](docs/README.md).

## Status

- **Increment 1** is built and tested ([test report](docs/Increments/Increment_1/04_Test_Report.md)): accounts and verification, organizations, training cycles, profiles with CV skill extraction, vacancies and placements, weekly and final reports, and the audit log.
- **Increment 2** is built and tested ([test report](docs/Increments/Increment_2/04_Test_Report.md)): AI matching of students to vacancies with a development plan, weekly attendance, company evaluations, grades with approval, and dashboards for every role.
- **Increment 3** is built and tested ([test report](docs/Increments/Increment_3/04_Test_Report.md)): similarity detection between reports of one university, notifications (in-app, email, web push) with reminders and escalations, Excel and PDF exports with Arabic text, an installable app that opens offline, the history of reports, evaluations, and grades, and role transfers.
- **Increment 4** is built and tested ([test report](docs/Increments/Increment_4/04_Test_Report.md)): completion certificates with a QR code and a public check page, the student's evaluation of the company and the job-offer survey, the leniency alert, anonymization of closed cycles after the retention period, and an offline mode (pages opened earlier stay readable, drafts typed offline are saved when the connection returns). The release checks ran: browser tests on three engines, the ZAP scan, a load test, and held-out AI sets. User acceptance testing is prepared ([plan](docs/Increments/Increment_4/05_UAT_Plan.md)).
- **Results:** every measured result of the project is in [docs/Key_Results.md](docs/Key_Results.md).
- **Deployment:** the zero-cost reference deployment is prepared and is switched on from a checklist ([docs/Deployment.md](docs/Deployment.md)).

## Run Locally

Needs Docker Desktop.

```bash
docker compose up -d --build
docker compose exec api python -m app.seed --demo
```

| **Service** | **Address** |
|:---|:---|
| Web app | http://localhost:5173 |
| API and its documentation | http://localhost:8000/api/v1/docs |
| Mailpit (every email sent by the app lands here) | http://localhost:8025 |
| PostgreSQL | `localhost:5433`, user, password, and database `internsync` |

The first build downloads the embedding model into the API image (the image is about 3 GB). For a smaller image without it, which uses basic matching, build with `docker compose build --build-arg WITH_AI=0 api`.

The demo command adds one account per role, all with the password `Demo-2026-pass` (local use only; refused when `ENV=production`):

| **Role** | **Email** |
|:---|:---|
| Platform Admin | `admin@internsync.example` |
| Coordinator | `coordinator@iau.edu.sa` |
| Academic supervisor | `f.alharbi@iau.edu.sa` |
| Company Admin | `sara@nakheel.example` |
| Company supervisor | `omar@nakheel.example` |
| Student (placed, with report slots) | `s1@iau.edu.sa` |
| Student (accepted, waiting for placement) | `s2@iau.edu.sa` |
| Student (not applied yet) | `s3@iau.edu.sa` |
| Former student of a closed spring cycle, with an accepted week 1 report | `s0@iau.edu.sa` |
| Former student of the closed summer 2025 cycle, Final grade, no certificate or answers yet | `s10@iau.edu.sa` |

The summer 2025 cycle (closed 13 months ago) holds eight former students with Final grades, one certificate, answers to the evaluation of the company and the survey, and five generous final evaluations at one company. Its statistics page shows the leniency alert and the job-offer rate, and its retention period has ended, so the coordinator can show the anonymization. The certificate can be checked at http://localhost:5173/verify.

In development the sidebar shows a demo clock that moves the server's time forward by a day or a week, to show late and missing reports.

To show a similarity flag, sign in as `s1@iau.edu.sa` and submit a weekly report whose "tasks performed" begins with the former student's paragraph:

> This week I worked on the order service of the e-commerce platform. I wrote a new endpoint that returns the order history of a customer with pagination and filters by date and status. To make the query fast I added a composite index on the customer and created date columns, which reduced the response time from two seconds to about two hundred milliseconds.

The academic supervisor (`f.alharbi@iau.edu.sa`) then sees the flag on the dashboard and the passages side by side on the report.

The installable app runs from a production build (`npm run build` then `npm run preview` in `frontend/`, at http://localhost:4173). Offline, pages opened earlier in the session stay readable and report drafts are kept on the device; the development server shows the same while the window stays open. For web push, add a key pair to `.env`: `python -m app.cli vapid-keys` prints one.

Without the demo data, create the first Platform Admin with:

```bash
docker compose exec api python -m app.cli create-platform-admin --email admin@example.org --name-en "Platform Admin" --name-ar "مشرف المنصة"
```

## Develop and Test

Backend (Python 3.11, from `backend/`):

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements-dev.txt     # .venv/bin/pip on Linux and macOS
docker compose up -d db mailpit
.venv/Scripts/alembic upgrade head
.venv/Scripts/python -m uvicorn app.main:app --reload
.venv/Scripts/ruff check app tests alembic scripts
.venv/Scripts/pytest --cov=app
```

The tests use their own database, `internsync_test`, created on first use. They use a small stand-in for the embedding model. To run the API with the real model, also install `requirements-ai.txt` (CPU PyTorch and sentence-transformers); without it the API uses basic matching.

The AI evaluation (skill extraction and matching on a labelled synthetic set) runs from the repository root with the backend's Python:

```bash
backend/.venv/Scripts/python ai-eval/evaluate.py            # with the model
backend/.venv/Scripts/python ai-eval/evaluate.py --basic    # rules only
backend/.venv/Scripts/python ai-eval/evaluate.py --heldout  # the held-out sets, never used to choose a setting
```

The release checks run against the Docker stack on its own database (`docker-compose.check.yml`), so the demo data stays as it is:

```bash
docker compose -f docker-compose.yml -f docker-compose.check.yml up -d db
docker compose exec db psql -U internsync -d postgres -c "CREATE DATABASE internsync_check"
docker compose -f docker-compose.yml -f docker-compose.check.yml up -d --build api web
docker compose exec api python -m app.seed --demo
cd frontend && npx playwright install && npx playwright test          # browser tests
locust -f backend/loadtest/locustfile.py --host http://localhost:8000 --headless -u 50 -r 5 -t 5m
```

The ZAP scan is the `security-scan.yml` workflow (Actions, Security scan, Run workflow); its commands also run locally with Docker.

Frontend (Node 22, from `frontend/`):

```bash
npm ci
npm run dev            # http://localhost:5173, API calls go to http://localhost:8000
npx tsc -b && npx vitest run && npx vite build
```

After an API change, refresh the generated types:

```bash
python ../backend/scripts/export_openapi.py src/api/openapi.json
npm run gen:api
```

CI (GitHub Actions) runs the same checks on every pull request.

## Repository

| **Folder** | **Contents** |
|:---|:---|
| `backend/` | FastAPI application, Alembic migrations, seed data, tests (with the permission matrix), scripts |
| `frontend/` | React, TypeScript, and Tailwind web app with Arabic and English texts |
| `ai-eval/` | Labelled synthetic profiles, vacancies, and reports (the tuning sets and the held-out sets), and the evaluation script |
| `frontend/e2e/` | Browser tests (Playwright) |
| `backend/loadtest/` | Load test (Locust) |
| `.github/workflows/` | CI with the browser tests, the weekly security scan, and the deployment, keep-alive, and backup workflows ([docs/Deployment.md](docs/Deployment.md)) |
| `docs/` | Project documents in Markdown and their submitted snapshots; [Key_Results.md](docs/Key_Results.md) |
| `docker-compose.yml` | Database, API, web app, and Mailpit for local use and the demo; `docker-compose.check.yml` for the release checks |
