# Increment 1 – Design

**Status:** Approved for implementation · Oct 23, 2026; implemented Oct 24, 2026 (changes in Section 12) · Author: Salam Alsaour  
**Input:** [01_Requirements.md](01_Requirements.md) (scope and decisions), [Design 1.2](../../Design/InternSync_Design.md), [API 1.1](../../Design/InternSync_API_Spec.md)

This document narrows the system design to what Increment 1 builds and records the implementation decisions that the system design leaves open. Where it says nothing, the system design and the API specification apply unchanged.

## 1. Decisions Taken in the Requirements Phase

The project owner delegated the decisions of 01_Requirements.md Section 5; the recommendations were adopted:

| **ID** | **Decision** | **Recorded in** |
|:---|:---|:---|
| RQ-1 | Eligibility now requires the vacancy's training type to equal the type of the student's cycle | CR-06; SRS FR-VAC-04 and FR-MAT-03; Design 4.4 and 6.2; API `NOT_ELIGIBLE` reason `training_type_mismatch` |
| RQ-2 | A student request waits while the college has no open cycle | This document, Section 6 |
| RQ-3 | The job runner is built now with the Missing-flag, document-purge, and clean-up jobs only | Section 7 |
| RQ-4 | Skill-extraction accuracy is measured at M4 | 01_Requirements.md |
| RQ-5 | The placement's company supervisor defaults to the vacancy owner | Section 6 |
| RQ-6 | FR-ORG-07 moves to Increment 3; FR-ORG-09, FR-CYC-05, FR-VAC-05, FR-VAC-08 are built in this increment if time allows | 01_Requirements.md |
| RQ-7 | M3 is demonstrated on Docker Compose; deployment to the free tiers starts Increment 2 | Section 9 |

## 2. Repository Layout

```
backend/                FastAPI application (Python 3.11 in Docker and CI)
  app/
    main.py             app factory: routers, error handlers, CORS, lifespan (scheduler)
    core/               config, db, errors, i18n messages, security, clock, audit, settings, mail, storage, deps
    models/             SQLAlchemy models, one file per module
    auth/ orgs/ cycles/ catalog/ profiles/ vacancies/ reports/ audit/ files/   router + schemas + service
    dev/                development-only demo clock (mounted when ENV is development or test)
    ai/                 text extraction, normalization, skill extractor
    jobs/               scheduler and job functions
    seed_data/          skills, majors, universities (JSON)
    seed.py, cli.py     reference and demo seed; create-platform-admin and run-job commands
  alembic/              migrations
  tests/                pytest suites, permission matrix (matrix.yaml)
  scripts/              demo_dry_run.py (M3 rehearsal against the running stack), export_openapi.py
frontend/               React 18 + Vite + TypeScript PWA shell
  src/api/              generated OpenAPI types (schema.d.ts) and the typed client
  src/i18n/             ar.json, en.json
  src/components/ src/pages/<role>/
docker-compose.yml      db (PostgreSQL 16, port 5433), api, web, mailpit
.github/workflows/ci.yml
```

The system design names `cycles` as the owner of the skill vocabulary and majors; they get their own package `catalog` to keep `cycles` small. Behaviour is unchanged.

## 3. Data

**Tables created in Increment 1** (35 of 49), exactly as in Design 4.3: `universities`, `colleges`, `companies`, `users`, `account_tokens`, `verification_requests`, `verification_documents`, `user_sessions`, `majors`, `skills`, `skill_resources`, `system_settings`, `training_cycles`, `cycle_weeks`, `grade_components`, `rubric_criteria`, `enrollments`, `student_profiles`, `cvs`, `cv_extracted_skills`, `student_skills`, `vacancies`, `vacancy_skills`, `vacancy_majors`, `vacancy_universities`, `applications`, `placements`, `report_slots`, `report_versions`, `report_attachments`, `report_reviews`, `report_comments`, `files`, `audit_log`, `job_runs`.

