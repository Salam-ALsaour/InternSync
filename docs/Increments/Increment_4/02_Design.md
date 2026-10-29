# Increment 4 – Design

**Status:** Approved Oct 28, 2026 · Author: Salam Alsaour  
**Inputs:** [01_Requirements.md](01_Requirements.md), [Design 1.5](../../Design/InternSync_Design.md) (Sections 4.3.6, 4.3.7, 4.5, 5.6, 5.7), [API 1.4](../../Design/InternSync_API_Spec.md) (Sections 3.12, 3.14, 3.16, 4.11)

The system design already describes the certificate, the evaluation of the company, the survey, and the leniency alert, so this document records only what the design left open and how it is built. Section 12 lists what changed during implementation.

## 1. Modules

| **Module** | **New in this increment** |
|:---|:---|
| `certificates` | Issue, list, view, revoke, and the public check; the certificate PDF with its QR code |
| `evaluations` | The student's evaluation of the company and the job-offer survey (`feedback.py`) |
| `dashboard` | Job-offer rates, company averages, leniency alerts; the new dashboard items |
| `privacy` | The retention period and the anonymization of a closed cycle |
| `exports` | The certificate page; the term summary gains the job-offer rate and the company averages |
| Frontend `lib/offline.ts` | The saved copy of the session, the offline idle limit, and the offline drafts |

## 2. Data (migration `0006`)

The three tables of Design 4.3.6 and 4.3.7, as specified there:

- `company_evaluations`;
- `outcome_surveys`;
- `certificates`, with its partial unique index of one `valid` certificate per placement.

The other additions:

| **Table** | **Change** | **Why** |
|:---|:---|:---|
| `colleges` | `retention_months smallint NOT NULL DEFAULT 12 CHECK 0–120` | NFR-PRV-04: the retention period is set per college (RQ-5) |
| `training_cycles` | `anonymized_at`, `anonymized_by` | Anonymization runs once per cycle and is shown on the cycle |
| `users` | `anonymized_at` | Marks anonymized accounts: they cannot sign in, and their audit entries are masked (Section 7) |
| `files` | `purged_at` | A file removed from storage answers `410 FILE_PURGED`, as verification documents already do |
| `system_settings` | `dashboard.leniency_min_evaluations` = 5, `dashboard.leniency_delta` = 0.8 | Design Table 4.1 (FR-DSH-04) |

Row level security is switched on for the three new tables, as for every table (migration `0003`).

## 3. Endpoints

The endpoints of API Sections 3.12 (evaluation of the company and survey), 3.14 (`/cycles/{id}/outcomes`, `/cycles/{id}/leniency-alerts`), and 3.16 (certificates), plus:

| **Method** | **Path** | **Roles** | **Purpose** |
|:--|:---|:---|:---|
| GET | `/placements/{id}/certificate` | CO, ST (own) | The placement's certificate (the valid one, else the latest), or `null`; with `can_issue` and `can_revoke` for the caller |
| GET | `/placements/{id}/feedback` | ST (own), CO | Both answers and whether the student can still give them (`open_from`, `can_evaluate`, `can_answer`) |
| GET | `/colleges/{id}/retention` | CO (own college) | `{retention_months}` |
| PUT | `/colleges/{id}/retention` | CO (own college) | `{retention_months}`, 0–120; audited |
| GET | `/cycles/{id}/anonymization` | CO | `status` (`open`, `waiting`, `ready`, `done`), `closed_at`, `eligible_at`, the number of students to anonymize and to skip |
| POST | `/cycles/{id}/anonymize` | CO | `{confirm: true}`; `409 RETENTION_NOT_OVER` before `eligible_at`, `409 ALREADY_ANONYMIZED` after it ran |

`GET /me` gains `idle_timeout_minutes`, so the app applies the same idle limit offline (RQ-2). Files of purpose `certificate` are served by `GET /files/{id}` to the student and to the coordinator of the student's college.

## 4. Certificates (FR-CER-01 – 03)

