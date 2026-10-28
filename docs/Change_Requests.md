# InternSync – Change Requests

Change log required by SRS Section 10.6 and SPMP Section 8. Each approved change raises the version of the documents it touches. Requirement IDs are never reused.

| **ID** | **Date** | **Change** | **Status** |
|:--:|:--:|:---|:--:|
| CR-01 | Oct 13, 2026 | Zero-cost reference deployment | Approved |
| CR-02 | Oct 13, 2026 | UC-15 added to SRS Table 3.1 | Approved |
| CR-03 | Oct 13, 2026 | Weekly working days added to FR-CYC-01 | Approved |
| CR-04 | Oct 13, 2026 | Change requests logged in the repository | Approved |
| CR-05 | Oct 20, 2026 | One platform for many universities and companies: open registration with verification, Platform Admin, direct vacancy publishing, no CSV import | Approved |
| CR-06 | Oct 23, 2026 | Training type part of eligibility | Approved |
| CR-07 | Oct 24, 2026 | Increment 1 implementation adjustments to the design and the API | Approved |
| CR-08 | Oct 26, 2026 | Increment 2 implementation adjustments to the design, the API, and the deployment | Approved |
| CR-09 | Oct 27, 2026 | Increment 3 implementation adjustments: PDF library, similarity passages, API details | Approved |

## CR-01 – Zero-cost reference deployment

- **Requested by:** Salam Alsaour (Team Leader), Oct 13, 2026.
- **Change:** replace the single Linux VM of SRS 3.4 and the Railway recommendation of diagram pack v1.0 with free tiers:
  - Vercel Hobby for the PWA.
  - Hugging Face Spaces CPU Basic (2 vCPU, 16 GB RAM) for the API container with the embedding model and scheduler.
  - Supabase Free for PostgreSQL with pgvector and private file storage.
  - Gmail SMTP for email.
  - Docker Compose stays the local and self-hosted option (NFR-PRT-02).
- **Reason:** the project must cost nothing. Railway's Free plan gives US$1 of credit per month and 0.5 GB RAM per service, which cannot run the API with the model all the time; its Hobby plan costs US$5 per month.
- **Affected:**
  - SRS 3.4, Section 5 introduction, NFR-PER-01 (acceptance criterion), 6.2, Table 6.2, C-04, C-10, and D-05.
  - SPMP 6.2, 6.3, and 7 (new risk).
  - Diagram 9.
  - Design document Section 3.
- **Effect on schedule:** none; less server administration. New risk: free-tier sleep, pause, and size limits, handled by a keep-alive job, nightly backups, and the Docker Compose fallback.
- **Decision:** approved by the Team Leader. SRS 1.1, SPMP 1.1, diagram pack 1.1.

## CR-02 – UC-15 in the use case table

- **Change:** add "UC-15 Send reminders, late flags, and escalations" (actor: scheduler) to SRS Table 3.1. The use case diagram already showed it.
- **Affected:** SRS 3.3.
- **Effect on schedule:** none.
- **Decision:** approved. SRS 1.1.

## CR-03 – Working days in the cycle definition

- **Change:** FR-CYC-01 now includes the weekly working days of the cycle. Its acceptance criterion now also checks each week's scheduled days.
- **Reason:** FR-ATT-01 records attendance "out of the scheduled working days" and assumption A-08 says they are the same for the whole cycle, but no requirement captured them.
- **Affected:** SRS FR-CYC-01; design `training_cycles.working_days` and `cycle_weeks.scheduled_days`.
- **Effect on schedule:** none.
- **Decision:** approved. SRS 1.1.

## CR-04 – Change requests logged in the repository

- **Change:** change requests are recorded in this file; a GitHub issue labelled "change-request" is optional.
- **Reason:** the requirements and design documents are now maintained as Markdown in the repository, so the change log lives next to them.
- **Affected:** SRS 10.6, SPMP 8.
- **Effect on schedule:** none.
- **Decision:** approved. SRS 1.1, SPMP 1.1.

## CR-05 – One platform for many universities and companies

