# Increment 4 – Requirements (Scope and Acceptance)

**Status:** Approved Oct 28, 2026 – the project owner delegated the decisions of Section 5, and the recommendations were adopted · Author: Salam Alsaour  
**Baseline:** [SRS 1.5](../../Project_4_SRS/InternSync_SRS.md), [Design 1.5](../../Design/InternSync_Design.md), [API 1.4](../../Design/InternSync_API_Spec.md), [SPMP 1.5](../../Project_3_SPMP/InternSync_SPMP.md), [Increment 3](../Increment_3/04_Test_Report.md)  
**Milestone:** M6 – Testing complete, **Dec 10, 2026**: test report; user acceptance testing with at least 8 participants, 80% or more of the scenarios completed without help.

## 1. Purpose

The SPMP plans three increments, then the testing phase (T7: testing, bug fixing, and the Could functions if time allows) and the final documentation (T8). Increments 1 to 3 finished early, so this fourth increment covers the build work of T7:

- the four Could functions and the Could privacy requirement;
- the release checks left for M6 by the earlier test reports;
- two requests of the project owner:
  - a working offline mode;
  - one file with every measured result, for the final presentation.

User acceptance testing needs volunteers, so it is prepared here and run by the owner (Section 7).

## 2. Process for this Increment

The same four phases as before. The project owner asked for the increment to run end to end, with one review at the pull request.

| **Phase** | **Artefact** | **Planned dates** |
|:---|:---|:---|
| 1. Requirements | `01_Requirements.md` (this document) | Oct 28 |
| 2. Design | `02_Design.md`: tables, endpoints, certificate, anonymization, offline mode, test design | Oct 28 |
| 3. Implementation | Code on branch `increment-4`, CI green | Oct 28 – Nov 30 |
| 4. Testing | `04_Test_Report.md`, the held-out evaluation sets, the release checks, [Key_Results.md](../../Key_Results.md) | Dec 1 – Dec 10 |

The increment starts 29 days ahead of the SPMP plan (Nov 26).

## 3. Use Cases Covered

| **Use case** | **Increment 4 coverage** |
|:---|:---|
| UC-13 Issue and verify a certificate | Full |
| UC-14 Evaluate the training entity and answer the survey | Full |
| UC-12 Export grade sheets and summaries | The term summary gains the job-offer rate and the company averages |
| All roles | Offline mode: pages opened earlier stay readable, and report and evaluation drafts typed offline are kept and saved later |

## 4. Requirements in Scope

### 4.1 Functional and Privacy Requirements

| **ID** | **Requirement (short)** | **Priority** | **Commitment** |
|:---|:---|:--:|:--:|
| FR-CER-01 | Certificate PDF with an unguessable code and a QR code to the public page, only for a Final grade | Could | Committed |
| FR-CER-02 | Public page without login: Valid, Revoked, or Not found, with the name, university, college, cycle, company, and dates; never the grade | Could | Committed |
| FR-CER-03 | The coordinator revokes a certificate with a reason | Could | Committed |
| FR-EVL-05 | The student evaluates the training entity at the end; visible to the coordinator only | Could | Committed |
| FR-DSH-03 | Job-offer survey; job-offer rate per cycle and per company | Could | Committed |
| FR-DSH-04 | Alert when a company with at least 5 final evaluations averages 0.8 or more above the cycle mean | Could | Committed |
| NFR-PRV-04 | The coordinator anonymizes a closed cycle after the college's retention period; statistics unchanged | Could | Committed |
| FR-PWA-03 | Offline mode, as changed by CR-10 (RQ-1) | Should | Committed |

**Totals:** 7 Could requirements and 1 changed Should requirement, all committed.

### 4.2 Release Checks Left for M6

| **ID** | **What is checked** | **How** |
|:---|:---|:---|
| NFR-SEC-05 | OWASP ZAP baseline scan with no high-risk finding; dependency audits clean | ZAP in Docker against the local stack, and a workflow that repeats it (RQ-8) |
| NFR-PER-01 | 95% of ordinary requests within 2 s with 50 concurrent users | Locust against the local stack; the reference deployment when it is switched on (RQ-9) |
| NFR-PRT-01 | Main tasks on Chrome, Edge, Firefox, Safari, and phones | Automated browser tests on the Chromium, Firefox, and WebKit engines at desktop and phone sizes in CI; real phones in the device check of the UAT (RQ-7) |
| NFR-USA-03 | No horizontal scrolling from 360 px to 1920 px | The same browser tests at 360, 768, 1366, and 1920 px |
| NFR-USA-04 | Contrast of at least 4.5:1; main tasks by keyboard | Automated accessibility check (axe) in the browser tests; a keyboard walkthrough |
| NFR-AI-03 | Matching and similarity results hold on data not used to choose the settings | Held-out sets written after the settings were frozen, run once (RQ-6) |
| NFR-REL-02 | A restore tested before delivery | Done on Oct 26 for the database (Deployment guide, Section 6); repeated for the new tables |
| NFR-USA-01 | UAT with at least 8 participants, 80% of scenarios without help | Plan, scenario cards, and result sheet prepared; the sessions are run by the owner (Section 7) |

