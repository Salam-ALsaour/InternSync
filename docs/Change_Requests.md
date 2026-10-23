# InternSync – Change Requests

Change log required by SRS Section 10.6 and SPMP Section 8. Each approved change raises the version of the documents it touches. Requirement IDs are never reused.

| **ID** | **Date** | **Change** | **Status** |
|:--:|:--:|:---|:--:|
| CR-01 | Oct 13, 2026 | Zero-cost reference deployment | Approved |
| CR-02 | Oct 13, 2026 | UC-15 added to SRS Table 3.1 | Approved |
| CR-03 | Oct 13, 2026 | Weekly working days added to FR-CYC-01 | Approved |
| CR-04 | Oct 13, 2026 | Change requests logged in the repository | Approved |
| CR-05 | Oct 20, 2026 | One platform for many universities and companies: open registration with verification, Platform Admin, direct vacancy publishing, no CSV import | Approved |

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
