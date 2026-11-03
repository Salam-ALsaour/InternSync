# InternSync – Software Test Specification (STS)

Based on IEEE 829 – adapted for student projects (CSC 305 STS template)

**IMAM ABDULRAHMAN BIN FAISAL UNIVERSITY** · College of Computer Science & Information Technology
CSC 305 – Software Engineering \| Semester 1 – 2026/2027 \| Section 5MA1 \| Group 3

| **Item** | **Value** |
|:---|:---|
| Project title | InternSync – Cooperative Training Coordination and Tracking System |
| Team name | Group 3 (Section 5MA1) |
| Advisor | Dr. Sultan Al-Enezi |
| Version | 1.0 |
| Date | 01-11-2026 |

> This Markdown file is the maintained version of the STS (Project 7). `InternSync_STS_v1.0.docx` and `.pdf` in this folder are generated from it on the course STS template ([build](build/README.md)). The table of Appendix 11.2 is generated from the increment documents by `build/acceptance_table.py`.

### Team Information

| **Team Member** | **Student ID** | **Project Role** |
|:---|:--:|:---|
| Salam Alsaour (Team Leader) | 2250009168 | Team leader; backend and AI services developer |
| Khalid Alajmi | 2250004309 | Frontend and backend developer |
| Ali Alghafly | 2250002460 | Frontend developer |
| Ahmed Kanaan | 2250009170 | AI services developer; deployment lead |
| Abdullah Abalhareth | 2250005266 | QA and documentation lead |
| Rakan Alzahrani | 2250000631 | UI/UX designer |

### Revision History

| **Version** | **Date** | **Description** | **Author** |
|:--:|:--:|:---|:--:|
| 1.0 | Nov 1, 2026 | First version for Project 7 (STS) on the course template (IEEE 829 adapted), from the acceptance tests and test reports of Increments 1 to 5, the UAT plan, and the key results. | Group 3 |

## Table of Contents

