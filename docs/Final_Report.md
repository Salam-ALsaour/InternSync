# InternSync – Final Report

CSC 305 – Software Engineering · Semester 1 – 2026/2027 · Group 3 · Imam Abdulrahman Bin Faisal University  
**Version 1.0 · Oct 29, 2026 · Milestone M7 (final delivery, Dec 15, 2026)** · Author: Salam Alsaour

## 1. Summary

- **Problem:** co-operative and summer training at universities is run with email, spreadsheets, and paper forms. Students struggle to find suitable training, weekly reports are late or copied, evaluations differ from company to company, and grades and statistics take weeks to assemble.
- **What was built:** InternSync is one bilingual (Arabic and English) web platform for universities, colleges, companies, and students. It covers the whole training cycle, from registration and verification, matching students to vacancies with explanations, and weekly reports and attendance, to evaluations on one rubric, grades with approval, certificates, and statistics.
- **Result:** all 19 product functions of the Proposal were delivered and tested. The measured results meet their targets, except the similarity check on reworded reports and the user acceptance test, which has not been run yet. The system runs at no cost.

## 2. The System

| **Aspect** | **Delivered** |
|:---|:---|
| Users | Student, company supervisor (and Company Admin), academic supervisor, coordinator, Platform Admin; public certificate check |
| Functions | F1–F19 of the Proposal: 125 requirements in the SRS (82 Must, 36 Should, 7 Could) |
| Size | 163 API endpoints, 49 database tables, 45 screens, 839 texts in each language |
| Architecture | React web app (installable, with an offline mode) → FastAPI API with scheduled jobs and an on-server embedding model → PostgreSQL with pgvector; files in private storage ([Design](Design/InternSync_Design.md), Section 2) |
| AI | Skill extraction from CVs; matching with a multilingual model (multilingual-e5-small) plus rules; similarity between reports. Every AI result is advisory and explained |
| Hosting | Zero-cost reference deployment prepared (Vercel, Hugging Face Spaces, Supabase, Gmail); local Docker Compose for development and demonstrations ([Deployment](Deployment.md)) |

## 3. How It Was Built

- **Process:** plan-driven development with incremental delivery ([SPMP](Project_3_SPMP/InternSync_SPMP.md), Section 1.1). Must functions came first (Increments 1 and 2), then Should (Increment 3), then the Could functions with the testing phase (Increment 4), then the final delivery (Increment 5).
- **Each increment** went through four phases, each with its document in `docs/Increments`:
  1. requirements, with the open decisions and the acceptance tests;
  2. design;
  3. implementation;
  4. testing, with a test report.
- **Quality practices:**
  - every change through a pull request with automated checks (CI);
  - API types generated from the code and compared in CI;
  - a permission test of every endpoint for every role;
  - change requests for every decision that changed a document.
- **Documents:** Markdown is the source of truth. The submitted Word and PDF files are generated from it ([document index](README.md)).

## 4. Schedule: Planned against Actual

| **Milestone** | **Planned** | **Actual** |
|:---|:--:|:---|
| M1 Requirements baseline | Oct 3 | SRS 1.0 on Oct 10 |
| M2 Design complete | Oct 15 | Oct 23, 8 days late after CR-05 (one platform for many universities) |
| M3 Increment 1 | Nov 1 | Built and tested Oct 24 |
| M4 Increment 2 (all Must) | Nov 15 | Built and tested Oct 26 |
| M5 Increment 3 (Should) | Nov 25 | Built and tested Oct 27 |
| M6 Testing complete | Dec 10 | Could functions and release checks done Oct 28; user acceptance testing not yet run |
| M7 Final delivery | Dec 15 | Documents, guide, demo script, and presentation ready Oct 29 |

Design took longer than planned because CR-05 widened the scope from one college to many universities and companies. The increments then finished ahead of plan, which left time for all the Could functions and for release checks the plan had not required (browser tests, a load test, a security scan, and held-out AI sets).

## 5. Changes

| **ID** | **Change** |
|:--:|:---|
| CR-01 | Zero-cost reference deployment |
| CR-02 | UC-15 added to the use cases |
| CR-03 | Weekly working days in the cycle |
| CR-04 | Change requests logged in the repository |
| CR-05 | One platform for many universities and companies: open registration with verification, Platform Admin, direct vacancy publishing |
| CR-06 | Training type part of eligibility |
| CR-07 – CR-09 | Implementation adjustments of Increments 1–3 (among them the PDF library, files streamed by the API, and sentence-length similarity passages) |
| CR-10 | Offline mode: a saved copy of the session and drafts kept on the device |
| CR-11 | Implementation adjustments of Increment 4 (retention and anonymization, certificate details, the idle limit on the device) |

Details and the documents each change affected are in [Change_Requests.md](Change_Requests.md).

## 6. Quality and Results

The numbers below are copied from [Key_Results.md](Key_Results.md), which gives the target and the way to repeat each one.

| **What** | **Result** | **Target** |
|:---|:---|:---|
| Automated tests | 202 backend tests (95% of the code covered), 19 frontend unit tests, 34 browser tests on four engines and sizes | All pass |
| Permission checks | 810 refused calls over 163 endpoints, none allowed | 0 (O1) |
| Matching, relevant vacancy in the top 5 | 100% on the tuning set and on the held-out set | 80% (O2) |
| Skills found in CVs | 97.2% | 70% |
| Copied reports flagged | 10 of 10 (tuning); 7 of 10 held-out: all copied word for word, none of the reworded | 9 of 10 (O5) |
| Original reports flagged | 0 of 10 on both sets | At most 1 |
| 50 users at once | 95% within 0.21 s, 0 errors | 2 s |
| Grade sheet of 100 students | 1.0–1.3 s Excel, 2.4–4.6 s PDF | 60 s (O6) |
| Security scan | 0 high-risk findings | 0 high |
| Languages | 100% of screens in Arabic and English | 100% (O7) |
| Cost | 0 | 0 |