- **Code:** 16 random bytes from `secrets` in base32 without padding, 26 characters. The lookup removes spaces and dashes and ignores case, so a code typed from paper still matches. The code is the only key on the public path; 128 random bits cannot be guessed.
- **Issue:** the coordinator of the student's college, only when the grade is Final (`409 GRADE_NOT_FINAL`) and no valid certificate exists (`409 CERTIFICATE_EXISTS`). The PDF is built at once, stored with purpose `certificate`, and linked by `file_id`. The cycle may already be closed: issuing is not a change to the cycle's records.
- **PDF (RQ-4):**
  - one A4 landscape page with the English text on the left and the Arabic text on the right;
  - the student's name in both languages, the university and college, the cycle, the company, and the training dates;
  - the issue date, the code, and a QR code of `FRONTEND_BASE_URL/verify/<code>`;
  - drawn with the fpdf2 document class of the exports, with the QR image from `qrcode`.
- **Revoke:** the coordinator gives a reason; the status, time, and person are stored, and a new certificate can then be issued.
- **Notifications:** `certificate.issued` and `certificate.revoked` go to the student.
- **Audit:** `issue` and `revoke` entries on the entity `certificate`.
- **Public check:** `GET /public/certificates/{code}` answers `200` in every case, with `status` `valid`, `revoked`, or `not_found`, and for the first two:
  - the student name in both languages;
  - the university and college;
  - the cycle;
  - the company;
  - the training dates.

  Nothing else, as FR-CER-02 lists: never the grade. For a student anonymized after the retention period, the name is left out and `name_removed` is true.

## 5. Evaluation of the Company and Survey (FR-EVL-05, FR-DSH-03)

- **Opens** (RQ-3) at the earlier of:
  - the training end date of the vacancy, in Riyadh time;
  - the moment the grade becomes Final.

  A cancelled placement never opens.
- **Evaluation:** the four ratings (1–5) and "would recommend" are required; the comment is optional. It is submitted once (`409 ALREADY_SUBMITTED` afterwards).
- **Survey:** `yes`, `no`, or `pending`; it can be changed later, and the change is stored in `updated_at`.
- **Who sees it:**
  - The student and the coordinator of the student's college.
  - Company supervisors and Company Admins are refused on every path, including the placement page, which never includes these answers for them.
- **Student dashboard:** the item `feedback_due` counts ended placements with a missing evaluation or survey answer, and links to `/student/feedback`.
- **Company averages** (`/cycles/{id}/company-evaluations`):
  - per company: the number of answers, the mean of each rating, and the share who would recommend;
  - for the whole cycle: the same figures.
- **Outcomes** (`/cycles/{id}/outcomes`):
  - for the cycle and for each company: the answers, the Yes answers, and the rate as Yes ÷ answers;
  - Pending counts as an answer;
  - a student who did not answer is not counted.

## 6. Leniency Alert (FR-DSH-04)

- **Values compared:** for each cycle, the mean of `evaluations.mean_score` over the submitted final evaluations:
  - of the whole cycle (the cycle mean);
  - of each company.
- **Alert:** a company with at least `dashboard.leniency_min_evaluations` final evaluations whose mean is at least `dashboard.leniency_delta` above the cycle mean.
- **Where it shows:**
  - the cycle statistics page;
  - the coordinator dashboard item `leniency_alerts`, which counts the alerts of the college's open cycles and links to the cycles page.
- **Effect:** the alert is informational and changes nothing.

## 7. Anonymization (NFR-PRV-04, RQ-5)

**When:** a closed cycle becomes eligible at `closed_at` plus the college's `retention_months`. The coordinator first sees the counts (`GET /cycles/{id}/anonymization`), then confirms. Everything below runs in one transaction with one audit entry (`anonymize`, entity `cycle`, with the counts). The cycle's `anonymized_at` is set.

**Students affected:** the students of the cycle's placements and enrollments. A student is skipped, and counted, while they have a placement or enrollment in another cycle that is open or not yet past its retention period. The next anonymization of that cycle covers them.

**For each student:**

