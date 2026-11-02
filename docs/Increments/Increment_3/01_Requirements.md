# Increment 3 – Requirements (Scope and Acceptance)

**Status:** Approved Oct 27, 2026 – the project owner delegated the decisions of Section 5, and the recommendations were adopted · Author: Salam Alsaour  
**Baseline:** [SRS 1.5](../../Project_4_SRS/InternSync_SRS.md), [Design 1.4](../../Design/InternSync_Design.md), [API 1.3](../../Design/InternSync_API_Spec.md), [SPMP 1.4](../../Project_3_SPMP/InternSync_SPMP.md), [Increment 2](../Increment_2/04_Test_Report.md)  
**Milestone:** M5 – Increment 3 delivered, **Nov 25, 2026**: demo of F11–F15; the Should functions pass their tests.

## 1. Purpose

This document fixes what Increment 3 delivers before its design starts: the requirements in scope and how far each is committed, the open points, the acceptance tests, the demo scenario for M5, and the Definition of Done. It adds no requirement; every item traces to SRS 1.5 (Table 6.4), to the SPMP risk plan (FR-ORG-07), or to a follow-up recorded in the Increment 2 test report.

## 2. Process for this Increment

The same four phases as Increments 1 and 2. The project owner asked for the increment to run end to end, with one review at the pull request.

| **Phase** | **Artefact** | **Planned dates** |
|:---|:---|:---|
| 1. Requirements | `01_Requirements.md` (this document) | Oct 27 |
| 2. Design | `02_Design.md`: tables, endpoints, similarity service, notification outbox, exports, PWA, screens, test design | Oct 27 |
| 3. Implementation | Code on branch `increment-3`, CI green | Oct 27 – Nov 18 |
| 4. Testing | `04_Test_Report.md`, the similarity evaluation, and the M5 dry run | Nov 19 – Nov 24 |

The increment starts 20 days ahead of the SPMP plan (Nov 16), because Increments 1 and 2 finished early.

## 3. Use Cases Covered

| **Use case** | **Increment 3 coverage** |
|:---|:---|
| UC-08 Review a report and check similarity | Similarity result, side-by-side passages, the supervisor's decision (the review itself was built in Increment 1) |
| UC-12 Export grade sheets and summaries | Full |
| UC-15 Send reminders, late flags, and escalations | Full (the Missing flag itself was built in Increment 1) |
| UC-16 Verify a coordinator or a company | The role transfer of FR-ORG-07, deferred from Increment 1 |
| All roles | Notification list with unread count, email in the recipient's language, web push, installable app, offline app shell, history of reports, evaluations, and grades |

F11 (match explanation, skill gaps, development plan) was delivered in Increment 2 (CR-08).

## 4. Requirements in Scope

### 4.1 Functional Requirements

| **ID** | **Requirement (short)** | **Priority** | **Commitment** |
|:---|:---|:--:|:--:|
| FR-SIM-01 | Each submitted report compared with all reports of the same university, never another university's | Should | Committed |
| FR-SIM-02 | Flag at the threshold (default 30%); score, source reference, passages side by side; the source author shown only to the author's coordinator | Should | Committed |
| FR-SIM-03 | Advisory: the supervisor records No issue or Overlap confirmed with a comment; nothing else changes | Should | Committed |
| FR-NOT-01 | In-app notification list with unread count; events also by email | Should | Committed |
| FR-NOT-02 | Reminder 24 hours before a report deadline if not submitted | Should | Committed |
| FR-NOT-03 | Missing report notice to the student and the academic supervisor within 1 hour | Should | Committed |
| FR-NOT-04 | Escalation to the coordinator of reports, attendance weeks, and evaluations 3 days overdue | Should | Committed |
| FR-NOT-05 | Notifications for the listed events to the user who must act or whose record changed | Should | Committed |
| FR-NOT-06 | Notifications and emails in the recipient's language | Should | Committed |
| FR-EXP-01 | Grade sheet of a cycle as Excel and PDF | Should | Committed |
| FR-EXP-02 | Term summary PDF with the cycle statistics | Should | Committed |
| FR-EXP-03 | Student training record PDF for the coordinator and the assigned academic supervisor | Should | Committed |
| FR-PWA-01 | Installable as a PWA | Should | Committed |
| FR-PWA-02 | Web push for the FR-NOT-05 events with permission; email as fallback | Should | Committed |
| FR-PWA-03 | Cached app shell: opens offline with a message; no submission offline | Should | Committed |
| FR-AUD-03 | History of each report, evaluation, and grade for the users allowed to view it | Should | Committed |
| FR-ORG-07 | Platform Admin transfers the coordinator role or the Company Admin right, with a reason | Should | Committed (deferred from Increment 1, SPMP risk plan) |

**Totals:** 17 requirements, all Should, all committed.

**Supporting work:**

