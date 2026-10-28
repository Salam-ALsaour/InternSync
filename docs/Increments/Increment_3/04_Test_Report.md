# Increment 3 – Test Report

**Status:** Complete · Oct 27, 2026 · Author: Salam Alsaour  
**Input:** [01_Requirements.md](01_Requirements.md) (acceptance tests, Section 6; demo scenario, Section 7; Definition of Done, Section 8), [02_Design.md](02_Design.md) (test design, Section 11; changes, Section 12)  
**Build tested:** branch `increment-3`; backend Python 3.11, PostgreSQL 16 with pgvector 0.8.7; embedding model `intfloat/multilingual-e5-small@614241f622f5`; frontend Node 22, React 18, Vite 8

## 1. Summary

| **Check** | **Result** |
|:---|:---|
| Backend tests (pytest, real PostgreSQL) | **187 passed**, 0 failed (158 at the end of Increment 2) |
| Backend line coverage | **95%** of `app` (gate 70%) |
| Permission matrix | 145 routes listed (16 new); **696** calls by callers that are not allowed, all answered `401` or `403` |
| Acceptance tests of 01_Requirements Section 6 | **21 of 21 pass in their automated part**; the device parts of AT-PWA-01 – 03 (install on a phone, a real push, airplane mode) are planned for M6 (Section 9) |
| Non-functional checks of 01_Requirements Section 4.2 | **11 of 11 met** |
| Similarity evaluation (`ai-eval/evaluate.py`) | **10 of 10** copied reports flagged (target 9 or more), **0 of 10** original reports flagged (target 1 or fewer); the copied reports hold 44–54% copied text. The setting was chosen on this set (Section 5) |
| Frontend | TypeScript strict build clean; **11 Vitest tests passed** (translation keys, date format, API errors, installable app); production build succeeds; 745 translation keys in each language |
| Lint | `ruff` clean on `app`, `tests`, `alembic`, `scripts` |
| Dependency audits | `pip-audit` on `requirements.txt`: no known vulnerabilities; `npm audit --omit=dev`: 0 vulnerabilities. Both now run in CI |
| M5 demo scenario | Steps 1–5 and 7–9 automated end to end through the HTTP API (`test_m5_demo_scenario`); step 6 checked in the browser; step 10 run |
| Container | The API image builds with the new libraries; inside it, the Arabic grade sheet is produced with both fonts embedded |
| Committed scope | 17 of 17 requirements (all Should), FR-ORG-07 included; the dashboard items left by Increment 2; the dependency audit. The three stretch follow-ups were not reached again (Section 9) |

## 2. How to Repeat the Tests

```bash
docker compose up -d db mailpit
cd backend
pip install -r requirements-dev.txt
ruff check app tests alembic scripts
pytest --cov=app                         # 187 tests; the tests use a stand-in for the model
pip-audit -r requirements.txt
cd ../frontend
npm ci
npx tsc -b && npx vitest run && npx vite build
npm audit --omit=dev
```

The evaluation needs the model packages (`pip install -r backend/requirements-ai.txt`):

```bash
python ai-eval/evaluate.py
```