**Left for later increments:** `match_scores` and the `embedding` columns of `student_profiles` and `vacancies` (with the `vector` extension, Increment 2); `attendance_weeks`, `evaluations`, `evaluation_scores`, `grades`, `grade_component_scores` (Increment 2); `report_passages`, `similarity_checks`, `similarity_matches`, `notifications`, `push_subscriptions` (Increment 3); `company_evaluations`, `outcome_surveys`, `certificates` (testing phase). The draft grade that a placement creates (Design 5.1) is created from Increment 2; that migration backfills it for existing placements.

**Extensions:** `pg_trgm` (vacancy search). `gen_random_uuid()` is built into PostgreSQL 13+.

**Audit log protection:** a trigger raises an error on `UPDATE` and `DELETE` of `audit_log` (FR-AUD-02).

**Settings:** the migration inserts the Increment 1 keys of Design Table 4.1 with their defaults: `auth.*`, `applications.max_active`, `files.cv_max_mb`, `files.attachment_max_mb`, `reports.max_attachments`, `verification.document_retention_days`, `auth.registrations_per_ip_hour`.

## 4. Endpoints

All endpoints of the API specification sections below are built, with their roles, scopes, and error codes:

| **API section** | **Built** | **Not in Increment 1** |
|:---|:---|:---|
| 3.1 Authentication and session | All | – |
| 3.2 Organizations, verification, accounts | All | The two transfer endpoints (FR-ORG-07) |
| 3.3 Training cycles | All | – (close and reopen are stretch; built if time allows) |
| 3.4 Skills, majors, settings | All | – |
| 3.5 Student profile and CV | All | – |
| 3.6 Vacancies | All | – |
| 3.7 Applications and placements | All | Withdraw, change supervisor, cancel (stretch) |
| 3.9 Reports | All | – |
| 3.18 Audit | `GET /audit-log` | `GET /history/...` (FR-AUD-03, Increment 3) |
| 3.19 Files | `GET /files/{id}` | – |
| 3.20 System | `/health`, `/version`, `/openapi.json`, `/docs` | – |

`GET /vacancies` returns `eligible` and `ineligible_reason` for students; the reasons are `major_not_eligible`, `gpa_below_minimum`, `training_type_mismatch`, `deadline_passed`, and `not_enrolled`.

## 5. Security Details

- **Pipeline order** (Design 2.3) is built as FastAPI dependencies: `current_session` (JWT and session row, idle timeout, `last_seen_at` at most once per minute) → `consent_gate` → `verification_gate` → `require_roles(...)` → scope-filtered query in the service. A role or gate failure returns before the request body is validated, so the permission matrix gets 401 or 403, never 422.
- **Tokens:** JWT HS256 with `sub`, `role`, `sid`, `iat`, `exp` (12 h). The frontend keeps the token in `sessionStorage`.
- **Email links:** 32 random bytes, URL-safe; the database stores SHA-256 only; a new link of the same purpose revokes the older one.
- **Registration rate limit:** in-process counter per IP address and hour (one API instance; Design 3.2).
- **Files:** type by content (`filetype` for PDF, PNG, JPEG; DOCX checked as a ZIP holding `[Content_Types].xml` and `word/document.xml`); random storage keys; local storage directory outside any web root; download only through `GET /files/{id}` after the owning record's permission rule. Verification documents: uploader and reviewer only; `410` after the purge.

## 6. Behaviour Details

- **Registration** creates in one transaction: the user (`verification_status = pending`), the student profile (students) or the company (`pending`, companies), the verification request with its documents, and the confirmation token. The email is sent after the commit.
- **Student approval (RQ-2):** the Coordinator chooses an open cycle of the college. With no open cycle the request stays pending and `GET /verification-requests` marks it `no_open_cycle: true`, so the screen explains why it cannot be approved yet.
- **Company approval:** the company becomes `verified`, the representative becomes `verified` with `is_company_admin = true`.
- **Eligibility (CR-06):** a student can apply when verified, enrolled in an open cycle, and the vacancy is published, before its deadline, open to the student's university, lists the student's major, has no minimum GPA above the student's GPA, and has the same training type as the student's cycle.
- **Placement (RQ-5):** `company_supervisor_id` defaults to the vacancy's owner; the Coordinator may name another active supervisor of the same company. The transaction creates the placement, one report slot per cycle week (deadline copied from `cycle_weeks`) and the final report slot, marks the application `placed`, withdraws the student's other active applications (`placed_elsewhere`), and closes the vacancy when its seats are filled (its remaining active applications become `withdrawn` with `vacancy_closed`).
- **Reports:** a draft version is created or updated by `PUT /report-slots/{id}/draft`; submit checks the required fields and the attachment limit, sets `submitted_at` from the server clock and `is_late` when `submitted_at ≥ due_at + 60 s`; resubmission copies the last submitted version and its attachments into the new draft. Transitions follow Design Table 5.3; any other returns `409 INVALID_TRANSITION`. Responses carry `allowed_actions`.
- **Emails in Increment 1:** confirmation, invitation, and password-reset emails are sent directly by the mail module after the commit, in the user's language (Arabic or English templates). The notification outbox and the delivery job come with the notifications in Increment 3.

