# Increment 5 – Test Report

**Date:** Oct 29, 2026 · Author: Salam Alsaour  
**Scope:** [01_Requirements.md](01_Requirements.md), deliverables D1–D7 and checks C-1 to C-7 · **Design:** [02_Design.md](02_Design.md)  
**Milestone:** M7 – Final delivery (Dec 15, 2026)

## 1. Summary

| **Check** | **Result** |
|:---|:---|
| C-1 Links | Every relative link and image in 32 maintained documents points to an existing file (`check_links.py`) |
| C-2 Traceability | 125 SRS requirements: 90 with an automated test named after them, 32 with a recorded result, 3 open (they need people or the hosted system), 0 untraced. `trace.py --check` passes |
| C-3 Screenshots | The 16 screenshots of the user guide were taken by `guide.capture.ts` on fresh demo data, without error |
| C-4 Exports | 11 PDF files written by `export_pdf.mjs`; the SRS 1.6 built in Word and PDF on the course template (Section 4) |
| C-5 Demo dry run | Every step of the demo script ran on fresh demo data, through the screenshot script and `test_m6_demo_scenario`. A timed rehearsal by the presenter remains for the week of the demonstration |
| C-6 Review | Each deliverable read against 01_Requirements. The numbers in the final report and the slides were compared with Key Results and are equal (Section 3) |
| C-7 Regression | Backend: **202 passed**, 95% coverage, ruff clean. Frontend: tsc clean, 19 Vitest tests passed. Browser tests: **34 passed** on Chromium, WebKit, Pixel 7, and iPhone 14, 18 skipped by design. CI runs them again with Firefox on the pull request |
| Deliverables | D1–D7 done; the presentation is a 14-slide deck with speaker notes ([link](https://claude.ai/artifact/3KnHXL8q7QgWXN1xwaynKp)), downloaded as PowerPoint or PDF from its page |

## 2. Defects Found and Fixed

| **Defect** | **Found by** | **Fix** |
|:---|:---|:---|
| On phones the side menu filled the whole first screen of every page, so each page opened on the menu | Reviewing the phone screenshots of the user guide | The menu folds behind a "Main menu" button below 768 px and closes after a link is followed (Design 1.7, Section 8.2); the browser tests open it where they need it |
| FR-MAT-06 had a test that did not carry its acceptance-test ID, so the requirement looked untraced | `trace.py` | Test renamed `test_at_mat_06_…` |
| NFR-USA-05 (error messages next to the field, in the user's language, saying how to fix) had no test | `trace.py` | `test_at_usa_05_field_errors_name_the_field_and_the_fix_in_the_users_language`, in Arabic and English |

## 3. Numbers Compared (C-6)

| **Number** | **Key Results** | **Final report** | **Slides** |
|:---|:--:|:--:|:--:|
| Backend tests | 202 | 202 | 202 |
| Refused permission checks / endpoints | 810 / 163 | 810 / 163 | 810 / 163 |
| Browser tests | 34 | 34 | 34 |
| Requirements traced | 125 (90 / 32 / 3) | 125 (90 / 32 / 3) | 125, 3 open |
| Matching top 5, tuning and held-out | 100%, 100% | 100%, 100% | 100%, 100% |
| Copied reports flagged, held-out | 7 of 10 | 7 of 10 | 7 of 10 |
| 50 users, 95th percentile | 0.21 s | 0.21 s | 0.21 s |
| High-risk security findings | 0 | 0 | 0 |

## 4. Submission Files (C-4)

`node docs/tools/export_pdf.mjs` wrote the PDFs of `docs/Final_Submission/`:

- the final report;
- the SPMP 1.7, the design 1.7, and the API specification 1.5;
- the five test reports;
- the UAT plan;
- the user guide;
- Key Results;
- the requirements status;
- the change requests;
- the demo script.

The SRS 1.6 was built with its own scripts on the course template:

- `gen_docx.py` fills the template;
- Word builds the table of contents and the PDF.

## 5. Notes

- **The local demo data.** Once during this increment the screenshot script ran against the main demo database instead of its own. It set six demo accounts to English, which was reverted, and submitted a weekly report of `s1@iau.edu.sa`, which cannot be undone in the system. The demo script starts from fresh demo data, so this has no effect on the demonstration. The script must always run with the API on its own database, as the user guide's header and README say.
- **User acceptance testing** was postponed by the project owner on Oct 29 (RQ-6). NFR-USA-01 stays open, with the plan ready.
- **Firefox** browser tests run in CI; Windows blocks the downloaded Firefox build on the development laptop.

## 6. Definition of Done

| **Criterion** | **Status** |
|:---|:---|
| D1–D7 delivered | Done |
| Checks C-1 to C-7 | Done; the timed rehearsal of C-5 is left for the presenter |
| Documents updated (SPMP 1.7, Design 1.7, document index, README, Key Results) | Done |
| Merged through a pull request with CI green | On this pull request |
