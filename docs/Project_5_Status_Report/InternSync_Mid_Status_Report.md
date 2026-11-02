# InternSync – Mid Status Report (Project 5)

Project Status Report – CSC 305 Project 5 · IMAM ABDULRAHMAN BIN FAISAL UNIVERSITY · College of Computer Science & Information Technology · CSC 305 – Software Engineering \| Semester 1 – 2026/2027 \| Section 5MA1 \| Group 3 · Version 1.1 · 02-11-2026

> This Markdown file is the maintained version of the Mid Status Report (Project 5). `InternSync_Mid_Status_Report_v1.1.docx` and `.pdf` in this folder are generated from it on the official Project Status Report template ([build](build/README.md)). Each `##` heading below is a heading of the template, in the template's order; the headings the template does not have (Team Members and Responsibilities, Revision History) are added in the same style. Version 1.0, on a stand-in template, is kept in [old](old/).

## Project Title

InternSync – Cooperative Training Coordination and Tracking System

## Reporting Period

September 25 – November 1, 2026 (project start to the M3 demonstration)

## Team Information

**Team name:** Group 3 (Section 5MA1) · **Advisor:** Dr. Sultan Al-Enezi · **Course:** CSC 305 – Software Engineering, Semester 1 – 2026/2027

<!-- widths: 40 20 25 15 -->
| **Team Members** | **Student ID** | **Signature** | **Date** |
|:---|:--:|:--:|:--:|
| Salam Alsaour (Team Leader) | 2250009168 | | |
| Khalid Alajmi | 2250004309 | | |
| Ali Alghafly | 2250002460 | | |
| Ahmed Kanaan | 2250009170 | | |
| Abdullah Abalhareth | 2250005266 | | |
| Rakan Alzahrani | 2250000631 | | |

Each member's project role and responsibilities are under Team Members and Responsibilities below.

## Summary of Progress

InternSync is one web platform for cooperative and summer training: universities and their colleges, training companies, and students. Students are verified, build a profile from their CV, apply to vacancies ranked by an AI fit score, and submit weekly and final reports; companies publish vacancies, record attendance, and evaluate trainees; academic supervisors review reports and enter grades; coordinators run the training cycles and approve grades. The interface is in Arabic and English.

- **Overall status: ahead of schedule.** All five increments are built and tested; the documents for the final delivery are ready. Open: user acceptance testing and switching on the hosted system.
- **Process:** plan-driven with incremental delivery (SPMP Section 1.1): Must functions first, then Should, then Could.
- **Scope:** 125 requirements in SRS 1.6; 11 change requests recorded and approved (CR-01 – CR-11).
- **Milestones:** M1 and M2 done; M3 demonstration on Nov 1; the work of M4 – M7 is built ahead of its dates, and their demonstrations stay on the planned dates.
- **Next milestone:** M4 demonstration of Increment 2 on Nov 15, 2026.

**Table 1 – Milestones against the plan (SPMP Section 5)**

<!-- widths: 36 14 50 -->
| **Milestone** | **Target date** | **Status on Nov 1, 2026** |
|:---|:--:|:---|
| M1: Requirements baseline (SRS) | Oct 3 | Done: SRS 1.0 submitted Oct 10 (Project 4); now 1.6 |
| M2: Design complete | Oct 15 | Done Oct 23, 8 days late after CR-05 (one platform for many universities and companies) |
| M3: Increment 1 delivered | Nov 1 | Built and tested Oct 24 (43 of 43 acceptance tests); demonstration Nov 1 |
| M4: Increment 2 delivered (all Must functions) | Nov 15 | Built and tested Oct 26 (27 of 27); demonstration Nov 15 |
| M5: Increment 3 delivered (Should functions) | Nov 25 | Built and tested Oct 27 (21 of 21); demonstration Nov 25 |
| M6: Testing complete | Dec 10 | Increment 4 (Could functions and release checks) built Oct 28 (12 of 13); user acceptance testing still open |
| M7: Final delivery | Dec 15 | Final report, user guide, demo script, and presentation ready Oct 29; demonstration Dec 15 |

## Tasks Completed

The tasks of the schedule (SPMP Section 4) with their owners; the details and the test results follow in Tables 2 – 4.

