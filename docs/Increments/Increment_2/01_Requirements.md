# Increment 2 – Requirements (Scope and Acceptance)

**Status:** Approved Oct 25, 2026 – the project owner delegated the decisions of Section 5, and the recommendations were adopted · Author: Salam Alsaour  
**Baseline:** [SRS 1.4](../../Project_4_SRS/InternSync_SRS.md), [Design 1.3](../../Design/InternSync_Design.md), [API 1.2](../../Design/InternSync_API_Spec.md), [SPMP 1.3](../../Project_3_SPMP/InternSync_SPMP.md), [Increment 1](../Increment_1/04_Test_Report.md)  
**Milestone:** M4 – Increment 2 delivered, **Nov 15, 2026**: demo of F4, F6, F7, F8, F9; every Must function passes its tests.

## 1. Purpose

This document fixes what Increment 2 delivers before its design starts: the requirements in scope and how far each is committed, the open points, the acceptance tests, the demo scenario for M4, and the Definition of Done. It adds no requirement; every item traces to SRS 1.4 (Table 6.4) or to a follow-up recorded in the Increment 1 test report.

## 2. Process for this Increment

The same four phases as Increment 1. The project owner asked for the increment to run end to end, with one review at the pull request.

| **Phase** | **Artefact** | **Planned dates** |
|:---|:---|:---|
| 1. Requirements | `01_Requirements.md` (this document) | Oct 25 |
| 2. Design | `02_Design.md`: tables, endpoints, matching service, screens, test design | Oct 25 – Oct 26 |
| 3. Implementation | Code on branch `increment-2`, CI green | Oct 26 – Nov 8 |
| 4. Testing | `04_Test_Report.md`, the AI evaluation script results, and the M4 dry run | Nov 9 – Nov 14 |

The increment starts 8 days ahead of the SPMP plan (Nov 2), because Increment 1 finished early.

## 3. Use Cases Covered

| **Use case** | **Increment 2 coverage** |
|:---|:---|
| UC-05 View ranked vacancies and apply | Ranking, fit score, matched and missing skills, basic-matching fallback. The development plan (FR-MAT-06) is stretch |
| UC-09 Record weekly attendance | Full |
| UC-10 Submit a periodic or final evaluation | Full |
| UC-11 Enter, submit, and approve a grade | Full |
| Role home pages (FR-DSH-01, 02, 05) | Dashboards with live counts for every role; coordinator cycle statistics; platform figures |

## 4. Requirements in Scope

### 4.1 Functional Requirements

| **ID** | **Requirement (short)** | **Priority** | **Commitment** |
|:---|:---|:--:|:--:|
| FR-MAT-01 | Rank the eligible vacancies of a student with confirmed skills by a fit score 0–100 | Must | Committed |
| FR-MAT-02 | Fit score = semantic similarity (multilingual embeddings) + required skills + major + GPA | Must | Committed |
| FR-MAT-03 | Ineligible vacancies left out of the ranking, shown with the reason when browsing | Must | Committed (the browsing part was built in Increment 1) |
| FR-MAT-04 | Rule-based "Basic matching" when the model or an embedding is missing | Must | Committed |
| FR-MAT-05 | Matched and missing required skills per ranked vacancy | Should | **Pulled forward** from Increment 3: the ranking computes them anyway (decision RQ-5) |
| FR-MAT-06 | Development plan with learning resources for missing skills | Should | Stretch (planned for Increment 3) |
| FR-MAT-07 | Results advisory; never block applying or decide on applicants | Must | Committed |
| FR-ATT-01 | Weekly attendance by the company supervisor; one-action full attendance | Must | Committed |
| FR-ATT-02 | Attendance editable for 7 days after the week; then unlocked by the coordinator | Should | Committed (small, and FR-ATT-04 needs the same week dates) |
| FR-ATT-03 | Attendance record and percentage for the student, both supervisors, the coordinator | Must | Committed |
| FR-ATT-04 | Week unrecorded 3 days after it ends is a pending action on the company dashboard | Must | Committed |
| FR-EVL-01 | Periodic and final evaluation on the cycle rubric, all criteria rated, comment required | Must | Committed |
| FR-EVL-02 | One rubric version per cycle; no company-specific criteria | Must | Committed |
| FR-EVL-03 | Periodic evaluation visible at once; final evaluation visible to the student when the grade is Final | Must | Committed |
| FR-EVL-04 | Submitted evaluation read-only; reopened once by the coordinator with a reason | Should | Committed (the grade flow needs a way to correct a final evaluation) |
| FR-WFL-02 | Grade = weighted sum of components; company component from the final evaluation | Must | Committed |
| FR-WFL-03 | Grade state machine; submit only when the preconditions are met | Must | Committed |
| FR-WFL-04 | Coordinator approves (Final) or returns with a comment | Must | Committed |
| FR-WFL-05 | Final grade locked; reopened by the coordinator with a reason | Must | Committed |
| FR-WFL-06 | Student sees the grade only when Final | Must | Committed |
| FR-WFL-07 | Bulk approval with one audit entry per grade | Should | Committed (one loop over the single approval) |
| FR-DSH-01 | Home dashboard with pending actions, counts, and links for every role | Must | Committed (similarity flags and escalations join in Increment 3 with FR-SIM and FR-NOT) |
| FR-DSH-02 | Coordinator cycle status overall and per company | Must | Committed |
| FR-DSH-05 | Platform Admin figures without academic records | Should | Committed (the counts already exist for the verification pages) |

