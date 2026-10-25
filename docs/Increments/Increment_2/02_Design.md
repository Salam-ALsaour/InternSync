# Increment 2 – Design

**Status:** Approved for implementation · Oct 25, 2026 · Author: Salam Alsaour  
**Input:** [01_Requirements.md](01_Requirements.md), [Design 1.3](../../Design/InternSync_Design.md), [API 1.2](../../Design/InternSync_API_Spec.md), [Increment 1 design](../Increment_1/02_Design.md)

This document narrows the system design to what Increment 2 builds and records the decisions the system design leaves open. Where it says nothing, the system design, the API specification, and the Increment 1 design apply unchanged.

## 1. Modules

```
backend/app/
  ai/embeddings.py      Embedder: the real model (sentence-transformers, loaded once, lazily) or the stand-in for tests
  matching/             service (texts, embedding on write, scoring, ranking, snapshot) and router (3.8)
  attendance/           service and router (3.11)
  evaluations/          service and router (3.12, without the Could items)
  grades/               service and router (3.13)
  dashboard/            service and router (3.14: /dashboard, /cycles/{id}/stats, /platform/stats)
  core/storage_supabase.py   Supabase Storage adapter for the reference deployment
ai-eval/                synthetic labelled set and evaluate.py (NFR-AI-03)
```

The matching score functions are pure (vectors and skill sets in, parts and score out), so the evaluation script and the unit tests call them without a database.

## 2. Data (migration `0002`)

| **Change** | **Notes** |
|:---|:---|
| `CREATE EXTENSION vector` | pgvector 0.8 (`halfvec`); local and CI image `pgvector/pgvector:pg16` |
| `student_profiles`, `vacancies`: `embedding halfvec(384)`, `embedding_model text`, `embedded_at timestamptz` | Design 4.3.3 and 4.3.4 |
| `match_scores` | As Design 4.3.4 |
| `attendance_weeks` | As Design 4.3.6, except that `attended_days`, `recorded_by`, and `recorded_at` may be null: a row can exist only to unlock a week that was never recorded (FR-ATT-02). A check keeps them all set or all null |
| `evaluations`, `evaluation_scores` | As Design 4.3.6; `created_at` added |
| `grades`, `grade_component_scores` | As Design 4.3.7; one `draft` grade inserted for every non-cancelled placement that has none (RQ-6) |
| New settings | `attendance.edit_days` 7, `attendance.pending_after_days` 3, `matching.weight_semantic` 0.5, `matching.weight_required` 0.4, `matching.weight_preferred` 0.1, `matching.semantic_floor` 0.70, `matching.semantic_ceiling` 0.95 |

The design's single JSON setting `matching.weights` becomes three numeric settings, so the settings page and its range checks treat every setting the same way (recorded as CR-08). Settings may now be decimals; each key keeps a minimum and a maximum.

The company evaluation by students and the outcome survey (FR-EVL-05, FR-DSH-03, Could) and certificates (Increment 3) get their tables in the increment that builds them.

## 3. Endpoints Built

All of API Sections 3.8, 3.11, 3.13, and these parts of 3.12 and 3.14:

- 3.12: `GET /placements/{id}/evaluations`, `PUT` and `POST …/submit` per type, `POST /evaluations/{id}/reopen`.
- 3.14: `GET /dashboard`, `GET /cycles/{id}/stats`, `GET /platform/stats`.
- 3.8: the development plan (`…/plan`, FR-MAT-06) only if the stretch item is reached.

`GET /placements/{id}` gains `attendance_percent` and `grade_status`. `POST /vacancies/{id}/applications` stores the fit-score snapshot (`fit_score`, `match_mode`, `model_version`), which the applicant list shows to the company.

## 4. Matching

