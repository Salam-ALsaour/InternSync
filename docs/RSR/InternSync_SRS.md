# InternSync – Software Requirements Specification (SRS)

**IMAM ABDULRAHMAN BIN FAISAL UNIVERSITY** · College of Computer Science & Information Technology  
CSC 305 – Software Engineering \| Semester 1 – 2026/2027 \| Section 5MA1 \| Group 3

**InternSync – Cooperative Training Coordination and Tracking System**  
Project 4 · Version 1.1 · October 2026

> This Markdown file is the maintained version of the SRS. `InternSync_SRS.docx` and `InternSync_SRS.pdf` in this folder are the v1.0 baseline as submitted. Changes after v1.0 are listed in the revision history and in [Change_Requests.md](../Change_Requests.md).

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
| 1.0 | Oct 10, 2026 | First baseline submitted as Project 4 (SRS). | Group 3 |
| 1.1 | Oct 13, 2026 | CR-01: zero-cost reference deployment (3.4, 5, NFR-PER-01, 6.2, 6.3, C-04, C-10, D-05). CR-02: UC-15 added to Table 3.1. CR-03: weekly working days added to FR-CYC-01. CR-04: change requests logged in the repository (10.6). | Salam Alsaour |

## Table of Contents

- [1. Introduction](#1-introduction)
  - [1.1 Purpose of this Document](#11-purpose-of-this-document)
  - [1.2 System Purpose](#12-system-purpose)
  - [1.3 Scope](#13-scope)
  - [1.4 Definitions, Acronyms, and Abbreviations](#14-definitions-acronyms-and-abbreviations)
  - [1.5 References](#15-references)
  - [1.6 Requirement Conventions](#16-requirement-conventions)
- [2. Stakeholders and User Classes](#2-stakeholders-and-user-classes)
  - [2.1 Stakeholders](#21-stakeholders)
  - [2.2 User Classes and Characteristics](#22-user-classes-and-characteristics)
  - [2.3 Access Rights by Role](#23-access-rights-by-role)
- [3. Overall Description](#3-overall-description)
  - [3.1 Product Perspective](#31-product-perspective)
  - [3.2 Co-op Life Cycle Supported](#32-co-op-life-cycle-supported)
  - [3.3 Use Case Overview](#33-use-case-overview)
  - [3.4 Operating Environment](#34-operating-environment)
  - [3.5 User Documentation](#35-user-documentation)
- [4. Functional Requirements](#4-functional-requirements)
  - [4.1 Accounts, Authentication, and Access Control](#41-accounts-authentication-and-access-control)
  - [4.2 Training Cycles and Configuration](#42-training-cycles-and-configuration)
  - [4.3 Student Profile, CV, and Data Import](#43-student-profile-cv-and-data-import)
  - [4.4 Vacancies and Placement](#44-vacancies-and-placement)
  - [4.5 Matching and Explanation](#45-matching-and-explanation)
  - [4.6 Weekly and Final Reports](#46-weekly-and-final-reports)
  - [4.7 Attendance](#47-attendance)
  - [4.8 Evaluations](#48-evaluations)
  - [4.9 Approval Workflow and Grades](#49-approval-workflow-and-grades)
  - [4.10 Similarity Detection](#410-similarity-detection)
  - [4.11 Notifications](#411-notifications)
  - [4.12 Dashboards and Statistics](#412-dashboards-and-statistics)
  - [4.13 Exports](#413-exports)
  - [4.14 Completion Certificates](#414-completion-certificates)
  - [4.15 Language and PWA Features](#415-language-and-pwa-features)
  - [4.16 Audit Trail](#416-audit-trail)
- [5. Non-Functional Requirements](#5-non-functional-requirements)
  - [5.1 Performance](#51-performance)
  - [5.2 Security](#52-security)
  - [5.3 Privacy and Data Protection](#53-privacy-and-data-protection)
  - [5.4 Usability and Accessibility](#54-usability-and-accessibility)
  - [5.5 Localization](#55-localization)
  - [5.6 Reliability and Availability](#56-reliability-and-availability)
  - [5.7 Maintainability and Portability](#57-maintainability-and-portability)
  - [5.8 AI Quality and Transparency](#58-ai-quality-and-transparency)
- [6. External Interface Requirements](#6-external-interface-requirements)
  - [6.1 User Interfaces](#61-user-interfaces)
  - [6.2 Hardware Interfaces](#62-hardware-interfaces)
  - [6.3 Software Interfaces](#63-software-interfaces)
    - [6.3.1 CSV Import Formats](#631-csv-import-formats)
  - [6.4 Communication Interfaces](#64-communication-interfaces)
- [7. Constraints](#7-constraints)
- [8. Assumptions and Dependencies](#8-assumptions-and-dependencies)
  - [8.1 Assumptions](#81-assumptions)
  - [8.2 Dependencies](#82-dependencies)
- [9. Requirement Prioritization](#9-requirement-prioritization)
  - [9.1 Method](#91-method)
  - [9.2 Priority Summary](#92-priority-summary)
  - [9.3 Mapping to Increments](#93-mapping-to-increments)
  - [9.4 Descoping Order](#94-descoping-order)
- [10. Requirement Validation Considerations](#10-requirement-validation-considerations)
  - [10.1 Validation and Verification](#101-validation-and-verification)
  - [10.2 Validation Techniques](#102-validation-techniques)
  - [10.3 Requirement Quality Checklist](#103-requirement-quality-checklist)
  - [10.4 Verification Methods](#104-verification-methods)
  - [10.5 Validation Risks and Open Issues](#105-validation-risks-and-open-issues)
  - [10.6 Baseline and Change Control](#106-baseline-and-change-control)
- [Appendix A. Traceability Matrix](#appendix-a-traceability-matrix)

## 1. Introduction

### 1.1 Purpose of this Document

This Software Requirements Specification (SRS) defines what InternSync must do and the qualities it must have. It turns the functions (F1–F19) and objectives (O1–O10) approved in the Project Proposal into numbered, testable requirements. Once approved, it is the baseline for design, implementation, and testing, and the reference for the change control described in the Software Project Management Plan (SPMP).

The intended readers are the course supervisor, who evaluates the specification; the development team, who design and build from it; the QA lead, who derives test cases from it; and the stakeholder representatives who take part in validating it (Section 10).

### 1.2 System Purpose

Cooperative training (Co-op) and summer internships are coordinated today through email, spreadsheets, and paper or PDF forms. Vacancies are circulated informally, weekly reports arrive as attachments, company evaluations are filled in once at the end, and grade sheets are compiled by hand (problems P1–P6 in the Proposal). The result is no single, reliable record of what happened during a training cycle.

InternSync is a role-based web platform, delivered as a responsive Progressive Web App (PWA) in Arabic and English, that manages the whole co-op life cycle in one place: publishing vacancies and matching students to them, weekly follow-up, standard evaluation, multi-stage grade approval, and official exports. Its purpose is to replace scattered manual work with one auditable record from which the official outputs are generated directly. The AI features (matching, skill gaps, similarity detection) support decisions; people make every final decision.

### 1.3 Scope

This release covers functions F1–F19 of the Proposal. Table 1.1 lists them with their priority and the section of this SRS that specifies them.

**Table 1.1 – Functions in scope**

| **ID** | **Function** | **Priority** | **SRS section** |
|:--:|:---|:--:|:--:|
| F1 | Role-based accounts, authentication, and authorization for four roles | Must | 4.1 |
| F2 | Student profile and CV upload with skill extraction; CSV import of student, course, and staff data | Must | 4.3 |
| F3 | Vacancy catalogue, applications, and placement confirmation | Must | 4.4 |
| F4 | Matching engine that ranks vacancies against the student profile | Must | 4.5 |
| F5 | Weekly and final report submission with deadlines and revision requests | Must | 4.6 |
| F6 | Weekly attendance confirmation by the company supervisor | Must | 4.7 |
| F7 | Periodic and final evaluations using one standard rubric | Must | 4.8 |
| F8 | Multi-stage approval workflow for reports and grades | Must | 4.9 |
| F9 | Role-specific dashboards with pending actions and status | Must | 4.12 |
| F10 | Arabic/English interface with RTL and LTR support | Must | 4.15 |
| F11 | Match explanation, skill-gap analysis, and development plan | Should | 4.5 |
| F12 | Similarity detection between reports stored in the system | Should | 4.10 |
| F13 | Scheduled notifications: reminders, late flags, escalation | Should | 4.11 |
| F14 | Export of grade sheets and summary reports (PDF and Excel) | Should | 4.13 |
| F15 | PWA features: installable app, web push, cached app shell | Should | 4.15 |
| F16 | Digital completion certificate with QR code and public verification | Could | 4.14 |
| F17 | Mutual evaluation: the student evaluates the training entity | Could | 4.8 |
| F18 | End-of-term survey and placement-to-job-offer statistics | Could | 4.12 |
| F19 | Evaluation-leniency alert for companies with at least 5 evaluations | Could | 4.12 |

Supporting requirements that serve several functions — training-cycle configuration (Section 4.2) and the audit trail (Section 4.16) — are also in scope.

**Out of scope** for this release (the “Won’t” category in Section 9):

- Live integration with the university student information system; student and staff data are imported from CSV files.

- Writing grades into the university system; grades leave InternSync as exported files only.

- A native mobile application; the responsive PWA covers phone use.

- Contracts, payroll, insurance, or any legal or HR processing with companies.

- Plagiarism detection against the internet or external databases, and detection of AI-generated text.

- Biometric or GPS-based attendance verification.

- Real-time chat; communication is limited to notifications and comments on submissions.

- Statistical calibration of grades across companies; a standard rubric is used instead.

### 1.4 Definitions, Acronyms, and Abbreviations

**Table 1.2 – Definitions**

| **Term** | **Definition** |
|:---|:---|
| Co-op | Cooperative training: a supervised training period at a company that is part of the degree plan. |
| Training cycle | One term’s run of co-op or summer training, with its own dates, deadlines, rubric, and grade weights. |
| Placement | Confirmed assignment of a student to a vacancy, a company supervisor, and an academic supervisor. |
| Company supervisor (CS) | Company employee who supervises the student during training. |
| Academic supervisor (AS) | Faculty member who follows the student’s progress and proposes the grade. |
| Coordinator (CO) | Staff member of the college co-op unit; also performs system administration in this release. |
| Student (ST) | Student enrolled in a training cycle. |
| Rubric | Fixed set of evaluation criteria, each rated on a 1–5 scale with a description for every level. |
| Skill vocabulary | List of normalized skills with English and Arabic names and synonyms, maintained by the coordinator. |
| Embedding | Numeric vector representation of text, used to compare meaning (CV with vacancy, report with report). |
| Fit score | Value from 0 to 100 used to rank vacancies for a student. |
| Similarity score | Percentage of a report’s text that overlaps with another stored report. |
| Default | Value set by this SRS that the coordinator can change without code changes (NFR-MNT-03). |
| MoSCoW | Prioritization into Must, Should, Could, and Won’t. |
| PWA | Progressive Web App: a web application that can be installed and can work partly offline. |
| RTL / LTR | Right-to-left (Arabic) / left-to-right (English) layout. |
| RBAC | Role-based access control. |
| JWT | JSON Web Token, used to authenticate API requests. |
| PDPL | Saudi Personal Data Protection Law. |
| UAT | User acceptance testing. |
| FR / NFR | Functional requirement / non-functional requirement. |
| SPMP | Software Project Management Plan. |

### 1.5 References

1.  InternSync – Project Proposal, CSC 305 Group 3, Oct 2, 2026.

2.  InternSync – Software Project Management Plan (SPMP), CSC 305 Group 3, Oct 3, 2026.

3.  InternSync – Project Idea Form, CSC 305 Group 3, Sep 5, 2026 (superseded by the Proposal where they differ, e.g., four roles instead of five).

4.  ISO/IEC/IEEE 29148:2018, Systems and software engineering — Life cycle processes — Requirements engineering.

5.  Personal Data Protection Law (PDPL), Kingdom of Saudi Arabia, and its implementing regulations.

6.  W3C, Web Content Accessibility Guidelines (WCAG) 2.1.

### 1.6 Requirement Conventions

- Every requirement has a unique ID: **FR-\<area\>-\<nn\>** for functional and **NFR-\<category\>-\<nn\>** for non-functional requirements. IDs are never reused; a removed requirement keeps its ID and is marked “Deleted”.

- Each requirement states one behavior using “shall” and has an acceptance criterion from which test cases are derived (Section 10).

- Priority is Must, Should, or Could, as defined in Section 9.

- Each group of requirements names its source function (F) and objective (O) from the Proposal; Appendix A gives the full traceability.

- Role abbreviations: ST student, CS company supervisor, AS academic supervisor, CO coordinator.

## 2. Stakeholders and User Classes

### 2.1 Stakeholders

Table 2.1 lists the people and groups affected by InternSync, what they need, and how their needs shape the requirements.

**Table 2.1 – Stakeholders**

| **Stakeholder** | **Type** | **Needs and interests** | **Interaction with the system** | **Effect on requirements** |
|:---|:---|:---|:---|:---|
| Student | Primary user | Find suitable vacancies and know which skills are missing; submit reports easily; get feedback during training; see grade and certificate. | Profile and CV, applications, weekly and final reports, evaluation of the company, dashboard. | Mobile-friendly, simple flows (NFR-USA); advisory, explained matching. |
| Company training supervisor | Primary user (external, occasional) | Spend little time: confirm attendance and evaluate quickly; reach qualified students. | Vacancies, applicant review, weekly attendance, periodic and final evaluation. | One-action attendance (FR-ATT-01); email reminders; nothing to install. |
| Academic supervisor | Primary user (faculty) | Review reports efficiently, notice copied work, propose grades with a clear record. | Report review, revision requests, similarity flags, grade entry. | Approval workflow (4.9); similarity is advisory (FR-SIM-03). |
| Co-op coordinator (co-op unit) | Primary user; system administrator in this release | Run cycles without manual work; control deadlines; produce official outputs; handle escalations. | Accounts and CSV import, cycles, rubric, vacancies, placements, grade approval, exports, audit log. | Configuration (4.2), exports (4.13), audit trail (4.16). |
| College administration | Indirect | Accurate program statistics and placement outcomes. | Receives term summaries exported by the coordinator; no account in this release. | FR-EXP-02, FR-DSH-03. |
| Partner companies and employers | Indirect | A reliable channel to students; verify that a student completed training. | Through company supervisor accounts; public certificate verification. | FR-CER-01 – 03. |
| CSC 305 course supervisor | Project stakeholder | A complete, testable SRS and delivery on schedule. | Reviews deliverables at each milestone. | Constraints (7) and prioritization (9). |
| Development team (Group 3) | Project stakeholder | A scope that fits about 480 person-hours. | Designs, builds, and tests the system. | Constraints (7) and descoping order (9.4). |

### 2.2 User Classes and Characteristics

The expected numbers describe one training cycle in the demonstration environment and are used as the sizing basis for the performance requirements (Section 5.1).

**Table 2.2 – User classes**

| **User class** | **Expected number per cycle** | **Frequency of use** | **Technical skill** | **Main device** |
|:---|:---|:---|:---|:---|
| Student | Up to 300 | Daily while searching; weekly during training | Medium to high | Phone and laptop |
| Company supervisor | Up to 100 | Weekly, a few minutes | Varies; may be non-technical | Laptop; phone through email links |
| Academic supervisor | Up to 30 | Weekly | Medium | Laptop |
| Coordinator | 1 to 3 | Daily during setup and grading | Medium | Laptop |
| Public verifier | Not known | Rare | Any | Phone (QR scan) |

### 2.3 Access Rights by Role

Table 2.3 defines which role may perform each action. “Own” means the user’s own records; “Assigned” means the records of students placed under that supervisor. FR-AUT-05 requires the server to enforce this table.

**Table 2.3 – Permission matrix**

| **Action** | **ST** | **CS** | **AS** | **CO** | **Public** |
|:---|:--:|:--:|:--:|:--:|:--:|
| Manage accounts; import CSV files | — | — | — | All | — |
| Configure cycles, rubric, grade weights, skill vocabulary | — | — | — | All | — |
| Edit profile, upload CV, confirm skills | Own | — | — | — | — |
| Create a vacancy | — | Own company | — | All | — |
| Publish, return, or close a vacancy | — | — | — | All | — |
| View ranked vacancies and apply | Own | — | — | — | — |
| Review applicants of a vacancy | — | Own vacancies | — | All | — |
| Confirm or cancel a placement | — | — | — | All | — |
| Submit weekly and final reports | Own | — | — | — | — |
| View reports | Own | Assigned (read) | Assigned | All | — |
| Accept a report or request revision | — | — | Assigned | — | — |
| Record attendance | — | Assigned | — | Unlock only | — |
| Submit periodic and final evaluations | — | Assigned | — | Reopen only | — |
| View similarity flags and record a decision | — | — | Assigned | View all | — |
| Enter and submit a grade | — | — | Assigned | — | — |
| Approve, return, or reopen a grade | — | — | — | All | — |
| View a final grade | Own | — | Assigned | All | — |
| Evaluate the training entity | Own | — | — | View all | — |
| Export grade sheets and reports | — | — | Assigned (records) | All | — |
| Issue or revoke a certificate | — | — | — | All | — |
| Verify a certificate | — | — | — | — | Yes |
| View the audit log | — | — | — | All | — |

## 3. Overall Description

### 3.1 Product Perspective

InternSync is a new, self-contained system that replaces the current mix of email, spreadsheets, and paper forms. It has no live connection to university systems: student and staff data enter through CSV files, and grades leave as exported PDF and Excel files. Figure 3.1 shows the system boundary, its users, and the external services it depends on.

![Figure 3.1 – Context diagram](../InternSync_Diagrams/png/02_context.png)

**Figure 3.1 – Context diagram**

Inside the boundary, a React PWA client talks to a single Python/FastAPI backend that also hosts the AI services (skill extraction, matching, similarity). PostgreSQL with pgvector stores relational data and embeddings, a scheduler runs reminder and escalation jobs, and file storage keeps CVs and attachments. These components are named only to show the boundary; their design is described in the design document (task T2).

### 3.2 Co-op Life Cycle Supported

1.  The coordinator opens a training cycle, imports students and academic supervisors from CSV files, and creates company supervisor accounts.

2.  Company supervisors submit vacancies; the coordinator reviews and publishes them.

3.  Students build their profiles, upload CVs, confirm the extracted skills, view vacancies ranked by fit with an explanation, and apply.

4.  Company supervisors accept or decline applicants; the coordinator confirms placements and assigns academic supervisors.

5.  During training, students submit weekly reports, company supervisors record attendance weekly and submit the periodic evaluation, and the system sends reminders and late flags.

6.  Academic supervisors review reports with the similarity indicator and accept them or request revisions.

7.  At the end of training, the student submits the final report, the company supervisor submits the final evaluation, and the grade passes through the approval workflow.

8.  The coordinator exports grade sheets and summaries and issues certificates; students evaluate the training entity and answer the outcome survey.

### 3.3 Use Case Overview

**Table 3.1 – Use cases**

| **UC** | **Use case** | **Primary actor** | **Requirements** |
|:--:|:---|:--:|:---|
| UC-01 | Open a training cycle and import users | CO | FR-CYC-01 – 04, FR-PRF-01, FR-AUT-02 |
| UC-02 | Activate account, log in, reset password | All roles | FR-AUT-01 – 04 |
| UC-03 | Build profile and confirm CV skills | ST | FR-PRF-02 – 05 |
| UC-04 | Submit and publish a vacancy | CS, CO | FR-VAC-01, FR-VAC-02 |
| UC-05 | View ranked vacancies and apply | ST | FR-VAC-03 – 05, FR-MAT-01 – 07 |
| UC-06 | Review applicants and confirm placement | CS, CO | FR-VAC-06 – 08 |
| UC-07 | Submit a weekly or final report | ST | FR-REP-01 – 04 |
| UC-08 | Review a report and check similarity | AS | FR-REP-05 – 07, FR-SIM-01 – 03 |
| UC-09 | Record weekly attendance | CS | FR-ATT-01 – 04 |
| UC-10 | Submit a periodic or final evaluation | CS | FR-EVL-01 – 04 |
| UC-11 | Enter, submit, and approve a grade | AS, CO | FR-WFL-02 – 07 |
| UC-12 | Export grade sheets and summaries | CO | FR-EXP-01 – 03 |
| UC-13 | Issue and verify a certificate | CO, Public | FR-CER-01 – 03 |
| UC-14 | Evaluate the training entity and answer the survey | ST | FR-EVL-05, FR-DSH-03 |
| UC-15 | Send reminders, late flags, and escalations | Scheduler (system timer) | FR-REP-04, FR-NOT-02 – 04 |

### 3.4 Operating Environment

- **Client:** current versions of Chrome, Edge, Firefox, and Safari on desktop, and Chrome and Safari on phones (NFR-PRT-01); installable as a PWA.

- **Server (reference demonstration deployment, zero cost):** the API container (FastAPI, embedding model, and scheduler) runs on Hugging Face Spaces, free CPU Basic hardware (2 vCPU, 16 GB RAM, no GPU); PostgreSQL with pgvector and the private file storage run on Supabase (Free plan); the PWA static build is served by Vercel (Hobby plan). The same containers also run on any Linux server with Docker Compose (minimum 2 vCPU and 4 GB RAM; NFR-PRT-02). No GPU is required.

- **Software:** Python with FastAPI; React with Vite; PostgreSQL 16 or later with pgvector; an open-source multilingual embedding model (for example, multilingual-e5-small) running inside the API container.

- **Time zone:** all deadlines are defined and evaluated in Saudi Arabia time (Asia/Riyadh, UTC+3).

### 3.5 User Documentation

- A bilingual quick-start guide for each role (PDF, at most 4 pages each).

- Help text on the main forms (report, attendance, evaluation, grade).

- A deployment and setup guide for the technical team (NFR-PRT-02).

## 4. Functional Requirements

Functional requirements are grouped by area. In each table, the acceptance criterion states the observable result that a test must confirm. Values marked “default” are configurable (NFR-MNT-03).

### 4.1 Accounts, Authentication, and Access Control

*Source: F1 · Objective O1*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-AUT-01** | The system shall support four roles — Student, Company Supervisor, Academic Supervisor, and Coordinator — and each account shall hold exactly one role. The Coordinator also performs system administration in this release. | Must | A user of each role logs in and sees only the menu items of that role. |
| **FR-AUT-02** | The system shall not offer public self-registration. The Coordinator shall create accounts one at a time or through CSV import (FR-PRF-01), and the system shall email each new user a one-time activation link valid for 72 hours (default). | Must | No registration page exists; an activation link works once; a used or expired link is rejected with a message. |
| **FR-AUT-03** | Users shall log in with email and password. A session shall end after 30 minutes of inactivity (default), and users shall be able to log out at any time. | Must | After 30 idle minutes the next action returns to the login page; after logout the old token is rejected. |
| **FR-AUT-04** | The system shall let a user reset a forgotten password through an emailed one-time link valid for 60 minutes. | Must | The link resets the password once; the old password stops working; an expired link is rejected. |
| **FR-AUT-05** | The system shall enforce the permission matrix of Table 2.3 on the server for every request: supervisors reach only the records of students assigned to them, and students only their own records. | Must | Automated permission tests cover every API endpoint for every role, with 0 failing tests (O1). |
| **FR-AUT-06** | The Coordinator shall be able to deactivate and reactivate accounts. A deactivated user cannot log in, and the records that user created remain unchanged. | Must | Login of a deactivated user fails; the user’s past reports and evaluations stay visible to authorized users. |

### 4.2 Training Cycles and Configuration

*Source: supports F3, F5, F7, F8 · Objectives O3, O4*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-CYC-01** | The Coordinator shall create a training cycle with a name, type (Co-op or Summer), start and end dates, number of training weeks, weekly working days (used for attendance, A-08), weekly report deadline (weekday and time), and due dates for the periodic evaluation, final evaluation, and final report. | Must | Creating a 12-week cycle generates 12 weekly deadlines on the configured weekday and time; each week's scheduled days equal the configured working days. |
| **FR-CYC-02** | The Coordinator shall define the grade components of a cycle and their weights; the system shall reject weights that do not sum to 100%. | Must | Weights 40/30/20 are rejected; 40/30/30 are saved. |
| **FR-CYC-03** | The Coordinator shall define one evaluation rubric per cycle: a list of criteria, each with a description for every level of a 1–5 scale. After the first evaluation of the cycle is submitted, the rubric shall become read-only. | Must | After one evaluation is submitted, editing the rubric is refused. |
| **FR-CYC-04** | The Coordinator shall maintain the skill vocabulary: each skill has an English name, an Arabic name, synonyms, and optional learning resources (title, link, estimated effort). | Must | A skill with the synonym “JS” is recognized in a CV containing “JS” and is shown as “JavaScript”. |
| **FR-CYC-05** | The Coordinator shall be able to close a cycle, which makes its records read-only; reopening a closed cycle requires a written reason, recorded in the audit log. | Should | Edits in a closed cycle are refused; reopening without a reason is refused. |

### 4.3 Student Profile, CV, and Data Import

*Source: F2 · Objectives O2, O7*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-PRF-01** | The Coordinator shall import students and academic supervisors from CSV files in the formats of Section 6.3.1. The system shall validate every row, create accounts for valid rows, and show an import report listing each rejected row with its reason (missing field, invalid email, duplicate ID). | Must | A 50-row file with 3 invalid rows creates 47 accounts and lists exactly the 3 rejected rows with reasons. |
| **FR-PRF-02** | A student shall maintain a profile with major and GPA (imported and read-only), confirmed skills, languages, and areas of interest. | Must | The student can edit skills and interests but not major or GPA. |
| **FR-PRF-03** | A student shall upload a CV as a PDF or DOCX file of up to 5 MB. The latest CV is used for matching, and earlier versions are kept. | Must | A 6 MB file or another file type is refused; after a second upload both versions appear in the CV history. |
| **FR-PRF-04** | After each CV upload, the system shall extract candidate skills from the CV text (Arabic or English), normalize them with the skill vocabulary, and show them to the student, who can add, edit, or remove skills before confirming. Only confirmed skills shall be used for matching. | Must | On a labelled set of 20 CVs (10 Arabic, 10 English), at least 70% of the skills listed by the annotators appear in the extracted list. |
| **FR-PRF-05** | If no text can be extracted from a CV (for example, a scanned image), the system shall inform the student and allow manual skill entry. | Must | Uploading an image-only PDF shows the message and an empty, editable skill list. |

### 4.4 Vacancies and Placement

*Source: F3 · Objective O1*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-VAC-01** | A Company Supervisor or the Coordinator shall create a vacancy with title, company, city, description, required skills, preferred skills, eligible majors, optional minimum GPA, number of seats, application deadline, and cycle. | Must | A vacancy missing a required field cannot be saved; a saved vacancy shows all fields. |
| **FR-VAC-02** | A vacancy has one of the statuses Draft, Pending Review, Published, or Closed. A vacancy created by a Company Supervisor shall become visible to students only after the Coordinator publishes it; the Coordinator may return it with a comment. A vacancy created by the Coordinator is published directly. | Must | Students cannot see a Pending Review vacancy; after publication it appears in their list. |
| **FR-VAC-03** | Students shall browse the published vacancies of their cycle, search by keyword, and filter by city, company, eligible major, and skill. | Must | Each filter returns only vacancies that satisfy it (checked on seeded data). |
| **FR-VAC-04** | A student shall apply to an open vacancy for which they are eligible, before its deadline. The system shall prevent duplicate applications and limit active applications to 5 per student (default). | Must | A second application to the same vacancy, an application after the deadline, and a sixth active application are each refused with a message. |
| **FR-VAC-05** | A student shall be able to withdraw an application until a decision has been made on it. | Should | The withdrawn application leaves the applicant list and frees an application slot. |
| **FR-VAC-06** | A Company Supervisor shall view the applicants to their own vacancies (profile, confirmed skills, CV) and mark each applicant Accepted or Declined. | Must | The supervisor sees applicants of own vacancies only; the decision is visible to the student and the Coordinator. |
| **FR-VAC-07** | The Coordinator shall confirm the placement of an accepted applicant by assigning the student to the vacancy, its Company Supervisor, and an Academic Supervisor. A student shall have at most one confirmed placement per cycle; confirming it withdraws the student’s other active applications, and a vacancy closes automatically when its seats are filled. | Must | A second placement for the same student is refused; filling the last seat changes the vacancy to Closed. |
| **FR-VAC-08** | The Coordinator shall be able to change a student’s Academic Supervisor or cancel a placement, giving a mandatory reason. | Should | The action without a reason is refused; the change appears in the audit log. |

### 4.5 Matching and Explanation

*Source: F4, F11 · Objectives O2, O7*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-MAT-01** | For a student with confirmed skills, the system shall rank the open vacancies of the student’s cycle for which the student is eligible by a fit score from 0 to 100, in descending order. | Must | On a labelled set of at least 20 student profiles, at least one relevant vacancy is in the top 5 for at least 80% of profiles (O2). |
| **FR-MAT-02** | The fit score shall combine the semantic similarity between the student’s CV and profile and the vacancy text (multilingual embeddings) with rule-based criteria: required-skill overlap, eligible major, and minimum GPA. | Must | Of two otherwise identical vacancies, the one whose required skills the student has scores higher (unit test). |
| **FR-MAT-03** | Vacancies for which the student is not eligible (major not listed, or GPA below the minimum) shall not appear in the ranked list; they stay visible in browsing with the reason. | Must | A vacancy with a minimum GPA above the student’s GPA is absent from the ranking and shows “GPA below minimum” when browsing. |
| **FR-MAT-04** | If the embedding model is unavailable or a text has no embedding, the system shall rank with the rule-based score only and label the results “Basic matching”. | Must | With the model service stopped, the ranking is still returned within the limit of NFR-PER-02 and carries the label. |
| **FR-MAT-05** | For each ranked vacancy, the system shall show the student’s matched skills and the missing required skills. | Should | In every test case the lists equal the set comparison of the student’s confirmed skills and the vacancy’s required skills after normalization. |
| **FR-MAT-06** | For a vacancy selected by the student, the system shall produce a development plan listing each missing skill with the learning resources linked to it in the skill vocabulary, or “No resource available yet”. | Should | Every missing skill appears in the plan; skills with linked resources show at least one resource. |
| **FR-MAT-07** | Matching results shall be labelled advisory. The ranking shall not prevent a student from applying to any eligible vacancy and shall never accept or decline applicants automatically. | Must | A student can apply to the lowest-ranked eligible vacancy; no application status changes without a human action. |

### 4.6 Weekly and Final Reports

*Source: F5 · Objective O3*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-REP-01** | For each confirmed placement, the system shall create one report slot per training week and one final report slot, each with the deadline set in the cycle. | Must | A placement in a 12-week cycle has 12 weekly slots and 1 final slot with the correct deadlines. |
| **FR-REP-02** | A student shall submit a weekly report with tasks performed, what was learned, challenges, and the plan for next week, and up to 3 attachments (PDF, DOCX, PNG, or JPG, up to 10 MB each). The final report accepts one main document and up to 3 attachments. | Must | A fourth attachment or an 11 MB file is refused; a valid submission is stored with all its files. |
| **FR-REP-03** | A student shall be able to save a report as a draft. After submission the report is read-only for the student unless a revision is requested. | Must | Editing after submission is refused; supervisors cannot see drafts. |
| **FR-REP-04** | The system shall record the server time of every submission. A report submitted after its deadline is flagged Late, and a slot with no submission at its deadline is flagged Missing; both flags stay in the record. Late submission remains possible until the Academic Supervisor closes the slot (FR-REP-07). | Must | Submissions 1 minute before and 1 minute after the deadline are flagged On time and Late; an empty slot shows Missing within 1 hour after the deadline (O3). |
| **FR-REP-05** | The Academic Supervisor shall accept a submitted report or request a revision with a mandatory comment. The student then resubmits, and every version is kept. | Must | A revision request without a comment is refused; after resubmission both versions can be viewed. |
| **FR-REP-06** | The student and the Academic Supervisor shall be able to exchange comments on a report; the student’s Company Supervisor shall be able to read the student’s reports. | Must | A comment appears to the other party with author and time; the Company Supervisor has read-only access. |
| **FR-REP-07** | The Academic Supervisor shall be able to close a report slot that has no submission, which makes it final as Missing and ends late submission for that slot. | Must | After closing, the student cannot submit to that slot. |

### 4.7 Attendance

*Source: F6 · Objective O1*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-ATT-01** | For each training week, the Company Supervisor shall record the days the student attended out of the scheduled working days, with an optional note on absences. A single action shall record full attendance. | Must | “Full attendance” records attended days equal to scheduled days in one action. |
| **FR-ATT-02** | Attendance for a week shall be editable by the Company Supervisor until 7 days after the week ends (default); later changes require the Coordinator to unlock the week. | Should | An edit on day 8 is refused until the week is unlocked; the unlock is in the audit log. |
| **FR-ATT-03** | The system shall show the attendance record and attendance percentage of a student to the student, both supervisors, and the Coordinator. | Must | The percentage equals attended days divided by scheduled days for seeded data. |
| **FR-ATT-04** | A week whose attendance is not recorded within 3 days after it ends (default) shall appear as a pending action on the Company Supervisor’s dashboard. | Must | A seeded unrecorded week appears on the dashboard on day 4. |

### 4.8 Evaluations

*Source: F7, F17 · Objective O4*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-EVL-01** | The Company Supervisor shall submit a periodic evaluation and a final evaluation for each assigned student using the cycle rubric: every criterion rated 1–5 against its level descriptions, plus a mandatory overall comment. | Must | The form cannot be submitted while any criterion is unrated or the comment is empty. |
| **FR-EVL-02** | All evaluations in a cycle shall use the same rubric version; the system shall not allow company-specific criteria. | Must | 100% of the evaluations in a test cycle reference one rubric version (O4). |
| **FR-EVL-03** | A periodic evaluation shall be visible to the student and the Academic Supervisor as soon as it is submitted; a final evaluation becomes visible to the student when the grade is Final. | Must | The student sees the periodic evaluation immediately and the final evaluation only after the grade is Final. |
| **FR-EVL-04** | A submitted evaluation shall be read-only. At the Company Supervisor’s request, the Coordinator may reopen it once with a written reason. | Should | Editing a submitted evaluation is refused; the reopening is in the audit log. |
| **FR-EVL-05** | At the end of the placement, the student shall be able to evaluate the training entity (learning opportunities, supervision quality, work environment, relevance to the major, and whether they would recommend it). Responses are visible to the Coordinator only, never to the Company Supervisor. | Could | A Company Supervisor account cannot access any student evaluation of a company (permission test). |

### 4.9 Approval Workflow and Grades

*Source: F8 · Objective O6*

Reports and grades are controlled by explicit state machines. Figure 4.1 shows the life cycle of a report slot, and Figure 4.2 the life cycle of a grade. Late and Missing are flags set by the deadline check (FR-REP-04), not separate states.

![Figure 4.1 – Report state machine](../InternSync_Diagrams/png/04a_report_states.png)

**Figure 4.1 – Report state machine**

![Figure 4.2 – Grade approval state machine](../InternSync_Diagrams/png/04b_grade_states.png)

**Figure 4.2 – Grade approval state machine**

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-WFL-01** | Weekly and final reports shall follow the state machine of Figure 4.1 (Draft, Submitted, Revision Requested, Accepted, Closed as Missing). Any transition not shown shall be rejected. | Must | An automated test exists for every allowed transition and for at least one disallowed transition from each state; all pass. |
| **FR-WFL-02** | The grade of a placement shall be the weighted sum of the cycle’s grade components (FR-CYC-02). The company-evaluation component is computed from the final evaluation as the mean rubric score ÷ 5 × 100; the other components are entered by the Academic Supervisor. | Must | For seeded inputs the computed grade equals a hand calculation to two decimal places. |
| **FR-WFL-03** | Grades shall follow the state machine of Figure 4.2. The Academic Supervisor can submit a grade only when the final evaluation is submitted, the final report is Accepted, and every weekly slot is Accepted or Closed as Missing. | Must | Submitting with any condition unmet is refused with a list of the missing items. |
| **FR-WFL-04** | The Coordinator shall approve a submitted grade, which makes it Final, or return it to the Academic Supervisor with a mandatory comment. | Must | Returning without a comment is refused; approval sets the status to Final with a timestamp. |
| **FR-WFL-05** | A Final grade shall be locked. Only the Coordinator may reopen it, with a mandatory reason; reopening returns it to Draft and notifies the student and the Academic Supervisor. | Must | Editing a Final grade is refused; reopening without a reason is refused; reopening is in the audit log. |
| **FR-WFL-06** | A student shall see their grade only when it is Final. | Must | The grade is hidden from the student in the Draft and Submitted states. |
| **FR-WFL-07** | The Coordinator shall be able to approve several submitted grades in one action; each approval is recorded separately. | Should | A bulk approval of 10 grades creates 10 audit entries. |

### 4.10 Similarity Detection

*Source: F12 · Objective O5*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-SIM-01** | When a report is submitted, the system shall compare it with all reports stored in the system (all students and all cycles), excluding earlier versions of the same report by the same student. | Should | A report copied from a previous cycle’s report is compared and flagged. |
| **FR-SIM-02** | If the similarity score with any stored report reaches the threshold (default 30%), the system shall flag the report and show the Academic Supervisor the score, the source report reference (cycle and week), and the matching passages side by side. The identity of the source report’s author is shown only to the Coordinator. | Should | Of 10 seeded reports with 40% or more copied text, at least 9 are flagged with passages shown; at most 1 of 10 independently written reports is flagged (O5). |
| **FR-SIM-03** | A similarity flag shall be advisory: the Academic Supervisor records a decision (No issue or Overlap confirmed) with a comment, and the system shall never change a report status or a grade because of a similarity score. | Should | A flagged report’s status changes only through the actions of FR-REP-05. |

### 4.11 Notifications

*Source: F13 · Objective O3*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-NOT-01** | Each user shall have an in-app notification list with an unread count; event notifications are also sent by email. | Should | Each event of FR-NOT-05 produces one in-app notification and one email. |
| **FR-NOT-02** | The system shall remind a student 24 hours before a report deadline (default) if the report has not been submitted. | Should | Reminders are sent only for unsubmitted slots, between 24 and 23 hours before the deadline. |
| **FR-NOT-03** | Within 1 hour after a deadline, the system shall notify the student and the Academic Supervisor of each Missing report. | Should | Notifications for all seeded missing reports arrive within 1 hour (O3). |
| **FR-NOT-04** | The system shall escalate to the Coordinator any report, attendance week, or evaluation still outstanding 3 days after its deadline (default). | Should | An escalation appears for each seeded overdue item on day 4. |
| **FR-NOT-05** | The system shall notify the user who must act, or whose record changed, when: a vacancy is returned or published, an application is decided, a placement is confirmed, a revision is requested, a report is accepted, an evaluation is submitted, or a grade is returned, made Final, or reopened. | Should | Each listed event produces a notification to the right user in a scripted test. |
| **FR-NOT-06** | Notifications and emails shall be sent in the recipient’s chosen language. | Should | A user with Arabic selected receives the Arabic email. |

### 4.12 Dashboards and Statistics

*Source: F9, F18, F19 · Objectives O1, O4, O10*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-DSH-01** | Each role shall have a home dashboard listing its pending actions with counts and direct links — ST: reports due, revisions requested, application status; CS: applicants to review, attendance to record, evaluations due; AS: reports to review, open similarity flags, grades to submit; CO: vacancies to publish, placements to confirm, grades to approve, escalations. | Must | For a seeded scenario, every count equals the number of pending items in the database. |
| **FR-DSH-02** | The Coordinator dashboard shall show the cycle status: students placed and not placed, report submission and late rates, attendance rate, and evaluation completion, overall and per company. | Must | Every figure equals the value computed directly from seeded data. |
| **FR-DSH-03** | At the end of a cycle, the system shall offer students a short survey (job offer from the training company: Yes, No, or Pending), and the Coordinator dashboard shall show the placement-to-job-offer rate per cycle and per company. | Could | The rate equals Yes answers divided by survey answers for seeded data (O10). |
| **FR-DSH-04** | For each company with at least 5 final evaluations, the system shall alert the Coordinator when the company’s mean rubric score is at least 0.8 points above the cycle mean (default). The alert is informational only. | Could | A seeded company with 5 evaluations averaging 4.8 against a cycle mean of 3.6 raises the alert; a company with 4 evaluations does not. |

### 4.13 Exports

*Source: F14 · Objective O6*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-EXP-01** | The Coordinator shall export the grade sheet of a cycle as Excel (.xlsx) and PDF, listing student ID, name, company, academic supervisor, each component score, total, and grade status. | Should | Exported values match stored values in 100% of rows; Arabic names display correctly in both files. |
| **FR-EXP-02** | The Coordinator shall export a term summary report (PDF) with the cycle statistics of FR-DSH-02, for the college administration. | Should | The PDF figures equal the dashboard figures. |
| **FR-EXP-03** | The Coordinator and the student’s Academic Supervisor shall export a student’s training record (PDF): placement details, weekly report statuses, attendance, evaluations, and final grade. | Should | The record matches the stored data for a seeded student. |

### 4.14 Completion Certificates

*Source: F16 · Objective O9*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-CER-01** | When a grade is Final, the Coordinator shall issue a completion certificate (PDF) with a unique, unguessable certificate ID and a QR code linking to the public verification page. | Could | A certificate cannot be issued for a grade that is not Final; the QR code opens the correct verification page. |
| **FR-CER-02** | The public verification page shall require no login and shall show only the certificate status (Valid, Revoked, or Not found), student name, cycle, company, and training dates. | Could | Valid, revoked, and altered IDs show Valid, Revoked, and Not found respectively (O9); no grade is shown. |
| **FR-CER-03** | The Coordinator shall be able to revoke a certificate with a mandatory reason. | Could | After revocation the verification page shows Revoked. |

### 4.15 Language and PWA Features

*Source: F10, F15 · Objectives O7, O1*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-LOC-01** | Users shall switch the interface between Arabic and English at any time, and the choice is saved per user. Arabic uses a right-to-left layout and English a left-to-right layout. | Must | Switching the language mirrors the layout on every screen of Table 6.1. |
| **FR-LOC-02** | All interface text, validation messages, notification texts, and email templates shall exist in both languages; user-entered content is shown as entered. | Must | An automated check finds no missing translation keys in either language. |
| **FR-PWA-01** | The application shall be installable as a PWA on supported browsers. | Should | The app installs from Chrome on Android and from Safari on iOS (Add to Home Screen) and opens full screen. |
| **FR-PWA-02** | Users who grant permission shall receive web push notifications for the events of FR-NOT-05; email remains the fallback. | Should | With permission the push arrives; with permission denied the email still arrives. |
| **FR-PWA-03** | The app shell shall be cached so the application opens offline and shows an offline message. Submissions are not accepted offline. | Should | In airplane mode the app opens with the offline message and submit buttons are disabled. |

### 4.16 Audit Trail

*Source: Proposal opportunity statement (auditable record) · Objective O6*

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **FR-AUD-01** | The system shall record an audit entry for every creation, change, and state transition of accounts, vacancies, placements, reports, attendance, evaluations, grades, and certificates: user, role, server time, action, and old and new values. | Must | Each action in the UAT script produces exactly one matching audit entry. |
| **FR-AUD-02** | Audit entries shall be append-only: no role can edit or delete them through the system. The Coordinator shall be able to filter the audit log by student, user, record type, and date. | Must | No API endpoint updates or deletes audit entries (permission test); filters return the correct entries. |
| **FR-AUD-03** | Each report, evaluation, and grade shall show its history (state changes with user and time) to users allowed to view the record. | Should | The history shown matches the audit entries. |

## 5. Non-Functional Requirements

Non-functional requirements state measurable qualities. Performance targets apply to the reference demonstration deployment (Section 3.4) loaded with the data volumes of Table 2.2.

### 5.1 Performance

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **NFR-PER-01** | For ordinary operations (open a dashboard, open or submit a form, list vacancies), 95% of requests shall complete within 2 seconds with 50 concurrent users. | Must | Load test (e.g., Locust) on the reference deployment with seeded data. |
| **NFR-PER-02** | The ranked vacancy list for one student shall be returned within 5 seconds for up to 300 open vacancies, also when the rule-based fallback is used. | Must | Timed test, 20 runs, 95th percentile. |
| **NFR-PER-03** | Extracted skills shall be shown within 30 seconds after uploading a CV of up to 5 MB. | Must | Timed test on the 20 labelled CVs. |
| **NFR-PER-04** | The similarity result of a submitted report shall be available within 2 minutes with up to 10,000 stored reports. | Should | Timed test with seeded reports. |
| **NFR-PER-05** | Grade sheets for a 100-student cohort shall be exported to PDF and to Excel in under 60 seconds each (O6). | Should | Timed export test. |

### 5.2 Security

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **NFR-SEC-01** | All traffic shall use HTTPS (TLS 1.2 or later); HTTP requests are redirected to HTTPS. | Must | Configuration inspection; an HTTP request is redirected. |
| **NFR-SEC-02** | Passwords shall be stored only as salted hashes with an adaptive algorithm (bcrypt or Argon2) and must have at least 8 characters with letters and digits. | Must | Database inspection shows no plain passwords; a weak password is refused. |
| **NFR-SEC-03** | After 5 consecutive failed login attempts, the account shall be locked for 15 minutes. | Must | The 6th attempt is refused even with the correct password; login works after 15 minutes. |
| **NFR-SEC-04** | Uploaded files shall be checked by content type and size, stored outside the public web root, and served only through links that check the requester’s permission. | Must | An executable renamed to .pdf is refused; a file URL requested without permission returns 403. |
| **NFR-SEC-05** | At release, an OWASP ZAP baseline scan shall report no high-risk findings, and dependency audits (pip-audit, npm audit) shall report no known critical vulnerabilities. | Should | Scan and audit reports attached to the test report. |

### 5.3 Privacy and Data Protection

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **NFR-PRV-01** | At first login, each user shall see a consent notice in their language explaining what personal data is processed and why; the system stores the time of acknowledgement. | Must | First login cannot continue until the notice is acknowledged; the timestamp is stored. |
| **NFR-PRV-02** | CV and report text shall be processed only by models running on the system’s own server; no personal data is sent to external AI services. | Must | Code and network-configuration inspection shows no outbound calls to AI services. |
| **NFR-PRV-03** | Each role shall see only the personal data needed for its tasks (Table 2.3); push notification payloads shall contain no personal data beyond the event title. | Must | Permission tests; inspection of push payloads. |
| **NFR-PRV-04** | The Coordinator shall be able to anonymize the personal data (names, contact details, CV files) of a closed cycle after the retention period set by the college, keeping anonymized statistics. | Could | After anonymization no name or CV of that cycle can be retrieved, and the statistics are unchanged. |

### 5.4 Usability and Accessibility

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **NFR-USA-01** | In user acceptance testing with at least 8 participants covering all four roles, at least 80% of the test scenarios shall be completed without help (O8). | Must | UAT results in the test report. |
| **NFR-USA-02** | Every pending action on a dashboard shall open with one click, and submitting a report, recording attendance, or submitting an evaluation shall take no more than 3 screens. | Must | Walkthrough of the main tasks against the screen flow. |
| **NFR-USA-03** | All screens shall be usable at widths from 360 px to 1920 px without horizontal scrolling. | Must | Each screen of Table 6.1 checked at 360, 768, 1366, and 1920 px. |
| **NFR-USA-04** | Text shall have a contrast ratio of at least 4.5:1, and the main tasks shall be operable with the keyboard alone (WCAG 2.1 AA subset). | Should | Automated contrast check (e.g., Lighthouse) and a keyboard walkthrough. |
| **NFR-USA-05** | Error messages shall state what went wrong and how to correct it, in the user’s language, next to the field concerned. | Should | Review of all form validation messages. |

### 5.5 Localization

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **NFR-L10N-01** | 100% of screens shall be available in Arabic and English with correct RTL and LTR layout (O7). | Must | Screen checklist reviewed in both languages. |
| **NFR-L10N-02** | Deadlines shall be defined and evaluated in Saudi Arabia time (UTC+3); timestamps are stored in UTC and displayed in local time as DD/MM/YYYY HH:mm. | Must | With a 23:59 deadline, a submission at 23:58 is On time and one at 00:00 is Late. |
| **NFR-L10N-03** | Arabic text in PDF exports shall render with correct letter joining and right-to-left order, using an embedded Arabic font. | Should | Visual check of exported PDFs containing Arabic names. |
| **NFR-L10N-04** | Skill extraction, matching, and similarity shall support Arabic, English, and mixed-language text; the target of FR-MAT-01 shall be met on the Arabic and the English test profiles separately (O7). | Must | Evaluation results reported per language subset. |

### 5.6 Reliability and Availability

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **NFR-REL-01** | During the testing phase, unplanned downtime of the demo server shall not exceed 1 hour per week, and the system shall be available for every scheduled UAT session and the final demonstration. | Must | Uptime monitor log. |
| **NFR-REL-02** | The database and uploaded files shall be backed up automatically every day; a restore shall be tested at least once before final delivery (maximum data loss: 24 hours). | Should | Restore test recorded in the test report. |
| **NFR-REL-03** | Scheduled jobs shall run at least every 15 minutes, shall not send the same reminder or escalation twice, and jobs missed while the server was down shall run within 1 hour after restart. | Should | Restart test during a deadline window. |
| **NFR-REL-04** | A submission shall be saved completely or not at all: if any attachment fails, the report is not marked Submitted and the draft is kept. | Must | Fault-injection test during upload. |

### 5.7 Maintainability and Portability

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **NFR-MNT-01** | Automated tests shall run on every pull request and cover at least 70% of the lines of the backend business-logic modules; a pull request with failing tests is not merged. | Must | CI coverage report. |
| **NFR-MNT-02** | The API shall be documented by an OpenAPI specification generated from the code, from which the frontend client is generated. | Must | Specification published by the server matches the implemented endpoints. |
| **NFR-MNT-03** | Every value marked “default” in this SRS (deadlines, limits, thresholds, reminder times) shall be changeable by the Coordinator or through configuration, without changing code. | Must | Each default is changed during testing and takes effect without a code change. |
| **NFR-PRT-01** | The application shall work on the two latest major versions of Chrome, Edge, Firefox, and Safari on desktop, and of Chrome on Android and Safari on iOS. | Must | Smoke test of the main tasks on each browser. |
| **NFR-PRT-02** | The whole system shall be deployable with one Docker Compose command on a Linux server, following a written setup guide. | Must | A team member who did not write the guide deploys it on a clean machine. |

### 5.8 AI Quality and Transparency

| **ID** | **Requirement** | **Priority** | **Acceptance criterion** |
|:---|:---|:--:|:---|
| **NFR-AI-01** | Every AI output (fit score, matched and missing skills, extracted skills, similarity flag) shall be labelled advisory and shown with its reason, and no AI output shall change the status of an application, placement, report, or grade without a human action. | Must | Inspection of every screen showing AI output; state-transition tests (FR-WFL-01). |
| **NFR-AI-02** | The model name and version shall be stored with each fit score and similarity result so that results can be reproduced. | Should | Inspection of stored results. |
| **NFR-AI-03** | The labelled evaluation sets (20 CVs and student profiles, 10 copied and 10 original reports) and the evaluation script shall be kept in the repository so the measurements of FR-PRF-04, FR-MAT-01, and FR-SIM-02 can be repeated. | Must | Running the script reproduces the reported numbers. |

## 6. External Interface Requirements

### 6.1 User Interfaces

- After login, each role lands on its dashboard (FR-DSH-01); navigation shows only the functions of that role.

- Every screen has a header with the language switch (العربية / English), the notification list, and the user menu.

- Arabic mode mirrors the whole layout (navigation, tables, directional icons) and uses an Arabic web font.

- Statuses (Draft, Submitted, Late, Missing, Accepted, Final, and so on) appear as labelled chips with text and color, never color alone.

- Forms validate fields inline and keep entered data when an error occurs.

- AI results appear in a separate panel labelled “Advisory”, together with their reason.

- The visual design follows the design system produced in Claude Design and Figma Make during task T3 (SPMP).

**Table 6.1 – Main screens**

| **Screen** | **Roles** | **Purpose (requirements)** |
|:---|:--:|:---|
| Login, activation, password reset | All | Access the system (FR-AUT-02 – 04) |
| Dashboard | All | Pending actions and status (FR-DSH-01 – 04) |
| Profile and CV | ST | Profile, CV upload, skill confirmation (FR-PRF-02 – 05) |
| Vacancies (browse and ranked) | ST | Browse, filter, ranked list with explanation, apply (FR-VAC-03 – 05, FR-MAT-01 – 07) |
| Vacancy editor and applicants | CS, CO | Create vacancies, review applicants (FR-VAC-01, FR-VAC-02, FR-VAC-06) |
| Placements | CO | Confirm placements, assign supervisors (FR-VAC-07, FR-VAC-08) |
| Report form and history | ST, AS, CS | Submit, review, comment, similarity panel (FR-REP-01 – 07, FR-SIM-02) |
| Attendance | CS | Weekly attendance (FR-ATT-01 – 03) |
| Evaluation form | CS, ST | Rubric evaluation; student evaluation of the company (FR-EVL-01 – 05) |
| Grades | AS, CO | Enter, submit, approve, reopen grades (FR-WFL-02 – 07) |
| Cycle settings | CO | Cycle, rubric, weights, vocabulary, defaults (FR-CYC-01 – 05) |
| Users and import | CO | Accounts and CSV import (FR-AUT-02, FR-AUT-06, FR-PRF-01) |
| Exports and certificates | CO, AS | Grade sheets, summaries, records, certificates (FR-EXP-01 – 03, FR-CER-01, FR-CER-03) |
| Audit log | CO | Search audit entries (FR-AUD-02) |
| Certificate verification | Public | Verify a certificate (FR-CER-02) |

Wireframes of these screens are produced in task T3 and will be included in the design document.

### 6.2 Hardware Interfaces

InternSync has no direct hardware interface. Users work from standard desktops, laptops, and phones. A certificate is verified by scanning its QR code with any phone camera, which opens the verification URL. The server side runs on hosted free tiers (Section 3.4) or on any Linux server with Docker (minimum 2 vCPU and 4 GB RAM); no GPU is needed because the embedding model is small enough to run on the CPU.

### 6.3 Software Interfaces

**Table 6.2 – Software interfaces**

| **Interface** | **Purpose** | **Data exchanged** | **Notes** |
|:---|:---|:---|:---|
| PostgreSQL 16 or later with pgvector (Supabase in the reference deployment) | Store relational data and text embeddings | SQL over TLS | Reached only by the API with a dedicated database role; the Supabase auto-generated Data API is disabled. |
| File storage (Supabase Storage private bucket; a local volume under Docker Compose) | Store CVs, report attachments, exports, and certificates | Files in and out | Reached only by the API; downloads use short-lived signed links issued after a permission check (NFR-SEC-04). |
| Multilingual embedding model (e.g., multilingual-e5-small via sentence-transformers) | Embeddings for matching and similarity | Text in, vector out | Runs on the server (NFR-PRV-02); fallback in FR-MAT-04. |
| PDF/DOCX text extraction library | Read CV and report text | File in, text out | Image-only files handled by FR-PRF-05. |
| Email provider (SMTP over TLS) | Activation, password reset, notifications | Outgoing email messages | Free provider (Gmail SMTP with an app password in the reference deployment); sending limits are dependency D-03. |
| Browser push services (Web Push with VAPID keys) | Push notifications | Event title and link | No personal data in the payload (NFR-PRV-03). |
| CSV import files | Students and academic supervisors | UTF-8 CSV files | Formats in Section 6.3.1. |
| Export files | Grade sheets, summaries, records, certificates | .xlsx (Office Open XML) and PDF | Embedded Arabic font (NFR-L10N-03). |

#### 6.3.1 CSV Import Formats

Files are UTF-8 encoded (with or without BOM), comma-separated, and start with a header row containing the column names below.

**Table 6.3 – students.csv**

| **Column** | **Type** | **Rule** |
|:---|:---|:---|
| student_id | Text, 10 digits | Required; unique |
| name_en | Text | Required |
| name_ar | Text | Required |
| email | Text | Required; valid email; unique |
| major | Text | Required; a major not yet in the system is added and reported in the import report |
| course_code | Text | Required; the training course the student is registered in for the cycle |
| gpa | Decimal, 2 places | Required; within the university’s GPA scale |
| level | Integer | Optional |

**Table 6.4 – staff.csv (academic supervisors)**

| **Column** | **Type** | **Rule**                      |
|:-----------|:---------|:------------------------------|
| staff_id   | Text     | Required; unique              |
| name_en    | Text     | Required                      |
| name_ar    | Text     | Required                      |
| email      | Text     | Required; valid email; unique |
| department | Text     | Required                      |

### 6.4 Communication Interfaces

- **Client–server:** HTTPS (TLS 1.2 or later) REST API with JSON bodies, versioned under /api/v1 and described by OpenAPI 3; requests are authenticated with JWT bearer tokens.

- **Email:** SMTP with TLS to the email provider.

- **Push:** Web Push protocol through the browser vendors’ push services.

- **Certificate verification:** public URL of the form https://\<host\>/verify/\<certificate-id\>, encoded in the certificate’s QR code.

- **Dates and times:** exchanged in ISO 8601 format with the UTC offset.

## 7. Constraints

Constraints limit the design and implementation choices. They come from the course, the Proposal, and the SPMP.

**Table 7.1 – Constraints**

| **ID** | **Constraint** | **Source** |
|:--:|:---|:---|
| C-01 | Fixed schedule: three increments delivered by Nov 1, Nov 15, and Nov 25, testing until Dec 10, and final delivery on Dec 15, 2026. Time is fixed; scope is the flexible variable. | SPMP schedule and milestones |
| C-02 | Effort is limited to about 480 person-hours (6 members × 8 hours × 10 weeks). | SPMP resource plan |
| C-03 | Technology: Python/FastAPI for the backend and AI services, React (Vite) PWA, PostgreSQL with pgvector, Docker, and GitHub. | Proposal 5.3; SPMP |
| C-04 | Zero cost: open-source tools and free hosting tiers only; no licence, paid plan, or paid service. | Proposal 9 (economic feasibility); CR-01 |
| C-05 | AI models run on the project server; CV and report text may not be sent to external AI services. | Proposal 5.3; PDPL |
| C-06 | No live integration with university systems: data enters by CSV, and grades leave as exported files. | Proposal 7.2 |
| C-07 | Processing of personal data must respect the Saudi PDPL (consent, purpose limitation, access control). | Proposal 9 (legal and privacy) |
| C-08 | The interface must support Arabic (RTL) and English (LTR). | F10, O7 |
| C-09 | Only synthetic or sample data is used for development, testing, and demonstration; no real student records. | Proposal 7.3 |
| C-10 | CPU-only hosting (free tier without GPU; self-hosted minimum 4 GB RAM) limits the embedding model to a small multilingual model running on the CPU. | SPMP resource plan; CR-01 |
| C-11 | Requirements are frozen after this SRS is approved; changes follow the change control of Section 10.6. | SPMP process model |

## 8. Assumptions and Dependencies

### 8.1 Assumptions

Assumptions are conditions taken as true without proof. If one proves false, the effect shown must be handled through change control.

**Table 8.1 – Assumptions**

| **ID** | **Assumption** | **Effect if false** |
|:--:|:---|:---|
| A-01 | Users have internet access and a supported browser (NFR-PRT-01). | Some users cannot use the system; an alternative channel would be needed. |
| A-02 | Each placement has exactly one company supervisor and one academic supervisor. | Data model and permissions would need multi-supervisor support. |
| A-03 | Company supervisors have a working email address and accept invitations from the co-op unit. | Attendance and evaluations cannot be collected; the Coordinator would have to enter them. |
| A-04 | Most CVs are text-based PDF or DOCX files, not scans. | More manual skill entry (FR-PRF-05) and weaker matching. |
| A-05 | The co-op unit can provide CSV files in the formats of Section 6.3.1. | The Coordinator must reformat files before import. |
| A-06 | A cycle has at most 300 students, 300 vacancies, 100 company supervisors, and 30 training weeks. | Performance targets (Section 5.1) must be re-checked. |
| A-07 | Grade components, weights, and rubric criteria are decided by the co-op unit and entered by the Coordinator; the system does not prescribe them. | Fixed values would have to be agreed and built in. |
| A-08 | The weekly working days are the same for all placements in a cycle. | Per-placement work calendars would be needed for attendance. |
| A-09 | Arabic and English are the only languages needed. | Further translation work. |

### 8.2 Dependencies

Dependencies are external factors the project relies on but does not control.

**Table 8.2 – Dependencies**

| **ID** | **Dependency** | **Affects** | **Response if unavailable** |
|:--:|:---|:---|:---|
| D-01 | An open-source multilingual embedding model (e.g., multilingual-e5) with a licence that allows this use | FR-PRF-04, FR-MAT, FR-SIM | Rule-based fallback (FR-MAT-04); switch to another model of similar size. |
| D-02 | The pgvector extension for PostgreSQL | FR-MAT, FR-SIM | Store vectors in a regular table and compare in Python at the demo data size. |
| D-03 | An email provider and its free-tier sending limits | FR-AUT-02, FR-NOT | Send only event emails; in-app notifications remain available. |
| D-04 | Browser support for Web Push (on iOS the app must be installed to the home screen) | FR-PWA-02 | Email fallback (FR-NOT-01). |
| D-05 | Free hosting tiers and their limits: Hugging Face Spaces (sleeps after 48 hours without visits; disk not persistent), Supabase Free (pauses after 7 days of low activity; 500 MB database, 1 GB files), Vercel Hobby | NFR-REL-01, NFR-REL-02 | A scheduled keep-alive check and the nightly backup keep the services active; if a provider is unavailable, run the same containers locally with Docker Compose. |
| D-06 | At least 8 volunteer users from all roles for UAT | NFR-USA-01 | Recruit during the design phase; faculty with industry experience act as company-supervisor proxies. |
| D-07 | An Arabic font with an open licence for PDF exports | FR-EXP, NFR-L10N-03 | Bundle the font in the repository. |
| D-08 | Approval of this SRS by the team and feedback from the course supervisor | All requirements | Requirements stay in draft until the baseline (Milestone M1). |

## 9. Requirement Prioritization

### 9.1 Method

InternSync uses MoSCoW prioritization, carried over from the Proposal so that scope, schedule, and priorities stay consistent.

**Table 9.1 – Priority levels**

| **Priority** | **Meaning** |
|:--:|:---|
| Must | Committed baseline. The system is not acceptable without it. Delivered in Increments 1 and 2. |
| Should | Planned and important. Delivered in Increment 3; dropped only if the schedule slips after all Could items are dropped. |
| Could | Desirable. Built during the testing phase only if time allows. |
| Won’t (this release) | The out-of-scope items of Section 1.3. |

Priorities were assigned to functions with four criteria:

1.  **Contribution** to the problems P1–P6 and objectives O1–O10 of the Proposal.

2.  **Dependency:** functions that other functions rely on (accounts, cycles, reports, workflow) are Must.

3.  **Risk and effort:** AI-heavy or uncertain features that have a simpler working alternative are Should (for example, the explanation in F11 builds on the basic ranking in F4).

4.  **Visibility** to stakeholders and in the course demonstrations.

Each requirement inherits the priority of its function, except convenience requirements inside a Must function, which are marked Should (FR-CYC-05, FR-VAC-05, FR-VAC-08, FR-ATT-02, FR-EVL-04, FR-WFL-07, FR-AUD-03).

### 9.2 Priority Summary

**Table 9.2 – Number of requirements by priority**

| **Category**               | **Must** | **Should** | **Could** | **Total** |
|:---------------------------|:--------:|:----------:|:---------:|:---------:|
| Functional (Section 4)     |    51    |     24     |     6     |    81     |
| Non-functional (Section 5) |    25    |     9      |     1     |    35     |
| **Total**                  |    76    |     33     |     7     |    116    |

### 9.3 Mapping to Increments

**Table 9.3 – Requirements by increment (SPMP schedule)**

| **Increment** | **Dates (2026)** | **Functions** | **Requirement groups** |
|:---|:---|:---|:---|
| Increment 1 | Oct 16 – Nov 1 | F1, F2, F3, F5, F10 | FR-AUT, FR-CYC, FR-PRF, FR-VAC, FR-REP, FR-LOC, FR-AUD-01 – 02 |
| Increment 2 | Nov 2 – Nov 15 | F4, F6, F7, F8, F9 | FR-MAT-01 – 04 and 07, FR-ATT, FR-EVL-01 – 04, FR-WFL, FR-DSH-01 – 02 |
| Increment 3 | Nov 16 – Nov 25 | F11 – F15 | FR-MAT-05 – 06, FR-SIM, FR-NOT, FR-EXP, FR-PWA, FR-AUD-03 |
| Testing phase (if time allows) | Nov 26 – Dec 10 | F16 – F19 | FR-CER, FR-EVL-05, FR-DSH-03 – 04 |

Should requirements inside Must groups are built at the end of their increment. Must non-functional requirements are checked at every increment demo (in particular FR-AUT-05 and NFR-SEC); the remaining ones are verified in the testing phase.

### 9.4 Descoping Order

If the schedule slips, items are removed in the order below, and each removal is recorded through change control. The order keeps longest the functions that remove the most manual work (deadline tracking and grade exports).

1.  Could functions: F19 (leniency alert), then F18 (outcome survey), then F17 (mutual evaluation), then F16 (certificates).

2.  F15 PWA features — the responsive web application still works on phones.

3.  FR-MAT-06 development plan — matched and missing skills (FR-MAT-05) are kept.

4.  F12 similarity detection.

5.  PDF format of FR-EXP-01 – 03 — the Excel grade sheet is kept.

6.  Email channel of F13 — in-app notifications and dashboard pending actions are kept.

Must requirements are never dropped. If a Must requirement is at risk, the Team Leader raises it with the course supervisor at the next milestone.

## 10. Requirement Validation Considerations

### 10.1 Validation and Verification

**Validation** checks that the requirements describe what the stakeholders actually need (building the right system). **Verification** checks, during testing, that the system meets each requirement (building the system right). This section describes how this SRS is validated before the baseline and how each requirement will be verified.

### 10.2 Validation Techniques

**Table 10.1 – Validation activities**

| **Technique** | **How it is applied** | **When** | **Owner** |
|:---|:---|:---|:---|
| Requirements review (inspection) | Every member reviews the SRS against the checklist of Table 10.2; defects are logged as GitHub issues and fixed before the baseline. | Before the baseline (M1) | Abdullah (lead), all members |
| Stakeholder walkthrough | The use cases of Table 3.1 are walked through with representatives: students, an academic who supervises co-op students, and, if available, a co-op unit staff member. A faculty member with industry experience acts as the company-supervisor proxy. | Design phase (T2–T3) | Salam, Abdullah |
| Prototyping | Clickable wireframes of the screens in Table 6.1 confirm the flows, especially the RTL layout, dashboards, and evaluation form. | T3 (Oct 4–15) | Rakan, Ali |
| Test-case derivation | At least one acceptance test is written for every Must and Should requirement before its increment starts; a requirement that cannot be turned into a test is rewritten. | Before each increment | Abdullah |
| Model validation | The state machines of Figures 4.1 and 4.2 are checked with scenario tables covering every transition, including returns and reopenings. | T2 | Khalid, Salam |
| AI evaluation sets | 20 CVs and profiles (10 Arabic, 10 English) are labelled by two members independently and disagreements are resolved together; 10 copied and 10 original reports are prepared for similarity. | T2 to Increment 2 | Ahmed, Salam |

### 10.3 Requirement Quality Checklist

The assignment requires requirements to be clear, consistent, and testable. Each requirement in Sections 4 and 5 is checked against Table 10.2 during the review.

**Table 10.2 – Quality checklist**

| **Attribute** | **Check applied to every requirement** |
|:---|:---|
| Clear | States one behavior with “shall”; avoids vague words such as “fast”, “easy”, or “user-friendly” unless a number defines them. |
| Testable | Has an acceptance criterion with a measurable result or an observable outcome. |
| Consistent | Does not conflict with other requirements, the Proposal, or the SPMP; uses the terms defined in Table 1.2. |
| Complete | Every function F1–F19 and objective O1–O10 is covered (Appendix A); every action in Table 2.3 is covered by a requirement. |
| Traceable | Has a unique ID and a source function or objective. |
| Feasible | Fits the constraints of Section 7 and the effort budget. |
| Prioritized | Has a Must, Should, or Could priority. |

### 10.4 Verification Methods

Each requirement is verified mainly by one of four methods; Appendix A gives the method for each function.

- **Test (T):** automated or manual test with a pass/fail result.

- **Demonstration (D):** shown working at a milestone demonstration.

- **Inspection (I):** review of code, configuration, or documents.

- **Analysis (A):** measurement on a labelled dataset or in a load test.

The measurable targets from the Proposal are verified as follows: 0 failing permission tests (O1, FR-AUT-05); a relevant vacancy in the top 5 for at least 80% of profiles (O2, FR-MAT-01); late flags within 1 hour (O3, FR-REP-04); one rubric for all evaluations (O4, FR-EVL-02); at least 9 of 10 copied reports flagged (O5, FR-SIM-02); export in under 60 seconds (O6, NFR-PER-05); 100% bilingual screens (O7, NFR-L10N-01); at least 80% of UAT scenarios completed without help (O8, NFR-USA-01).

### 10.5 Validation Risks and Open Issues

**Table 10.3 – Validation risks and open issues**

| **Issue** | **Effect** | **How it is handled** |
|:---|:---|:---|
| No direct access to real company supervisors | Company-side needs may be guessed | Faculty proxy in the walkthrough; company flows kept minimal (FR-ATT-01); checked again in UAT. |
| Grade components, weights, and rubric criteria not yet confirmed by the co-op unit | Wrong default values | Made configurable (FR-CYC-02, FR-CYC-03); the demo uses example values agreed with the course supervisor. |
| AI targets measured on small labelled sets (20 profiles, 20 reports) | Results are indicative, not statistically strong | Measurements reported with their dataset; AI stays advisory (NFR-AI-01). |
| Synthetic data may not reflect real CVs and reports | Matching and similarity may perform worse on real data | Mix Arabic, English, and mixed-language samples with realistic formatting. |
| Web push on iOS requires installing the app | Some users miss push notifications | Email fallback (FR-NOT-01). |
| Default values (limits, thresholds, reminder times) chosen by the team | May not match co-op unit practice | Configurable (NFR-MNT-03); confirmed in the stakeholder walkthrough. |

### 10.6 Baseline and Change Control

After the review of Section 10.2 and the course supervisor’s feedback, this SRS becomes baseline version 1.0 (Milestone M1). From then on:

- Each change request is recorded in the change log of the repository (`docs/Change_Requests.md`), and optionally as a GitHub issue labelled “change-request”, with the requested change, the affected requirement IDs, the effect on the schedule and on other requirements, and the decision.

- Changes are decided by team vote with the Team Leader’s approval and are accepted only if they fit the schedule (SPMP).

- Approved changes raise the SRS version (1.1, 1.2, …) and are listed in the revision history; requirement IDs are never reused.

## Appendix A. Traceability Matrix

Table A.1 traces each function of the Proposal to its requirements, objectives, problems, increment, and main verification methods. Table A.2 traces each objective to the requirements that verify its measure of success.

**Table A.1 – Functions to requirements**

| **F** | **Requirements** | **Objective** | **Problem** | **Priority** | **Increment** | **Verification** |
|:--:|:---|:--:|:--:|:--:|:--:|:--:|
| F1 | FR-AUT-01 – 06 | O1 | All | Must | 1 | T |
| F2 | FR-PRF-01 – 05 | O2, O7 | P1 | Must | 1 | T, A |
| F3 | FR-VAC-01 – 08 | O1 | P1 | Must | 1 | T, D |
| F4 | FR-MAT-01 – 04, FR-MAT-07 | O2 | P1 | Must | 2 | A, T |
| F5 | FR-REP-01 – 07 | O3 | P2 | Must | 1 | T |
| F6 | FR-ATT-01 – 04 | O1 | P3 | Must | 2 | T |
| F7 | FR-EVL-01 – 04 | O4 | P3 | Must | 2 | T, I |
| F8 | FR-WFL-01 – 07 | O6 | P5 | Must | 2 | T |
| F9 | FR-DSH-01 – 02 | O1 | P2, P5 | Must | 2 | T, D |
| F10 | FR-LOC-01 – 02 | O7 | — | Must | 1 | I, T |
| F11 | FR-MAT-05 – 06 | O2 | P1 | Should | 3 | T |
| F12 | FR-SIM-01 – 03 | O5 | P4 | Should | 3 | A |
| F13 | FR-NOT-01 – 06 | O3 | P2 | Should | 3 | T |
| F14 | FR-EXP-01 – 03 | O6 | P5 | Should | 3 | T, A |
| F15 | FR-PWA-01 – 03 | O1 | — | Should | 3 | D |
| F16 | FR-CER-01 – 03 | O9 | P6 | Could | Testing | T |
| F17 | FR-EVL-05 | — | P3 | Could | Testing | T |
| F18 | FR-DSH-03 | O10 | P6 | Could | Testing | T |
| F19 | FR-DSH-04 | O4 | P3 | Could | Testing | T |
| Supp. | FR-CYC-01 – 05 | O3, O4, O6 | P2, P3 | Must | 1 | T |
| Supp. | FR-AUD-01 – 03 | O6 | P2, P5 | Must | 1 | T, I |

**Table A.2 – Objectives to requirements**

| **O** | **Measure of success (Proposal)** | **Verified by** |
|:--:|:---|:---|
| O1 | All Must functions implemented; 0 failing permission tests | Requirements of F1–F10; FR-AUT-05 |
| O2 | A relevant vacancy in the top 5 for at least 80% of 20 profiles; matched and missing skills listed | FR-MAT-01, FR-MAT-05, NFR-L10N-04 |
| O3 | All weekly deadlines tracked; reminders before the deadline; late flags within 1 hour | FR-REP-04, FR-NOT-02, FR-NOT-03 |
| O4 | All periodic and final evaluations use one rubric | FR-CYC-03, FR-EVL-01, FR-EVL-02 |
| O5 | At least 9 of 10 seeded copied reports flagged with passages shown | FR-SIM-02 |
| O6 | No grade final without every required approval; 100-student export in under 60 s | FR-WFL-03, FR-WFL-04, NFR-PER-05 |
| O7 | 100% of screens in both languages; Arabic and English CVs matched | FR-LOC-01, FR-LOC-02, NFR-L10N-01, NFR-L10N-04 |
| O8 | UAT with at least 8 participants; at least 80% of scenarios completed without help | NFR-USA-01 |
| O9 | Valid certificates confirmed; tampered or revoked ones rejected | FR-CER-02, FR-CER-03 |
| O10 | Placement-to-job-offer rate per cycle and per company | FR-DSH-03 |
