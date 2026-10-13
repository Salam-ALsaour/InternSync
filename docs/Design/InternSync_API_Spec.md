# InternSync – API Specification

CSC 305 – Software Engineering · Semester 1 – 2026/2027 · Section 5MA1 · Group 3  
Task T2 (System design) · Milestone M2 · Version 1.0 · October 13, 2026

| **Version** | **Date** | **Description** | **Author** |
|:--:|:--:|:---|:--:|
| 1.0 | Oct 13, 2026 | First version for Milestone M2. | Salam Alsaour |

This document is the API contract agreed before implementation (SPMP risk "integration problems"). During development, FastAPI generates the OpenAPI 3.1 document from the code at `/api/v1/openapi.json` (NFR-MNT-02), and the frontend client is generated from it. The generated document must match this specification; any difference is either a bug or a change that is recorded here first.

Related: [System Design Document](InternSync_Design.md) (data model, state machines, security) and [SRS v1.1](../RSR/InternSync_SRS.md).

## Table of Contents

- [1. Conventions](#1-conventions)
- [2. Roles and Scope Notation](#2-roles-and-scope-notation)
- [3. Endpoints](#3-endpoints)
- [4. Main Payloads](#4-main-payloads)
- [5. Error Codes](#5-error-codes)
- [6. Verification](#6-verification)

## 1. Conventions

| **Topic** | **Rule** |
|:---|:---|
| Base URL | `https://<api-host>/api/v1`. Reference deployment: the Hugging Face Space URL; local: `http://localhost:8000/api/v1`. |
| Transport | HTTPS only (NFR-SEC-01). CORS allows only the configured frontend origins. |
| Format | JSON in UTF-8. File uploads use `multipart/form-data`. Field names are `snake_case`. |
| Authentication | `Authorization: Bearer <access_token>` from `POST /auth/login`. The token carries a session ID; the session ends after 30 idle minutes or at logout (FR-AUT-03). Endpoints marked **Public** need no token. |
| Language | Error messages and generated texts use the user's saved language, or `Accept-Language: ar` / `en` before login. User-entered content is returned as entered (FR-LOC-02). |
| Identifiers | UUID strings, except `code` of certificates (26-character base32). |
| Dates and times | ISO 8601 with offset. The server returns UTC (`2026-11-05T20:59:00Z`); the client shows Asia/Riyadh time as `DD/MM/YYYY HH:mm` (NFR-L10N-02). Plain dates use `YYYY-MM-DD`. |
| Enumerations | Lowercase values, the same as the database (for example `pending_review`, `revision_requested`). |
| Lists | Paginated with `?page=1&page_size=20` (maximum 100). Response: `{"items": [...], "page": 1, "page_size": 20, "total": 134}`. Sorting with `?sort=field` or `?sort=-field`. |
| State changes | Each transition of a state machine is its own `POST /<resource>/{id}/<action>` endpoint, so each maps to one row of the transition tables in the design document (Section 5.1). Every successful change writes one audit entry (FR-AUD-01). |
| Errors | `application/problem+json` (RFC 9457) with a stable `code` (Section 5). |
| Downloads | Files are never served from a public URL. `GET /files/{id}` checks permission and redirects to a short-lived link (NFR-SEC-04). Export endpoints return the file directly. |

**Status codes used:** `200` OK, `201` created, `202` accepted, `204` no content, `302` redirect to a file, `400` malformed request, `401` not logged in or session ended, `403` role, scope, or consent not allowed, `404` not found, `409` conflict with the current state or a limit, `410` link already used or expired, `413` file too large, `415` file type not allowed, `422` validation failed, `423` account locked, `429` too many requests.

**Error body**

```json
{
  "type": "about:blank",
  "title": "Application limit reached",
  "status": 409,
  "code": "APPLICATION_LIMIT_REACHED",
  "detail": "لديك 5 طلبات نشطة. اسحب طلباً قبل التقديم على فرصة أخرى.",
  "errors": []
}
```

For `422`, `errors` lists each field: `{"field": "weights", "code": "WEIGHTS_NOT_100", "message": "…"}`. Some codes add data, for example `missing` for `PRECONDITIONS_UNMET` (Section 4.9).

## 2. Roles and Scope Notation

| **Notation** | **Meaning** |
|:---|:---|
| ST, CS, AS, CO | Student, Company Supervisor, Academic Supervisor, Coordinator |
| Public | No login needed |
| Any | Any logged-in user |
| (own) | Only the caller's own records |
| (own vacancy) | Vacancies whose `company_supervisor_id` is the caller, and their applications |
| (assigned) | Placements where the caller is the company or academic supervisor, and the records under them |
| (all) | Every record (Coordinator) |

A request for a record outside the caller's scope returns `403 FORBIDDEN`. Each endpoint below is in the permission matrix test (Section 6).

## 3. Endpoints

### 3.1 Authentication and Session

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| POST | `/auth/login` | Public | Log in with email and password; returns the access token and the user | FR-AUT-03, NFR-SEC-03 |
| POST | `/auth/logout` | Any | End the current session; the token stops working | FR-AUT-03 |
| GET | `/auth/tokens/{token}` | Public | Check an activation or reset link before showing its form: `{purpose, valid, reason}` | FR-AUT-02, FR-AUT-04 |
| POST | `/auth/activate` | Public | `{token, password}`: set the first password and activate the account | FR-AUT-02 |
| POST | `/auth/password/forgot` | Public | `{email}`: always `202`; sends a reset link if the account exists | FR-AUT-04 |
| POST | `/auth/password/reset` | Public | `{token, password}`: set a new password and end all sessions | FR-AUT-04 |
| GET | `/me` | Any | The current user, role, language, and `consent_required` | FR-AUT-01 |
| PATCH | `/me` | Any | `{language}` | FR-LOC-01 |
| POST | `/me/consent` | Any | Acknowledge the privacy notice | NFR-PRV-01 |

### 3.2 Users, Companies, and Imports

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/users` | CO | Search accounts: `?role&q&is_active&company_id&cycle_id` | FR-AUT-02 |
| POST | `/users` | CO | Create one account and email its activation link | FR-AUT-02 |
| GET | `/users/{id}` | CO | Account details | FR-AUT-02 |
| PATCH | `/users/{id}` | CO | Names, company, department, staff ID | FR-AUT-02 |
| POST | `/users/{id}/deactivate` | CO | Deactivate and end all sessions | FR-AUT-06 |
| POST | `/users/{id}/reactivate` | CO | Reactivate | FR-AUT-06 |
| POST | `/users/{id}/resend-activation` | CO | New activation link; the old one is revoked | FR-AUT-02 |
| GET | `/companies` | CO (all), CS (own) | List companies | FR-VAC-01 |
| POST | `/companies` | CO | `{name, city}` | FR-VAC-01 |
| PATCH | `/companies/{id}` | CO | Edit a company | FR-VAC-01 |
| POST | `/imports/students` | CO | Multipart `file` (students.csv) and `cycle_id`; returns the import report | FR-PRF-01 |
| POST | `/imports/staff` | CO | Multipart `file` (staff.csv); returns the import report | FR-PRF-01 |
| GET | `/imports` | CO | Earlier imports | FR-PRF-01 |
| GET | `/imports/{id}` | CO | One import report | FR-PRF-01 |

### 3.3 Training Cycles

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/cycles` | Any (ST: enrolled cycles; CS, AS: cycles of their records; CO: all) | List cycles | FR-CYC-01 |
| POST | `/cycles` | CO | Create a cycle; generates its weeks and deadlines | FR-CYC-01 |
| GET | `/cycles/{id}` | Same as list | Cycle details | FR-CYC-01 |
| PATCH | `/cycles/{id}` | CO | Edit; dates, weeks, working days, and report day and time only before the first placement (`409 SCHEDULE_LOCKED`) | FR-CYC-01 |
| GET | `/cycles/{id}/weeks` | Same as list | Weeks with dates, report deadline, scheduled days | FR-CYC-01 |
| PATCH | `/cycles/{id}/weeks/{week_no}` | CO | `{report_due_at, reason}`: move one week's deadline; updates the slots still in draft | FR-CYC-01 |
| POST | `/cycles/{id}/close` | CO | Make the cycle read-only | FR-CYC-05 |
| POST | `/cycles/{id}/reopen` | CO | `{reason}` | FR-CYC-05 |
| GET | `/cycles/{id}/grade-components` | CO, AS | Components and weights | FR-CYC-02 |
| PUT | `/cycles/{id}/grade-components` | CO | Replace the list; total must be 100 (`422 WEIGHTS_NOT_100`); refused after a grade is submitted (`409 GRADES_EXIST`) | FR-CYC-02 |
| GET | `/cycles/{id}/rubric` | Any in the cycle | Criteria with the five level descriptions | FR-CYC-03 |
| PUT | `/cycles/{id}/rubric` | CO | Replace the criteria; refused after the first evaluation (`409 RUBRIC_LOCKED`) | FR-CYC-03 |
| GET | `/cycles/{id}/enrollments` | CO | Enrolled students | FR-PRF-01 |

### 3.4 Skill Vocabulary, Majors, and Settings

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/skills` | Any | Search skills: `?q` matches both names and synonyms | FR-CYC-04 |
| POST | `/skills` | CO | `{name_en, name_ar, synonyms}` | FR-CYC-04 |
| PATCH | `/skills/{id}` | CO | Edit names, synonyms, `is_active` | FR-CYC-04 |
| GET | `/skills/{id}/resources` | Any | Learning resources | FR-CYC-04 |
| PUT | `/skills/{id}/resources` | CO | Replace the resources (title, URL, effort, language) | FR-CYC-04 |
| GET | `/majors` | Any | List majors | FR-VAC-01 |
| POST | `/majors` | CO | Add a major | FR-VAC-01 |
| PATCH | `/majors/{id}` | CO | Edit names | FR-VAC-01 |
| GET | `/settings` | CO | All configurable defaults with their values | NFR-MNT-03 |
| PATCH | `/settings` | CO | `{ "<key>": <value>, … }`; each value is validated; takes effect at once | NFR-MNT-03 |

### 3.5 Student Profile and CV

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/students/me/profile` | ST | Profile: major and GPA (read-only), languages, interests, confirmed skills, current CV | FR-PRF-02 |
| PATCH | `/students/me/profile` | ST | `{languages, interests}`; major and GPA are refused (`422 READ_ONLY_FIELD`) | FR-PRF-02 |
| GET | `/students/me/cvs` | ST | CV history | FR-PRF-03 |
| POST | `/students/me/cvs` | ST | Multipart `file` (PDF or DOCX, ≤ 5 MB): stores the CV, extracts text and skills | FR-PRF-03 – 05, NFR-PER-03 |
| GET | `/students/me/skills` | ST | Confirmed skills | FR-PRF-04 |
| PUT | `/students/me/skills` | ST | `{skills: [{skill_id, source}]}`: confirm the list; recomputes the profile embedding | FR-PRF-04 |
| GET | `/students/{id}/profile` | CS (applicant to own vacancy, or assigned), AS (assigned), CO | Profile, confirmed skills, current CV file | FR-VAC-06 |

### 3.6 Vacancies

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/vacancies` | ST (published, enrolled cycles), CS (own company), CO (all) | Browse: `?cycle_id&q&city&company_id&major_id&skill_id&status`. For ST each item carries `eligible` and `ineligible_reason` | FR-VAC-03, FR-MAT-03 |
| POST | `/vacancies` | CS (own company; created as `draft`), CO (created as `published`) | Create a vacancy | FR-VAC-01, FR-VAC-02 |
| GET | `/vacancies/{id}` | Same as list | Details with required and preferred skills and eligible majors | FR-VAC-01 |
| PATCH | `/vacancies/{id}` | CS (own vacancy, `draft`), CO | Edit; a published vacancy is embedded again | FR-VAC-01 |
| POST | `/vacancies/{id}/submit` | CS (own vacancy) | `draft` → `pending_review` | FR-VAC-02 |
| POST | `/vacancies/{id}/publish` | CO | `pending_review` → `published` | FR-VAC-02 |
| POST | `/vacancies/{id}/return` | CO | `{comment}`: `pending_review` → `draft` | FR-VAC-02 |
| POST | `/vacancies/{id}/close` | CO | `published` → `closed` | FR-VAC-02 |

### 3.7 Applications and Placements

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| POST | `/vacancies/{id}/applications` | ST | Apply; stores the fit-score snapshot | FR-VAC-04 |
| GET | `/vacancies/{id}/applications` | CS (own vacancy), CO | Applicants with profile summary, confirmed skills, fit snapshot | FR-VAC-06 |
| GET | `/applications` | ST (own), CO (all) | `?status&cycle_id&placed=false` (CO: accepted applicants waiting for a placement) | FR-VAC-04, FR-VAC-07 |
| GET | `/applications/{id}` | ST (own), CS (own vacancy), CO | One application | FR-VAC-06 |
| POST | `/applications/{id}/withdraw` | ST (own) | `submitted` → `withdrawn` | FR-VAC-05 |
| POST | `/applications/{id}/accept` | CS (own vacancy), CO | `submitted` → `accepted` | FR-VAC-06 |
| POST | `/applications/{id}/decline` | CS (own vacancy), CO | `submitted` → `declined` | FR-VAC-06 |
| POST | `/placements` | CO | `{application_id, academic_supervisor_id, company_supervisor_id?}`: confirm; creates report slots and the draft grade | FR-VAC-07, FR-REP-01 |
| GET | `/placements` | ST (own), CS, AS (assigned), CO (all) | `?cycle_id&company_id&academic_supervisor_id&status` | FR-VAC-07 |
| GET | `/placements/{id}` | Same as list | Overview: student, vacancy, supervisors, status, attendance %, report summary, grade status | FR-VAC-07, FR-ATT-03 |
| PATCH | `/placements/{id}/academic-supervisor` | CO | `{academic_supervisor_id, reason}` | FR-VAC-08 |
| POST | `/placements/{id}/cancel` | CO | `{reason}` | FR-VAC-08 |

### 3.8 Matching

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/students/me/matches` | ST | Ranked eligible vacancies: `?cycle_id&limit`. Needs confirmed skills (`409 SKILLS_NOT_CONFIRMED`) | FR-MAT-01 – 05, FR-MAT-07, NFR-PER-02 |
| GET | `/students/me/matches/{vacancy_id}` | ST | One vacancy's fit with its explanation | FR-MAT-05 |
| GET | `/students/me/matches/{vacancy_id}/plan` | ST | Development plan for the missing skills | FR-MAT-06 |

### 3.9 Weekly and Final Reports

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/placements/{id}/report-slots` | ST (own), CS (assigned, read), AS (assigned), CO | All slots with status, deadline, Late and Missing flags | FR-REP-01, FR-REP-04 |
| GET | `/report-slots/{id}` | Same | Slot with submitted versions, reviews, and attachments; the draft only for ST | FR-REP-03, FR-REP-05 |
| PUT | `/report-slots/{id}/draft` | ST (own) | Create or update the draft's text fields | FR-REP-03 |
| POST | `/report-slots/{id}/draft/attachments` | ST (own) | Multipart `file` and `role` (`main` or `attachment`) | FR-REP-02 |
| DELETE | `/report-slots/{id}/draft/attachments/{attachment_id}` | ST (own) | Remove an attachment from the draft | FR-REP-02 |
| POST | `/report-slots/{id}/submit` | ST (own) | Submit or resubmit the draft; records server time and the Late flag; starts the similarity check | FR-REP-02, FR-REP-04, FR-SIM-01 |
| POST | `/report-slots/{id}/accept` | AS (assigned) | `submitted` → `accepted` | FR-REP-05 |
| POST | `/report-slots/{id}/request-revision` | AS (assigned) | `{comment}`: `submitted` → `revision_requested` | FR-REP-05 |
| POST | `/report-slots/{id}/close-missing` | AS (assigned) | `draft` → `closed_missing` after the deadline | FR-REP-07 |
| GET | `/report-slots/{id}/comments` | ST (own), CS (assigned, read), AS (assigned), CO | Comments with author and time | FR-REP-06 |
| POST | `/report-slots/{id}/comments` | ST (own), AS (assigned) | `{body}` | FR-REP-06 |
| GET | `/report-versions/{id}` | ST (own), CS, AS (assigned), CO | One version; drafts only for ST | FR-REP-05 |

### 3.10 Similarity

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/report-versions/{id}/similarity` | AS (assigned), CO | Status, score, flag, sources with matching passages; source author only for CO | FR-SIM-02 |
| POST | `/report-versions/{id}/similarity/decision` | AS (assigned) | `{decision: no_issue \| overlap_confirmed, comment}`; only for flagged checks | FR-SIM-03 |
| GET | `/similarity-checks` | AS (assigned), CO | `?cycle_id&flagged=true&decided=false` | FR-DSH-01 |

### 3.11 Attendance

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/placements/{id}/attendance` | ST (own), CS, AS (assigned), CO | Weeks with recorded days, pending or locked state, and the percentage | FR-ATT-03, FR-ATT-04 |
| PUT | `/placements/{id}/attendance/{week_no}` | CS (assigned) | `{attended_days, note}` or `{full: true}`; refused before the week starts or when locked | FR-ATT-01, FR-ATT-02 |
| POST | `/placements/{id}/attendance/{week_no}/unlock` | CO | `{reason, until}` (default: 7 days from now) | FR-ATT-02 |

### 3.12 Evaluations

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/placements/{id}/evaluations` | CS, AS (assigned), CO; ST (own: periodic when submitted, final only when the grade is Final) | Evaluations with scores | FR-EVL-03 |
| PUT | `/placements/{id}/evaluations/{type}` | CS (assigned) | Save a draft: `{scores: [{criterion_id, score}], overall_comment}`; `type` is `periodic` or `final` | FR-EVL-01 |
| POST | `/placements/{id}/evaluations/{type}/submit` | CS (assigned) | Submit; every criterion and the comment are required; locks the rubric | FR-EVL-01, FR-CYC-03 |
| POST | `/evaluations/{id}/reopen` | CO | `{reason}`; once per evaluation | FR-EVL-04 |
| GET | `/placements/{id}/company-evaluation` | ST (own), CO | The student's evaluation of the training entity | FR-EVL-05 |
| PUT | `/placements/{id}/company-evaluation` | ST (own) | Submit it once the placement has ended | FR-EVL-05 |
| GET | `/cycles/{id}/company-evaluations` | CO | Averages per company | FR-EVL-05 |
| GET | `/placements/{id}/outcome-survey` | ST (own), CO | Job-offer answer | FR-DSH-03 |
| PUT | `/placements/{id}/outcome-survey` | ST (own) | `{job_offer: yes \| no \| pending}` | FR-DSH-03 |

### 3.13 Grades

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/placements/{id}/grade` | AS (assigned), CO; ST (own, only when Final, otherwise `{"visible": false}`) | Components, total, status, history link | FR-WFL-02, FR-WFL-06 |
| PUT | `/placements/{id}/grade` | AS (assigned) | `{component_scores: [{component_id, score}]}` while `draft`; the company component is computed | FR-WFL-02 |
| GET | `/placements/{id}/grade/preconditions` | AS (assigned), CO | Checklist of the FR-WFL-03 conditions | FR-WFL-03 |
| POST | `/grades/{id}/submit` | AS (assigned) | `draft` → `submitted`, or `409 PRECONDITIONS_UNMET` with the missing items | FR-WFL-03 |
| POST | `/grades/{id}/approve` | CO | `submitted` → `final` | FR-WFL-04 |
| POST | `/grades/{id}/return` | CO | `{comment}`: `submitted` → `draft` | FR-WFL-04 |
| POST | `/grades/{id}/reopen` | CO | `{reason}`: `final` → `draft` | FR-WFL-05 |
| POST | `/grades/bulk-approve` | CO | `{grade_ids}`; one audit entry per grade; result per grade | FR-WFL-07 |
| GET | `/grades` | AS (assigned), CO | `?cycle_id&status` | FR-DSH-01 |

### 3.14 Dashboards and Statistics

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/dashboard` | Any | Pending actions of the caller's role with counts and links | FR-DSH-01 |
| GET | `/cycles/{id}/stats` | CO | Cycle status overall and per company: `?company_id` | FR-DSH-02 |
| GET | `/cycles/{id}/outcomes` | CO | Placement-to-job-offer rate per cycle and per company | FR-DSH-03 |
| GET | `/cycles/{id}/leniency-alerts` | CO | Companies whose mean final score is ≥ 0.8 above the cycle mean | FR-DSH-04 |
| GET | `/escalations` | CO | Items overdue 3 days or more: `?cycle_id&type` | FR-NOT-04 |

### 3.15 Exports

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/cycles/{id}/exports/grade-sheet?format=xlsx\|pdf` | CO | Grade sheet file | FR-EXP-01, NFR-PER-05 |
| GET | `/cycles/{id}/exports/term-summary` | CO | Term summary PDF | FR-EXP-02 |
| GET | `/placements/{id}/exports/training-record` | CO, AS (assigned) | Student training record PDF | FR-EXP-03 |

### 3.16 Certificates

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| POST | `/placements/{id}/certificate` | CO | Issue a certificate; the grade must be Final | FR-CER-01 |
| GET | `/certificates` | CO | `?cycle_id&status` | FR-CER-01 |
| GET | `/certificates/{id}` | CO, ST (own) | Certificate details and file | FR-CER-01 |
| POST | `/certificates/{id}/revoke` | CO | `{reason}` | FR-CER-03 |
| GET | `/public/certificates/{code}` | Public | Status (`valid`, `revoked`, `not_found`), student name, cycle, company, training dates; never the grade | FR-CER-02 |

### 3.17 Notifications and Push

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/notifications` | Any (own) | `?unread_only`; includes `unread_count` | FR-NOT-01 |
| POST | `/notifications/{id}/read` | Any (own) | Mark one as read | FR-NOT-01 |
| POST | `/notifications/read-all` | Any (own) | Mark all as read | FR-NOT-01 |
| GET | `/push/vapid-public-key` | Any | Public key for the browser subscription | FR-PWA-02 |
| POST | `/push/subscriptions` | Any (own) | `{endpoint, keys: {p256dh, auth}}` | FR-PWA-02 |
| DELETE | `/push/subscriptions` | Any (own) | `{endpoint}` | FR-PWA-02 |

### 3.18 Audit and History

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/audit-log` | CO | `?student_id&user_id&entity_type&entity_id&from&to`; read-only, no update or delete endpoint exists | FR-AUD-02 |
| GET | `/history/{entity_type}/{entity_id}` | Anyone allowed to view the record; `entity_type` is `report_slot`, `evaluation`, or `grade` | State changes with user and time | FR-AUD-03 |

### 3.19 Files

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/files/{id}` | Anyone allowed to view the record that owns the file | `302` to a signed link valid for 60 s (or the file itself with local storage); `403` otherwise | NFR-SEC-04 |

### 3.20 System

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/health` | Public | `{status}`; with `?deep=true` also database, model, and scheduler status (keep-alive and uptime log) | NFR-REL-01 |
| GET | `/version` | Public | Application version and embedding model version | NFR-AI-02 |
| GET | `/openapi.json`, `/docs` | Public | Generated OpenAPI document and its viewer | NFR-MNT-02 |

## 4. Main Payloads

Examples show the main fields; the generated OpenAPI document holds the complete schemas.

### 4.1 Login

`POST /auth/login`

```json
{ "email": "sara.ahmed@example.edu", "password": "••••••••" }
```

`200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs…",
  "token_type": "bearer",
  "expires_at": "2026-11-05T08:00:00Z",
  "idle_timeout_minutes": 30,
  "user": {
    "id": "6f1c…", "role": "student", "name_en": "Sara Ahmed", "name_ar": "سارة أحمد",
    "language": "ar", "consent_required": true
  }
}
```

Errors: `401 INVALID_CREDENTIALS`, `423 ACCOUNT_LOCKED` (with `locked_until`), `403 ACCOUNT_INACTIVE`, `403 ACCOUNT_NOT_ACTIVATED`.

### 4.2 Create a Training Cycle

`POST /cycles`

```json
{
  "name": "Co-op Fall 2026", "type": "coop",
  "start_date": "2026-09-06", "end_date": "2026-11-28", "weeks": 12,
  "working_days": [7, 1, 2, 3, 4],
  "report_weekday": 4, "report_time": "23:59",
  "periodic_eval_due_at": "2026-10-15T20:59:00Z",
  "final_eval_due_at": "2026-11-26T20:59:00Z",
  "final_report_due_at": "2026-11-26T20:59:00Z"
}
```

`201 Created` returns the cycle with its `weeks`: `[{"week_no": 1, "starts_on": "2026-09-06", "ends_on": "2026-09-12", "report_due_at": "2026-09-10T20:59:00Z", "scheduled_days": 5}, …]`.

### 4.3 CSV Import Report

`POST /imports/students` → `201 Created`

```json
{
  "id": "b7e2…", "kind": "students", "cycle_id": "0a9d…", "file_name": "students.csv",
  "total_rows": 50, "created_count": 47,
  "rejected": [
    { "row": 7,  "column": "email",      "code": "INVALID_EMAIL" },
    { "row": 19, "column": "student_id", "code": "DUPLICATE_ID" },
    { "row": 33, "column": "gpa",        "code": "MISSING_FIELD" }
  ],
  "new_majors": ["Cybersecurity"]
}
```

### 4.4 CV Upload

`POST /students/me/cvs` (multipart `file`) → `201 Created`

```json
{
  "cv": { "id": "9c3a…", "version_no": 2, "file_id": "e41b…", "uploaded_at": "2026-10-20T09:12:44Z" },
  "text_status": "ok",
  "language": "mixed",
  "extracted_skills": [
    { "skill_id": "1d2e…", "name_en": "JavaScript", "name_ar": "جافا سكربت", "evidence": "…built a dashboard in JS and React…" },
    { "skill_id": "7a8b…", "name_en": "SQL", "name_ar": "إس كيو إل", "evidence": "…قواعد بيانات SQL…" }
  ],
  "advisory": true
}
```

With `text_status: "no_text"` the list is empty and the client shows the FR-PRF-05 message with manual entry.

### 4.5 Ranked Vacancies

`GET /students/me/matches?cycle_id=0a9d…`

```json
{
  "mode": "semantic",
  "model_version": "intfloat/multilingual-e5-small@<revision>",
  "advisory": true,
  "items": [
    {
      "vacancy": { "id": "51f0…", "title": "Junior Data Analyst", "company": "Example Co.", "city": "Dammam",
                   "application_deadline": "2026-09-01T20:59:00Z" },
      "fit_score": 82.40,
      "parts": { "semantic": 0.78, "required": 1.0, "preferred": 0.5 },
      "matched_skills": [ { "id": "7a8b…", "name_en": "SQL", "name_ar": "إس كيو إل" } ],
      "missing_skills": [],
      "already_applied": false
    }
  ]
}
```

In basic mode `mode` is `"basic"`, `parts.semantic` is `null`, and the client shows the "Basic matching" label (FR-MAT-04).

### 4.6 Development Plan

`GET /students/me/matches/{vacancy_id}/plan`

```json
{
  "vacancy_id": "51f0…",
  "missing_skills": [
    { "skill": { "id": "c0d1…", "name_en": "Power BI", "name_ar": "باور بي آي" },
      "resources": [ { "title": "Power BI for beginners", "url": "https://…", "estimated_effort": "8 hours", "language": "en" } ] },
    { "skill": { "id": "f9e8…", "name_en": "Statistics", "name_ar": "الإحصاء" },
      "resources": [], "message": "No resource available yet" }
  ],
  "advisory": true
}
```

### 4.7 Report Slot

`GET /report-slots/{id}` (as the academic supervisor)

```json
{
  "id": "3e5f…", "placement_id": "a1b2…", "kind": "weekly", "week_no": 3,
  "due_at": "2026-09-24T20:59:00Z", "status": "submitted",
  "is_late": true, "is_missing": true,
  "versions": [
    { "id": "77aa…", "version_no": 1, "submitted_at": "2026-09-25T06:30:12Z", "is_late": true,
      "tasks_performed": "…", "learning": "…", "challenges": "…", "next_week_plan": "…",
      "attachments": [ { "id": "c1…", "file_id": "f1…", "original_name": "diagram.png", "role": "attachment" } ],
      "similarity": { "status": "done", "max_score": 0.12, "is_flagged": false },
      "review": null }
  ],
  "allowed_actions": ["accept", "request_revision"]
}
```

`allowed_actions` lists the transitions the caller may run now, so the client shows only valid buttons.

### 4.8 Similarity Result

`GET /report-versions/{id}/similarity` (as the academic supervisor)

```json
{
  "status": "done", "max_score": 0.46, "is_flagged": true, "threshold": 0.30,
  "model_version": "intfloat/multilingual-e5-small@<revision>",
  "advisory": true,
  "matches": [
    { "source": { "version_id": "5d6c…", "cycle": "Co-op Spring 2026", "week_no": 3, "kind": "weekly" },
      "score": 0.46,
      "passages": [ { "report": [120, 410], "report_text": "…", "source": [88, 371], "source_text": "…", "cosine": 0.95 } ] }
  ],
  "decision": null
}
```

For the Coordinator, `source` also includes `"author": {"id": "…", "name_en": "…", "name_ar": "…"}` (FR-SIM-02).

### 4.9 Grade Submission Refused

`POST /grades/{id}/submit` → `409 Conflict`

```json
{
  "status": 409, "code": "PRECONDITIONS_UNMET",
  "title": "The grade cannot be submitted yet",
  "detail": "Complete the items below first.",
  "missing": [
    { "item": "final_evaluation", "message": "The final evaluation is not submitted." },
    { "item": "report_slot", "week_no": 7, "message": "Week 7 report is not accepted or closed as missing." }
  ]
}
```

### 4.10 Dashboard

`GET /dashboard` (as the academic supervisor)

```json
{
  "role": "academic_supervisor",
  "items": [
    { "type": "reports_to_review", "count": 6, "link": "/academic?filter=to_review" },
    { "type": "open_similarity_flags", "count": 1, "link": "/academic?filter=similarity" },
    { "type": "grades_to_submit", "count": 2, "link": "/academic/grades?status=draft" }
  ]
}
```

### 4.11 Public Certificate Verification

`GET /public/certificates/7K2M9QX4…` → `200 OK`

```json
{ "status": "valid", "student_name": { "en": "Sara Ahmed", "ar": "سارة أحمد" },
  "cycle": "Co-op Fall 2026", "company": "Example Co.",
  "training_start": "2026-09-06", "training_end": "2026-11-28" }
```

An unknown or altered code returns `200` with `{"status": "not_found"}`, so the page can always show a clear result (FR-CER-02).

## 5. Error Codes

| **Code** | **HTTP** | **When** | **SRS** |
|:---|:--:|:---|:---|
| `VALIDATION_ERROR` | 422 | Field-level validation failed (see `errors`) | NFR-USA-05 |
| `UNAUTHENTICATED` | 401 | Missing or invalid token | FR-AUT-03 |
| `SESSION_EXPIRED` | 401 | Idle timeout, logout, or maximum session length reached | FR-AUT-03 |
| `FORBIDDEN` | 403 | Role or record scope not allowed | FR-AUT-05 |
| `CONSENT_REQUIRED` | 403 | Privacy notice not yet acknowledged | NFR-PRV-01 |
| `NOT_FOUND` | 404 | Record does not exist | – |
| `INVALID_TRANSITION` | 409 | Action not allowed from the current state | FR-WFL-01 |
| `CYCLE_CLOSED` | 409 | Write to a closed cycle | FR-CYC-05 |
| `RATE_LIMITED` | 429 | Too many login or reset requests | NFR-SEC-03 |
| `INVALID_CREDENTIALS` | 401 | Wrong email or password | FR-AUT-03 |
| `ACCOUNT_LOCKED` | 423 | 5 failed logins; includes `locked_until` | NFR-SEC-03 |
| `ACCOUNT_INACTIVE` | 403 | Deactivated account | FR-AUT-06 |
| `ACCOUNT_NOT_ACTIVATED` | 403 | Activation not completed | FR-AUT-02 |
| `TOKEN_INVALID` | 400 | Unknown activation or reset link | FR-AUT-02, FR-AUT-04 |
| `TOKEN_EXPIRED`, `TOKEN_USED` | 410 | Link expired or already used | FR-AUT-02, FR-AUT-04 |
| `WEAK_PASSWORD` | 422 | Fewer than 8 characters, or no letter or digit | NFR-SEC-02 |
| `READ_ONLY_FIELD` | 422 | Student tried to change major or GPA | FR-PRF-02 |
| `WEIGHTS_NOT_100` | 422 | Grade component weights do not total 100 | FR-CYC-02 |
| `GRADES_EXIST` | 409 | Components changed after a grade was submitted | FR-CYC-02 |
| `RUBRIC_LOCKED` | 409 | Rubric changed after the first evaluation | FR-CYC-03 |
| `SCHEDULE_LOCKED` | 409 | Cycle schedule changed after the first placement | FR-CYC-01 |
| `REASON_REQUIRED`, `COMMENT_REQUIRED` | 422 | Mandatory reason or comment missing | FR-VAC-02, FR-VAC-08, FR-REP-05, FR-WFL-04, FR-WFL-05, FR-CER-03 |
| `FILE_TOO_LARGE` | 413 | CV over 5 MB or attachment over 10 MB | FR-PRF-03, FR-REP-02 |
| `UNSUPPORTED_FILE_TYPE` | 415 | Content is not an allowed type (checked by content, not extension) | NFR-SEC-04 |
| `TOO_MANY_ATTACHMENTS` | 409 | More than 3 attachments | FR-REP-02 |
| `MAIN_DOCUMENT_REQUIRED` | 422 | Final report without its main document | FR-REP-02 |
| `SKILLS_NOT_CONFIRMED` | 409 | Matching requested before skills are confirmed | FR-MAT-01 |
| `NOT_ENROLLED` | 403 | Student not enrolled in the vacancy's cycle | FR-VAC-03 |
| `NOT_ELIGIBLE` | 409 | Major not eligible or GPA below minimum; `reason` is `major_not_eligible` or `gpa_below_minimum` | FR-VAC-04, FR-MAT-03 |
| `VACANCY_NOT_OPEN` | 409 | Vacancy not published | FR-VAC-04 |
| `DEADLINE_PASSED` | 409 | Application after the vacancy deadline | FR-VAC-04 |
| `DUPLICATE_APPLICATION` | 409 | Second application to the same vacancy | FR-VAC-04 |
| `APPLICATION_LIMIT_REACHED` | 409 | Already 5 active applications | FR-VAC-04 |
| `ALREADY_PLACED` | 409 | Student already has a placement in the cycle | FR-VAC-07 |
| `NO_SEATS` | 409 | Vacancy has no free seat | FR-VAC-07 |
| `SLOT_CLOSED` | 409 | Submission to a slot closed as missing | FR-REP-07 |
| `NOTHING_TO_SUBMIT` | 409 | Submit without a draft | FR-REP-03 |
| `REQUIRED_FIELDS_MISSING` | 422 | Weekly report fields empty | FR-REP-02 |
| `DEADLINE_NOT_PASSED` | 409 | Close as missing before the deadline | FR-REP-07 |
| `NOT_FLAGGED` | 409 | Decision on a similarity check that is not flagged | FR-SIM-03 |
| `WEEK_NOT_STARTED` | 409 | Attendance for a future week | FR-ATT-01 |
| `WEEK_LOCKED` | 409 | Attendance edit after the edit window without an unlock | FR-ATT-02 |
| `ATTENDED_EXCEEDS_SCHEDULED` | 422 | More attended days than scheduled | FR-ATT-01 |
| `EVALUATION_INCOMPLETE` | 422 | Unrated criterion or empty comment | FR-EVL-01 |
| `ALREADY_REOPENED` | 409 | Second reopen of an evaluation | FR-EVL-04 |
| `PLACEMENT_NOT_ENDED` | 409 | Student evaluation of the company before the placement ended | FR-EVL-05 |
| `PRECONDITIONS_UNMET` | 409 | Grade submit with missing items; includes `missing` | FR-WFL-03 |
| `GRADE_LOCKED` | 409 | Edit of a Final grade | FR-WFL-05 |
| `GRADE_NOT_FINAL` | 409 | Certificate for a grade that is not Final | FR-CER-01 |
| `CERTIFICATE_EXISTS` | 409 | A valid certificate already exists for the placement | FR-CER-01 |

## 6. Verification

- **Permission matrix (FR-AUT-05):** `backend/tests/permissions/matrix.yaml` has one entry per endpoint of Section 3 with the expected status for ST, CS, AS, CO, and Public, plus scope cases (own record and another user's record). A test fails if any route registered in FastAPI is missing from the matrix.
- **State machines (FR-WFL-01):** one test per allowed transition and at least one refused transition from each state, through the endpoints of Sections 3.6, 3.7, 3.9, 3.12, and 3.13.
- **Contract:** CI regenerates the TypeScript client from `/openapi.json` and fails if it differs from the committed client, so frontend and backend stay in step.
- **Changes:** a new or changed endpoint is added to this document and to the permission matrix in the same pull request.