**Supporting work:**

- **Results file:** [docs/Key_Results.md](../../Key_Results.md). It collects every measured result of the project in one place, with the target, the result, and how to repeat it, for the final presentation (RQ-10).
- **Demo data:** a completed placement with a certificate, an evaluation of the company, a survey answer, a company with five generous final evaluations, and a closed cycle past its retention period.

## 5. Decisions

| **ID** | **Open point** | **Decision (recommended and adopted)** |
|:---|:---|:---|
| RQ-1 | What the app does offline (owner's request) | Today the app only opens offline with a message (FR-PWA-03, Increment 3 RQ-5). Change it with **CR-10**: (a) pages opened earlier in the same signed-in window stay readable offline, marked "Saved copy" with its time; (b) text typed into a weekly or final report draft, or an evaluation draft, is kept on the device and saved to the server as a draft as soon as the connection returns; (c) submitting and every other change still need a connection, so deadlines and Late flags keep using server time. Uploads and file downloads are not available offline |
| RQ-2 | Personal data on the device in offline mode | The saved copy lives in the window's session storage: it is deleted at sign-out and when the window closes, and it is never readable after the 30-minute idle limit (FR-AUT-03), which the app now also applies offline. Drafts typed offline are kept in local storage under the user's ID until they are saved to the server, or for 7 days at most, and are deleted at sign-out. Files, CVs, exports, the audit log, and the Platform Admin's pages are never saved |
| RQ-3 | When the student can evaluate the company and answer the survey (UC-14 "the placement has ended") | From the training end date of the placement or when the grade is Final, whichever comes first. The evaluation of the company is submitted once and cannot be changed afterwards, so the averages stay stable. The job-offer answer can be changed later (for example from Pending to Yes) |
| RQ-4 | Certificate layout and language | One A4 landscape page in Arabic and English, with the student, university, college, cycle, company, training dates, the issue date, the code, and the QR code. No grade, as on the public page. The PDF is stored once at issue (`files`, purpose `certificate`) |
| RQ-5 | Retention period and what anonymization keeps (NFR-PRV-04) | A retention period per college in months (default 12, 0 to 120), set by the coordinator. A closed cycle can be anonymized once `closed_at` plus the period has passed. Students who still have a placement in another cycle that is open or not yet past its period are skipped and counted. Names, contact details, student numbers, CV files and text, skills, embeddings, report text and attachments, comments, and certificate files are removed. Statuses, scores, dates, majors, and companies stay, so the cycle statistics do not change. The audit log stays as it is: it is append-only and holds IDs and changed fields |
| RQ-6 | Held-out evaluation sets | The Increment 2 and 3 reports asked for sets "written by another person". Nobody else is available, so the sets are written by the author **after** the settings were frozen and are run once, with the results reported as they come out. Similarity: 10 copied reports, including 3 reworded ones that are harder to catch, and 10 originals on the same topics. Matching: 10 harder profiles with more eligible vacancies each and vacancies described in free text only |
| RQ-7 | Browser tests | Playwright on Chromium, Firefox, and WebKit (the engine of Safari), at desktop size and at the sizes of an Android phone and an iPhone, in a CI job against the Docker stack. They cover sign-in, the main task of each role, the language switch, the offline mode, and the certificate page. Real phones and real Safari remain in the device check (Section 7) |
| RQ-8 | ZAP scan | The ZAP baseline scan (passive, no attack) in Docker against the local stack, the web app and the API's OpenAPI document. The workflow `security-scan.yml` runs it on request and every week; high-risk findings fail it |
| RQ-9 | Load test | Locust with 50 simulated users, against the local Docker stack on the development laptop, with a mix of dashboards, lists, and form saves of the seeded roles. The same script runs against the reference deployment once it is switched on |
| RQ-10 | Results file (owner's request) | `docs/Key_Results.md`: one table per topic (quality, AI accuracy, speed, security, languages and devices, cost), each row with the target, the result, the date, and the command or test that repeats it. Updated at the end of each increment; the numbers in it are copied from the test reports, never typed separately |

## 6. Acceptance Tests

Each test comes from the SRS acceptance criterion of its requirement. *API* tests run against a test database; *Unit* tests check one function; *Eval* runs the evaluation script; *E2E* runs in the browser tests; *Browser* items are checked by hand in the running app.

| **Test** | **Requirement** | **Scenario and expected result** | **Level** |
|:---|:---|:---|:--:|
| AT-CER-01 | FR-CER-01 | A certificate cannot be issued for a grade that is not Final; issued for a Final grade, it has a 26-character code, and its PDF holds the code and a QR code that opens `/verify/<code>`; a second valid certificate for the same placement is refused | API, Unit |
| AT-CER-02 | FR-CER-02 | Without login, a valid code shows Valid with the listed fields and no grade; a revoked code shows Revoked; an altered code shows Not found | API, E2E |
| AT-CER-03 | FR-CER-03 | Revoking needs a reason and is audited; after it the page shows Revoked, and a new certificate can be issued | API |
| AT-EVL-05 | FR-EVL-05 | The student evaluates the company once, only after the training end date or a Final grade; the coordinator sees it and the averages per company; a company supervisor and a Company Admin are refused | API |
| AT-DSH-03 | FR-DSH-03 | With seeded answers, the job-offer rate equals Yes answers ÷ survey answers, per cycle and per company; a student who skipped is not counted | API |
| AT-DSH-04 | FR-DSH-04 | A company with 5 final evaluations averaging 4.8 against a cycle mean of 3.6 raises the alert; a company with 4 evaluations does not; the alert changes nothing else | API |
| AT-PRV-04 | NFR-PRV-04 | Before the retention period ends, anonymizing is refused; after it, no name, email, student number, CV, report text, or certificate file of the cycle can be retrieved, students still in another active cycle are skipped, and the cycle statistics are unchanged | API |
| AT-PWA-03 | FR-PWA-03 (CR-10) | Offline: a page opened before shows its saved copy with the time; a page never opened shows that it is not saved; a report draft typed offline is saved after the connection returns; submit buttons stay disabled; after sign-out nothing is left in session storage and no draft is left | E2E, Browser |
| AT-SEC-05 | NFR-SEC-05 | ZAP baseline with no high-risk finding; pip-audit and npm audit with no critical finding | Scan |
| AT-PER-01 | NFR-PER-01 | 50 users: 95th percentile of ordinary requests under 2 s | Load |
| AT-PRT-01 | NFR-PRT-01, NFR-USA-03 | The browser tests pass on the three engines and at 360, 768, 1366, and 1920 px without horizontal scrolling | E2E |
| AT-USA-04 | NFR-USA-04 | The accessibility check finds no contrast failure on the main pages; the main tasks can be done with the keyboard | E2E, Browser |
| AT-AI-03 | NFR-AI-03 | The held-out sets give their numbers in one run with the frozen settings; targets: at least 9 of 10 copied flagged and at most 1 of 10 originals flagged; a relevant vacancy in the top 5 for at least 80% of profiles | Eval |

## 7. User Acceptance Testing and Device Check (prepared, run by the owner)

- **The plan** is [05_UAT_Plan.md](05_UAT_Plan.md):
  - scenarios for each of the five roles;
  - the task cards handed to the participants;
  - the consent text;
  - how "completed without help" is scored;
  - a result sheet that computes the share of scenarios completed.
- **Participants:** at least 8 volunteers covering the five roles (SRS D-06).
- **Device check:** in the same sessions, on at least one Android phone and one iPhone:
  - install the app;
  - receive a push;
  - use airplane mode.
- **Results:** they go into this increment's test report. M6 is complete when they are recorded.

## 8. Demo Scenario (M6 dry run and final demonstration)

1. The coordinator issues the certificate of a student with a Final grade. Scanning the QR code with a phone opens the public page: Valid, with no grade.
2. The coordinator revokes it with a reason; the page shows Revoked. An altered code shows Not found.
3. The student evaluates the company and answers the survey. The coordinator sees the averages per company and the job-offer rate. The company supervisor cannot see them.
4. The statistics of the summer 2025 cycle show the leniency alert for the generous company (the dashboard item counts the alerts of open cycles).
5. The coordinator anonymizes the closed demo cycle; its statistics stay the same and its names are gone.
6. With the network off, the student opens the reports page opened earlier (saved copy), writes next week's report, and turns the network back on; the draft is saved.
7. `Key_Results.md` is shown as the summary of the measured results.

## 9. Definition of Done

A requirement is done when:

- its code is merged into `main` through a pull request with CI green;
- its acceptance test in Section 6 is automated and passes (or checked in the browser where marked), and its endpoints are in the permission matrix;
- its screens exist in Arabic and English and follow the wireframes (`Verify_Mobile`, `CO_Exports`) or the existing layout where no wireframe exists;
- its actions write audit entries;
- the design document, the API specification, or the SRS are updated if the implementation changed anything.

The increment is done when every committed requirement is done, the release checks of Section 4.2 have their results in `04_Test_Report.md` and in `Key_Results.md`, and the UAT materials are ready. M6 is complete when the UAT results are added.

## 10. Risks for this Increment

| **Risk** | **Effect** | **Response** |
|:---|:---|:---|
| Personal data left on a shared device by the offline mode | Privacy | Session storage only for the saved copy, the idle limit applied offline, drafts deleted at sign-out and after 7 days (RQ-2); a browser test checks that nothing is left after sign-out |
| A draft typed offline overwrites a newer draft saved from another device | Lost text | The draft is saved only if the server's draft has not changed since the page was opened; otherwise the student chooses which text to keep |
| Anonymization removes data still needed | Lost records | Only closed cycles past the retention period; students active elsewhere are skipped; a confirmation with the counts first; statistics compared before and after in the test |
| Held-out results below target | Weaker AI claims | Reported as they are; the advisory label and the human decision stay; any change of setting is a new CR with a new held-out set |
| Browser tests flaky in CI | Red builds | Run against the Docker stack with seeded data, retries only for the start-up, and traces kept on failure |
| Volunteers for UAT not available in time | M6 late | Materials ready now, 6 weeks before the M6 date; sessions of 20 minutes, possible online |