**Totals:** 24 requirements – 18 Must (all committed), 6 Should (4 committed, 1 pulled forward, 1 stretch).

**Supporting work:**

- **Matching data:** profile and vacancy embeddings, the `match_scores` cache, and the fit-score snapshot on each application (columns that already exist).
- **Grades for existing placements:** placements confirmed in Increment 1 get their `draft` grade in the migration (decision RQ-6).
- **AI evaluation set and script (NFR-AI-03):** 20 synthetic CVs with labelled skills (10 Arabic, 10 English), the student profiles with their relevant vacancies, and `ai-eval/evaluate.py`. It also measures the skill-extraction recall deferred from Increment 1 (FR-PRF-04, its RQ-4).
- **Reference deployment (decision RQ-8):** the zero-cost deployment of Design Section 3, prepared in this increment.
- **Follow-ups from the Increment 1 test report:**
  - Tailwind CSS 4: stretch.
  - A backend type checker: stretch.
  - Automated browser tests for the main flows: stretch.

### 4.2 Non-Functional Requirements Checked at M4

The Must checks of Increment 1 are repeated by CI. Added for Increment 2:

| **ID** | **What is checked at M4** |
|:---|:---|
| NFR-PER-02 | Ranked list for one student with 1,000 open vacancies within 5 s (95th percentile of 20 runs), also in basic mode |
| NFR-PER-03 | Extracted skills shown within 30 s after uploading a 5 MB CV |
| NFR-PRV-02 | The embedding model runs inside the API container; no text leaves it |
| NFR-AI-01 | Every fit score labelled advisory with its reason (parts, matched and missing skills); no AI output changes an application |
| NFR-AI-02 | Model name and version stored with each fit score and each application snapshot |
| NFR-AI-03 | Labelled sets and evaluation script in the repository; running it reproduces the reported numbers |
| NFR-L10N-01 | Every Increment 2 screen in Arabic and English with the right direction |
| NFR-USA-02 | Attendance and evaluation each fit in at most 3 screens; full attendance is one button |

NFR-PER-01 (50 concurrent users) and NFR-REL-01 (uptime) are measured on the reference deployment in the testing phase (M6), as the SPMP plans.

## 5. Decisions