## 7. Jobs

APScheduler `BackgroundScheduler` inside the API process, started only when `SCHEDULER_ENABLED=true`. Each job runs in one transaction under a transaction-level PostgreSQL advisory lock (`pg_try_advisory_xact_lock`) and writes a `job_runs` row; `python -m app.cli run-job <name>` runs one by hand.

| **Job** | **Every** | **Does** |
|:---|:---|:---|
| `flag_missing` | 15 min, first run 30 s after start | Slots in `draft` past `due_at` with `is_missing = false`: set `is_missing` and `missing_flagged_at`; audit entry by `system` |
| `purge_verification_documents` | Daily 03:00 Asia/Riyadh | Documents of requests decided more than `verification.document_retention_days` days ago: delete the stored file, set `purged_at` |
| `cleanup` | Daily 03:30 Asia/Riyadh | Delete expired sessions and tokens, and `job_runs` older than 30 days |

The job functions are plain functions so tests call them directly with a fixed clock.

## 8. Skill Extraction

Design 6.1 asks for an Aho–Corasick automaton. Because every term is a whole word or a phrase of at most four words, the same result is reached with a dictionary of normalized n-grams: the normalized text is split into tokens (`[a-z0-9+#.]+` and Arabic letter runs), every n-gram of 1 to 4 tokens is looked up in a dictionary built from the active skills' `match_terms`, and the longest match wins at each position. The dictionary is rebuilt when the vocabulary changes. It needs no extra library and runs in milliseconds for a CV.

The seed vocabulary holds 160 skills (computing plus common professional skills) with English and Arabic names and common synonyms. Synonyms that are everyday words (for example "rest", "spring", "office", "العربية") were left out because they matched ordinary text; "Go" and "R" are named "Go (Golang)" and "R Programming" for the same reason.

## 9. Environments

- **Local and demo (M3):** `docker compose up` starts PostgreSQL 16 on port 5433, the API on 8000 (`alembic upgrade head` then `uvicorn`), the web app on 5173, and Mailpit (SMTP 1025, inbox at 8025). The API container loads the reference data (majors, skills, universities) on every start; `docker compose exec api python -m app.seed --demo` adds the demo accounts (password `Demo-2026-pass`, local use only, refused when `ENV=production`).
- **CI:** GitHub Actions with a PostgreSQL service: `ruff`, `pytest` with coverage (gate 70%), the OpenAPI contract check, then for the frontend the generated-types check, `tsc` (strict), `vitest` (including the translation-key check), and `vite build`.
- **Free-tier deployment:** start of Increment 2 (RQ-7).

## 10. Frontend

React 18, Vite, TypeScript, React Router, TanStack Query, react-i18next, Tailwind CSS with logical properties. The API types are generated from `/openapi.json` by `openapi-typescript`; requests go through `openapi-fetch`.