<!-- widths: 42 20 15 23 -->
| **Task** | **Assigned To** | **Date Completed** | **Status** |
|:---|:---|:--:|:---|
| T1: Plan and requirements | Salam, Abdullah | Oct 10, 2026 | ✅ Done |
| T2: System design | Khalid, Ahmed, Salam | Oct 23, 2026 | ✅ Done |
| T3: UI/UX design | Rakan, Ali | Oct 23, 2026 | ✅ Done |
| T4: Increment 1 (registration, verification, login, profiles, vacancies, reports) | All developers | Oct 24, 2026 | ✅ Done; demonstration Nov 1 (M3) |
| T5: Increment 2 (matching, attendance, evaluations, grades, dashboards) | All developers | Oct 26, 2026 | ✅ Done; demonstration Nov 15 (M4) |
| T6: Increment 3 (similarity, notifications, exports, installable app) | All developers | Oct 27, 2026 | ✅ Done; demonstration Nov 25 (M5) |
| T7: Increment 4 (Could functions and release checks) | Abdullah, all | Oct 28, 2026 | ✅ Built (12 of 13 acceptance tests); user acceptance testing open |
| T8: Increment 5 (final documents and presentation) | Abdullah, Salam | Oct 29, 2026 | ✅ Done; final demonstration Dec 15 (M7) |

**Table 2 – Planning, requirements, and design**

<!-- widths: 22 18 10 50 -->
| **Task (SPMP)** | **Planned** | **Done** | **Result** |
|:---|:--:|:--:|:---|
| T1: Plan and requirements | Sep 25 – Oct 3 | Oct 10 | SPMP 1.0 (Oct 3) and SRS 1.0 (Oct 10); SRS on the course template (1.3) on Oct 23 |
| T2: System design | Oct 4 – Oct 15 | Oct 23 | System design document (architecture, zero-cost deployment, 49-table data model, state machines, security), API specification, diagram pack |
| T3: UI/UX design | Oct 4 – Oct 15 | Oct 23 | 32 clickable wireframes in Arabic and English, design system |

**Table 3 – Implementation and testing**

<!-- widths: 12 15 9 40 24 -->
| **Increment (task)** | **Planned** | **Done** | **What was delivered** | **Tests** |
|:---|:--:|:--:|:---|:---|
| 1 (T4) | Oct 16 – Nov 1 | Oct 24 | Registration and verification of universities, colleges, companies, and students; Platform Admin; login, sessions, and roles; cycles; profiles and CV skill extraction; vacancies and placements; weekly and final reports; audit log; Arabic and English | 43 of 43 acceptance tests; 108 backend tests; 95% coverage |
| 2 (T5) | Nov 2 – Nov 15 | Oct 26 | AI matching with explanation and development plan; attendance; evaluations; grades with approval; dashboards for every role | 27 of 27; 158 backend tests |
| 3 (T6) | Nov 16 – Nov 25 | Oct 27 | Similarity detection; notifications (in-app, email, web push) with reminders and escalations; Excel and PDF exports with Arabic; installable app; history; role transfers | 21 of 21; 187 backend tests |
| 4 (T7) | Nov 26 – Dec 10 | Oct 28 | Completion certificates with QR code and public check page; student evaluation of the company and job-offer survey; leniency alert; anonymization; offline mode; release checks | 12 of 13; 201 backend tests; 34 browser tests |
| 5 (T8) | Dec 11 – Dec 15 | Oct 29 | Final report, requirements status, user guide, demonstration script, presentation, submission files; phone menu | Regression: 202 backend, 19 frontend, 34 browser tests |

**Table 4 – Measured results**

<!-- widths: 34 48 18 -->
| **Measure** | **Result** | **Target** |
|:---|:---|:---|
| Permission checks | 810 calls by users who must be refused, over 163 endpoints: 0 got through | 0 |
| Matching: relevant vacancy in the top 5 | 100% on the tuning set and on the held-out set | 80% |
| Skills found in CVs | 97.2% (Arabic 96.9%, English 97.4%) | 70% |
| Copied reports flagged | 10 of 10 on the tuning set; 7 of 10 on the held-out set (reworded copies missed) | 9 of 10 |
| 50 users at once (local stack) | 95% of requests within 0.21 s, 0 errors | Within 2 s |
| Security scan (OWASP ZAP) | 0 high-risk findings | 0 |
| Running cost | 0 (free tiers only, CR-01) | 0 |