| **ID** | **Open point** | **Decision (recommended and adopted)** |
|:---|:---|:---|
| RQ-1 | How to run the embedding model | `sentence-transformers` with the CPU build of PyTorch inside the API image; the model `intfloat/multilingual-e5-small` is downloaded at image build time. Tests use a small deterministic stand-in embedder, so CI downloads no model |
| RQ-2 | Where vectors live | PostgreSQL with pgvector, `halfvec(384)` as in the design. The local and CI database image becomes `pgvector/pgvector:pg16`; Supabase has the extension |
| RQ-3 | When embeddings are computed | When a profile's confirmed skills, interests, or CV change, and when a vacancy is created or edited. A job embeds whatever is missing (for example after the model was unavailable), so ranking never waits for the model |
| RQ-4 | Who labels the evaluation set | The SRS asks for two members labelling independently; the project is built by one person, so the author labels the synthetic set alone and the test report says so. The data is synthetic (C-09) |
| RQ-5 | FR-MAT-05 (Should, Increment 3) | Pulled forward: the matched and missing skills are by-products of the score and are in the API response of Section 4.5 |
| RQ-6 | Grades of placements confirmed in Increment 1 | The migration creates their `draft` grades; new placements create them on confirmation |
| RQ-7 | Dashboard items that belong to Increment 3 | Similarity flags (AS) and escalations (CO) are added with FR-SIM and FR-NOT in Increment 3; the dashboard is built so that new item types plug in |
| RQ-8 | Reference deployment | Database and file storage on Supabase and the web app on Vercel, through the owner's connected accounts. The API runs on a Hugging Face Space, which needs an account that only the owner can create. Everything is prepared in this increment (container, workflows, storage adapter, settings); the owner then creates the Space and the email app password, and the deployment is switched on from a short checklist |
| RQ-9 | Settings with decimal and JSON values | `system_settings` already stores JSON; the settings service is extended to decimals and the matching weights, with the same range checks |

## 6. Acceptance Tests

Each test comes from the SRS acceptance criterion of its requirement. *API* tests run against a test database; *Unit* tests check one function; *Eval* runs the AI evaluation script; *Demo* items are checked by hand in the M4 dry run.

| **Test** | **Requirement** | **Scenario and expected result** | **Level** |
|:---|:---|:---|:--:|
| AT-MAT-01 | FR-MAT-01 | Ranking holds only eligible vacancies in descending fit; on the labelled set a relevant vacancy is in the top 5 for at least 80% of the profiles | API, Eval |
| AT-MAT-02 | FR-MAT-02 | Of two otherwise identical vacancies, the one whose required skills the student has scores higher | Unit |
| AT-MAT-03 | FR-MAT-03 | A vacancy whose minimum GPA is above the student's GPA is absent from the ranking and shows "GPA below minimum" when browsing | API |
| AT-MAT-04 | FR-MAT-04 | With the model off, the ranking is returned within 5 s and labelled basic | API, Unit |
| AT-MAT-05 | FR-MAT-05 | Matched and missing skills equal the set comparison of confirmed and required skills | Unit, API |
| AT-MAT-07 | FR-MAT-07 | The student can apply to the lowest-ranked eligible vacancy; ranking changes no application | API |
| AT-ATT-01 | FR-ATT-01 | "Full attendance" records attended days equal to scheduled days in one action; more days than scheduled is refused | API |
| AT-ATT-02 | FR-ATT-02 | An edit on day 8 after the week is refused until the coordinator unlocks the week; the unlock is in the audit log | API |
| AT-ATT-03 | FR-ATT-03 | The percentage equals attended ÷ scheduled days for seeded data; each role sees only its placements | API |
| AT-ATT-04 | FR-ATT-04 | A seeded unrecorded week appears on the company supervisor's dashboard on day 4, not on day 3 | API |
| AT-EVL-01 | FR-EVL-01 | Submitting with an unrated criterion or an empty comment is refused | API |
| AT-EVL-02 | FR-EVL-02 | A score for a criterion of another cycle is refused; every evaluation of a test cycle uses that cycle's criteria | API |
| AT-EVL-03 | FR-EVL-03 | The student sees the periodic evaluation at once and the final evaluation only when the grade is Final | API |
| AT-EVL-04 | FR-EVL-04 | Editing a submitted evaluation is refused; the coordinator reopens it once with a reason, which is audited; a second reopening is refused | API |
| AT-WFL-02 | FR-WFL-02 | For seeded inputs the computed grade equals a hand calculation to two decimals | Unit, API |
| AT-WFL-03 | FR-WFL-03 | Submitting with any precondition unmet is refused with the list of missing items | API |
| AT-WFL-04 | FR-WFL-04 | Returning without a comment is refused; approval sets Final with a timestamp and completes the placement | API |
| AT-WFL-05 | FR-WFL-05 | Editing a Final grade is refused; reopening without a reason is refused; reopening is audited | API |
| AT-WFL-06 | FR-WFL-06 | The student's grade view is hidden in Draft and Submitted and shown when Final | API |
| AT-WFL-07 | FR-WFL-07 | A bulk approval of 10 grades creates 10 audit entries | API |
| AT-DSH-01 | FR-DSH-01 | For a seeded scenario, every dashboard count of every role equals the pending items in the database | API |
| AT-DSH-02 | FR-DSH-02 | Every cycle figure, overall and per company, equals the value computed from seeded data | API |
| AT-DSH-05 | FR-DSH-05 | Every platform figure equals the seeded value; no report, evaluation, or grade is reachable by the Platform Admin | API |
| AT-PER-02 | NFR-PER-02 | 1,000 open vacancies: 95th percentile of 20 ranking requests ≤ 5 s, semantic and basic | API (timed) |
| AT-AI-02 | NFR-AI-02 | Each stored fit score and each application snapshot has the model version | API |
| AT-AI-03 | NFR-AI-03, FR-PRF-04 | The evaluation script prints skill-extraction recall (target ≥ 70%) and the top-5 hit rate (target ≥ 80%) | Eval |
| AT-LOC-03 | NFR-L10N-01, FR-LOC-02 | The translation-key check passes with the new screens; each new screen checked in both languages | Unit, Demo |

