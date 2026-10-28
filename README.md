# InternSync

One platform for cooperative and summer training: universities and their colleges, training companies, and students. Students register and are verified, build a profile from their CV, apply to vacancies, and submit weekly and final reports; companies publish vacancies and review applicants; academic supervisors review reports; coordinators run the training cycles and placements. The interface is in Arabic (right to left) and English.

CSC 305 – Software Engineering, Imam Abdulrahman Bin Faisal University, Semester 1 – 2026/2027, Group 3. The project documents (SPMP, SRS, design, API specification, increment reports) are in [docs](docs/README.md).

## Status

- **Increment 1** is built and tested ([test report](docs/Increments/Increment_1/04_Test_Report.md)): accounts and verification, organizations, training cycles, profiles with CV skill extraction, vacancies and placements, weekly and final reports, and the audit log.
- **Increment 2** is built and tested ([test report](docs/Increments/Increment_2/04_Test_Report.md)): AI matching of students to vacancies with a development plan, weekly attendance, company evaluations, grades with approval, and dashboards for every role.
- **Increment 3** is built and tested ([test report](docs/Increments/Increment_3/04_Test_Report.md)): similarity detection between reports of one university, notifications (in-app, email, web push) with reminders and escalations, Excel and PDF exports with Arabic text, an installable app that opens offline, the history of reports, evaluations, and grades, and role transfers.
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

In development the sidebar shows a demo clock that moves the server's time forward by a day or a week, to show late and missing reports.

To show a similarity flag, sign in as `s1@iau.edu.sa` and submit a weekly report whose "tasks performed" begins with the former student's paragraph:

> This week I worked on the order service of the e-commerce platform. I wrote a new endpoint that returns the order history of a customer with pagination and filters by date and status. To make the query fast I added a composite index on the customer and created date columns, which reduced the response time from two seconds to about two hundred milliseconds.

The academic supervisor (`f.alharbi@iau.edu.sa`) then sees the flag on the dashboard and the passages side by side on the report.

The installable app and its offline page run from a production build (`npm run build` then `npm run preview` in `frontend/`, at http://localhost:4173). For web push, add a key pair to `.env`: `python -m app.cli vapid-keys` prints one.

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
```

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
| `ai-eval/` | Labelled synthetic profiles and vacancies, and the evaluation script |
| `.github/workflows/` | CI, and the deployment, keep-alive, and backup workflows ([docs/Deployment.md](docs/Deployment.md)) |
| `docs/` | Project documents in Markdown and their submitted snapshots |
| `docker-compose.yml` | Database, API, web app, and Mailpit for local use and the demo |