The installable app and the offline page: `npm run build` then `npm run preview` in `frontend/` (http://localhost:4173), with the API running.

## 3. Acceptance Tests

| **Test** | **Automated test(s), or check** | **Result** |
|:---|:---|:--:|
| AT-SIM-01 | `test_at_sim_01_02_copied_report_flagged_within_the_university_only` (the same text stored at another university is never a source), `test_at_sim_01_earlier_versions_of_the_same_report_are_not_sources` | Pass |
| AT-SIM-02 | The same API test (score, cycle, week, passages; the author only for the author's coordinator); evaluation script 10 of 10 and 0 of 10 (Section 5) | Pass |
| AT-SIM-03 | `test_at_sim_03_advisory_decision_changes_nothing_else` (comment required, only a flagged check, status unchanged, audited) | Pass |
| AT-NOT-01 | `test_at_not_01_list_unread_count_and_one_email_each`, `test_failed_email_is_retried_then_marked_failed` | Pass |
| AT-NOT-02 | `test_at_not_02_reminder_once_between_24_and_23_hours` | Pass |
| AT-NOT-03 | `test_at_not_03_missing_notice_to_student_and_supervisor` | Pass |
| AT-NOT-04 | `test_at_not_04_escalation_on_day_4_never_twice` (reports, attendance, evaluations; the list and the dashboard count) | Pass |
| AT-NOT-05 | `test_at_not_05_application_and_placement_events`, `test_at_not_05_report_evaluation_and_grade_events`, `test_at_not_05_verification_events`; the transfer events in AT-ORG-07 | Pass |
| AT-NOT-06 | `test_at_not_01…` (an Arabic and an English recipient of the same events); M5 step 4 | Pass |
| AT-EXP-01 | `test_at_exp_01_grade_sheet_values_equal_stored_values` (every cell read back from the Excel file; the PDF text read back), `test_unit_formula_injection_guard` | Pass |
| AT-EXP-02 | `test_at_exp_02_term_summary_equals_the_dashboard` | Pass |
| AT-EXP-03 | `test_at_exp_03_training_record_for_the_assigned_supervisor` (another supervisor and the student are refused) | Pass |
| AT-PWA-01 | `src/pwa.test.ts` (manifest fields and icons, service worker rules, page links); production build in the browser: service worker active, app shell cached, manifest served | Pass; the install itself on phones in M6 |
| AT-PWA-02 | `test_at_pwa_02_push_has_title_and_link_only` (payload `{title, link}` only, email when no subscription), `test_gone_subscription_is_deleted`, `test_push_subscription_endpoints`; the page shows the right state when the browser blocks notifications | Pass; a real push on a device in M6 |
| AT-PWA-03 | Production build with the browser's offline state: the offline banner appears and every action button is disabled; back online, the banner goes | Pass; airplane mode on a phone in M6 |
| AT-AUD-03 | `test_at_aud_03_history_matches_the_audit_entries`; the student never sees the similarity decision (`test_at_sim_03…`) | Pass |
| AT-ORG-07 | `test_at_org_07_coordinator_role_transfer`, `test_at_org_07_company_admin_transfer` | Pass |
| AT-PER-04 | `test_at_per_04_result_within_2_minutes_with_10000_stored_reports` (Section 4) | Pass |
| AT-PER-05 | `test_at_per_05_grade_sheet_of_100_students_under_60_seconds` (Section 4) | Pass |
| AT-REL-03 | Every job test runs the job twice and checks that nothing is sent twice; the escalation test jumps the clock as after a downtime and the next run catches up | Pass |
| AT-L10N-03 | `test_at_l10n_03_arabic_pdf_embeds_the_arabic_font`; the exported pages rendered and checked by eye (Section 7) | Pass |

## 4. Non-Functional Checks

| **ID** | **Evidence** | **Result** |
|:---|:---|:--:|
| NFR-PER-04 | With 10,000 stored reports (20,000 passages in the HNSW index), submitting a report and running its check took **0.35–0.42 s** over two runs with the stand-in model (limit 2 minutes). With the real model, embedding a report's passages adds well under a second | Met |
| NFR-PER-05 | 100-student grade sheet: **1.0–1.3 s** for Excel and **2.4–4.6 s** for PDF over two runs, the slower one while the evaluation ran beside it (limit 60 s each) | Met |
| NFR-REL-03 | Jobs every 1 to 15 minutes; idempotency keys per recipient; repeated runs send nothing twice (AT-REL-03) | Met |
| NFR-PRV-03 | The push payload is the title and the link only, with no name or grade (`test_at_pwa_02…`, M5 step 5) | Met |
| NFR-L10N-03 | fpdf2 with HarfBuzz shaping and the embedded Noto Naskh Arabic font; letters joined and right to left in the rendered pages, also in the Linux container | Met |
| NFR-L10N-04 | The similarity set has 5 Arabic and 5 English pairs of copied and original reports, several Arabic ones with English terms inside; all copied ones flagged, no original flagged | Met |
| NFR-AI-01 | The similarity panel is under the Advisory label with its score and passages; a decision changes no status (AT-SIM-03) | Met |
| NFR-AI-02 | Each check stores `model_version` and the threshold in force | Met |
| NFR-AI-03 | `ai-eval/data/similarity.json` and the script; two runs gave the same numbers | Met |
| NFR-SEC-05 | Dependency audits clean and in CI; the ZAP scan is part of the release check in M6 | Met for this increment |
| NFR-L10N-01 | Browser check of every new screen in Arabic and English: notification list and bell, similarity panel and list, history panels, escalations, exports, transfer dialog, offline banner | Met |

New pages have no horizontal scrolling at 375 px (NFR-USA-03). The checks of Increments 1 and 2 still pass in CI.

## 5. Similarity Evaluation

Run on Oct 27, 2026 with `ai-eval/evaluate.py`. The set is synthetic (C-09), written and labelled by the author (Increment 3, RQ-6): 10 stored reports, 10 reports that copy two or three of their sentences (44–54% of the copying report, some with a word changed) among their own sentences, and 10 original reports on the same topics as the stored ones, half in Arabic and half in English.

| **Measure** | **Result** | **Target** |
|:---|:--:|:--:|
| Copied reports flagged | 10 of 10 (English 5, Arabic 5) | 9 or more |
| Original reports flagged | 0 of 10 | 1 or fewer |
| Scores of the copied reports | 0.42 – 0.54 (close to their real copied share) | – |
| Scores of the original reports | 0.00 | – |

How to read these numbers:

- **The first version of the method failed this set.** With passages of 40–80 words (the design), only 4 of 10 copied reports were flagged and no Arabic one, because the copied sentences shared a passage with the student's own words. Sentence-sized passages, compared with the source's nearby passages taken together, give the result above (CR-09).
- **The setting was chosen on the same set.** The numbers are therefore optimistic. A held-out set, written by someone else, is planned for M6 together with the matching one.
- **The first version of the set was too easy.** Its copied reports held over 70% copied text, which hid the problem; the set now follows the 40% of the acceptance criterion.

The matching and skill-extraction numbers of Increment 2 are unchanged (skill recall 97.2%; relevant vacancy first for every profile, against 37.4% by chance).

## 6. M5 Demo Scenario

`test_m5_demo_scenario` runs these steps through the HTTP API:

| **Step** | **Result** |
|:---|:---|
| 1. A weekly report copied from a report of an earlier cycle is flagged; the supervisor's dashboard shows it; score, source cycle and week, passages | Pass |
| 2. "Overlap confirmed" with a comment; the report status unchanged; the coordinator sees the author | Pass |
| 3. The same text at another university is not a source | Pass |
| 4. Reminder, Missing notice (student and supervisor), escalation on day 4; emails in Arabic and English | Pass |
| 5. A Final grade: in-app notification, email, and web push for the student | Pass |
| 6. Installable app; offline banner and disabled buttons | Pass in the browser (Section 3) |
| 7. Grade sheet (Excel and PDF) with Arabic names, term summary, training record | Pass |
| 8. History of a report, an evaluation, and a grade | Pass |
| 9. Coordinator role transferred; the previous coordinator loses access; audit entry | Pass |
| 10. Evaluation script | Pass (Section 5) |

In the browser, on the seeded demo data:
- The demo student submitted the former student's paragraph, and the academic supervisor saw the flag on the dashboard and the three copied sentences side by side.
- The supervisor recorded the decision, and it appeared in the report's history.
- The coordinator's escalations, exports, and notifications were opened in Arabic and English and at phone width.
- The Platform Admin's transfer dialog listed the right candidates.

## 7. Defects Found and Fixed

| **Defect** | **Found by** | **Fix** |
|:---|:---|:---|
| Half-copied reports were missed (4 of 10 found) | Evaluation script, once the set followed the 40% criterion | Sentence-sized passages and the joined-neighbour rule (CR-09) |
| A copied passage that spans two source passages was missed | Evaluation script (report C07) | Compared with the source's nearby passages taken together |
| The side-by-side view listed unrelated source passages | Browser check | Only passages that share words with the copied one |
| Grade weights printed as "30.00"; Arabic footer in the wrong order; a gap left by the total page count; percent sign placement; cycle name and dates reordering each other | Rendering the exported PDFs | Weight without decimals; footer in separate cells with the page number only; Arabic percent sign; dates on their own line |
| The history arrow pointed backwards in English | Browser check | Arrow by direction |
| "11 أيام" in Arabic | Browser check | Days overdue shown as a number under its header |
| The escalation filter was named `kind` instead of the specification's `type` | Review against the API specification | Renamed |
| The first similarity speed test loaded its 20,000 passages row by row and ran for minutes | Running the test | The data is made inside the database |

## 8. Notes on the Tests

- **Background check in tests:** the test client runs the background task of a submission before it returns, so the API tests see the finished check, as a user does a moment after submitting.
- **Model in tests:** the tests use the stand-in embedder of Increment 2. The real model was used for the evaluation, the demo data, and the browser check.

## 9. Known Limitations and Follow-Up

- **Device checks (M6):**
  - Installing the app from Chrome on Android and Safari on iOS.
  - Receiving a real web push: the built-in browser used here blocks notifications.
  - Opening the app in airplane mode: the offline state was simulated in the browser here, and the service worker's offline page was checked by its cache contents.
- **Similarity:**
  - The setting was tuned on its own evaluation set (Section 5).
  - The check needs the model. Without it, checks wait and the retry job runs them, up to 3 attempts.
- **Stretch follow-ups not reached again:** Tailwind CSS 4, a backend type checker, and automated browser tests. `npm audit` still lists 3 moderate advisories in Tailwind 3's build tools, which never reach users.
- **Notifications:**
  - Delivered by a job every minute, so an email arrives within about a minute of the event.
  - Real Gmail delivery is checked when the deployment is switched on.
- **PDF page total:** pages show their number but not the total.

## 10. Definition of Done

| **Item (01_Requirements Section 8)** | **Status** |
|:---|:---|
| Code merged into `main` through a pull request with CI green | Pull request opened from `increment-3`; merge after CI passes |
| Acceptance tests automated and passing, or checked in the browser where marked; endpoints in the permission matrix | Done (Sections 3 and 1); device parts in M6 |
| Screens in Arabic and English following the wireframes | Done |
| Actions write audit entries | Done: similarity decision, exports, role transfers; the history shows them |
| Design, API, or SRS updated where the implementation changed something | Done: [CR-09](../../Change_Requests.md), Design 1.5, API 1.4, SPMP 1.5, Deployment 1.1, [02_Design.md](02_Design.md) Section 12 |
| Demo scenario runs without help | Done (Section 6) |
| Test report with the similarity evaluation | This document |