| **Data** | **Result** |
|:---|:---|
| Account | Names become "Student 3F2A1C" and "طالب 3F2A1C" (from the ID); email `anonymized+<id>@invalid`; no password; inactive; sessions, account links, and push subscriptions deleted; `anonymized_at` set |
| Profile | Student number becomes `A` and 16 characters of the ID; interests and languages emptied; embedding cleared. Major, GPA, and level stay for statistics |
| CVs and skills | Files removed from storage (`files.purged_at`, name "removed"); extracted text cleared; extracted and confirmed skills deleted; match scores deleted |
| Verification requests | `submitted_data` replaced by `{"anonymized": true}`; documents removed if still stored |
| Reports | Text fields and `body_text` cleared; attachment files removed; stored passages for similarity deleted; comments and review comments replaced by "—" |
| Evaluations and grades | Overall comments, attendance notes, and grade comments and reasons cleared; scores, statuses, and dates stay |
| Evaluation of the company | Comment cleared; ratings stay |
| Certificates | File removed; the row stays, so the public page still answers, without the name |
| Notifications | The student's own notifications, and the notifications of other users that link to this placement, deleted |

**What stays:** statuses, scores, dates, majors, companies, survey answers, similarity scores, and the audit log, so the statistics of the cycle (`/cycles/{id}/stats`, outcomes, company averages) are unchanged.

**The audit log** is append-only and is not changed. For an anonymized student:

- `GET /audit-log` hides the old and new values and the reason of every entry by or about that student;
- `GET /history` hides the reasons, which may quote the student, and keeps the statuses and scores.

The registration entry no longer stores the email address (it is in the account), so new entries hold no contact details.

## 8. Offline Mode (FR-PWA-03 as changed by CR-10; RQ-1, RQ-2)

**Saved copy.**

- **What is saved:** the answers of the API that the app has shown in this window, as the query cache of TanStack Query.
- **Where:** in `sessionStorage` under `internsync.saved`, written at most once a second.
- **What is never saved:**
  - files and exports, which are not part of the query cache;
  - the audit log;
  - the notification count;
  - every page of the Platform Admin.
- **On start:** with a token but no connection, the app keeps the session and the saved user instead of signing out, and pages show the saved answers with "Saved copy · <time>".
- **A page never opened:** it shows "This page is not saved on this device. Open it when you are online."
- **Deleted:**
  - at sign-out;
  - when another user signs in;
  - when the window closes, because session storage ends with the window;
  - when the idle limit passes.
- **Idle limit:** the app records the last key, click, or touch. After `idle_timeout_minutes` without one it clears the session and the saved copy, online or not, and shows the sign-in page with "Your session ended".

**Offline drafts.**

- **Where:** the report editor and the evaluation form keep what is typed in `localStorage` under `internsync.draft.<user>.<kind>.<id>`. With it they keep the base: the server's draft at the moment the editing started.
- **Saving:** when the connection returns, the draft is saved with the normal draft request if the server's draft still equals the base. If someone saved another version meanwhile, the page shows both texts and the user chooses.
- **Deleted:** after a successful save, at sign-out, and after 7 days.
- **Submitting** and every other change still need the connection, and buttons stay disabled offline, as in Increment 3. Uploading an attachment needs the connection too.

**The service worker** stays as built: it caches the app shell and never caches API answers, so the saved copy exists only in the window's session.

## 9. Frontend

| **Screen** | **Route** | **Role** |
|:---|:---|:---|
| Certificate check (wireframe `Verify_Mobile`) | `/verify/:code` and `/verify` (enter a code) | Public |
| Evaluation of the company and survey | `/student/feedback` | ST |
| Certificate card on the grade page: issue, view, revoke | `/placements/:id` (grade tab) | CO; ST views |
| Certificates of a cycle | `/coordinator/certificates` | CO |
| Job-offer rate, company averages, leniency alerts | Cycle statistics (`/coordinator/cycles/:id`) | CO |
| Retention period and anonymization | Cycle page | CO |
| Saved-copy and not-saved notices, draft status ("Saved on this device", "Saved") | All pages | All except PA |

## 10. Release Checks