- **Dashboard items** left for this increment by Increment 2 (its decision RQ-7): flagged similarity checks without a decision for the academic supervisor, escalations for the coordinator.
- **Similarity evaluation set (NFR-AI-03):** 10 reports copied with 40% or more of their text and 10 written independently, in Arabic and English, with `ai-eval/evaluate.py` measuring the flags.
- **Dependency audit (NFR-SEC-05):** `pip-audit` and `npm audit` in CI.
- **Follow-ups from the Increment 2 test report:**
  - Stretch items carried over: Tailwind CSS 4, a backend type checker, and automated browser tests.
  - The harder held-out matching set stays planned for M6.

### 4.2 Non-Functional Requirements Checked at M5

The checks of Increments 1 and 2 are repeated by CI. Added for Increment 3:

| **ID** | **What is checked at M5** |
|:---|:---|
| NFR-PER-04 | Similarity result of a submitted report within 2 minutes with 10,000 stored reports |
| NFR-PER-05 | Grade sheet of a 100-student cohort exported to PDF and to Excel in under 60 s each |
| NFR-REL-03 | Jobs run at least every 15 minutes, never send the same reminder or escalation twice, and catch up after a restart |
| NFR-PRV-03 | Push payloads hold the event title and a link only |
| NFR-L10N-03 | Arabic in PDF exports joined and right to left, with an embedded Arabic font |
| NFR-L10N-04 | Similarity works on Arabic, English, and mixed text |
| NFR-AI-01 | The similarity flag is labelled advisory with its reason; it changes no report status or grade |
| NFR-AI-02 | Model name and version stored with each similarity result |
| NFR-AI-03 | The similarity set and the script reproduce the reported numbers |
| NFR-SEC-05 | Dependency audits report no known critical vulnerability (the ZAP scan is part of the release check in M6) |
| NFR-L10N-01 | Every Increment 3 screen in Arabic and English with the right direction |

FR-PWA-01 asks for installation on Android and iOS. This increment checks installability in desktop Chrome and with the browser's PWA criteria; the phone installs are part of the device smoke test of NFR-PRT-01 in M6.

## 5. Decisions

| **ID** | **Open point** | **Decision (recommended and adopted)** |
|:---|:---|:---|
| RQ-1 | PDF library | Design 5.6 names WeasyPrint, which needs Pango and GTK system libraries that do not install with pip, notably on the Windows machines used for development. Use **fpdf2** with HarfBuzz text shaping (`uharfbuzz`), which joins Arabic letters and orders right-to-left text, with the Noto Naskh Arabic and Noto Sans fonts bundled (SIL Open Font License). Pure pip installs on every platform. Recorded as a change request with the design |
| RQ-2 | When the similarity check runs | Right after the submission is saved, in a background thread of the API, so the student does not wait. The `similarity_retry` job runs checks that are still pending or failed, so a restart or a missing model never loses one |
| RQ-3 | How notifications are delivered | Every event writes one row to `notifications` in the same transaction as the change (the outbox of Design 4.3.8); the `deliver_notifications` job sends the email and the push. The account emails of Increment 1 (confirmation, invitation, reset) stay direct, because the user is waiting for them |
| RQ-4 | Web push keys | VAPID keys from the environment (`VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_SUBJECT`); without them, push is marked skipped and email still goes out. A command generates a key pair for the deployment |
| RQ-5 | Service worker | A small hand-written service worker: cached app shell and static files, network first for pages, no caching of API answers (personal data stays off the device). No build plugin, so the Vite version does not constrain it |
| RQ-6 | Similarity evaluation set | 20 synthetic reports (10 copied, 10 original), written and labelled by the author, as for the matching set (Increment 2, RQ-4); the test report says so |
| RQ-7 | Reports of other universities | The search is filtered by `university_id` stored on each passage, and a test seeds the same text at another university to prove it is never compared |
| RQ-8 | Escalation and reminder windows | As Design 5.3: reminders for slots due within 24 hours, Missing notices at the deadline job, escalations at 3 days, all keyed by idempotency keys so no message is sent twice |
| RQ-9 | Dependency audit in CI | `pip-audit` on `requirements.txt` and `requirements-ai.txt`, `npm audit --omit=dev` with level `critical`; both fail the build only on critical findings |

## 6. Acceptance Tests

Each test comes from the SRS acceptance criterion of its requirement. *API* tests run against a test database; *Unit* tests check one function; *Eval* runs the evaluation script; *Browser* items are checked by hand in the running app.

