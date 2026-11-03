# Increment 5 – Design

**Status:** Approved Oct 29, 2026 · Author: Salam Alsaour  
**Inputs:** [01_Requirements.md](01_Requirements.md), [Key_Results.md](../../Key_Results.md), the test reports of Increments 1–4

No part of the system changes in this increment. This document fixes the structure of each deliverable and the tools that produce them. Section 6 lists what changed while they were written.

## 1. Single Sources

| **Fact** | **Source** | **Used by** |
|:---|:---|:---|
| Measured results | [Key_Results.md](../../Key_Results.md) | Final report, presentation |
| Requirements and priorities | SRS | Requirements status |
| What each increment delivered | Each increment's `01_Requirements.md`, Section 4 | Requirements status, final report |
| Test outcomes | Test code (`backend/tests`, `frontend/src`, `frontend/e2e`) and each `04_Test_Report.md`, Section 3 | Requirements status |
| Schedule and milestones | SPMP | Final report |
| Changes | [Change_Requests.md](../../Change_Requests.md) | Final report |

A number appears in a new document only if it is in one of these sources, so the documents cannot contradict each other.

## 2. Tools

| **Tool** | **What it does** |
|:---|:---|
| `docs/tools/trace.py` | Python, no extra package. It writes [Requirements_Status.md](../../Requirements_Status.md) from these sources:<ul><li>every `FR-` and `NFR-` row of the SRS, with its priority;</li><li>the first increment that lists the requirement in its scope;</li><li>the automated tests whose name holds the acceptance-test ID (`test_at_sim_02_…` for FR-SIM-02);</li><li>the result recorded in the test reports.</li></ul>`--check` fails when the written file is out of date, when an SRS requirement is missing, or when a Must or Should requirement has neither a test nor a recorded check |
| `docs/tools/check_links.py` | Every relative link and image in the maintained Markdown documents must point to an existing file; anchors are not checked |
| `docs/tools/export_pdf.mjs` | Renders each maintained document from Markdown to HTML (`marked`) with a print stylesheet, sets the document's folder as the base so its diagrams load, and prints A4 PDFs with page numbers. It uses the Chromium installed for the browser tests. Output: `docs/Final_Submission/` |
| `frontend/e2e/guide.capture.ts` | A Playwright script, not part of the test run, that signs in as each demo role and saves the screenshots of the user guide in `docs/User_Guide/` |
| SRS build | Unchanged ([Project_4_SRS/build](../../Project_4_SRS/build/README.md)): the course template filled by `gen_docx.py`, then Word builds the contents and the PDF |

## 3. Final Report (D1)

1. Summary: the problem, the system, the result in five lines.
2. The system: users and functions F1–F19, architecture, technology, zero cost.
3. How it was built: the plan-driven incremental process; the four phases of each increment; reviews and CI.
4. Schedule: each milestone planned against actual.
5. Changes: CR-01 to CR-11 in one table.
6. Quality and results: the headline numbers of Key Results.
7. Requirements status: counts by priority, from D2.
8. Risks: which occurred and what was done.
9. Limitations and open items:
   - UAT;
   - the device check;
   - the reference deployment;
   - paraphrased reports in the similarity check;
   - the held-out sets written by the author.
10. Lessons learned.
11. Future work.
12. Index of documents.

## 4. User Guide (D3), Demo Script (D4), Presentation (D5)

- **User guide:**
  - Getting started: sign-in, language, consent, the installable app, offline use.
  - Then one section per role, ordered by the course of a training cycle. Each task has numbered steps and, where it helps, a screenshot.
  - Ends with frequently asked questions.
- **Demo script:**
  - Preparation: fresh demo data, browser windows, a phone for the QR code.
  - Then 15 timed steps that show one function of each increment.
  - A fallback for each risky step (no network, Docker down, the model slow to load).
  - The questions examiners are likely to ask, with the document that answers each.
- **Presentation:** about 14 slides:
  1. Title.
  2. The problem.
  3. The users and what each gets.
  4. The solution in one picture.
  5. How it was built: process and increments.
  6. Architecture and zero cost.
  7. AI that explains, not decides.
  8. The demo flow.
  9. Quality numbers.
  10. AI accuracy, with the honest held-out result.
  11. Speed.
  12. Security and privacy.
  13. Lessons and what is open.
  14. Thank you and questions.

  Speaker notes on each slide.

## 5. Submission Folder (D6)

| **File** | **From** |
|:---|:---|
| `InternSync_Final_Report.pdf` | `docs/Final_Report.md` |
| `InternSync_SRS_v1.6.docx`, `InternSync_SRS_v1.6.pdf` | SRS build on the course template |
| `InternSync_SPMP_v1.7.pdf`, `InternSync_Design_v1.7.pdf`, `InternSync_API_Spec_v1.5.pdf` | The maintained documents |
| `InternSync_Test_Reports.pdf` | The five test reports, one after another |
| `InternSync_User_Guide.pdf`, `InternSync_Key_Results.pdf`, `InternSync_Requirements_Status.pdf`, `InternSync_Change_Requests.pdf`, `InternSync_Demo_Script.pdf` | The maintained documents |

## 6. Changes During Writing

None yet.