| **Check** | **Where** | **Design** |
|:---|:---|:---|
| Browser tests (RQ-7) | `frontend/e2e/`, `playwright.config.ts`, CI job `e2e` | Playwright 1.x against `docker compose` with the demo data:<br>- projects `chromium`, `firefox`, `webkit`, `mobile-chrome` (Pixel 7), and `mobile-safari` (iPhone 14);<br>- one test file per role plus the public check, offline, and layout widths;<br>- `@axe-core/playwright` for contrast on the main pages;<br>- traces kept on failure |
| ZAP baseline (RQ-8) | `.github/workflows/security-scan.yml`, `docker-compose.check.yml` | `ghcr.io/zaproxy/zaproxy:stable` `zap-baseline.py` against the web app; `zap-api-scan.py` against `/api/v1/openapi.json`; the report is kept as an artifact; a high-risk alert fails the run |
| Load test (RQ-9) | `backend/loadtest/locustfile.py` | 50 users, spawn 5 per second, 5 minutes. A mix of `GET /dashboard`, lists (vacancies, reports, placements, grades), and a draft save, signed in as the seeded roles; the 95th percentile per request type is reported |
| Held-out sets (RQ-6) | `ai-eval/data/heldout_matching.json`, `ai-eval/data/heldout_similarity.json`, `evaluate.py --heldout` | Written after the settings of CR-09 were frozen; run once; the results are reported as they are |
| Results file (RQ-10) | `docs/Key_Results.md` | Each row: what, target, result, date, how to repeat; links to the test reports |

## 11. Test Design

| **Area** | **Tests** |
|:---|:---|
| Certificates | Issue refused before Final, a second valid one refused, code length and alphabet, PDF text holds the code and both names, QR decodes to the page address, public answers for valid, revoked, altered, and anonymized, no grade in the answer, revoke needs a reason, audit entries, notifications |
| Evaluation of the company and survey | Opens at the end date or the Final grade; once only; survey can change; CO sees, CS and CA refused on every path; averages and rates on seeded answers; skipped students not counted |
| Leniency | 5 evaluations at 4.8 against 3.6 alert; 4 do not; the delta and minimum come from the settings |
| Anonymization | Refused before the period and twice; counts before; after it: no name, email, student number, CV file, report text, comment, or certificate file of the cycle through any endpoint; skipped students untouched; statistics equal before and after; audit and history masked; the account cannot sign in |
| Offline | Unit tests of the saved copy (what is kept and left out, cleared at sign-out and at the idle limit) and of the draft store (base check, 7-day expiry); browser tests of the saved copy, the not-saved notice, and the draft saved after reconnecting |
| Permission matrix | Every new route with every role |
| Release checks | Section 10 |

## 12. Changes During Implementation

Recorded in CR-11 unless noted.

- **Idle limit on the device:** `GET /me` returns `idle_timeout_minutes`, and the app ends the session after that idle time online as well as offline. The notification count, polled every minute, kept the server session alive (test report, defect 1).
- **Saved copy:** also written when the page is left or reloaded, not only once a second (defect 2).
- **Security headers:**
  - `vercel.json` gains the Content-Security-Policy that Design 7.1 relied on, with `font-src 'self' data:` because the build inlines small fonts, and `Cross-Origin-Opener-Policy`.
  - The production preview sends the same headers.
  - Every API answer carries `X-Content-Type-Options: nosniff` and `Cross-Origin-Resource-Policy: same-origin` (defects 3 and 4).
- **Registration audit entry:** no longer stores the email address (defect 6).
- **Certificates:**
  - The list shows the valid certificate first.
  - An anonymized student gets no new certificate (`409 ALREADY_ANONYMIZED`).
  - The public answer has `name_removed`.
  - `certificate.revoked` notifies the student, besides `certificate.issued`.
- **Release checks:** `docker-compose.check.yml` runs the stack without the model on its own database (`internsync_check`). It also lets the web app answer to the host name `web`, so the ZAP container reaches it on the Compose network. The browser tests in CI run on pull requests only, to save Actions minutes.
- **Demo data:** the closed summer 2025 cycle is built directly in the tables (its dates are in the past) and closed 13 months before the seed runs. The leniency alert of the demo is shown on that cycle's statistics page; the dashboard item counts open cycles only, as designed.