## Tasks In Progress

<!-- widths: 25 15 14 46 -->
| **Task** | **Assigned To** | **Expected Completion** | **Status** |
|:---|:---|:--:|:---|
| M3 demonstration of Increment 1 | Salam, with all members | Nov 1, 2026 | On Nov 1; the dry run passed twice with real emails (10 of 10 steps) |
| Software Design Description (Project 6) | Salam, Khalid, Abdullah | Week 13 | Written on the course SDD template (IEEE 1016), with a new class diagram; due in Week 13 |
| Software Test Specification (Project 7) | Abdullah, with all members | Week 15 | Written on the course STS template (IEEE 829): 43 functional and 13 non-functional test cases, every member with assigned test cases; due in Week 15 |
| Switching on the hosted system | Ahmed, Salam | Before Dec 10, 2026 | The deployment is prepared and documented. The team bought the domain `internsync.tech`, and its steps are added to the deployment guide. Waiting for the owner's Hugging Face and Gmail accounts |
| Scheduling user acceptance testing | Abdullah, Rakan | Before Dec 10, 2026 | Plan, consent text, scenario cards for the five roles, and the result sheet are ready; participants and dates are being found |
| Dependency security | Salam | Nov 1, 2026 | ✅ Done: new advisories for `pypdf` (Oct 31) fixed by moving to 6.21.4; merged Nov 1 |

## Upcoming Tasks

The start dates are those of the schedule (SPMP Section 4); the due dates are the milestone and submission dates.

<!-- widths: 34 14 13 14 25 -->
| **Task** | **Assigned To** | **Start Date** | **Due** | **Status** |
|:---|:---|:--:|:--:|:---|
| M4 demonstration (Increment 2: matching, attendance, evaluations, grades, dashboards) | All members | Nov 2, 2026 | Nov 15, 2026 | Ready: Increment 2 built and tested Oct 26 |
| M5 demonstration (Increment 3: similarity, notifications, exports, installable app) | All members | Nov 16, 2026 | Nov 25, 2026 | Ready: Increment 3 built and tested Oct 27 |
| Submit the SDD (Project 6) | Salam, Abdullah | Week 13 | Week 13 | Written; to be submitted |
| Switch on the hosted system on `internsync.tech`; repeat the load test and the security scan on it; check HTTPS and uptime | Ahmed | When the owner's accounts are ready | Before Dec 10, 2026 | Waiting for the owner's Hugging Face and Gmail accounts |
| User acceptance testing with at least 8 participants (students, faculty, company representatives) and the device check on phones | Abdullah, Rakan | Nov 26, 2026 | By Dec 10, 2026 (M6) | Materials ready; participants and dates being found |
| Submit the STS (Project 7) with the UAT results | Abdullah | Week 15 | Week 15 | Written; the UAT results to be added |
| Final regression, presentation rehearsal, and final demonstration | All members | Dec 11, 2026 | Dec 15, 2026 (M7) | Final report, user guide, demo script, and presentation ready Oct 29 |

## Issues and Risks

Issues are risks that have occurred; the risks still open follow in Table 5.

<!-- widths: 27 15 12 30 16 -->
| **Issue** | **Impact** | **Owner** | **Action** | **Status** |
|:---|:---|:---|:---|:---|
| Scope grew during design (CR-05: one platform for many universities and companies, with verification and a Platform Admin) | Design finished 8 days late (Oct 23) | Salam | Absorbed by faster increments; FR-ORG-07 moved to Increment 3 as planned; nothing dropped | ✅ Closed |
| Volunteers for user acceptance testing not available | UAT not run; M6 open | Abdullah, Rakan | Materials ready; sessions to be booked with students, faculty, and companies before Dec 10 | Open |
| The similarity check misses reports reworded sentence by sentence (7 of 10 on the held-out set) | AT-AI-03 not met for similarity | Salam | The flag stays advisory and a supervisor decides; the limit is stated in the final report | Accepted |
| The planned PDF library did not install on Windows | Arabic PDF exports at risk | Salam | Replaced by fpdf2 with HarfBuzz shaping (CR-09); Arabic joined and right to left | ✅ Closed |
| A 5 MB CV took 94 s to read | Upload over the 30 s limit | Ahmed | Found by a timed test; limits added; now 2–6 s | ✅ Closed |
| New advisories for a PDF library (`pypdf`) failed the dependency audit in CI | CI red on Oct 31 | Salam | Updated to 6.21.4; audit clean | ✅ Closed |

