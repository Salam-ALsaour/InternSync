# Increment 1 – Requirements (Scope and Acceptance)

**Status:** Draft for review · Oct 23, 2026 · Author: Salam Alsaour  
**Baseline:** [SRS 1.3](../../RSR/InternSync_SRS.md), [Design 1.2](../../Design/InternSync_Design.md), [API 1.1](../../Design/InternSync_API_Spec.md), [SPMP 1.2](../../Software%20Project%20Management%20Plan%20%28SPMP%29/InternSync_SPMP.md)  
**Milestone:** M3 – Increment 1 delivered, **Nov 1, 2026**: demo of the F1, F2, F3, F5, and F10 foundation; automated tests pass.

## 1. Purpose

This document fixes what Increment 1 delivers before its design starts: the requirements in scope and how far each is committed, the open points in those requirements, the acceptance tests that will prove each one, the demo scenario for M3, and the Definition of Done. It does not add requirements; every item traces to SRS 1.3.

## 2. Process for this Increment

Each phase ends with an artefact in this folder and a review by the project owner. The next phase starts only after approval.

| **Phase** | **Artefact** | **Review gate** | **Planned dates** |
|:---|:---|:---|:---|
| 1. Requirements | `01_Requirements.md` (this document) | Scope, decisions in Section 5, acceptance tests | Oct 23 |
| 2. Design | `02_Design.md`: increment-level design (modules, tables, endpoints, screens, test design) refined from Design 1.2 | Design review | Oct 24 |
| 3. Implementation | Code in feature branches merged by pull request, CI green | Review of each pull request | Oct 25 – Oct 30 |
| 4. Testing | `04_Test_Report.md`: results of the acceptance tests and the demo dry run | Test report review; M3 demo | Oct 31 – Nov 1 |

The increment starts 8 days late (planned Oct 16) because M2 closed on Oct 23 after CR-05. Nine working days remain, so the scope in Section 4 separates committed work from stretch work.

## 3. Use Cases Covered

| **Use case** | **Increment 1 coverage** |
|:---|:---|
| UC-01 Open a training cycle | Full, except closing and reopening a cycle (FR-CYC-05, stretch) |
| UC-02 Register, confirm email, log in, reset password | Full |
| UC-03 Build profile and confirm CV skills | Full |
| UC-04 Publish a vacancy | Full |
| UC-05 View ranked vacancies and apply | Browse, filter, and apply. Ranking and explanation come in Increment 2 (FR-MAT) |
| UC-06 Review applicants and confirm placement | Full, except changing the academic supervisor or cancelling (FR-VAC-08, stretch) |
| UC-07 Submit a weekly or final report | Full |
| UC-08 Review a report and check similarity | Review, comments, revision, close as Missing. Similarity comes in Increment 3 (FR-SIM) |
| UC-15 Send reminders, late flags, and escalations | Missing flag only (FR-REP-04). Reminders and escalations come in Increment 3 (FR-NOT) |
| UC-16 Verify a coordinator or a company | Full, except the role transfer (FR-ORG-07, deferred) |
| UC-17 Verify a student and enrol them in a cycle | Full |
| UC-18 Invite and manage academic supervisors | Full |
| UC-19 Invite and manage company supervisors | Full |
| UC-20 Manage universities, colleges, and the skill vocabulary | Full, except the platform dashboard (FR-DSH-05, Increment 2) |

UC-09 – UC-14 belong to later increments.

## 4. Requirements in Scope

**Commitment:** *Committed* – delivered and demonstrated at M3. *Stretch* – built at the end of the increment if the committed work is done; otherwise moved to Increment 3. *Deferred* – moved to Increment 3 now (needs approval, Section 5).

### 4.1 Functional Requirements