| **Test** | **Requirement** | **Scenario and expected result** | **Level** |
|:---|:---|:---|:--:|
| AT-SIM-01 | FR-SIM-01 | A report copied from a previous cycle's report of the same university is flagged; the same text stored at another university is not compared; earlier versions of the same report are not sources | API |
| AT-SIM-02 | FR-SIM-02 | Of 10 reports with 40% or more copied text, at least 9 are flagged with passages; at most 1 of 10 original reports is flagged. The academic supervisor sees score, cycle, week, and passages, not the author; the author's coordinator sees the author | API, Eval |
| AT-SIM-03 | FR-SIM-03 | A decision needs a comment and only a flagged check takes one; report status and grade do not change | API |
| AT-NOT-01 | FR-NOT-01 | Each FR-NOT-05 event creates one in-app notification and one email; the unread count drops when read | API |
| AT-NOT-02 | FR-NOT-02 | Reminders only for unsubmitted slots due within 24 hours, once each | API |
| AT-NOT-03 | FR-NOT-03 | Every seeded missing report gives a notice to the student and the academic supervisor within 1 hour | API |
| AT-NOT-04 | FR-NOT-04 | An escalation for each seeded overdue report, attendance week, and evaluation on day 4, none on day 3, never twice | API |
| AT-NOT-05 | FR-NOT-05 | Each listed event notifies the right user in a scripted test | API |
| AT-NOT-06 | FR-NOT-06 | A user with Arabic selected receives the Arabic email and notification text | API |
| AT-EXP-01 | FR-EXP-01 | Exported values equal stored values in every row of the Excel and PDF grade sheets; Arabic names are present in both | API, Unit |
| AT-EXP-02 | FR-EXP-02 | The term summary figures equal the dashboard figures | API |
| AT-EXP-03 | FR-EXP-03 | The training record matches the stored data of a seeded student; another supervisor is refused | API |
| AT-PWA-01 | FR-PWA-01 | The manifest and service worker meet the browser's install criteria; the app installs in desktop Chrome | Unit, Browser |
| AT-PWA-02 | FR-PWA-02 | With a subscription the push is sent with only the title and a link; with none the email still goes out; a gone subscription is deleted | API |
| AT-PWA-03 | FR-PWA-03 | Offline, the app opens with the offline message and submit buttons are disabled | Browser |
| AT-AUD-03 | FR-AUD-03 | The history shown for a report, an evaluation, and a grade equals their audit entries; other users are refused | API |
| AT-ORG-07 | FR-ORG-07 | After a transfer the previous holder loses the rights and the new one has them; a reason is required; the transfer is in the audit log; both are notified | API |
| AT-PER-04 | NFR-PER-04 | With 10,000 stored reports the similarity result is ready within 2 minutes | API (timed) |
| AT-PER-05 | NFR-PER-05 | 100-student grade sheet in Excel and PDF in under 60 s each | API (timed) |
| AT-REL-03 | NFR-REL-03 | Running each job twice sends nothing twice; after a simulated downtime the next run catches up | API |
| AT-L10N-03 | NFR-L10N-03 | The exported PDF embeds the Arabic font and its text holds the shaped Arabic names; checked visually | Unit, Browser |

## 7. M5 Demo Scenario

The demo runs on seeded data, on the reference deployment when it is switched on, otherwise on `docker compose up`:

1. A student submits a weekly report copied from a report of an earlier cycle. The academic supervisor's dashboard shows a similarity flag, and the report shows the score, the source cycle and week, and the passages side by side under the Advisory label.
2. The supervisor records "Overlap confirmed" with a comment; the report's status does not change. The coordinator sees who wrote the source.
3. The same text stored at another university is not listed.
4. The notification bell shows the unread count: the reminder 24 hours before a deadline, the Missing notice after it (student and supervisor), and the escalation to the coordinator on day 4. The emails are in Mailpit, each in its recipient's language.
5. A grade is made Final: the student gets an in-app notification, an email, and a web push.
6. The app is installed from Chrome; with the network off, it opens with the offline message and the submit buttons disabled.
7. The coordinator exports the grade sheet as Excel and PDF, with Arabic names joined correctly, and the term summary; the academic supervisor exports a student's training record.
8. The history of a report, an evaluation, and a grade is shown.
9. The Platform Admin transfers a college's coordinator role with a reason; the previous coordinator loses access, and the audit log shows the transfer.
10. The evaluation script prints the similarity results.

## 8. Definition of Done

A requirement is done when:

- its code is merged into `main` through a pull request with CI green;
- its acceptance test in Section 6 is automated and passes (or checked in the browser where marked), and its endpoints are in the permission matrix;
- its screens exist in Arabic and English and follow the wireframes (`AS_ReportReview` with the similarity panel, `CO_Exports`, the notification list, the offline banner of `ST_Dashboard_Mobile`);
- its actions write audit entries;
- the design document, the API specification, or the SRS are updated if the implementation changed anything.

The increment is done when every committed requirement is done, the demo scenario runs without help, and `04_Test_Report.md` records the results, including the similarity evaluation.

## 9. Risks for this Increment

| **Risk** | **Effect** | **Response** |
|:---|:---|:---|
| Similarity search slow with 10,000 reports on a free CPU | NFR-PER-04 missed | Passage vectors in an HNSW index filtered by university; only 5 neighbours per passage; the lexical check runs on those candidates only |
| False flags between reports on the same topic | Supervisors lose trust in the flag | Two conditions per passage pair (cosine and 5-gram containment); measured on the original reports of the evaluation set |
| Arabic in PDFs without a system library | Broken letters in exports | HarfBuzz shaping with an embedded Noto font (RQ-1); a test reads the text back from the PDF |
| Email provider limits | Notifications delayed | Outbox with retries (up to 5); Gmail allows about 500 a day, far above the demo's needs |
| Push differs between browsers | FR-PWA-02 untestable on some devices | Standard Web Push with VAPID; email is the fallback by design; device checks in M6 |
| A large increment | Schedule slip | 20 days of margin from the early start; the descoping order of SRS 6.3.4 applies if needed |