**Table 5 – Risks (SPMP Section 7)**

<!-- widths: 32 12 10 46 -->
| **Risk** | **Probability** | **Impact** | **Mitigation** |
|:---|:--:|:--:|:---|
| UAT participants still not found by early December | High | High | Book sessions now; run them at the college on the local stack if the hosted system is not on; at least 8 participants across the roles |
| Hosted system not switched on in time (owner accounts, public Space decision) | Medium | Medium | Steps documented; the local Docker stack is the fallback for the demonstrations and the UAT |
| Free hosting tiers sleep or hit limits | Medium | Medium | Keep-alive every 6 hours, nightly encrypted backups, small demo data |
| Team availability around exams | High | Medium | The remaining work is testing and demonstrations, not new features; tasks have named owners |
| AI evaluation sets are synthetic and written by the same author | Medium | Medium | Held-out sets kept separate from tuning; AI results always advisory |
| Permission errors expose another organization's data | Low | High | Every endpoint tested for every role (810 refused calls); scope tests across colleges and companies |

## Team Members and Responsibilities

<!-- widths: 17 18 40 25 -->
| **Team Member** | **Role** | **Responsibilities** | **Next tasks** |
|:---|:---|:---|:---|
| Salam Alsaour (Team Leader) | Team leader; backend and AI services developer | Plans and tracks the schedule, runs the weekly meeting, reports to the supervisor, integrates the components; matching engine and similarity detection; weekly reports, evaluations, scheduled notifications, exports | Run the M3 – M5 demonstrations; submit the SDD; final regression |
| Khalid Alajmi | Frontend and backend developer | Database schema, authentication and role-based access control, approval workflow, profile and vacancy API; report, evaluation, and certificate screens | SDD sections on data and security; permission and organization tests of the STS |
| Ali Alghafly | Frontend developer | React PWA: role dashboards, forms, Arabic and English with right-to-left layout, notifications in the browser | Browser tests on all engines; offline and language checks for the demonstrations |
| Ahmed Kanaan | AI services developer; deployment lead | Skill extraction, match explanation, development plan; deployment with Docker and the hosting services | Switch on the hosted system on `internsync.tech`; load test and AI evaluation |
| Abdullah Abalhareth | QA and documentation lead | Test plan and test cases, user acceptance testing, SRS and design documents, task board and risk register | Book and run the UAT; submit the STS; keep the risk register |
| Rakan Alzahrani | UI/UX designer | Wireframes and design system, usability of key screens | UAT scenario sessions and the device check on phones; accessibility check |

## Notes / Comments

- **Team:** all six members have named tasks to Dec 15. The remaining work is testing, demonstrations, and documents, not new features, so the exam period is the main pressure on the schedule (Table 5).
- **Support needed:** help in reaching students, faculty members, and company representatives for the user acceptance testing sessions (at least 8 participants before Dec 10).
- **Hosted system:** the owner's Hugging Face and Gmail accounts are needed to switch it on at `internsync.tech`; until then the demonstrations run on the local Docker stack.

## Revision History

<!-- widths: 12 18 52 18 -->
| **Version** | **Date** | **Description** | **Author** |
|:--:|:--:|:---|:--:|
| 1.0 | Nov 1, 2026 | Mid status report for Project 5: progress to Nov 1, 2026 against SPMP 1.7. | Group 3 |
| 1.1 | Nov 2, 2026 | Moved to the official Project Status Report template: reporting period, team table with signatures, tasks with owners and dates, issue owners, notes and comments. No content removed. | Group 3 |