## 7. M4 Demo Scenario

The demo runs on seeded data, on the reference deployment when it is switched on, otherwise on `docker compose up`:

1. The student opens the dashboard (reports due, application status), then the recommended vacancies: fit scores, matched and missing skills, the Advisory label; applies to one.
2. With the model switched off, the same list shows "Basic matching".
3. The company supervisor's dashboard shows applicants to review and attendance to record; records full attendance for a week and a partial week with a note.
4. A week older than 7 days is refused; the coordinator unlocks it and the supervisor corrects it.
5. The company supervisor submits the periodic evaluation (the student sees it at once) and the final evaluation.
6. The academic supervisor accepts the remaining reports, enters the grade components, sees the computed company component, and submits; a submission with a missing item is refused with the list first.
7. The coordinator returns one grade with a comment, then approves grades in bulk; the student sees the Final grade and the final evaluation.
8. The coordinator reopens a Final grade with a reason; the audit log shows it.
9. The coordinator's cycle statistics and the Platform Admin's figures are shown.
10. The AI evaluation script is run and its numbers are shown.

## 8. Definition of Done

A requirement is done when:

- its code is merged into `main` through a pull request with CI green;
- its acceptance test in Section 6 is automated and passes, and its endpoints are in the permission matrix;
- its screens exist in Arabic and English and follow the wireframes (`ST_Vacancies` recommended tab, `CS_Attendance`, `CS_Evaluation`, `AS_Grade`, `CO_Grades`, the role dashboards);
- its actions write audit entries;
- the design document, the API specification, or the SRS are updated if the implementation changed anything.

The increment is done when every committed requirement is done, the demo scenario runs without help, and `04_Test_Report.md` records the results, including the evaluation script's numbers.

## 9. Risks for this Increment

| **Risk** | **Effect** | **Response** |
|:---|:---|:---|
| Model size and speed on free CPU | Slow image builds, slow ranking | Small model (e5-small, 384 dimensions); embeddings stored, ranking only compares vectors; basic mode as fallback |
| Top-5 target missed on the labelled set | FR-MAT-01 acceptance fails | Tune the floor and ceiling settings on the set; improve the vocabulary; report the numbers honestly |
| Grade preconditions depend on many records | Hard to demo and test | Factories build a placement with all reports and evaluations in one call; the preconditions endpoint lists what is missing |
| Deployment needs the owner's accounts | Reference deployment not live by M4 | Everything prepared and tested locally first; the go-live checklist takes the owner a few minutes; the demo falls back to Docker Compose |
| pgvector changes the database image | Local data or CI breaks | Same PostgreSQL major version (16); the migration creates the extension; CI uses the same image |
