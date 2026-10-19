# InternSync – API Specification

CSC 305 – Software Engineering · Semester 1 – 2026/2027 · Section 5MA1 · Group 3  
Task T2 (System design) · Milestone M2 · Version 1.1 · October 20, 2026

| **Version** | **Date** | **Description** | **Author** |
|:--:|:--:|:---|:--:|
| 1.0 | Oct 13, 2026 | First version for Milestone M2. | Salam Alsaour |
| 1.1 | Oct 20, 2026 | CR-05: registration, email confirmation, invitations, verification requests, universities and colleges, company team, Platform Admin endpoints and scope; vacancy review endpoints and CSV import removed. | Salam Alsaour |

This document is the API contract agreed before implementation (SPMP risk "integration problems"). During development, FastAPI generates the OpenAPI 3.1 document from the code at `/api/v1/openapi.json` (NFR-MNT-02), and the frontend client is generated from it. The generated document must match this specification; any difference is either a bug or a change that is recorded here first.

Related: [System Design Document](InternSync_Design.md) (data model, state machines, security) and [SRS v1.2](../RSR/InternSync_SRS.md).

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
| Enumerations | Lowercase values, the same as the database (for example `revision_requested`, `platform_admin`). |
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
| ST, CS, AS, CO, PA | Student, Company Supervisor, Academic Supervisor, Coordinator, Platform Admin |
| CA | Company Admin: the Company Supervisor who holds the admin right of the company |
| Public | No login needed |
| Any | Any logged-in, verified user |
| (unverified) | Also allowed while the account's verification is pending or rejected |
| (own) | Only the caller's own records |
| (own vacancy) | Vacancies whose `company_supervisor_id` is the caller, and their applications |
| (assigned) | Placements where the caller is the company or academic supervisor, and the records under them |
| (college) | Records of students of the Coordinator's college, and the college's cycles and users. A plain "CO" below always means this scope |
| (company) | Records of the Company Admin's company. A plain "CA" below always means this scope |
| (all) | Every record of its kind on the platform (Platform Admin; never academic records) |

A request for a record outside the caller's scope returns `403 FORBIDDEN`. An account that is not yet verified gets `403 VERIFICATION_REQUIRED` from every endpoint not marked (unverified). Each endpoint below is in the permission matrix test (Section 6).

## 3. Endpoints

### 3.1 Authentication and Session

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| POST | `/auth/register` | Public | Multipart: `kind` (`student`, `coordinator`, `company`), account fields, the fields of that kind, and the documents (Section 4.3). Creates the account and its verification request and emails a confirmation link | FR-ORG-02 – 05 |
| POST | `/auth/email/confirm` | Public | `{token}`: confirm the email address | FR-AUT-02 |
| POST | `/auth/email/resend` | Public | `{email}`: always `202`; sends a new confirmation link if the account exists and is unconfirmed | FR-AUT-02 |
| POST | `/auth/login` | Public | Log in with email and password; returns the access token and the user. Refused before the email is confirmed (`403 EMAIL_NOT_CONFIRMED`) | FR-AUT-03, NFR-SEC-03 |
| POST | `/auth/logout` | Any (unverified) | End the current session; the token stops working | FR-AUT-03 |
| GET | `/auth/tokens/{token}` | Public | Check a confirmation, invitation, or reset link before showing its form: `{purpose, valid, reason}` | FR-AUT-02, FR-AUT-04 |
| POST | `/auth/invitations/accept` | Public | `{token, password}`: set the password of an invited account | FR-ORG-06 |
| POST | `/auth/password/forgot` | Public | `{email}`: always `202`; sends a reset link if the account exists | FR-AUT-04 |
| POST | `/auth/password/reset` | Public | `{token, password}`: set a new password and end all sessions | FR-AUT-04 |
| GET | `/me` | Any (unverified) | The current user, role, organization, language, `verification_status`, `is_company_admin`, and `consent_required` | FR-AUT-01, FR-ORG-02 |
| PATCH | `/me` | Any (unverified) | `{language}` | FR-LOC-01 |
| POST | `/me/consent` | Any (unverified) | Acknowledge the privacy notice | NFR-PRV-01 |
| GET | `/me/verification` | Any (unverified) | The caller's verification requests with status, reason, and documents | FR-ORG-02, FR-ORG-09 |
| POST | `/me/verification` | Any (unverified) | Multipart: corrected data and documents; a new request after a rejection | FR-ORG-09 |