| **ID** | **Requirement (short)** | **Priority** | **Commitment** |
|:---|:---|:--:|:--:|
| FR-AUT-01 | Five roles, one role per account; Company Admin right | Must | Committed |
| FR-AUT-02 | Self-registration for three roles; invitations; one-time links valid 72 h | Must | Committed |
| FR-AUT-03 | Login; session ends after 30 idle minutes; logout | Must | Committed |
| FR-AUT-04 | Password reset by one-time link valid 60 min | Must | Committed |
| FR-AUT-05 | Permission matrix enforced on the server for every request | Must | Committed (all Increment 1 endpoints) |
| FR-AUT-06 | Deactivate and reactivate accounts and organizations | Must | Committed |
| FR-ORG-01 | Universities and colleges maintained by the Platform Admin | Must | Committed |
| FR-ORG-02 | Registration; unverified accounts limited to their status page (students may also edit their profile and browse) | Must | Committed |
| FR-ORG-03 | Coordinator registration and verification; one Coordinator per college | Must | Committed |
| FR-ORG-04 | Company registration and verification; Company Admin | Must | Committed |
| FR-ORG-05 | Student registration, verification, and enrolment by the Coordinator | Must | Committed |
| FR-ORG-06 | Invitations of academic and company supervisors | Must | Committed |
| FR-ORG-07 | Transfer of the Coordinator role or the Company Admin right | Should | **Deferred** to Increment 3 |
| FR-ORG-08 | Verification documents visible only to uploader and reviewer; purged 30 days after the decision | Must | Committed |
| FR-ORG-09 | New request after a rejection; history kept | Should | Stretch |
| FR-CYC-01 | Training cycle with weeks, working days, and deadlines | Must | Committed |
| FR-CYC-02 | Grade components with weights summing to 100% | Must | Committed |
| FR-CYC-03 | One rubric per cycle; read-only after the first evaluation | Must | Committed (the lock is triggered by evaluations, which arrive in Increment 2; the rule and its test are built now) |
| FR-CYC-04 | Skill vocabulary maintained by the Platform Admin | Must | Committed (seeded with about 150 skills; list, add, and edit) |
| FR-CYC-05 | Close and reopen a cycle with a reason | Should | Stretch |
| FR-PRF-02 | Student profile; academic data read-only after verification | Must | Committed |
| FR-PRF-03 | CV upload (PDF or DOCX, 5 MB) with version history | Must | Committed |
| FR-PRF-04 | Skill extraction from the CV and confirmation by the student | Must | Committed (accuracy target measured in Increment 2, Section 5, RQ-4) |
| FR-PRF-05 | CV without extractable text: message and manual entry | Must | Committed |
| FR-VAC-01 | Vacancy creation by a verified company | Must | Committed |
| FR-VAC-02 | Draft, Published, Closed; direct publishing; target universities | Must | Committed |
| FR-VAC-03 | Browse, search, and filter vacancies open to the student's university | Must | Committed |
| FR-VAC-04 | Apply: eligibility, deadline, no duplicates, at most 5 active | Must | Committed |
| FR-VAC-05 | Withdraw an undecided application | Should | Stretch |
| FR-VAC-06 | Review applicants; accept or decline | Must | Committed |
| FR-VAC-07 | Confirm placement; one per cycle; auto-close on last seat | Must | Committed |
| FR-VAC-08 | Change the academic supervisor or cancel a placement with a reason | Should | Stretch |
| FR-REP-01 | Weekly and final report slots per placement | Must | Committed |
| FR-REP-02 | Report content and up to 3 attachments (10 MB each) | Must | Committed |
| FR-REP-03 | Draft; read-only after submission | Must | Committed |
| FR-REP-04 | Server time; Late and Missing flags | Must | Committed |
| FR-REP-05 | Accept or request a revision with a comment; versions kept | Must | Committed |
| FR-REP-06 | Comments between student and academic supervisor; company supervisor reads | Must | Committed |
| FR-REP-07 | Close an empty slot as Missing | Must | Committed |
| FR-WFL-01 | Report state machine; any other transition rejected | Must | Committed (**pulled forward** from Increment 2: the report screens cannot work without it) |
| FR-LOC-01 | Arabic and English, right-to-left and left-to-right, saved per user | Must | Committed |
| FR-LOC-02 | All interface, validation, and email text in both languages | Must | Committed |
| FR-AUD-01 | Audit entry for every creation, change, and transition | Must | Committed |
| FR-AUD-02 | Audit log append-only; filters for the Coordinator and the Platform Admin | Must | Committed (screen for the Coordinator; the Platform Admin filter through the API, its screen is stretch) |

**Totals:** 44 requirements – 39 Must (all committed) and 5 Should (4 stretch, 1 deferred). FR-WFL-01 is pulled forward; everything else follows SRS Table 6.4.