- [1. Introduction](#1-introduction)
- [2. Test Items](#2-test-items)
- [3. Features to Be Tested](#3-features-to-be-tested)
- [4. Features Not to Be Tested](#4-features-not-to-be-tested)
- [5. Test Approach](#5-test-approach)
- [6. Test Cases](#6-test-cases)
- [7. Test Data](#7-test-data)
- [8. Test Environment](#8-test-environment)
- [9. Responsibilities and Schedule](#9-responsibilities-and-schedule)
- [10. Deliverables](#10-deliverables)
- [11. Appendices](#11-appendices)

## 1. Introduction

### 1.1 Purpose

This Software Test Specification (STS) defines how InternSync is tested: what is tested and what is not, at which levels and with which tools, the test cases with their inputs, expected and actual results, the test data and environment, who is responsible for each part, and when it runs. It follows IEEE Std 829 as adapted in the CSC 305 template, and it records the results of the test runs of Increments 1 to 5.

### 1.2 Scope of Testing

| **Level** | **What it covers** | **How** |
|:---|:---|:---|
| Unit | Single functions: deadlines, state transitions, grade computation, skill extraction, scoring, passage splitting, date format, translation keys | pytest and Vitest, automated |
| Integration (API) | Each endpoint with the real PostgreSQL database: business rules, permissions, scope across organizations, audit, notifications, files | pytest with the HTTP test client, automated on every pull request |
| System | The whole stack in a browser: role tasks, both languages, offline mode, phones and desktops; plus load, security, and AI accuracy runs | Playwright, Locust, OWASP ZAP, the AI evaluation script |
| Acceptance | One acceptance test per requirement (Appendix 11.2), and user acceptance testing with at least 8 participants | Automated where possible; UAT sessions with scenario cards |

Every requirement of the SRS has an acceptance test or a recorded check. The tests run against the system as merged on `main` at the end of Increment 5.

### 1.3 Reference Documents

| **Document** | **Use in this STS** |
|:---|:---|
| [SRS 1.6](../Project_4_SRS/InternSync_SRS.md) | Requirements and their acceptance criteria |
| [SDD 1.0](../Project_6_SDD/InternSync_SDD.md) and the [System Design Document 1.7](../Design/InternSync_Design.md) | State machines, algorithms, thresholds, and the test design |
| [SPMP 1.7](../Project_3_SPMP/InternSync_SPMP.md) | Roles, schedule, and milestones M3 – M7 |
| Increment documents ([1](../Increments/Increment_1/01_Requirements.md), [2](../Increments/Increment_2/01_Requirements.md), [3](../Increments/Increment_3/01_Requirements.md), [4](../Increments/Increment_4/01_Requirements.md)) | Acceptance tests of each increment (Section 6 of each) |
| Test reports ([1](../Increments/Increment_1/04_Test_Report.md), [2](../Increments/Increment_2/04_Test_Report.md), [3](../Increments/Increment_3/04_Test_Report.md), [4](../Increments/Increment_4/04_Test_Report.md), [5](../Increments/Increment_5/04_Test_Report.md)) | Execution results and defect logs |
| [UAT plan](../Increments/Increment_4/05_UAT_Plan.md) | Participants, scenario cards, and the result sheet |
| [Key results](../Key_Results.md) and [Requirements status](../Requirements_Status.md) | Measured results and requirement-to-test tracing |
| IEEE Std 829-1998 | IEEE Standard for Software Test Documentation |

## 2. Test Items

The item under test is InternSync as merged on `main` at the end of Increment 5 (commit `0662647`): the backend image, the web app build, and the database migrations.

| **Item** | **Parts** | **Main tests** |
|:---|:---|:---|
| Authentication and access control | Registration, login, sessions, password reset, lockout, consent, role and scope gates, permission matrix | `backend/tests/test_auth.py`, `tests/permissions` |
| Organizations and verification | Universities, colleges, companies, verification requests and documents, invitations, role transfer | `test_orgs.py` |
| Training cycles | Weeks and deadlines, grade components, rubric, enrolments, closing and reopening | `test_cycles.py` |
| Student profile and CV | Profile, CV upload and type checks, skill extraction and confirmation | `test_profiles.py` |
| Vacancies and placement | Vacancies, applications, placements, filters | `test_vacancies.py` |
| Matching (AI) | Eligibility, fit score, explanation, development plan, basic fallback | `test_matching.py`, `ai-eval/evaluate.py` |
| Reports | Report slots, drafts, attachments, submission, review, comments, lateness, missing flag | `test_reports.py` |
| Similarity detection (AI) | Passages, checks, flags, decisions | `test_similarity.py`, `ai-eval/evaluate.py` |
| Attendance, evaluations, grades | Attendance and unlocks, evaluations, grade computation and approval workflow | `test_attendance_evaluations.py`, `test_grades_dashboard.py` |
| Dashboards, exports, certificates | Pending actions, statistics, leniency alert, grade sheet, term summary, training record, certificates | `test_grades_dashboard.py`, `test_feedback.py`, `test_exports.py`, `test_certificates.py` |
| Notifications and scheduler | Outbox, email, web push, reminders, missing flags, escalations, job locks | `test_notifications.py`, `test_audit_jobs.py` |
| Audit and privacy | Audit log, history, anonymization, purge of verification documents | `test_audit_jobs.py`, `test_privacy.py` |
| Web app (PWA) | Screens of every role, Arabic and English, offline mode, install, accessibility, layouts | `frontend/src/**/*.test.ts`, `frontend/e2e/*.spec.ts` |
| Database and storage | Migrations, constraints, row level security, append-only audit trigger, file storage adapters | Every backend test on a fresh database; `test_storage.py`, `test_config.py` |
| Demo scenarios | The M3 to M6 demonstration scripts end to end through the API | `test_demo_scenario.py`, `test_demo_m4.py`, `test_demo_m5.py`, `test_demo_m6.py` |

## 3. Features to Be Tested

Every feature below is traced from its SRS requirements to the design and to its acceptance tests (Appendix 11.2). The [requirements status](../Requirements_Status.md) lists all 125 requirements with their tests.

| **Feature** | **SRS requirements** | **SDD section** | **Acceptance tests** |
|:---|:---|:---|:---|
| Login, sessions, and roles | FR-AUT-01 – 06, NFR-SEC-02/03 | 5.8 | AT-AUT-01 – 06 |
| Registration and verification of organizations and students | FR-ORG-01 – 09 | 5.1, 5.3 | AT-ORG-01 – 09 |
| Training cycles and configuration | FR-CYC-01 – 05 | 5.6.5 | AT-CYC-01 – 05 |
| Student profile and CV skill extraction | FR-PRF-02 – 05 | 5.6.1 | AT-PRF-02 – 05 |
| Vacancies, applications, and placements | FR-VAC-01 – 08 | 5.3 | AT-VAC-01 – 08 |
| Matching, explanation, and development plan | FR-MAT-01 – 07, NFR-AI-02/03 | 5.6.2 | AT-MAT-01 – 07, AT-AI-02/03 |
| Weekly and final reports, and their workflow | FR-REP-01 – 07, FR-WFL-01 | 5.2, 5.3 | AT-REP-01 – 07, AT-WFL-01 |
| Attendance | FR-ATT-01 – 04 | 5.1 | AT-ATT-01 – 04 |
| Evaluations | FR-EVL-01 – 05 | 5.1 | AT-EVL-01 – 05 |
| Grades and approval | FR-WFL-02 – 07 | 5.3, 5.6.4 | AT-WFL-02 – 07 |
| Similarity detection | FR-SIM-01 – 03 | 5.6.3 | AT-SIM-01 – 03 |
| Notifications and reminders | FR-NOT-01 – 06, NFR-REL-03 | 5.7 | AT-NOT-01 – 06, AT-REL-03 |
| Dashboards and statistics | FR-DSH-01 – 05 | 5.1 | AT-DSH-01 – 05 |
| Exports and completion certificates | FR-EXP-01 – 03, FR-CER-01 – 03, NFR-L10N-03 | 5.1 | AT-EXP-01 – 03, AT-CER-01 – 03, AT-L10N-03 |
| Language and installable app | FR-LOC-01/02, FR-PWA-01 – 03 | 5.9 | AT-LOC-01 – 03, AT-PWA-01 – 03 |
| Audit trail and privacy | FR-AUD-01 – 03, NFR-PRV-01 – 04 | 5.8, 6.4 | AT-AUD-01 – 03, AT-PRV-04 |
| Performance | NFR-PER-01 – 05 | 4.4 | AT-PER-01 – 05 |
| Security, portability, and usability | NFR-SEC-04/05, NFR-PRT-01, NFR-USA-03/04 | 5.8 | AT-SEC-05, AT-PRT-01, AT-USA-04 |

## 4. Features Not to Be Tested

| **Item** | **Reason** |
|:---|:---|
| Services of other providers: Gmail delivery, the browser vendors' push services, Vercel, Hugging Face, Supabase | Outside the project; only the system's calls to them are tested (emails caught by Mailpit, push sent through a stand-in sender) |
| Uptime of the hosted system (NFR-REL-01) and HTTPS on it (NFR-SEC-01) | The reference deployment is prepared but switched on only by the owner; checked after the switch-on (Section 9.2) |
| Load above 50 concurrent users | The SRS asks for 50 users (NFR-PER-01); about 400 students in the demonstration |
| Real (non-synthetic) personal data | Only synthetic data is used (SRS C-09); no real CV, report, or grade enters the system |
| Old browsers and Internet Explorer | Outside the supported environment (SRS 2.4); current Chromium, WebKit, and Firefox are tested |
| Native mobile apps | There are none; the web app is installable on phones as a PWA |
| Framework messages for wrongly typed values (for example letters in a number field) | They come from the framework in English; the forms prevent most of them, and every business rule answers in the user's language |
| Wireframes | Design artefacts, reviewed in task T3, not executable |

## 5. Test Approach

### 5.1 Strategy

- **Automated first.** Every acceptance test is automated where possible and named after its ID (for example `test_at_rep_04_on_time_late_and_missing`), so each result traces to a requirement. Manual checks are kept for what needs eyes: layouts in both languages, the shaped Arabic in PDFs, and installation on a phone.
- **Black-box at the API.** Most tests call the HTTP API as a real user of a given role and check status codes, error codes, stored data, audit entries, and notifications. White-box unit tests cover the algorithms (deadlines, grade total, matching score, passage splitting) with exact expected values.
- **Positive and negative cases.** Each rule is tested where it allows and where it refuses: every allowed state transition passes, and at least one disallowed transition from each state is rejected.
- **Permissions exhaustively.** A matrix lists every endpoint with the callers allowed past the role gates; one test calls each endpoint as every other caller and expects `401` or `403`, and another fails if an endpoint is missing from the matrix. Scope across organizations is tested with two universities, three colleges, and two companies.
- **Controlled time.** The application reads time from one clock that tests can move, so deadlines, the 30-minute idle limit, the 15-minute lockout, purges after 30 days, and escalations after 3 days are tested without waiting.
- **Honest AI numbers.** The AI is tuned on labelled tuning sets, then measured once on held-out sets written after the settings were frozen.
- **Regression on every change.** CI runs lint, the backend tests with a 70% coverage gate, the API contract check, the frontend tests and build, the dependency audits, and the browser tests on every pull request.

### 5.2 Tools

| **Tool** | **Used for** |
|:---|:---|
| pytest, pytest-cov, httpx test client | Unit and API tests on a real PostgreSQL database; coverage |
| Vitest | Frontend unit tests (translation keys, date format, offline storage) |
| Playwright | Browser tests on Chromium, WebKit, Firefox, and phone sizes; offline mode; keyboard-only task |
| axe-core (through Playwright) | Accessibility: colour contrast and keyboard use |
| Locust | Load test with 50 concurrent users |
| OWASP ZAP | Baseline scan of the web app and API scan in safe mode |
| pip-audit, npm audit | Known vulnerabilities in dependencies |
| `ai-eval/evaluate.py` | Skill extraction recall, matching top-5 rate, similarity detection rates |
| Mailpit | Catches every email the system sends |
| GitHub Actions | Runs the suites on every pull request |

### 5.3 Entry and Exit Criteria

| **Criterion** | **Rule** |
|:---|:---|
| Entry | The increment's acceptance tests are written in its requirements document; the build passes lint and compiles |
| Pass of a test case | The actual result equals the expected result, including the status and error code |
| Exit of an increment | Every acceptance test passes or has a recorded reason; coverage ≥ 70%; no open defect of high severity; the demo dry run passes |
| Defects | Logged in the test report of the increment with how it was found and the fix; the fix gets a regression test |
| Suspension | A failing migration or a broken build stops testing until fixed |

## 6. Test Cases

### 6.1 Functional Test Cases

Each case comes from an acceptance test of Appendix 11.2 (named in the Feature column). Positive cases check that a valid action succeeds; negative cases check that an invalid one is refused.

**Table 6.1 – Functional test cases**

| **Test Case ID** | **Feature** | **Input** | **Expected Output** | **Actual Result** | **Pass/Fail** |
|:---|:---|:---|:---|:---|:---|
| TC-01 | Login by role (AT-AUT-01) | Each demo account (student, company supervisor, Company Admin, academic supervisor, coordinator, Platform Admin) signs in with its password | Each role gets only its own menu; the Company Admin also gets the team menu | Each role saw only its menu; team menu for the Company Admin only | Pass |
| TC-02 | Account lockout (NFR-SEC-03) | Five wrong passwords for one account, then the right password; the clock moved 16 minutes | Locked after the fifth failure (`423 ACCOUNT_LOCKED`), even with the right password; open again after 15 minutes | Locked, then open after 16 minutes | Pass |
| TC-03 | Idle timeout and logout (AT-AUT-03) | A request after 30 idle minutes; the old token after logout | `401` in both cases | `401 SESSION_EXPIRED` in both cases | Pass |
| TC-04 | One-time links (AT-AUT-02, AT-AUT-04) | An email confirmation link used twice; an expired link; a password reset link used twice | The first use works; a second or expired use is rejected; the old password fails after the reset | As expected | Pass |
| TC-05 | Permission matrix (AT-AUT-05) | All 163 endpoints called by every caller not allowed (public, unverified, ST, CS, CA, AS, CO, PA) | `401` or `403` for every call | 810 refused calls, none got through | Pass |
| TC-06 | Scope across colleges (AT-ORG-05) | The coordinator of college B opens the verification request of a student of college A | `403 FORBIDDEN` | `403` | Pass |
| TC-07 | Student verification (AT-ORG-05) | The coordinator approves a student's request and chooses the cycle | The student is verified and enrolled and can apply | Verified, enrolled, application accepted | Pass |
| TC-08 | Rejection needs a reason (AT-ORG-03, AT-ORG-05) | A coordinator or the Platform Admin rejects a request with an empty reason | Refused with `422` | `422` | Pass |
| TC-09 | Unverified accounts (AT-ORG-02) | An unverified student applies; an unverified company creates a vacancy | `403 VERIFICATION_REQUIRED` | `403 VERIFICATION_REQUIRED` | Pass |
| TC-10 | Duplicate company (AT-ORG-04) | A company registers with a commercial registration number already used | Refused with an error | Refused | Pass |
| TC-11 | Weekly deadlines (AT-CYC-01) | A 12-week cycle with report day Thursday at 23:59 | 12 deadlines, each on Thursday at 23:59 Riyadh time; scheduled days equal the working days | 12 deadlines on the right day and time | Pass |
| TC-12 | Grade weights (AT-CYC-02) | Weights 40/30/20, then 40/30/30 | 40/30/20 refused; 40/30/30 saved | As expected | Pass |
| TC-13 | CV upload checks (AT-PRF-03, NFR-SEC-04) | A 6 MB PDF; a PNG renamed `.pdf`; a ZIP renamed `.docx`; a second valid CV | Oversized file `413`; wrong types `415`; both valid versions kept | As expected | Pass |
| TC-14 | Skill extraction (AT-PRF-04, AT-CYC-04) | An English PDF CV, an Arabic DOCX CV, and a CV containing "JS" | Non-empty candidate lists; "JS" shown as "JavaScript"; only confirmed skills become profile skills | As expected | Pass |
| TC-15 | CV without text (AT-PRF-05) | An image-only PDF | The "no readable text" message and an empty editable skill list | Message and empty list shown | Pass |
| TC-16 | Vacancy visibility (AT-VAC-02) | A draft vacancy; a vacancy open only to university A | The draft is hidden from students; the targeted vacancy is visible only to A's students | As expected | Pass |
| TC-17 | Application rules (AT-VAC-04) | A duplicate application, one after the deadline, one of the wrong training type, and a sixth active one | Each refused with its own message | Each refused with its message | Pass |
| TC-18 | Placement (AT-VAC-07) | The coordinator confirms a placement on the last seat, then a second placement for the same student | Placement confirmed; vacancy closed; the student's other applications withdrawn; second placement refused | As expected | Pass |
| TC-19 | Ranked vacancies (AT-MAT-01) | A student profile with confirmed skills; seeded vacancies | Only eligible vacancies, by fit score from high to low; a relevant vacancy in the top 5 for at least 80% of labelled profiles | Ordered by fit; relevant vacancy in the top 5 for 100% | Pass |
| TC-20 | Ineligible vacancy (AT-MAT-03) | A vacancy whose minimum GPA is above the student's GPA | Absent from the ranking; shows "GPA below minimum" when browsing | As expected | Pass |
| TC-21 | Basic matching (AT-MAT-04) | Ranking with the model switched off (`AI_ENABLED=false`) | A ranking within 5 s labelled "Basic matching" | Returned and labelled basic | Pass |
| TC-22 | Match explanation (AT-MAT-05) | A student and a vacancy with some required skills missing | Matched skills = confirmed ∩ required; missing skills = required − confirmed | Sets equal | Pass |
| TC-23 | Report slots (AT-REP-01) | A placement in a 12-week cycle | 12 weekly slots and 1 final slot with the right deadlines | As expected | Pass |
| TC-24 | Report attachments (AT-REP-02) | A fourth attachment; an 11 MB file; a valid report with 3 files | Fourth file and 11 MB file refused; the valid report stored with its files | As expected | Pass |
| TC-25 | Required fields (AT-REP-02) | A weekly report submitted with "challenges" empty | `422 REQUIRED_FIELDS_MISSING` naming the field | `422` with the field | Pass |
| TC-26 | On time, late, and missing (AT-REP-04) | Deadline 23:59: submissions at 23:58 and 00:00; a slot left empty | 23:58 On time; 00:00 Late; the empty slot flagged Missing within 1 hour | On time, Late; Missing at the next job run (every 15 minutes) | Pass |
| TC-27 | Revision cycle (AT-REP-05) | A revision request with no comment; a revision with a comment, then a resubmission | No comment refused; after resubmission both versions viewable | As expected | Pass |
| TC-28 | Invalid transitions (AT-WFL-01) | Accept a draft report; submit to a slot closed as missing | `409 INVALID_TRANSITION`; `409 SLOT_CLOSED` | As expected | Pass |
| TC-29 | Attendance (AT-ATT-01, AT-ATT-02) | "Full attendance" for a week; more days than scheduled; an edit on day 8 after the week, before and after an unlock | Full week saved in one action; extra days refused; edit refused until the coordinator unlocks the week (audited) | As expected | Pass |
| TC-30 | Evaluations (AT-EVL-01, AT-EVL-04) | An evaluation with an unrated criterion or no comment; a second reopening by the coordinator | Both refused; the first reopening needs a reason and is audited | As expected | Pass |
| TC-31 | Grade computation (AT-WFL-02) | Seeded component scores and weights | The total equals a hand calculation to two decimals | Equal | Pass |
| TC-32 | Grade preconditions (AT-WFL-03) | The academic supervisor submits a grade while the final report is not accepted | `409 PRECONDITIONS_UNMET` with the list of missing items | Refused with the list | Pass |
| TC-33 | Grade approval (AT-WFL-04, AT-WFL-06) | The coordinator approves a submitted grade; the student views the grade before and after | Final with a timestamp; placement completed; the student sees the grade only when Final | As expected | Pass |
| TC-34 | Similarity flag (AT-SIM-01, AT-SIM-02) | A report copied from an earlier report of the same university; the same text stored at another university | Flagged with the passages side by side; reports of another university never compared | As expected | Pass |
| TC-35 | Similarity decision (AT-SIM-03) | A decision without a comment; a decision on a check that is not flagged | Both refused; a valid decision changes neither the report status nor the grade | As expected | Pass |
| TC-36 | Notifications (AT-NOT-01, AT-NOT-06) | A report is submitted; the supervisor has chosen Arabic | One in-app notification and one email, in Arabic; the unread count drops when read | As expected | Pass |
| TC-37 | Reminders and escalations (AT-NOT-02, AT-NOT-04) | Unsubmitted slots due within 24 hours and later; items 3 and 4 days overdue; each job run twice | Reminders only for the slots due within 24 hours, once each; escalation on day 4, not day 3, never twice | As expected | Pass |
| TC-38 | Grade sheet export (AT-EXP-01) | A cycle with students whose names are in Arabic | Excel and PDF values equal the stored values; Arabic names present and shaped | As expected | Pass |
| TC-39 | Certificate (AT-CER-01, AT-CER-02) | Issue for a grade that is not Final; issue for a Final grade; open the public page with the code and with an altered code | First refused; certificate with a 26-character code and QR code; page shows Valid without the grade; altered code shows Not found | As expected | Pass |
| TC-40 | Offline mode (AT-PWA-03) | The network turned off after opening pages; a report draft typed offline; the network back | Saved copy shown with its time; a never-opened page says it is not saved; submit disabled; the draft saved when back online | As expected in Chromium and WebKit | Pass |
| TC-41 | Language (AT-LOC-01, AT-LOC-02) | Switch each screen between Arabic and English; run the translation-key check | Screens mirror right to left and left to right; the choice is saved; no missing key | 839 texts in both languages; no missing key | Pass |
| TC-42 | Audit log (AT-AUD-01, AT-AUD-02) | Each action of the demo script; an `UPDATE` and a `DELETE` on `audit_log` in the database | Exactly one audit entry per action; the database refuses to change entries | As expected | Pass |
| TC-43 | Anonymization (AT-PRV-04) | Anonymize a closed cycle before and after its retention period | Refused before; after it no name, email, student number, CV, report text, or certificate file can be retrieved, and the statistics stay | As expected | Pass |

### 6.2 Non-Functional Test Cases

**Table 6.2 – Non-functional test cases**

| **Test Case ID** | **Feature** | **Input** | **Expected Output** | **Actual Result** | **Pass/Fail** |
|:---|:---|:---|:---|:---|:---|
| NF-01 | Response time under load (AT-PER-01) | 50 simulated users for 5 minutes (Locust), local stack | 95% of ordinary requests within 2 s | 95% within 0.21 s; 0 errors in 7,785 requests | Pass (local stack) |
| NF-02 | Ranking speed (AT-PER-02) | 1,000 published vacancies; 20 ranking requests per mode | 95th percentile ≤ 5 s, semantic and basic | 0.83 s semantic, 0.76 s basic | Pass |
| NF-03 | CV processing time (NFR-PER-03) | A 4.8 MB PDF packed with text | Skills suggested within 30 s | About 2–6 s | Pass |
| NF-04 | Similarity at scale (AT-PER-04) | A new report checked against 10,000 stored reports | Result within 2 minutes | 0.35–0.42 s | Pass |
| NF-05 | Export speed (AT-PER-05) | Grade sheet of 100 students | Excel and PDF each under 60 s | Excel 1.0–1.3 s, PDF 2.4–4.6 s | Pass |
| NF-06 | Job idempotency (AT-REL-03) | Each scheduled job run twice; a simulated downtime | Nothing sent twice; the next run catches up | As expected | Pass |
| NF-07 | Security scan (AT-SEC-05) | ZAP baseline and API scan; pip-audit; npm audit | No high-risk finding; no critical vulnerable dependency | 0 high-risk after two fixes; 0 vulnerable dependencies | Pass |
| NF-08 | Browsers and screen sizes (AT-PRT-01) | Browser tests on Chromium, WebKit, Firefox, and widths 360, 768, 1366, 1920 px | All pass with no horizontal scrolling | 34 passed on Chromium, WebKit, Pixel 7, iPhone 14; Firefox in CI | Pass |
| NF-09 | Accessibility (AT-USA-04) | axe check of the main pages; a main task with the keyboard only | No contrast failure; task completed by keyboard | One contrast failure (3.86:1) fixed, then none | Pass |
| NF-10 | Arabic in PDFs (AT-L10N-03) | Exported PDF with Arabic names | The Arabic font embedded; text joined and right to left | As expected | Pass |
| NF-11 | Skill extraction accuracy (FR-PRF-04) | 20 labelled CVs, Arabic and English | Recall ≥ 70% | 97.2% (English 97.4%, Arabic 96.9%) | Pass |
| NF-12 | AI on held-out sets (AT-AI-03) | Held-out sets run once with the frozen settings | Relevant vacancy in the top 5 for ≥ 80% of profiles; ≥ 9 of 10 copied reports flagged; ≤ 1 of 10 originals flagged | Matching 100%; 7 of 10 copied flagged (the 3 reworded ones missed); 0 of 10 originals flagged | Fail (similarity part) |
| NF-13 | Coverage (NFR-MNT-01) | `pytest --cov=app` | ≥ 70% of the backend code | 95% | Pass |

NF-12 is the one recorded failure: the similarity check finds text copied word for word, not reports reworded sentence by sentence. It stays advisory, a supervisor decides, and the limit is stated in the final report.

### 6.3 Execution Summary

| **Run** | **Date** | **Acceptance tests** | **Other results** |
|:---|:--:|:---|:---|
| Increment 1 | Oct 24, 2026 | 43 of 43 passed | 108 backend tests; 494 refused calls in the permission matrix |
| Increment 2 | Oct 26, 2026 | 27 of 27 passed | 158 backend tests; matching on the tuning set |
| Increment 3 | Oct 27, 2026 | 21 of 21 passed in their automated part | 187 backend tests; device parts of AT-PWA-01 – 03 moved to M6 |
| Increment 4 | Oct 28, 2026 | 12 of 13 met (AT-AI-03 not met for similarity) | 201 backend tests; 34 browser tests; ZAP, load test, held-out AI sets |
| Increment 5 | Oct 29, 2026 | Regression | 202 backend tests, 19 frontend tests, 34 browser tests, all passing |
| User acceptance testing | Planned for M6 | Scenario cards for the five roles | Postponed on Oct 29; open (Section 9.2) |

102 distinct acceptance tests were run 104 times (AT-AI-03 in Increments 2 and 4, AT-PWA-03 in Increments 3 and 4); 101 are met and one is met in part. 35 defects were found and fixed (Section 10).

## 7. Test Data

| **Dataset** | **Content** | **Valid and invalid cases** |
|:---|:---|:---|
| Test fixtures (`backend/tests`) | Two universities, three colleges, two companies, users of every role, cycles, vacancies, placements; a fresh database per test run | Records of another college or company for the scope tests |
| Demo data (`python -m app.seed --demo`) | One account per role (password `Demo-2026-pass`, refused in production), students in every state (placed, accepted and waiting, not applied, former students), a closed summer 2025 cycle with Final grades | Late and missing reports, a copied report, a generous company for the leniency alert |
| Files | Generated PDF and DOCX CVs in Arabic and English, an image-only PDF, a 4.8 MB PDF, report attachments | A 6 MB CV, an 11 MB attachment, a PNG renamed `.pdf`, a ZIP renamed `.docx`, plain text |
| AI tuning sets (`ai-eval`) | 20 labelled CVs, profiles with their relevant vacancies, 10 copied and 10 original reports | Copied reports at 44–54% copied text; originals on the same topics |
| AI held-out sets (`ai-eval --heldout`) | New profiles with 15 eligible vacancies each; 10 copied and 10 original reports, written after the settings were frozen | 3 reports reworded sentence by sentence |
| Load and scale data | 1,000 published vacancies; 10,000 stored reports; 100 students for the grade sheet; 50 Locust users | – |
| Invalid inputs | Weights 40/30/20, rejection without a reason, expired and used links, a sixth application, wrong training type, edits after a deadline, disallowed transitions from every state | Each must be refused with its error code |

## 8. Test Environment

| **Part** | **Configuration** |
|:---|:---|
| Development laptops | Windows with Docker Desktop; the whole stack with `docker compose up` (database, API, web app, Mailpit) |
| Backend | Python 3.11, FastAPI; PostgreSQL 16 with pgvector (`pgvector/pgvector:pg16`) and `pg_trgm`; a separate test database `internsync_test` |
| Frontend | Node 22, React 18, Vite, TypeScript strict |
| Browsers | Chromium and WebKit (Playwright), Firefox in CI; phone sizes Pixel 7 and iPhone 14; widths 360, 768, 1366, and 1920 px |
| CI | GitHub Actions on Ubuntu: lint, backend tests with a PostgreSQL service container, OpenAPI and client checks, frontend tests and build, dependency audits, and browser tests against the Docker stack on its own database (`docker-compose.check.yml`) |
| Email | Mailpit catches every email (inbox on port 8025) |
| AI model | `intfloat/multilingual-e5-small` on CPU; a small stand-in model in the unit tests |
| Release checks | Locust, OWASP ZAP (Docker), pip-audit, npm audit |
| Hosted system (after switch-on) | Vercel, a Hugging Face Space, Supabase, Gmail SMTP, for the checks of Section 4 |

## 9. Responsibilities and Schedule

### 9.1 Responsibilities

| **Team Member** | **Testing responsibilities** | **Test cases** |
|:---|:---|:---|
| Salam Alsaour (Team Leader) | Test strategy and integration; CI; tests of reports, the report workflow, grades, and similarity; reviews every test pull request | TC-23 – TC-28, TC-31 – TC-35, NF-04, NF-12, NF-13 |
| Khalid Alajmi | Tests of authentication, access control, the permission matrix, organizations and verification, vacancies, applications, and placements | TC-01 – TC-10, TC-16 – TC-18, NF-06 |
| Ali Alghafly | Frontend tests: translation keys, both languages and directions, offline mode, browser tests on all engines and sizes | TC-40, TC-41, NF-08 |
| Ahmed Kanaan | AI tests and evaluation (skill extraction, matching, held-out sets); load test; checks on the hosted system after the switch-on | TC-14, TC-15, TC-19 – TC-22, NF-01 – NF-03, NF-11 |
| Abdullah Abalhareth | QA lead: this STS, the acceptance tests of each increment, cycles, CV checks, attendance, evaluations, notifications, exports, certificates, audit, and privacy; the security scan; the defect log; organizes the UAT | TC-11 – TC-13, TC-29, TC-30, TC-36 – TC-39, TC-42, TC-43, NF-07 |
| Rakan Alzahrani | Usability and accessibility: the accessibility check, the Arabic PDF layout, the UAT scenario cards and sessions, the device check on phones | NF-09, NF-10, the UAT scenarios |

### 9.2 Schedule

| **Activity** | **Dates** | **Status** |
|:---|:--:|:---|
| Acceptance tests written for Increment 1 (with the requirements) | Oct 16 – 23, 2026 | Done |
| Increment 1 test run and M3 dry run | Oct 24, 2026 | Done (43 of 43) |
| Increment 2 test run, AI tuning sets | Oct 26, 2026 | Done (27 of 27) |
| Increment 3 test run, similarity evaluation | Oct 27, 2026 | Done (21 of 21) |
| Increment 4 release checks: browser tests, ZAP, load test, held-out AI sets | Oct 28, 2026 | Done (12 of 13) |
| Increment 5 regression | Oct 29, 2026 | Done |
| Regression on every pull request | Continuous | Running in CI |
| Milestone demos M3, M4, M5 | Nov 1, Nov 15, Nov 25, 2026 | Planned |
| User acceptance testing with at least 8 participants, and the device check on phones | By Dec 10, 2026 (M6) | Postponed on Oct 29; to be scheduled |
| Checks on the hosted system: uptime, HTTPS, load test repeated | After the switch-on, before Dec 10, 2026 | Waiting for the owner's accounts |
| Final regression before the demonstration | Dec 14 – 15, 2026 (M7) | Planned |

## 10. Deliverables

| **Deliverable** | **Where** |
|:---|:---|
| Test cases document | This STS; the acceptance tests in Section 6 of each increment's requirements document |
| Automated test suites | `backend/tests` (202 tests and the permission matrix), `frontend/src/**/*.test.ts` (19 tests), `frontend/e2e` (browser tests), `backend/loadtest`, `ai-eval` |
| Test execution reports | The test report of each increment (`docs/Increments/Increment_N/04_Test_Report.md`) and the key results |
| Defect log | Section "Defects Found and Fixed" of each test report: 8, 9, 8, 7, and 3 defects in Increments 1 to 5, each with how it was found and its fix |
| UAT materials | The UAT plan with the consent text, scenario cards for the five roles, the result sheet, and the device check |
| Security and load evidence | ZAP reports (kept 30 days as workflow artifacts), the Locust run, the dependency audits in CI |
| Traceability | The requirements status: 125 requirements, 90 with an automated test named after them, 32 with a recorded result, 3 open |

## 11. Appendices

### 11.1 Glossary

| **Term** | **Meaning** |
|:---|:---|
| Acceptance test (AT) | A test that checks one requirement's acceptance criterion; named `AT-<area>-<number>` |
| Regression testing | Running the existing tests again after a change to make sure nothing that worked is broken |
| Test stub | A simple stand-in for a part of the system that is not under test, such as the push sender used in the tests |
| Mock data | Made-up data with the shape of real data; InternSync uses only synthetic data |
| Fixture | Data and set-up prepared before a test, such as the two universities and two companies |
| Permission matrix | The table of every endpoint with the callers allowed past its role gates; tested for every other caller |
| End-to-end (E2E) test | A test that drives the app in a real browser, from the screen to the database |
| Held-out set | Test data kept aside and used once, after the settings were chosen, so the result is not tuned to it |
| Coverage | The share of the code run by the tests |
| Load test | A test with many simulated users at once to measure response times |
| Idempotent | Running it twice has the same effect as running it once |
| UAT | User acceptance testing: real users try the main tasks with scenario cards |

### 11.2 Acceptance Tests and Results

The table lists every acceptance test with its requirement, its scenario and expected result, its level, and its latest result. Levels: *Unit* checks one function; *API* calls the HTTP API with a test database; *E2E* drives the browser; *Eval* runs the AI evaluation; *Load* and *Scan* are the release checks.

<!-- acceptance-table -->

**Table 11.1 – The 102 acceptance tests and their latest results**

| **Test** | **Requirement** | **Scenario and expected result** | **Level** | **Result** |
|:---|:---|:---|:---|:---|
| AT-AUT-01 | FR-AUT-01 | A user of each role logs in and receives only that role's menu; a Company Admin also gets the team menu | API, E2E | Pass |
| AT-AUT-02 | FR-AUT-02 | Registration offered only for student, coordinator, company; confirmation and invitation links work once; used or expired link rejected | API | Pass |
| AT-AUT-03 | FR-AUT-03 | After 30 idle minutes the next request returns 401; after logout the old token is rejected | API | Pass |
| AT-AUT-04 | FR-AUT-04 | Reset link works once; old password fails afterwards; expired link rejected | API | Pass |
| AT-AUT-05 | FR-AUT-05 | Permission matrix test: every Increment 1 endpoint × every role, with 2 colleges and 2 companies; 0 failures, no access across organizations | API | Pass |
| AT-AUT-06 | FR-AUT-06 | Deactivated user cannot log in; past records still visible; a Coordinator cannot deactivate a user of another college | API | Pass |
| AT-ORG-01 | FR-ORG-01 | A new college appears in the registration options; a deactivated college does not | API | Pass |
| AT-ORG-02 | FR-ORG-02 | Unverified student cannot apply; unverified coordinator sees no student; unverified company cannot create a vacancy | API | Pass |
| AT-ORG-03 | FR-ORG-03 | Second coordinator registration for a college refused; rejection without reason refused | API | Pass |
| AT-ORG-04 | FR-ORG-04 | Duplicate commercial registration number refused; before approval no vacancy and no invitation | API | Pass |
| AT-ORG-05 | FR-ORG-05 | After approval the student is enrolled and can apply; rejection without reason refused; another college's coordinator cannot see the request | API | Pass |
| AT-ORG-06 | FR-ORG-06 | Invited academic supervisor belongs to the inviting coordinator's college; used or expired invitation rejected | API | Pass |
| AT-ORG-08 | FR-ORG-08 | Another coordinator gets 403 on the document; after the purge job (clock set 31 days ahead) the file returns 410 and the decision remains | API | Pass |
| AT-ORG-09 | FR-ORG-09 (stretch) | After a rejection a new request is accepted; the reviewer sees the earlier decision | API | Pass |
| AT-CYC-01 | FR-CYC-01 | A 12-week cycle generates 12 weekly deadlines on the configured weekday and time; scheduled days equal the working days | Unit, API | Pass |
| AT-CYC-02 | FR-CYC-02 | Weights 40/30/20 refused; 40/30/30 saved | API | Pass |
| AT-CYC-03 | FR-CYC-03 | With the lock timestamp set, editing the rubric is refused | API | Pass |
| AT-CYC-04 | FR-CYC-04 | Skill with synonym "JS" is recognized in a CV containing "JS" and shown as "JavaScript" | Unit, API | Pass |
| AT-CYC-05 | FR-CYC-05 (stretch) | Edit in a closed cycle refused; reopening without reason refused | API | Pass |
| AT-PRF-02 | FR-PRF-02 | After verification the student edits skills and interests but not student number, major, or GPA | API | Pass |
| AT-PRF-03 | FR-PRF-03 | 6 MB file or other type refused; second upload keeps both versions | API | Pass |
| AT-PRF-04 | FR-PRF-04 | Sample Arabic and English CVs produce a non-empty candidate list; only confirmed skills are stored as profile skills | Unit, API | Pass |
| AT-PRF-05 | FR-PRF-05 | Image-only PDF shows the message and an empty editable list | API, E2E | Pass |
| AT-VAC-01 | FR-VAC-01 | Missing required field cannot be saved; saved vacancy shows all fields; unverified company refused | API | Pass |
| AT-VAC-02 | FR-VAC-02 | Draft invisible to students; vacancy targeted at university A visible to A's students only | API | Pass |
| AT-VAC-03 | FR-VAC-03 | Each filter returns only matching vacancies on seeded data | API | Pass |
| AT-VAC-04 | FR-VAC-04 | Duplicate, after-deadline, wrong-training-type (CR-06), and sixth active applications each refused with a message | API | Pass |
| AT-VAC-05 | FR-VAC-05 (stretch) | Withdrawn application leaves the list and frees a slot | API | Pass |
| AT-VAC-06 | FR-VAC-06 | Supervisor sees own vacancies' applicants only; Company Admin sees the company's; decision visible to student and coordinator | API | Pass |
| AT-VAC-07 | FR-VAC-07 | Second placement for the student refused; filling the last seat closes the vacancy; other active applications withdrawn | API | Pass |
| AT-VAC-08 | FR-VAC-08 (stretch) | Change or cancel without reason refused; change in the audit log | API | Pass |
| AT-REP-01 | FR-REP-01 | Placement in a 12-week cycle has 12 weekly slots and 1 final slot with correct deadlines | API | Pass |
| AT-REP-02 | FR-REP-02 | Fourth attachment or 11 MB file refused; valid submission stored with its files | API | Pass |
| AT-REP-03 | FR-REP-03 | Editing after submission refused; supervisors cannot see drafts | API | Pass |
| AT-REP-04 | FR-REP-04, NFR-L10N-02 | Submissions 1 minute before and after the deadline flagged On time and Late; empty slot Missing within 1 hour after the deadline (job run) | Unit, API | Pass |
| AT-REP-05 | FR-REP-05 | Revision request without comment refused; after resubmission both versions viewable | API | Pass |
| AT-REP-06 | FR-REP-06 | Comment visible to the other party with author and time; company supervisor read-only | API | Pass |
| AT-REP-07 | FR-REP-07 | After closing, the student cannot submit to that slot | API | Pass |
| AT-WFL-01 | FR-WFL-01 | Every allowed report transition passes; at least one disallowed transition from each state is rejected | Unit | Pass |
| AT-LOC-01 | FR-LOC-01 | Switching language mirrors every Increment 1 screen; the choice is saved per user | E2E | Pass |
| AT-LOC-02 | FR-LOC-02 | Automated check finds no missing translation key in either language | Unit | Pass |
| AT-AUD-01 | FR-AUD-01 | Each action of the demo script produces exactly one matching audit entry | API | Pass |
| AT-AUD-02 | FR-AUD-02 | No endpoint updates or deletes audit entries; filters return the right entries | API | Pass |
| AT-MAT-01 | FR-MAT-01 | Ranking holds only eligible vacancies in descending fit; on the labelled set a relevant vacancy is in the top 5 for at least 80% of the profiles | API, Eval | Pass |
| AT-MAT-02 | FR-MAT-02 | Of two otherwise identical vacancies, the one whose required skills the student has scores higher | Unit | Pass |
| AT-MAT-03 | FR-MAT-03 | A vacancy whose minimum GPA is above the student's GPA is absent from the ranking and shows "GPA below minimum" when browsing | API | Pass |
| AT-MAT-04 | FR-MAT-04 | With the model off, the ranking is returned within 5 s and labelled basic | API, Unit | Pass |
| AT-MAT-05 | FR-MAT-05 | Matched and missing skills equal the set comparison of confirmed and required skills | Unit, API | Pass |
| AT-MAT-07 | FR-MAT-07 | The student can apply to the lowest-ranked eligible vacancy; ranking changes no application | API | Pass |
| AT-ATT-01 | FR-ATT-01 | "Full attendance" records attended days equal to scheduled days in one action; more days than scheduled is refused | API | Pass |
| AT-ATT-02 | FR-ATT-02 | An edit on day 8 after the week is refused until the coordinator unlocks the week; the unlock is in the audit log | API | Pass |
| AT-ATT-03 | FR-ATT-03 | The percentage equals attended ÷ scheduled days for seeded data; each role sees only its placements | API | Pass |
| AT-ATT-04 | FR-ATT-04 | A seeded unrecorded week appears on the company supervisor's dashboard on day 4, not on day 3 | API | Pass |
| AT-EVL-01 | FR-EVL-01 | Submitting with an unrated criterion or an empty comment is refused | API | Pass |
| AT-EVL-02 | FR-EVL-02 | A score for a criterion of another cycle is refused; every evaluation of a test cycle uses that cycle's criteria | API | Pass |
| AT-EVL-03 | FR-EVL-03 | The student sees the periodic evaluation at once and the final evaluation only when the grade is Final | API | Pass |
| AT-EVL-04 | FR-EVL-04 | Editing a submitted evaluation is refused; the coordinator reopens it once with a reason, which is audited; a second reopening is refused | API | Pass |
| AT-WFL-02 | FR-WFL-02 | For seeded inputs the computed grade equals a hand calculation to two decimals | Unit, API | Pass |
| AT-WFL-03 | FR-WFL-03 | Submitting with any precondition unmet is refused with the list of missing items | API | Pass |
| AT-WFL-04 | FR-WFL-04 | Returning without a comment is refused; approval sets Final with a timestamp and completes the placement | API | Pass |
| AT-WFL-05 | FR-WFL-05 | Editing a Final grade is refused; reopening without a reason is refused; reopening is audited | API | Pass |
| AT-WFL-06 | FR-WFL-06 | The student's grade view is hidden in Draft and Submitted and shown when Final | API | Pass |
| AT-WFL-07 | FR-WFL-07 | A bulk approval of 10 grades creates 10 audit entries | API | Pass |
| AT-DSH-01 | FR-DSH-01 | For a seeded scenario, every dashboard count of every role equals the pending items in the database | API | Pass |
| AT-DSH-02 | FR-DSH-02 | Every cycle figure, overall and per company, equals the value computed from seeded data | API | Pass |
| AT-DSH-05 | FR-DSH-05 | Every platform figure equals the seeded value; no report, evaluation, or grade is reachable by the Platform Admin | API | Pass |
| AT-PER-02 | NFR-PER-02 | 1,000 open vacancies: 95th percentile of 20 ranking requests ≤ 5 s, semantic and basic | API (timed) | Pass |
| AT-AI-02 | NFR-AI-02 | Each stored fit score and each application snapshot has the model version | API | Pass |
| AT-AI-03 | NFR-AI-03 | The held-out sets give their numbers in one run with the frozen settings; targets: at least 9 of 10 copied flagged and at most 1 of 10 originals flagged; a relevant vacancy in the top 5 for at least 80% of profiles | Eval | Matching met; similarity **not met** |
| AT-LOC-03 | NFR-L10N-01, FR-LOC-02 | The translation-key check passes with the new screens; each new screen checked in both languages | Unit, Demo | Pass |
| AT-SIM-01 | FR-SIM-01 | A report copied from a previous cycle's report of the same university is flagged; the same text stored at another university is not compared; earlier versions of the same report are not sources | API | Pass |
| AT-SIM-02 | FR-SIM-02 | Of 10 reports with 40% or more copied text, at least 9 are flagged with passages; at most 1 of 10 original reports is flagged. The academic supervisor sees score, cycle, week, and passages, not the author; the author's coordinator sees the author | API, Eval | Pass |
| AT-SIM-03 | FR-SIM-03 | A decision needs a comment and only a flagged check takes one; report status and grade do not change | API | Pass |
| AT-NOT-01 | FR-NOT-01 | Each FR-NOT-05 event creates one in-app notification and one email; the unread count drops when read | API | Pass |
| AT-NOT-02 | FR-NOT-02 | Reminders only for unsubmitted slots due within 24 hours, once each | API | Pass |
| AT-NOT-03 | FR-NOT-03 | Every seeded missing report gives a notice to the student and the academic supervisor within 1 hour | API | Pass |
| AT-NOT-04 | FR-NOT-04 | An escalation for each seeded overdue report, attendance week, and evaluation on day 4, none on day 3, never twice | API | Pass |
| AT-NOT-05 | FR-NOT-05 | Each listed event notifies the right user in a scripted test | API | Pass |
| AT-NOT-06 | FR-NOT-06 | A user with Arabic selected receives the Arabic email and notification text | API | Pass |
| AT-EXP-01 | FR-EXP-01 | Exported values equal stored values in every row of the Excel and PDF grade sheets; Arabic names are present in both | API, Unit | Pass |
| AT-EXP-02 | FR-EXP-02 | The term summary figures equal the dashboard figures | API | Pass |
| AT-EXP-03 | FR-EXP-03 | The training record matches the stored data of a seeded student; another supervisor is refused | API | Pass |
| AT-PWA-01 | FR-PWA-01 | The manifest and service worker meet the browser's install criteria; the app installs in desktop Chrome | Unit, Browser | Pass; the install itself on phones in M6 |
| AT-PWA-02 | FR-PWA-02 | With a subscription the push is sent with only the title and a link; with none the email still goes out; a gone subscription is deleted | API | Pass; a real push on a device in M6 |
| AT-PWA-03 | FR-PWA-03 (CR-10) | Offline: a page opened before shows its saved copy with the time; a page never opened shows that it is not saved; a report draft typed offline is saved after the connection returns; submit buttons stay disabled; after sign-out nothing is left in session storage and no draft is left | E2E, Browser | Pass |
| AT-AUD-03 | FR-AUD-03 | The history shown for a report, an evaluation, and a grade equals their audit entries; other users are refused | API | Pass |
| AT-ORG-07 | FR-ORG-07 | After a transfer the previous holder loses the rights and the new one has them; a reason is required; the transfer is in the audit log; both are notified | API | Pass |
| AT-PER-04 | NFR-PER-04 | With 10,000 stored reports the similarity result is ready within 2 minutes | API (timed) | Pass |
| AT-PER-05 | NFR-PER-05 | 100-student grade sheet in Excel and PDF in under 60 s each | API (timed) | Pass |
| AT-REL-03 | NFR-REL-03 | Running each job twice sends nothing twice; after a simulated downtime the next run catches up | API | Pass |
| AT-L10N-03 | NFR-L10N-03 | The exported PDF embeds the Arabic font and its text holds the shaped Arabic names; checked visually | Unit, Browser | Pass |
| AT-CER-01 | FR-CER-01 | A certificate cannot be issued for a grade that is not Final; issued for a Final grade, it has a 26-character code, and its PDF holds the code and a QR code that opens `/verify/<code>`; a second valid certificate for the same placement is refused | API, Unit | Pass |
| AT-CER-02 | FR-CER-02 | Without login, a valid code shows Valid with the listed fields and no grade; a revoked code shows Revoked; an altered code shows Not found | API, E2E | Pass |
| AT-CER-03 | FR-CER-03 | Revoking needs a reason and is audited; after it the page shows Revoked, and a new certificate can be issued | API | Pass |
| AT-EVL-05 | FR-EVL-05 | The student evaluates the company once, only after the training end date or a Final grade; the coordinator sees it and the averages per company; a company supervisor and a Company Admin are refused | API | Pass |
| AT-DSH-03 | FR-DSH-03 | With seeded answers, the job-offer rate equals Yes answers ÷ survey answers, per cycle and per company; a student who skipped is not counted | API | Pass |
| AT-DSH-04 | FR-DSH-04 | A company with 5 final evaluations averaging 4.8 against a cycle mean of 3.6 raises the alert; a company with 4 evaluations does not; the alert changes nothing else | API | Pass |
| AT-PRV-04 | NFR-PRV-04 | Before the retention period ends, anonymizing is refused; after it, no name, email, student number, CV, report text, or certificate file of the cycle can be retrieved, students still in another active cycle are skipped, and the cycle statistics are unchanged | API | Pass |
| AT-SEC-05 | NFR-SEC-05 | ZAP baseline with no high-risk finding; pip-audit and npm audit with no critical finding | Scan | Pass |
| AT-PER-01 | NFR-PER-01 | 50 users: 95th percentile of ordinary requests under 2 s | Load | Pass on the local stack |
| AT-PRT-01 | NFR-PRT-01, NFR-USA-03 | The browser tests pass on the three engines and at 360, 768, 1366, and 1920 px without horizontal scrolling | E2E | Pass; Firefox in CI, real phones in the UAT |
| AT-USA-04 | NFR-USA-04 | The accessibility check finds no contrast failure on the main pages; the main tasks can be done with the keyboard | E2E, Browser | Pass |

<!-- /acceptance-table -->

### 11.3 References

1. IEEE Std 829-1998, *IEEE Standard for Software Test Documentation*, IEEE Computer Society, 1998.
2. IEEE Std 1016-1998, *IEEE Recommended Practice for Software Design Descriptions*, IEEE Computer Society, 1998.
3. I. Sommerville, *Software Engineering*, 10th ed., Pearson, 2016.
4. Group 3, *InternSync – Software Requirements Specification*, version 1.6, Oct 28, 2026.
5. Group 3, *InternSync – Software Design Description*, version 1.0, Nov 1, 2026.
6. Group 3, *InternSync – Test Reports of Increments 1 to 5* and *Key Results*, Oct 24 – 29, 2026.