### 3.2 Organizations, Verification, and Accounts

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/universities` | Public | Active universities with their active colleges (registration form) | FR-ORG-01 |
| POST | `/universities` | PA | Add a university: names, email domains, GPA scale | FR-ORG-01 |
| PATCH | `/universities/{id}` | PA | Edit or deactivate | FR-ORG-01 |
| POST | `/universities/{id}/colleges` | PA | Add a college | FR-ORG-01 |
| GET | `/colleges/{id}` | PA, CO | College with its Coordinator and counts | FR-ORG-01 |
| PATCH | `/colleges/{id}` | PA | Edit or deactivate | FR-ORG-01 |
| POST | `/colleges/{id}/coordinator/transfer` | PA | `{user_id, reason}` | FR-ORG-07 |
| GET | `/colleges/{id}/academic-supervisors` | CO, PA | The college's academic supervisors with student counts | FR-ORG-06 |
| POST | `/colleges/{id}/invitations` | CO | `{email, name_en, name_ar}`: invite an academic supervisor | FR-ORG-06 |
| GET | `/companies` | PA (all), CS (own) | List companies: `?status&q` | FR-ORG-04 |
| GET | `/companies/{id}` | PA, CS (own) | Company profile with status | FR-ORG-04 |
| PATCH | `/companies/{id}` | CA | City and website | FR-ORG-04 |
| POST | `/companies/{id}/suspend` | PA | `{reason}`: closes its published vacancies | FR-AUT-06 |
| POST | `/companies/{id}/reactivate` | PA | Reactivate | FR-AUT-06 |
| POST | `/companies/{id}/admin/transfer` | PA | `{user_id, reason}` | FR-ORG-07 |
| GET | `/companies/{id}/supervisors` | CA, PA | The company's supervisors with trainee counts | FR-ORG-06 |
| POST | `/companies/{id}/invitations` | CA | `{email, name_en, name_ar}`: invite a company supervisor | FR-ORG-06 |
| GET | `/verification-requests` | PA (coordinator and company requests), CO (student requests of the college) | `?status&kind` | FR-ORG-03 – 05, FR-DSH-01 |
| GET | `/verification-requests/{id}` | The reviewer; the applicant | Submitted data, earlier decisions of the same account, document links | FR-ORG-09 |
| POST | `/verification-requests/{id}/approve` | PA (coordinator, company), CO (student) | Student requests: `{cycle_id}` of an open cycle of the college | FR-ORG-03 – 05 |
| POST | `/verification-requests/{id}/reject` | PA (coordinator, company), CO (student) | `{reason}` | FR-ORG-03 – 05 |
| GET | `/users` | PA (account fields), CO, CA | Search accounts: `?role&q&is_active&verification_status` | FR-AUT-06 |
| GET | `/users/{id}` | PA, CO, CA | Account details | FR-AUT-06 |
| POST | `/users/{id}/deactivate` | PA (any), CO (the college's academic supervisors and students), CA (the company's supervisors) | Deactivate and end all sessions | FR-AUT-06 |
| POST | `/users/{id}/reactivate` | Same | Reactivate | FR-AUT-06 |
| POST | `/users/{id}/invitation/resend` | CO, CA | New invitation link for an account that has not accepted it; the old one is revoked | FR-ORG-06 |

### 3.3 Training Cycles

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/cycles` | Any (ST: own enrolment; CS, AS: cycles of their records; CO: the college's) | List cycles | FR-CYC-01 |
| POST | `/cycles` | CO | Create a cycle for the college; generates its weeks and deadlines | FR-CYC-01 |
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
| GET | `/cycles/{id}/enrollments` | CO | Enrolled students (created by approving their verification) | FR-ORG-05 |

### 3.4 Skill Vocabulary, Majors, and Settings

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/skills` | Any (unverified) | Search skills: `?q` matches both names and synonyms | FR-CYC-04 |
| POST | `/skills` | PA | `{name_en, name_ar, synonyms}` | FR-CYC-04 |
| PATCH | `/skills/{id}` | PA | Edit names, synonyms, `is_active` | FR-CYC-04 |
| GET | `/skills/{id}/resources` | Any (unverified) | Learning resources | FR-CYC-04 |
| PUT | `/skills/{id}/resources` | PA | Replace the resources (title, URL, effort, language) | FR-CYC-04 |
| GET | `/majors` | Public | List majors (registration form) | FR-PRF-02, FR-VAC-01 |
| POST | `/majors` | PA | Add a major | FR-VAC-01 |
| PATCH | `/majors/{id}` | PA | Edit names | FR-VAC-01 |
| GET | `/settings` | PA | All configurable defaults with their values | NFR-MNT-03 |
| PATCH | `/settings` | PA | `{ "<key>": <value>, … }`; each value is validated; takes effect at once | NFR-MNT-03 |

### 3.5 Student Profile and CV

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/students/me/profile` | ST (unverified) | Profile: student number, major, GPA, and level (read-only after verification), languages, interests, confirmed skills, current CV | FR-PRF-02 |
| PATCH | `/students/me/profile` | ST (unverified) | `{languages, interests}`; student number, major, and GPA are refused after verification (`422 READ_ONLY_FIELD`) | FR-PRF-02 |
| GET | `/students/me/cvs` | ST (unverified) | CV history | FR-PRF-03 |
| POST | `/students/me/cvs` | ST (unverified) | Multipart `file` (PDF or DOCX, ≤ 5 MB): stores the CV, extracts text and skills | FR-PRF-03 – 05, NFR-PER-03 |
| GET | `/students/me/skills` | ST (unverified) | Confirmed skills | FR-PRF-04 |
| PUT | `/students/me/skills` | ST (unverified) | `{skills: [{skill_id, source}]}`: confirm the list; recomputes the profile embedding | FR-PRF-04 |
| GET | `/students/{id}/profile` | CS (applicant to own vacancy, or assigned), CA, AS (assigned), CO | Profile, confirmed skills, current CV file | FR-VAC-06 |

### 3.6 Vacancies

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/vacancies` | ST (unverified; published and open to the student's university), CS (own company), CO (published, read-only), PA (all, read-only) | Browse: `?q&city&company_id&major_id&skill_id&training_type&status`. For ST each item carries `eligible` and `ineligible_reason` | FR-VAC-03, FR-MAT-03 |
| POST | `/vacancies` | CS of a verified company | Create a vacancy as `draft`, or published at once with `publish: true`; `target_university_ids` optional | FR-VAC-01, FR-VAC-02 |
| GET | `/vacancies/{id}` | Same as list | Details with required and preferred skills, eligible majors, and target universities | FR-VAC-01 |
| PATCH | `/vacancies/{id}` | CS (own vacancy), CA | Edit; a published vacancy is embedded again; seats cannot drop below the confirmed placements | FR-VAC-01 |
| POST | `/vacancies/{id}/publish` | CS (own vacancy), CA | `draft` → `published` | FR-VAC-02 |
| POST | `/vacancies/{id}/close` | CS (own vacancy), CA | `published` → `closed` | FR-VAC-02 |

### 3.7 Applications and Placements

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| POST | `/vacancies/{id}/applications` | ST | Apply; stores the fit-score snapshot | FR-VAC-04 |
| GET | `/vacancies/{id}/applications` | CS (own vacancy), CA | Applicants with university, college, profile summary, confirmed skills, fit snapshot | FR-VAC-06 |
| GET | `/applications` | ST (own), CO (students of the college) | `?status&cycle_id&placed=false` (CO: accepted applicants waiting for a placement) | FR-VAC-04, FR-VAC-07 |
| GET | `/applications/{id}` | ST (own), CS (own vacancy), CA, CO | One application | FR-VAC-06 |
| POST | `/applications/{id}/withdraw` | ST (own) | `submitted` → `withdrawn` | FR-VAC-05 |
| POST | `/applications/{id}/accept` | CS (own vacancy), CA | `submitted` → `accepted`; notifies the student's Coordinator | FR-VAC-06 |
| POST | `/applications/{id}/decline` | CS (own vacancy), CA | `submitted` → `declined` | FR-VAC-06 |
| POST | `/placements` | CO (the student's college) | `{application_id, academic_supervisor_id, company_supervisor_id?}`: confirm in the student's cycle; creates report slots and the draft grade | FR-VAC-07, FR-REP-01 |
| GET | `/placements` | ST (own), CS (assigned), CA, AS (assigned), CO | `?cycle_id&company_id&academic_supervisor_id&status` | FR-VAC-07 |
| GET | `/placements/{id}` | Same as list | Overview: student, vacancy, supervisors, status, attendance %, report summary, grade status | FR-VAC-07, FR-ATT-03 |
| PATCH | `/placements/{id}/academic-supervisor` | CO | `{academic_supervisor_id, reason}` | FR-VAC-08 |
| POST | `/placements/{id}/cancel` | CO | `{reason}` | FR-VAC-08 |

### 3.8 Matching

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/students/me/matches` | ST | Ranked eligible vacancies: `?limit`. Needs a verified, enrolled student (`403 VERIFICATION_REQUIRED`) and confirmed skills (`409 SKILLS_NOT_CONFIRMED`) | FR-MAT-01 – 05, FR-MAT-07, NFR-PER-02 |
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
| GET | `/platform/stats` | PA | Universities, colleges with and without a coordinator, verified companies, users by role, pending verification requests and their age, published vacancies; no academic records | FR-DSH-05 |

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
| GET | `/public/certificates/{code}` | Public | Status (`valid`, `revoked`, `not_found`), student name, university and college, cycle, company, training dates; never the grade | FR-CER-02 |

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
| GET | `/audit-log` | CO (the college's entries), PA (entries about accounts, organizations, and verification) | `?student_id&user_id&entity_type&entity_id&from&to`; read-only, no update or delete endpoint exists | FR-AUD-02 |
| GET | `/history/{entity_type}/{entity_id}` | Anyone allowed to view the record; `entity_type` is `report_slot`, `evaluation`, or `grade` | State changes with user and time | FR-AUD-03 |

### 3.19 Files

| **Method** | **Path** | **Roles** | **Purpose** | **SRS** |
|:--|:---|:---|:---|:---|
| GET | `/files/{id}` | Anyone allowed to view the record that owns the file; for verification documents only the uploader and the reviewer | `302` to a signed link valid for 60 s (or the file itself with local storage); `403` otherwise; `410` for a purged verification document | NFR-SEC-04, FR-ORG-08 |

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
    "language": "ar", "consent_required": true,
    "verification_status": "verified", "is_company_admin": false,
    "organization": { "university": "Example University", "college": "College of Computer Science", "college_id": "3c1d…" }
  }
}
```

Errors: `401 INVALID_CREDENTIALS`, `423 ACCOUNT_LOCKED` (with `locked_until`), `403 ACCOUNT_INACTIVE`, `403 EMAIL_NOT_CONFIRMED`.

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

### 4.3 Registration and Verification

`POST /auth/register` (multipart) for each kind:

| **Kind** | **Fields** | **Documents** |
|:---|:---|:---|
| `student` | `email`, `password`, `name_en`, `name_ar`, `college_id`, `student_number`, `major_id`, `gpa`, `level` | `course_registration` (required) |
| `coordinator` | `email`, `password`, `name_en`, `name_ar`, `college_id` | `appointment_letter` (required) |
| `company` | `email`, `password`, `name_en`, `name_ar`, `company_name`, `commercial_reg_no`, `city`, `website` | `commercial_registration` and `authorization_letter` (both required) |

`201 Created`

```json
{
  "user_id": "a41e…", "kind": "student", "email_confirmation_sent": true,
  "verification": { "request_id": "77c0…", "status": "pending",
                    "reviewer": "coordinator", "college": "College of Computer Science" }
}
```

Errors: `409 EMAIL_TAKEN`, `409 COLLEGE_HAS_COORDINATOR`, `409 DUPLICATE_COMMERCIAL_REG`, `422 DOCUMENT_REQUIRED`, `422 GPA_ABOVE_SCALE`, `429 RATE_LIMITED`.

`GET /verification-requests?status=pending` (as a Coordinator) → items such as:

```json
{
  "id": "77c0…", "kind": "student", "status": "pending", "submitted_at": "2026-10-19T08:40:00Z",
  "applicant": { "name_en": "Sara Ahmed", "name_ar": "سارة أحمد", "email": "sara.ahmed@example.edu",
                 "email_matches_university_domain": true },
  "submitted_data": { "student_number": "4400012345", "major": "Computer Science", "gpa": 4.21, "level": 8 },
  "documents": [ { "kind": "course_registration", "file_id": "f9…", "original_name": "schedule.pdf" } ],
  "earlier_decisions": []
}
```

`POST /verification-requests/{id}/approve` with `{"cycle_id": "0a9d…"}` → `200 OK` with the request `approved` and the new enrolment; `409 CYCLE_NOT_OPEN` if the cycle is closed. `POST /verification-requests/{id}/reject` with `{"reason": "…"}` → `200 OK`; `422 REASON_REQUIRED` without a reason.

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

`GET /students/me/matches?limit=20`

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
| `EMAIL_NOT_CONFIRMED` | 403 | Login before the email address is confirmed | FR-AUT-02 |
| `VERIFICATION_REQUIRED` | 403 | The account's verification is pending or rejected, or the student is not enrolled | FR-ORG-02 |
| `EMAIL_TAKEN` | 409 | Registration or invitation with an email already in use | FR-ORG-02 |
| `COLLEGE_HAS_COORDINATOR` | 409 | Coordinator registration for a college that already has one | FR-ORG-03 |
| `DUPLICATE_COMMERCIAL_REG` | 409 | Company registration with a registration number already on the platform | FR-ORG-04 |
| `DOCUMENT_REQUIRED` | 422 | A required verification document is missing | FR-ORG-03 – 05 |
| `GPA_ABOVE_SCALE` | 422 | GPA above the university's scale | FR-ORG-05 |
| `CYCLE_NOT_OPEN` | 409 | Student approval with a closed cycle | FR-ORG-05 |
| `COMPANY_NOT_VERIFIED` | 409 | Vacancy or invitation by a company that is not verified, or is suspended | FR-ORG-04, FR-VAC-01 |
| `TOKEN_INVALID` | 400 | Unknown confirmation, invitation, or reset link | FR-AUT-02, FR-AUT-04 |
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
| `NOT_ELIGIBLE` | 409 | Major not eligible or GPA below minimum; `reason` is `major_not_eligible` or `gpa_below_minimum`. A vacancy not open to the student's university is out of scope (`403 FORBIDDEN`) | FR-VAC-04, FR-MAT-03 |
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

- **Permission matrix (FR-AUT-05):** `backend/tests/permissions/matrix.yaml` has one entry per endpoint of Section 3 with the expected status for ST, CS, CA, AS, CO, PA, an unverified account, and Public, plus scope cases: own record, another user's record, and a record of another college or company (the test data hold two universities, three colleges, and two companies). A test fails if any route registered in FastAPI is missing from the matrix.
- **State machines (FR-WFL-01):** one test per allowed transition and at least one refused transition from each state, through the endpoints of Sections 3.6, 3.7, 3.9, 3.12, and 3.13.
- **Contract:** CI regenerates the TypeScript client from `/openapi.json` and fails if it differs from the committed client, so frontend and backend stay in step.
- **Changes:** a new or changed endpoint is added to this document and to the permission matrix in the same pull request.