| **Area** | **Screens (wireframe)** |
|:---|:---|
| Public | Login (`Login`), Register (`Register`), confirm email, accept invitation, forgot and reset password |
| All roles | Privacy notice (`Consent`), verification status (`Verification_Pending`), role home page, language switch |
| Student | Profile and CV with skill confirmation (`ST_Profile`), vacancies browse and apply (`ST_Vacancies`, browse tab), my applications, report list and report form (`ST_Report`) |
| Company | Vacancies and editor (`CS_VacancyEditor`), applicants (`CS_Applicants`), team (`CS_Team`), trainees' reports (read-only) |
| Academic supervisor | My students, report review with comments (`AS_ReportReview`, without the similarity panel) |
| Coordinator | Students and verification (`CO_Students`), academic supervisors (`CO_Supervisors`), cycle settings (`CO_CycleSettings`), placements (`CO_Placements`), audit log (`CO_Audit`) |
| Platform Admin | Verifications (`PA_Verifications`), universities, colleges, and companies (`PA_Organizations`), skills, majors, and settings (`PA_Settings`) |

The role home page lists the role's menu with short descriptions; the dashboards with counts come in Increment 2.

## 11. Test Design

- **Database:** tests run against a real PostgreSQL (Docker locally, a service in CI). The schema is created once per session with Alembic; every test starts from empty tables (`TRUNCATE … CASCADE`) plus the seed of the fixture it needs.
- **Clock:** `app.core.clock.now()` is the only source of time; tests freeze and move it.
- **Email and files:** an in-memory mail outbox and a temporary storage directory per test session.
- **Fixtures:** factories (`tests/factories.py`) create universities, colleges, companies, users of every role (verified or not), cycles, vacancies, applications, and placements, and sample PDF, DOCX, and PNG files; `f.headers(user)` returns the headers of a signed-in session. The `w` fixture builds the standard world.
- **Suites:** `test_auth`, `test_orgs`, `test_cycles`, `test_profiles` (with the catalog), `test_vacancies`, `test_reports`, `test_audit_jobs`, `test_config`, the end-to-end `test_demo_scenario`, unit tests for time, eligibility, report transitions, and skill extraction inside those files, and the permission suite.
- **Permission matrix:** `tests/permissions/matrix.yaml` lists every route with the roles allowed to call it (`public`, `unverified`, `st`, `cs`, `ca`, `as`, `co`, `pa`). The suite calls every route as every role that is not allowed and expects `401` or `403`; a second test fails if a registered route is missing from the matrix. Scope rules (other college, other company, other student) are tested in the module suites with two universities, three colleges, and two companies.
- **Acceptance tests:** each test of 01_Requirements.md Section 6 is a named test function (`test_at_vac_04_…`), so the test report can list them.
- **Frontend:** Vitest checks that `ar.json` and `en.json` have the same keys, that every key used in the code exists, and that placeholders match (FR-LOC-02), plus the date format (NFR-L10N-02); the screens are checked by hand in both languages during the demo dry run.

## 12. Changes During Implementation

Recorded as [CR-07](../../Change_Requests.md); the system design (1.3) and the API specification (1.2) were updated in the same pull request. The test results are in [04_Test_Report.md](04_Test_Report.md).

| **Change** | **Why** |
|:---|:---|
| `PATCH /me` answers before consent | The privacy notice must be readable in either language |
| Purged verification documents keep `file_id` and set `purged_at` | Setting it to null lost the record of what was submitted; the file endpoint answers `410 FILE_PURGED` |
| Transaction-level advisory locks for jobs | A test showed that a session-level lock could stay on a pooled connection after a failed run, so the job would never run again |
| `GET /admin/universities`, `GET /placements/candidates`, `company_id` filter on `GET /placements` | Needed by the organizations page and the coordinator's placement screen |
| Development-only demo clock `/dev/clock` | The M3 demo shows late and missing reports without waiting a week |
| Supervisors see the cycles of their own placements | The report pages show the cycle's schedule |
| Error codes added to the API specification | They were raised by the code but missing from the contract |

Defects found by the tests and fixed before the pull request:

- The access token's issue time was checked against the system clock instead of the application clock, so sessions failed whenever the two differed.
- Error messages were not shown in the user's saved language: the language was set in a worker thread and lost before the error was written. It is now kept on the request.
- Publishing a vacancy in the same request that created it failed, because the database session did not flush the new majors before checking them.
- The job lock described above.
- The API container stopped at start when `CORS_ORIGINS` was a plain comma-separated value.
- The Missing flag waited 15 minutes after every restart; it now also runs 30 seconds after start.
- Numbers such as `3.10 / 5.00` were reversed in Arabic pages; they are now shown left to right.