1. **Embedder.** `get_embedder()` returns the model when `AI_ENABLED=true` and `sentence-transformers` can load `EMBEDDING_MODEL`; otherwise `None`, and every caller takes the basic path. The model is loaded once, on first use, under a lock. The version string is `<model>@<revision>` from the model's config, or the model name if no revision is known. Tests install a stand-in embedder that hashes tokens into 384 dimensions, which is deterministic and makes texts with shared words closer.
2. **Texts (Design 6.2).** Profile: confirmed skill names in both languages, interests, and the first 2,000 characters of the current CV text, with `query: `. Vacancy: title, description, required and preferred skill names, with `passage: `.
3. **Embedding on write (RQ-3).** After the student confirms skills, edits interests, or uploads a CV, and after a vacancy is created or edited, the record is embedded in the same request when the model is loaded; if embedding fails, the request still succeeds and the `embed_missing` job (every 15 minutes) fills the gap.
4. **Ranking.** One query selects the eligible vacancies (the Increment 1 eligibility rules, now as SQL) with `1 − (embedding <=> profile)` as the cosine when both vectors exist; one query loads their skills. Scores are computed in Python, sorted by fit, then the required part, then the earlier deadline, and written to `match_scores` with one bulk upsert. The response is the API Section 4.5 shape; `mode` is `basic` when the profile has no embedding or the model is off, and per item when a vacancy has no embedding.
5. **Requirements for a ranking.** Verified and enrolled student (`403 VERIFICATION_REQUIRED`), confirmed skills (`409 SKILLS_NOT_CONFIRMED`).
6. **Snapshot.** On applying, the score of that one vacancy is computed the same way and stored on the application.

## 5. Attendance

- Weeks come from `cycle_weeks`. A week ends at 23:59:59 Asia/Riyadh on `ends_on`.
- States per week: `upcoming` (not started), `open` (started, editable), `pending` (ended, not recorded), `overdue` (pending more than `attendance.pending_after_days` days), `recorded`, `locked` (more than `attendance.edit_days` days after the end and not unlocked).
- `PUT …/attendance/{week_no}` by the placement's company supervisor: `{full: true}` or `{attended_days, note}`. Refused with `409 WEEK_NOT_STARTED` before the week starts, `409 WEEK_LOCKED` when locked, `422 ATTENDED_EXCEEDS_SCHEDULED`, and `409 CYCLE_CLOSED` or `INVALID_TRANSITION` for a closed cycle or an inactive placement.
- Unlock by the coordinator: `{reason, until?}` (default now + 7 days), audited.
- Percentage: attended ÷ scheduled over the recorded weeks, one decimal; `null` before the first record.

## 6. Evaluations

- Rows are created on the first save. Scores must cover criteria of the placement's cycle only (`422 VALIDATION_ERROR` otherwise, FR-EVL-02).
- Submit: every criterion of the cycle rated and the comment non-empty (`422 EVALUATION_INCOMPLETE` with the missing criteria); stores `mean_score`; sets the cycle's `rubric_locked_at` on the first submitted evaluation (FR-CYC-03).
- Due dates: the cycle's `periodic_eval_due_at` and `final_eval_due_at`.
- Reopen by the coordinator: once (`409 ALREADY_REOPENED`), with a reason, back to `draft`. A final evaluation cannot be reopened while its grade is submitted or Final (`409 INVALID_TRANSITION`): the grade is returned or reopened first.
- Visibility: the assigned company supervisor and the Company Admin, the assigned academic supervisor, the coordinator. The student sees a submitted periodic evaluation, and the final evaluation only when the grade is Final.

## 7. Grades

- Created in `draft` on placement confirmation (and by the migration for older placements).
- Components come from the cycle (`grade_components`). The company component is the final evaluation's mean ÷ 5 × 100 once it is submitted; the academic supervisor enters the others (0–100) with `PUT …/grade` while `draft`.
- `total = Σ weight × score ÷ 100`, rounded half up to two decimals, shown as soon as every component has a score and stored on submit and approval.
- Preconditions (FR-WFL-03), returned by `GET …/grade/preconditions` and by `409 PRECONDITIONS_UNMET`: the final evaluation submitted; the final report accepted; each weekly slot accepted or closed as missing; each academic component entered.
- Approve (single or bulk) sets `final`, `approved_at`, and the placement to `completed`; return needs a comment; reopen needs a reason and sets the placement back to `active`. Bulk approval reports a result per grade and writes one audit entry per approved grade.
- The student's `GET …/grade` answers `{visible: false}` until the grade is Final.

## 8. Dashboards

`GET /dashboard` returns `{role, items: [{type, count, link}]}` with live counts (Design 5.7):