**Supporting work that is not a requirement but is needed:** a role home page with navigation (the real dashboards with counts are FR-DSH-01 – 02 in Increment 2); a seed script with the Platform Admin, 2 universities, 4 colleges, majors, the skill vocabulary, and demo companies (Design Section 10); a command that creates a Platform Admin (FR-AUT-02: only the provider creates them); a job runner that runs the Missing-flag job and the document-purge job.

### 4.2 Non-Functional Requirements Checked at M3

Must non-functional requirements are checked at every increment demo (SRS 6.3.3). For Increment 1 these apply:

| **ID** | **What is checked at M3** |
|:---|:---|
| NFR-SEC-02 | Argon2id hashes only; a weak password is refused |
| NFR-SEC-03 | Lock for 15 minutes after 5 failed logins |
| NFR-SEC-04 | File type checked by content; files outside the web root; 403 without permission |
| NFR-PRV-01 | Consent notice at first login, acknowledgement time stored |
| NFR-PRV-02 | Skill extraction runs locally; no external AI call |
| NFR-PRV-03 | Each role sees only its data; the Platform Admin sees no CV or report |
| NFR-REL-04 | A report with a failing attachment is not submitted; the draft is kept |
| NFR-L10N-01 | Every Increment 1 screen in Arabic and English with the right direction |
| NFR-L10N-02 | Deadlines in Saudi Arabia time; 23:58 on time, 00:00 late |
| NFR-MNT-01 | CI runs the tests on every pull request; at least 70% line coverage of the business-logic modules |
| NFR-MNT-02 | OpenAPI generated by the server; frontend client generated from it |
| NFR-MNT-03 | Increment 1 defaults (link validity, session timeout, application limit, file sizes, purge days) read from settings |
| NFR-PRT-02 | The whole system starts with one `docker compose up` |
| NFR-USA-03 | Increment 1 screens usable from 360 px to 1920 px wide |

NFR-SEC-01 (HTTPS) and NFR-PRT-01 (browsers) are checked once the system is deployed (Section 5, RQ-7). Performance (NFR-PER) is measured in the testing phase.

## 5. Decisions Needed

Requirement analysis for this increment found the points below. Each has a recommendation; **R** marks a change to the SRS (a change request), **C** a clarification only.

| **ID** | **Point** | **Recommendation** | **Type** |
|:---|:---|:---|:--:|
| RQ-1 | **Training type is not part of eligibility.** A student enrolled in a Summer cycle could apply to a Co-op vacancy (FR-VAC-04, FR-MAT-03, Design 4.4). | Add to eligibility: the vacancy's training type equals the type of the student's cycle. Browsing still shows the other vacancies with the reason. | R (CR-06) |
| RQ-2 | **Student registers when the college has no open cycle.** FR-ORG-05 requires enrolment in an open cycle at approval. | The request stays pending and the Coordinator sees "no open cycle"; approval is possible once a cycle is opened. | C |
| RQ-3 | **Missing flag needs a scheduled job,** while scheduled notifications (F13) are in Increment 3. | Build the job runner now with two jobs only: Missing flags (FR-REP-04) and document purge (FR-ORG-08). Reminders and escalations stay in Increment 3. | C |
| RQ-4 | **FR-PRF-04 target (70% on 20 labelled CVs)** needs the labelled set, which is planned for Increment 2 (Design Section 10). | Increment 1 proves the function on sample CVs; the 70% measurement is reported at M4. | C |
| RQ-5 | **Which company supervisor gets the placement** (FR-VAC-07). | Default: the owner of the vacancy; the Coordinator may choose another active supervisor of the same company. | C |
| RQ-6 | **Scope versus time.** Nine days remain for 44 requirements. | Defer FR-ORG-07 to Increment 3 (already named in the SPMP risk); keep FR-ORG-09, FR-CYC-05, FR-VAC-05, FR-VAC-08 as stretch. | C (plan) |
| RQ-7 | **Where the M3 demo runs.** Deployment to the free tiers needs accounts that only the owner can create (Gmail, Hugging Face, Supabase, Vercel). | Demo M3 on Docker Compose (emails caught by Mailpit). Deploy to the free tiers in the first days of Increment 2, after the accounts exist. | C (plan) |

## 6. Acceptance Tests