- **Requested by:** Salam Alsaour, Oct 20, 2026.
- **Change:**
  - InternSync becomes one platform, run by its provider, that connects many universities, their colleges, many companies, and students.
  - A fifth role, **Platform Admin** (the provider), maintains universities, colleges, and the skill vocabulary, verifies coordinators and companies, and sets the platform defaults. It sees no academic records.
  - **Open registration with verification** (new SRS Section 4.17, FR-ORG-01 – 09):
    - A student registers for one college with proof of registration in the co-op course; the college's Coordinator verifies the student and enrols them in a cycle.
    - A coordinator registers for one college with an appointment letter; the Platform Admin verifies. Each college has exactly one Coordinator.
    - A company representative registers the company with the commercial registration and a letter of authorization; the Platform Admin verifies, and the representative becomes the **Company Admin**.
    - Academic supervisors are invited by their Coordinator, and further company supervisors by the Company Admin; invitations need no verification.
    - Verification documents are seen only by the uploader and the reviewer and are deleted 30 days after the decision.
  - A company supervisor's trainees may come from any university and any academic supervisor.
  - **Companies publish vacancies directly** (Draft, Published, Closed); the coordinator's review of vacancies is removed. A vacancy may be limited to target universities. The Coordinator still confirms each placement.
  - **CSV import is removed** (FR-PRF-01 deleted, SRS 6.3.1 removed).
  - Similarity checks compare reports of the same university only.
  - F16 – F19 (Could) stay in scope.
- **Reason:** the product is meant to work like an open network (as on LinkedIn) where anyone can join and trust comes from verification, instead of one university importing its users. Direct publishing removes a review step from the coordinators, and self-registration makes the CSV import unnecessary.
- **Affected:**
  - SRS 1 – 4, 4.17 (new), 5, 6.1 – 6.3, 7, 8, 9.1 – 9.3, 10.5, and Appendix A: 125 active requirements (82 Must, 36 Should, 7 Could); use cases UC-16 – UC-20 added; FR-MAT-03 made consistent with FR-VAC-02.
  - Design document 1.2: organizations and verification tables (49 tables), routes, scoping, jobs, Table 8.1.
  - API specification 1.1: registration, invitations, verification requests, organizations, Platform Admin scope; `NOT_ELIGIBLE` no longer covers a vacancy outside the student's university (that is `403`).
  - Diagrams 1, 2, 3a, 4c, 5, 6a – 6d (ERD in four parts), 7b, 8, 11; diagram pack 1.2.
  - Wireframes: `Register`, `Verification_Pending`, `CS_Team`, `CO_Students`, `CO_Supervisors`, and four Platform Admin screens added; `CO_Import` removed; 14 screens edited.
  - SPMP 1.2: T4, M2 status, data plan, and risks.
- **Effect on schedule:** milestones are unchanged. Increment 1 gains the registration and verification work (FR-ORG, 7 Must) and starts 5 days late because the design was redone; part of this is offset by removing the CSV import and the vacancy review. Tracked as a new SPMP risk.
- **Decision:** approved by Salam Alsaour. SRS 1.2, design document 1.2, API specification 1.1, SPMP 1.2, diagram pack 1.2, wireframes 1.1.
- **Follow-up (SRS 1.3, Oct 23, 2026):** NFR-MNT-03 and the glossary now name the Platform Admin for platform defaults and the skill vocabulary. The same version restructures the SRS to the course template; that is an editorial change, not a change request.

## CR-06 – Training type part of eligibility

- **Requested by:** Salam Alsaour, Oct 23, 2026 (found during the Increment 1 requirements analysis, decision RQ-1).
- **Change:** a student may apply only to a vacancy whose training type (Co-op or Summer) equals the type of the cycle the student is enrolled in. Other vacancies stay visible when browsing, with the reason.
- **Reason:** without this rule a student of a Summer cycle could apply to a Co-op vacancy and be placed in training of the wrong kind; nothing in the SRS prevented it.
- **Affected:** SRS FR-VAC-04 and FR-MAT-03 (version 1.4); design document 4.4 and 6.2; API error `NOT_ELIGIBLE` with reason `training_type_mismatch`.
- **Effect on schedule:** none; one more condition in the eligibility check, built in Increment 1.
- **Decision:** approved. SRS 1.4.