| **Role** | **Items** |
|:---|:---|
| Student | `verification` (pending or rejected), `reports_due` (draft or revision requested, due within 7 days or overdue), `revisions_requested`, `applications_submitted`, `applications_accepted`, `grade_final` |
| Company supervisor | `applicants_to_review` (own vacancies; the Company Admin: the company's), `attendance_to_record` (overdue weeks of assigned placements), `evaluations_due` (not submitted, due within 7 days or overdue) |
| Academic supervisor | `reports_to_review`, `grades_to_submit` (draft grades whose preconditions are met), `grades_returned` |
| Coordinator | `students_to_verify`, `placements_to_confirm`, `grades_to_approve` |
| Platform Admin | `verifications_pending` (with the oldest age in days) |

`GET /cycles/{id}/stats?company_id` returns, overall and per company: enrolled, placed, and unplaced students; report submission rate and late rate over slots whose deadline has passed; attendance rate over recorded weeks; evaluation completion over evaluations that are due. `GET /platform/stats` returns the counts of FR-DSH-05 and nothing about students' records.

## 9. Frontend

| **Area** | **Screens (wireframe)** |
|:---|:---|
| All roles | The home page becomes the dashboard: pending items with counts and links, then the menu (`ST_Dashboard`, `CS_Dashboard`, `AS_Dashboard`, `CO_Dashboard`, `PA_Dashboard`) |
| Student | Vacancies get a "Recommended" tab: fit score, parts, matched and missing skills, Advisory label, "Basic matching" label (`ST_Vacancies`); the placement page shows attendance, the visible evaluations, and the Final grade |
| Company | The placement page gets an attendance tab with "Full attendance" per week (`CS_Attendance`) and the evaluation form (`CS_Evaluation`); applicants show the fit-score snapshot |
| Academic supervisor | Grade tab on the placement page: components, computed company component, preconditions checklist, submit (`AS_Grade`) |
| Coordinator | Grades page: submitted grades with approve, return, bulk approve, and reopen (`CO_Grades`); cycle statistics on the cycle page; attendance unlock and evaluation reopen on the placement page |
| Platform Admin | Platform figures on the dashboard |

The placement page (`/placements/:id`) becomes the single place for one trainee: tabs Reports, Attendance, Evaluations, Grade, shown by role.

## 10. Deployment (RQ-8)

| **Part** | **Prepared in this increment** | **Owner step** |
|:---|:---|:---|
| Database | Supabase project (free) with `vector` and `pg_trgm`; migrations run by the API on start; Data API off, RLS on every table | – (through the connected account) |
| File storage | `STORAGE_BACKEND=supabase` adapter: private bucket, uploads and signed links of 60 s | Copy the service key into the Space secrets |
| API | `backend/Dockerfile` with the model baked in, port from `PORT` (7860 on Spaces); `deploy-api.yml` pushes `backend/` to the Space when `HF_TOKEN` is set | Create the Hugging Face account, the Space, and the token |
| Web app | Vercel project for `frontend/`, `VITE_API_URL` pointing at the Space, SPA rewrites in `vercel.json` | – (through the connected account) |
| Email | Gmail SMTP settings | Create the app password |
| Operations | `keepalive.yml` (every 6 hours) and `backup.yml` (nightly, encrypted `pg_dump`), both skipped while their secrets are missing | Add the secrets |

The checklist with the exact values goes to `docs/Deployment.md`.

## 11. Test Design

- **Stand-in embedder** in `conftest.py`; one test runs with `AI_ENABLED=false` semantics (no embedder) for the basic mode.
- **Factories:** `f.complete_placement(...)` builds a placement whose reports are all accepted, its attendance recorded, and both evaluations submitted, so grade tests start from the point they need.
- **Timed test** (NFR-PER-02): 1,000 published vacancies with embeddings, 20 ranking requests, 95th percentile under 5 s; marked `slow` and run in CI.
- **Permission matrix:** the new routes are added; the module suites check scope (the other company, the other college, the other student).
- **Evaluation script:** `python ai-eval/evaluate.py` with the real model prints extraction recall and the top-5 hit rate; the numbers go into the test report.
