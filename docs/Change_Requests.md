# InternSync – Change Requests

Change log required by SRS Section 10.6 and SPMP Section 8. Each approved change raises the version of the documents it touches. Requirement IDs are never reused.

| **ID** | **Date** | **Change** | **Status** |
|:--:|:--:|:---|:--:|
| CR-01 | Oct 13, 2026 | Zero-cost reference deployment | Approved |
| CR-02 | Oct 13, 2026 | UC-15 added to SRS Table 3.1 | Approved |
| CR-03 | Oct 13, 2026 | Weekly working days added to FR-CYC-01 | Approved |
| CR-04 | Oct 13, 2026 | Change requests logged in the repository | Approved |

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