Each test comes from the SRS acceptance criterion of its requirement and will be automated at the level shown. *API* tests call the HTTP API against a test database; *E2E* tests drive the browser; *Unit* tests check one function; *Demo* items are checked by hand in the M3 dry run.

| **Test** | **Requirement** | **Scenario and expected result** | **Level** |
|:---|:---|:---|:--:|
| AT-AUT-01 | FR-AUT-01 | A user of each role logs in and receives only that role's menu; a Company Admin also gets the team menu | API, E2E |
| AT-AUT-02 | FR-AUT-02 | Registration offered only for student, coordinator, company; confirmation and invitation links work once; used or expired link rejected | API |
| AT-AUT-03 | FR-AUT-03 | After 30 idle minutes the next request returns 401; after logout the old token is rejected | API |
| AT-AUT-04 | FR-AUT-04 | Reset link works once; old password fails afterwards; expired link rejected | API |
| AT-AUT-05 | FR-AUT-05 | Permission matrix test: every Increment 1 endpoint × every role, with 2 colleges and 2 companies; 0 failures, no access across organizations | API |
| AT-AUT-06 | FR-AUT-06 | Deactivated user cannot log in; past records still visible; a Coordinator cannot deactivate a user of another college | API |
| AT-ORG-01 | FR-ORG-01 | A new college appears in the registration options; a deactivated college does not | API |
| AT-ORG-02 | FR-ORG-02 | Unverified student cannot apply; unverified coordinator sees no student; unverified company cannot create a vacancy | API |
| AT-ORG-03 | FR-ORG-03 | Second coordinator registration for a college refused; rejection without reason refused | API |
| AT-ORG-04 | FR-ORG-04 | Duplicate commercial registration number refused; before approval no vacancy and no invitation | API |
| AT-ORG-05 | FR-ORG-05 | After approval the student is enrolled and can apply; rejection without reason refused; another college's coordinator cannot see the request | API |
| AT-ORG-06 | FR-ORG-06 | Invited academic supervisor belongs to the inviting coordinator's college; used or expired invitation rejected | API |
| AT-ORG-08 | FR-ORG-08 | Another coordinator gets 403 on the document; after the purge job (clock set 31 days ahead) the file returns 410 and the decision remains | API |
| AT-ORG-09 | FR-ORG-09 (stretch) | After a rejection a new request is accepted; the reviewer sees the earlier decision | API |
| AT-CYC-01 | FR-CYC-01 | A 12-week cycle generates 12 weekly deadlines on the configured weekday and time; scheduled days equal the working days | Unit, API |
| AT-CYC-02 | FR-CYC-02 | Weights 40/30/20 refused; 40/30/30 saved | API |
| AT-CYC-03 | FR-CYC-03 | With the lock timestamp set, editing the rubric is refused | API |
| AT-CYC-04 | FR-CYC-04 | Skill with synonym "JS" is recognized in a CV containing "JS" and shown as "JavaScript" | Unit, API |
| AT-CYC-05 | FR-CYC-05 (stretch) | Edit in a closed cycle refused; reopening without reason refused | API |
| AT-PRF-02 | FR-PRF-02 | After verification the student edits skills and interests but not student number, major, or GPA | API |
| AT-PRF-03 | FR-PRF-03 | 6 MB file or other type refused; second upload keeps both versions | API |
| AT-PRF-04 | FR-PRF-04 | Sample Arabic and English CVs produce a non-empty candidate list; only confirmed skills are stored as profile skills | Unit, API |
| AT-PRF-05 | FR-PRF-05 | Image-only PDF shows the message and an empty editable list | API, E2E |
| AT-VAC-01 | FR-VAC-01 | Missing required field cannot be saved; saved vacancy shows all fields; unverified company refused | API |
| AT-VAC-02 | FR-VAC-02 | Draft invisible to students; vacancy targeted at university A visible to A's students only | API |
| AT-VAC-03 | FR-VAC-03 | Each filter returns only matching vacancies on seeded data | API |
| AT-VAC-04 | FR-VAC-04 | Duplicate, after-deadline, and sixth active applications each refused with a message | API |
| AT-VAC-05 | FR-VAC-05 (stretch) | Withdrawn application leaves the list and frees a slot | API |
| AT-VAC-06 | FR-VAC-06 | Supervisor sees own vacancies' applicants only; Company Admin sees the company's; decision visible to student and coordinator | API |
| AT-VAC-07 | FR-VAC-07 | Second placement for the student refused; filling the last seat closes the vacancy; other active applications withdrawn | API |
| AT-VAC-08 | FR-VAC-08 (stretch) | Change or cancel without reason refused; change in the audit log | API |
| AT-REP-01 | FR-REP-01 | Placement in a 12-week cycle has 12 weekly slots and 1 final slot with correct deadlines | API |
| AT-REP-02 | FR-REP-02 | Fourth attachment or 11 MB file refused; valid submission stored with its files | API |
| AT-REP-03 | FR-REP-03 | Editing after submission refused; supervisors cannot see drafts | API |
| AT-REP-04 | FR-REP-04, NFR-L10N-02 | Submissions 1 minute before and after the deadline flagged On time and Late; empty slot Missing within 1 hour after the deadline (job run) | Unit, API |
| AT-REP-05 | FR-REP-05 | Revision request without comment refused; after resubmission both versions viewable | API |
| AT-REP-06 | FR-REP-06 | Comment visible to the other party with author and time; company supervisor read-only | API |
| AT-REP-07 | FR-REP-07 | After closing, the student cannot submit to that slot | API |
| AT-WFL-01 | FR-WFL-01 | Every allowed report transition passes; at least one disallowed transition from each state is rejected | Unit |
| AT-LOC-01 | FR-LOC-01 | Switching language mirrors every Increment 1 screen; the choice is saved per user | E2E |
| AT-LOC-02 | FR-LOC-02 | Automated check finds no missing translation key in either language | Unit |
| AT-AUD-01 | FR-AUD-01 | Each action of the demo script produces exactly one matching audit entry | API |
| AT-AUD-02 | FR-AUD-02 | No endpoint updates or deletes audit entries; filters return the right entries | API |