## CR-07 – Increment 1 implementation adjustments

- **Requested by:** Salam Alsaour, Oct 24, 2026 (found while building and testing Increment 1).
- **Change:** no requirement changes; the design and the API contract follow what the tests showed was needed:
  - `PATCH /me` answers before the privacy notice is acknowledged, so the notice can be read in the other language.
  - A purged verification document keeps its file reference and gets `purged_at`; the file endpoint answers `410 FILE_PURGED`. Before, the reference was set to null, which lost the record of what was submitted.
  - Scheduled jobs take a transaction-level advisory lock. With a session-level lock, a pooled database connection could keep the lock after a run, and the job would never run again. The Missing flag also runs 30 seconds after the API starts, so a restarted or woken API catches up at once.
  - New endpoints: `GET /admin/universities` (the Platform Admin also sees inactive universities and colleges) and `GET /placements/candidates` (accepted applicants waiting for the coordinator, with the company's supervisors). `GET /placements` gains the `company_id` filter of the specification.
  - Development-only demo clock (`/dev/clock`), mounted only when `ENV` is `development` or `test`, so the M3 demo can show late and missing reports without waiting a week.
  - Error codes added to the specification: `STUDENT_NUMBER_TAKEN`, `DUPLICATE_NAME`, `FILE_PURGED`, `SEATS_BELOW_PLACEMENTS`, `ACADEMIC_SUPERVISOR_INVALID`, `COMPANY_SUPERVISOR_INVALID`, `INTERNAL_ERROR`; `RATE_LIMITED` described as the registration limit; audit filters named `date_from` and `date_to`.
  - Academic and company supervisors see the cycles of their own placements.
  - The permission matrix lists the callers allowed past the role gates; scope cases are tested in the module suites. CI checks that the committed OpenAPI document and TypeScript types match the code.
- **Reason:** each item either closes a defect found by the tests or records behaviour the screens need.
- **Affected:** design document 2.3, 4 (data dictionary), 5.3, and 7.2 (version 1.3); API specification 3.1, 3.2, 3.7, 3.18, 3.20, 5, and 6 (version 1.2); Increment 1 design, Section 12.
- **Effect on schedule:** none.
- **Decision:** approved. Design 1.3, API specification 1.2.

## CR-08 – Increment 2 implementation adjustments

- **Requested by:** Salam Alsaour, Oct 26, 2026 (found while building and testing Increment 2).
- **Change:** no requirement changes. The design, the API contract, and the deployment follow what the build and the tests showed was needed:
  - **Matching settings:** the JSON setting `matching.weights` becomes three numeric settings (`matching.weight_semantic`, `matching.weight_required`, `matching.weight_preferred`), so every setting has the same range check. Settings may be decimals.
  - **Downloads:** `GET /files/{id}` streams the file after the permission check with both storage backends instead of redirecting to a signed link, so no link to the bucket ever leaves the API. The unused setting `files.signed_url_seconds` is removed. NFR-SEC-04 is unchanged; one line of SRS Section 4.3 describes the interface.
  - **Attendance:** an `attendance_weeks` row may hold only an unlock (`attended_days`, `recorded_by`, and `recorded_at` null together), so the coordinator can unlock a week that was never recorded. The week's `locked` flag is reported apart from its state.
  - **Evaluations:** a final evaluation is reopened only while its grade is `draft` (`409 INVALID_TRANSITION` otherwise).
  - **Payloads:**
    - The ranking has `total` and a `mode` per item.
    - The development plan has no `message`; the client shows "No resource available yet".
    - The `missing` items of `PRECONDITIONS_UNMET` carry no text.
    - Attendance and grades carry `can_*` flags for the caller.
    - Placements carry `attendance_percent` and `grade_status`.
    - Dashboard items may carry `status` or `oldest_days`; the grade items link to the grades page.
    - `/version` and the deep health check name the loaded model.
  - **Schema names:** unique names in the OpenAPI document (`AttendanceWeekOut`, `DashboardItem`, `EvaluationItem`, `EvaluationDraftIn`, `EvaluationOverview`, `GradeCommentIn`).
  - **Deployment:**
    - Row level security on every table (migration `0003`); the skill synonyms added in this increment reach older databases once (migration `0004`), since the seed never changes existing skills.
    - The API refuses to start in production without a real `JWT_SECRET`.
    - The model is downloaded into the image and read offline.
    - The backup keeps the database for 30 days and the files for 7 days, because artifact storage of a private repository is limited to 500 MB.
    - The GitHub Actions limits are those of a private repository.
    - The Supabase and Vercel projects are created when the deployment is switched on, after the owner's Hugging Face steps ([Deployment](Deployment.md)).
  - **Schedule:** the development plan (FR-MAT-06), a stretch item planned for Increment 3, was delivered in Increment 2.
- **Reason:** each item either closes a defect found by the tests or the browser check, or records behaviour the screens and the deployment need.
- **Affected:**
  - Design document 3.2, 3.4, 3.5, 4.3.2 (Table 4.1), 4.3.6, 5.1, and 5.5 (version 1.4).
  - API specification 3.7, 3.11, 3.12, 3.19, 3.20, 4.5, 4.6, 4.9, and 4.10 (version 1.3).
  - SRS 4.3 (version 1.5).
  - SPMP Sections 4 and 5 (version 1.4).
  - Increment 2 design, Sections 2, 4, 8, 10, 11, and 12.
- **Effect on schedule:** none; FR-MAT-06 is delivered earlier than planned.
- **Decision:** approved. Design 1.4, API specification 1.3, SRS 1.5, SPMP 1.4.

## CR-09 – Increment 3 implementation adjustments

- **Requested by:** Salam Alsaour, Oct 27, 2026 (found while building and testing Increment 3).
- **Change:** no requirement changes. The design and the API contract follow what the build and the tests showed was needed:
  - **PDF library:** fpdf2 with HarfBuzz text shaping (`uharfbuzz`) instead of WeasyPrint. WeasyPrint needs Pango and GTK system libraries that do not install with pip, notably on Windows. fpdf2 installs with pip everywhere and, with the bundled Noto fonts, joins Arabic letters and orders right-to-left text (NFR-L10N-03, D-07).
  - **Similarity passages:** about one sentence (8 to 25 words) instead of 40 to 80 words. A passage counts for a source report when the source report's passages near it, taken together, contain at least half of its word 5-grams.
    - On the evaluation set, reports that copied about half of their text were found 4 times out of 10 with the old passages, and 10 times out of 10 with the new ones; no original report was flagged in either case.
    - Copied sentences shared a long passage with the student's own words, and the passages of two reports seldom line up.
    - The setting was chosen on the same set that measures it; a held-out set is planned for M6.
  - **Data:** `report_passages` gains `slot_id`, so every version of the same report is left out without a join; `similarity_checks` gains `attempts` and `created_at` for the retry job.
  - **API details:**
    - The transfer rules: an active member who has set a password; a coordinator without active students. New error codes `TRANSFER_TARGET_INVALID` and `SUPERVISOR_HAS_STUDENTS`.
    - The similarity result as built (`status` `none`; `sources` with `author` and `can_decide`).
    - Notification items carry their text in the caller's language; the push endpoints answer `204`.
    - The history entry fields; exports in the caller's language and audited.
  - **Demo data:** a former student of an earlier, closed cycle with an accepted week 1 report, so the M5 demo can show a similarity flag.
- **Reason:** the PDF library would not install on the development machines; the evaluation showed the original passage size missed half-copied reports; the rest records behaviour the screens need.
- **Affected:**
  - Design document 1.3, 4.3.5, 5.6, and 6.3 (version 1.5).
  - API specification 3.2, 3.10, 3.15, 3.17, 3.18, 4.8, and 5 (version 1.4).
  - Increment 3 design, Section 12.
- **Effect on schedule:** none.
- **Decision:** approved. Design 1.5, API specification 1.4.