## 7. Requirements Status

From [Requirements_Status.md](Requirements_Status.md), generated from the SRS, the increment documents, and the tests:

| **Priority** | **Requirements** | **Tested (automated)** | **Checked (result recorded)** | **Open** |
|:---|:--:|:--:|:--:|:--:|
| Must | 82 | 54 | 25 | 3 |
| Should | 36 | 29 | 7 | 0 |
| Could | 7 | 7 | 0 | 0 |
| **All** | **125** | **90** | **32** | **3** |

"Tested" counts requirements with an automated test named after their acceptance test; many "Checked" ones are also automated under other names, as their test reports say.

The three open requirements need people or the hosted system:

- **NFR-USA-01:** user acceptance testing.
- **NFR-REL-01:** uptime of the hosted server.
- **NFR-SEC-01:** HTTPS on the hosted system.

## 8. Risks

| **Risk (SPMP Section 7)** | **What happened** |
|:---|:---|
| Late requirement changes and scope creep | Occurred: CR-05 widened the scope during design. Absorbed by a slower design phase and faster increments; nothing was dropped |
| Increment 1 grows after CR-05 | Occurred and handled as planned: FR-ORG-07 moved to Increment 3 |
| Matching or similarity results unreliable | Partly: matching held on a harder held-out set; similarity misses reworded copies (Section 9). Both stay advisory with a person deciding |
| Extracting skills from CVs in different formats | A 5 MB CV took 94 s; found by a timed test and reduced to 2–6 s |
| Arabic in PDF exports | The planned PDF library did not install on Windows; replaced (CR-09), and Arabic is joined and right to left |
| Permission errors expose data | Did not occur: every endpoint is tested for every role |
| Free hosting tiers sleep or hit limits | The reference deployment waits for the owner's accounts; demonstrations run on the local stack, as planned |
| Volunteers for user acceptance testing | Occurred: the test has not been run; the plan, cards, and sheet are ready |

## 9. Limitations and Open Items

- **User acceptance testing (O8)** and the device check on real phones have not been run. The materials are in [05_UAT_Plan.md](Increments/Increment_4/05_UAT_Plan.md).
- **The reference deployment** is prepared and off until the owner creates the accounts ([Deployment](Deployment.md), Section 3). The load test and the security scan were run on the local stack.
- **The similarity check** finds text copied word for word, not reports reworded sentence by sentence (7 of 10 on the held-out set).
- **The AI evaluation sets** are synthetic and written by the same author. The held-out sets are independent of the settings, not of the author.
- **Validation messages for wrongly typed values** (for example letters in a number field) come from the framework in English; the forms prevent most of them, and every business rule answers in the user's language.

## 10. Lessons Learned

1. **A contract the machine checks prevents integration bugs.** The frontend's API types are generated from the backend and compared in every build, so a mismatch fails the build instead of a screen.
2. **Testing permissions exhaustively is cheap.** One table of endpoints and roles, and one test, checked 810 refusals and caught every route added without a rule.
3. **Measure on data you did not tune on.** The similarity check scored 10 of 10 on its tuning set and 7 of 10 on new data; only the held-out set showed the limit.
4. **Automated scans find what reviews miss.** The security scan showed that the hosted app had no Content-Security-Policy, although the design said it had one.
5. **Check time, not only results.** A timed test found a CV that took 94 s to read, and looking at what the app does while idle found that a session never expired while a window stayed open.
6. **Keep the documents next to the code and change them in the same pull request.** With a change request per decision and a generated requirements status, the documents stayed consistent through 11 changes.
7. **Book people early.** User acceptance testing needs volunteers and dates; it was the only planned activity not completed.

## 11. Future Work

- Run the user acceptance test and the device check; switch on the reference deployment.
- Detect reworded copies with an embedding-only rule, evaluated on its own held-out set before use.
- Sign-in with the university's accounts (single sign-on) and import of enrolment lists.
- Statistics across universities for the Platform Admin; more languages.

## 12. Documents

| **Document** | **Purpose** |
|:---|:---|
| [SRS](Project_4_SRS/InternSync_SRS.md) | What the system must do (version 1.6) |
| [SPMP](Project_3_SPMP/InternSync_SPMP.md) | How the project was planned and run |
| [System design](Design/InternSync_Design.md) and [API specification](Design/InternSync_API_Spec.md) | How the system is built |
| [Increment documents](README.md) | Requirements, design, and test report of each increment |
| [Change requests](Change_Requests.md) | Every change and its effect |
| [Requirements status](Requirements_Status.md) | Each requirement with its tests |
| [Key results](Key_Results.md) | Every measured result |
| [User guide](User_Guide.md) | How each role uses the system |
| [Demo script](Demo_Script.md) | The final demonstration |
| [Deployment](Deployment.md) | The zero-cost deployment and how to switch it on |
| [Final presentation](https://claude.ai/artifact/3KnHXL8q7QgWXN1xwaynKp) | 14 slides with speaker notes; downloadable as PowerPoint or PDF from the deck's page |
| `Final_Submission/` | PDF of each document, and the SRS in Word and PDF on the course template |