The non-functional checks of Section 4.2 are added to the same suites (security and privacy as API tests, the rest as CI or demo checks).

## 7. M3 Demo Scenario

The demo runs end to end on seeded data and shows every committed function:

1. The Platform Admin logs in (seeded), adds a college to a university, and adds a skill.
2. A coordinator registers for the college with an appointment letter; the Platform Admin approves.
3. The coordinator opens a 12-week Co-op cycle with weights and a rubric, and invites an academic supervisor, who accepts.
4. A company registers with its commercial registration; the Platform Admin approves; the Company Admin invites a colleague and publishes a vacancy targeted at the university.
5. A student registers with a course-registration document, confirms the email, sees the pending status, completes the profile, uploads a CV, and confirms the extracted skills.
6. The coordinator approves the student and enrols them in the cycle; the student browses, filters, and applies.
7. The company supervisor accepts the applicant; the coordinator confirms the placement with the academic supervisor; report slots appear.
8. The student submits week 1 late (clock moved); the academic supervisor requests a revision; the student resubmits; the supervisor accepts; week 2 is closed as Missing.
9. The interface is switched to English and back to Arabic.
10. The coordinator filters the audit log and finds every step above.

## 8. Definition of Done

A requirement is done when:

- its code is merged into `main` through a pull request with CI green (lint, type checks, tests);
- its acceptance test in Section 6 is automated and passes, and its endpoints are in the permission matrix test;
- its screens exist in Arabic and English and follow the wireframes;
- its actions write audit entries (FR-AUD-01);
- the design document, API specification, or SRS are updated if the implementation changed anything.

The increment is done when every committed requirement is done, the demo scenario of Section 7 runs without help, and `04_Test_Report.md` records the results.

## 9. Risks for this Increment

| **Risk** | **Effect** | **Response** |
|:---|:---|:---|
| Nine days for 44 requirements | Committed work not finished by Nov 1 | Stretch items first to go; daily check against Section 4; FR-ORG-07 deferred |
| Frontend volume (about 20 screens in two languages) | UI falls behind the API | Build screens from the wireframes with one component set; Arabic and English strings from day one |
| Skill extraction quality on Arabic CVs | Weak candidate lists | Vocabulary synonyms in both languages; the student always confirms (FR-PRF-04); accuracy measured at M4 |
| Email delivery during the demo | Confirmation and invitation links not received | Mailpit in Docker Compose catches every email for the demo |
