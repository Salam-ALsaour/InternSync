# Increment 2 – Test Report

**Status:** Complete · Oct 26, 2026 · Author: Salam Alsaour  
**Input:** [01_Requirements.md](01_Requirements.md) (acceptance tests, Section 6; demo scenario, Section 7; Definition of Done, Section 8), [02_Design.md](02_Design.md) (test design, Section 11; changes, Section 12)  
**Build tested:** branch `increment-2`; backend Python 3.11, PostgreSQL 16 with pgvector; embedding model `intfloat/multilingual-e5-small@614241f622f5`; frontend Node 22, React 18, Vite 8

## 1. Summary

| **Check** | **Result** |
|:---|:---|
| Backend tests (pytest, real PostgreSQL) | **158 passed**, 0 failed (108 at the end of Increment 1) |
| Backend line coverage | **95%** of `app` (5,190 statements; gate 70%) |
| Permission matrix | 129 routes listed (22 new); **627** calls by callers that are not allowed, all answered `401` or `403` |
| Acceptance tests of 01_Requirements Section 6 | **27 of 27 passed** (automated; AT-LOC-03 also checked in the browser) |
| Non-functional checks of 01_Requirements Section 4.2 | **8 of 8 met** |
| AI evaluation (`ai-eval/evaluate.py`) | Skill extraction recall **97.2%** (target 70%); top-5 hit rate **100%** (target 80%). The set is easy; see Section 5 for what that number does and does not show |
| Frontend | TypeScript strict build clean; **8 Vitest tests passed**; production build succeeds; 648 translation keys in each language |
| Lint | `ruff` clean on `app`, `tests`, `alembic`, `scripts` |
| M4 demo scenario | Steps 1–9 automated end to end through the HTTP API (`test_m4_demo_scenario`); step 10 run; the screens walked through in the browser |
| Regression on the full stack | `docker compose up` with the new image: the M3 dry run passed **10 of 10** steps; the student's ranking ran with the model |
| Deployment parts | Image built with the model; started as the Space starts it (production settings, port 7860): model loaded offline in about 15 s, jobs ran; backup and restore rehearsed |
| Dependencies shipped to users (`npm audit --omit=dev`) | 0 known vulnerabilities |
| Committed scope | 24 of 24 requirements: 18 Must, 4 committed Should, FR-MAT-05 pulled forward, and FR-MAT-06 (stretch) delivered. The three stretch follow-ups from Increment 1 were not reached (Section 9) |

## 2. How to Repeat the Tests

```bash
docker compose up -d db mailpit
cd backend
pip install -r requirements-dev.txt
ruff check app tests alembic scripts
pytest --cov=app                          # 158 tests; the tests use a stand-in for the model
cd ../frontend
npm ci
npx tsc -b && npx vitest run && npx vite build
```

The AI evaluation needs the model packages (`pip install -r backend/requirements-ai.txt`; the model is downloaded once):

```bash
python ai-eval/evaluate.py                # with the model
python ai-eval/evaluate.py --basic        # rules only
```

The full stack and the M3 rehearsal:

```bash
docker compose up -d --build
docker compose exec api python -m app.seed --demo
python backend/scripts/demo_dry_run.py
```

## 3. Acceptance Tests

Every test of 01_Requirements Section 6 has a named test in `backend/tests`; the AT ID is in the function name.

| **Test** | **Automated test(s)** | **Result** |
|:---|:---|:--:|
| AT-MAT-01 | `test_at_mat_01_ranking_holds_eligible_vacancies_in_descending_fit`; evaluation script (Section 5) | Pass |
| AT-MAT-02 | `test_at_mat_02_unit_required_skills_raise_the_score` | Pass |
| AT-MAT-03 | `test_at_mat_03_gpa_below_minimum_is_left_out_and_explained` | Pass |
| AT-MAT-04 | `test_at_mat_04_unit_basic_mode_without_a_vector`, `test_at_mat_04_basic_mode_without_the_model`, `test_vacancy_without_embedding_is_scored_by_the_rules`; the timed test in basic mode | Pass |
| AT-MAT-05 | `test_at_mat_05_unit_matched_and_missing_are_the_set_comparison`; the API lists in `test_at_mat_01…` | Pass |
| AT-MAT-07 | `test_at_mat_07_ranking_is_advisory_and_any_eligible_vacancy_can_be_applied_to` | Pass |
| AT-ATT-01 | `test_at_att_01_full_attendance_in_one_action` | Pass |
| AT-ATT-02 | `test_at_att_02_locked_after_seven_days_until_unlocked` | Pass |
| AT-ATT-03 | `test_at_att_03_percentage_and_visibility` | Pass |
| AT-ATT-04 | `test_at_att_04_unrecorded_week_on_the_company_dashboard_on_day_4` | Pass |
| AT-EVL-01 | `test_at_evl_01_all_criteria_and_comment_required` | Pass |
| AT-EVL-02 | `test_at_evl_02_only_the_cycle_rubric` | Pass |
| AT-EVL-03 | `test_at_evl_03_student_sees_periodic_now_and_final_when_the_grade_is_final` | Pass |
| AT-EVL-04 | `test_at_evl_04_read_only_after_submit_and_reopened_once`, `test_final_evaluation_cannot_be_reopened_while_the_grade_is_submitted` | Pass |
| AT-WFL-02 | `test_at_wfl_02_unit_total_rounds_half_up`, `test_at_wfl_02_grade_equals_the_hand_calculation` | Pass |
| AT-WFL-03 | `test_at_wfl_03_submit_refused_with_the_missing_items` | Pass |
| AT-WFL-04 | `test_at_wfl_04_and_06_return_approve_and_what_the_student_sees` | Pass |
| AT-WFL-05 | `test_at_wfl_05_final_grade_locked_and_reopened_with_a_reason` | Pass |
| AT-WFL-06 | `test_at_wfl_04_and_06_…`, `test_grade_visibility` | Pass |
| AT-WFL-07 | `test_at_wfl_07_bulk_approval_one_audit_entry_each` (10 grades, 10 audit entries) | Pass |
| AT-DSH-01 | `test_at_dsh_01_every_count_equals_the_database` | Pass |
| AT-DSH-02 | `test_at_dsh_02_cycle_figures_overall_and_per_company` | Pass |
| AT-DSH-05 | `test_at_dsh_05_platform_figures` | Pass |
| AT-PER-02 | `test_at_per_02_ranking_1000_vacancies_within_5_seconds` (Section 4) | Pass |
| AT-AI-02 | `test_application_keeps_the_fit_snapshot`, `test_version_and_health_name_the_loaded_model` | Pass |
| AT-AI-03 | `ai-eval/evaluate.py` (Section 5) | Pass |
| AT-LOC-03 | `frontend/src/i18n/keys.test.ts` (648 keys, same in both files, every literal key exists, placeholders match); browser check of every new screen in both languages | Pass |

## 4. Non-Functional Checks

| **ID** | **Evidence** | **Result** |
|:---|:---|:--:|
| NFR-PER-02 | 1,000 published vacancies, 20 ranking requests per mode: median 0.69 s and 95th percentile **0.83 s** with the embeddings, 0.68 s and **0.76 s** in basic mode (limit 5 s) | Met |
| NFR-PER-03 | `test_nfr_per_03_skills_from_a_5_mb_cv_within_30_seconds`: a 4.8 MB PDF packed with text is read and its skills suggested in about 2–6 s (limit 30 s). Before the fix in Section 7 the same file took 94 s | Met |
| NFR-PRV-02 | The model runs inside the API process; the image holds it and sets `HF_HUB_OFFLINE=1`. In the container started as on the Space, the log shows no request to the Hugging Face Hub | Met |
| NFR-AI-01 | Every ranking carries `advisory: true`, the parts, and the matched and missing skills, shown under the Advisory label; AT-MAT-07 shows that no application changes without a person | Met |
| NFR-AI-02 | `match_scores` and each application snapshot store `model_version`; `/version` and the deep health check name the loaded model | Met |
| NFR-AI-03 | `ai-eval/data` (20 profiles, 30 vacancies) and `ai-eval/evaluate.py` are in the repository; three runs on Oct 25–26 gave the same numbers | Met |
| NFR-L10N-01 | Browser check of every new screen in Arabic (right to left) and English (left to right): dashboards of the five roles, recommended vacancies and the plan, the placement tabs (reports, attendance, evaluations, grade), the grades page, cycle statistics, platform figures, the new settings | Met |
| NFR-USA-02 | Attendance: one table and one dialog, "Full attendance" is one button. Evaluation: one page with the rubric and the comment | Met |

Repeated from Increment 1 and still met: CI runs every check above on the pull request (NFR-MNT-01); the OpenAPI document and the generated types match the code (NFR-MNT-02); the new settings are editable on the settings page (NFR-MNT-03); `docker compose up -d --build` starts the stack with the model (NFR-PRT-02); new pages have no horizontal scrolling at 375 px (NFR-USA-03).

## 5. AI Evaluation

Run on Oct 26, 2026 with `ai-eval/evaluate.py`. The set is synthetic (C-09): 20 student profiles (10 Arabic, 10 English) and 30 vacancies, written and labelled by the author (decision RQ-4).

| **Measure** | **With the model** | **Rules only (`--basic`)** | **Random order** | **Target** |
|:---|:--:|:--:|:--:|:--:|
| Skill extraction recall | 97.2% (English 97.4%, Arabic 96.9%) | same (no model involved) | – | ≥ 70% |
| Relevant vacancy in the top 5 | 100% | 100% | 79.7% | ≥ 80% |
| Relevant vacancy first | 100% | 100% | 37.4% | – |
| Mean reciprocal rank | 1.000 | 1.000 | 0.559 | – |
| Text similarity alone, top 5 / first | 100% / 100% | – | – | – |

How to read these numbers:

- **The top-5 target is met, but on this set it shows little.** A profile has 9.2 eligible vacancies on average, 2 or 3 of them relevant, so a random order already puts one in the top 5 for 79.7% of the profiles. The ranking's real strength shows in the other two rows: the relevant vacancy comes first for every profile, against 37.4% by chance.
- **The model and the rules agree here.** Text similarity alone also ranks a relevant vacancy first for every profile, so the model works; the set is simply too easy to show what it adds to the skill rules.
- **The recall figure is optimistic.** Arabic recall was 67.7% at the first run. The fixes (attached particles and six synonyms, Section 7) were found on this same set, so it is no longer a held-out measure.
- **Missed skills:** Machine Learning (E03), ERP Systems (E09), Project Management (A07), GitHub (A08).

A harder held-out set (more eligible vacancies per profile, vacancies described only in free text, profiles labelled by another person) is planned for M6.

## 6. M4 Demo Scenario

`test_m4_demo_scenario` runs steps 1–9 of 01_Requirements Section 7 through the HTTP API, with the clock moved 11 days for steps 3 and 4:

| **Step** | **Result** |
|:---|:---|
| 1. Student dashboard; recommended vacancies with fit, matched and missing skills, Advisory; development plan; applies | Pass |
| 2. Model off: the same list is labelled basic | Pass |
| 3. Company dashboard: applicants to review and overdue attendance; full week and partial week with a note | Pass |
| 4. Week older than 7 days refused; coordinator unlocks; supervisor corrects it | Pass |
| 5. Periodic evaluation visible to the student at once; final evaluation hidden until Final | Pass |
| 6. Grade submission refused with the missing items; components entered; company part computed (80.00); total 86.00 submitted | Pass |
| 7. One grade returned with a comment and resubmitted; two grades approved in bulk; the student sees the Final grade and the final evaluation | Pass |
| 8. Final grade reopened with a reason; the audit entry carries it | Pass |
| 9. Cycle statistics (2 placed, attendance 80%) and platform figures (counts only) | Pass |
| 10. Evaluation script run | Pass (Section 5) |

The same screens were walked through in the browser on the demo data in both languages and at phone width (Section 4).

## 7. Defects Found and Fixed

| **Defect** | **Found by** | **Fix** |
|:---|:---|:---|
| A week past its edit window but never recorded was treated as locked and left out of the company's overdue count | `test_at_att_04…` | State and lock reported separately |
| Arabic skill extraction recall 67.7% | Evaluation script | Attached particles (و، ف، ب، ل، ك، لل) handled; six synonyms added, and brought to existing databases by migration `0004` |
| The model version showed `@local` | Evaluation script | Read from the cached snapshot |
| The web app showed the bare status text ("Conflict") instead of the server's message on every typed call, since Increment 1 | Browser check (grade submission) | Message taken from the body the client already read; `client.test.ts` |
| The first ranking after a restart waited about 90 s for the model, which also contacted the Hugging Face Hub | Browser check | Model loaded at start in the background, from the local copy |
| Reading a 5 MB PDF packed with text took 89 s, and a compressed file could unpack to megabytes | New timed test of NFR-PER-03 | Text read from at most 20 pages, 512 KB of instructions per page, 2 MB per file; DOCX above 50 MB unzipped refused for reading |
| The API image stopped at start outside Docker Compose: its default file folder was not writable | Container started as on the Space | Image default `LOCAL_STORAGE_DIR=/data/storage` |
| The API could start in production with the development signing key | Deployment review | Refused at start |
| Wording and display (outdated texts on two pages, "Grade: Draft" shown to the student, a submitted evaluation shown as "awaiting review", twelve precondition lines, "3 طالب", no Cancel in the attendance dialog, dashboard grade links to the wrong page) | Browser check | Fixed; listed in [02_Design.md](02_Design.md) Section 12 |

## 8. Deployment Checks

The reference deployment is prepared but not switched on: it needs the owner's Hugging Face account and a Gmail app password ([Deployment.md](../../Deployment.md), Section 3). What was checked without it:

- **Image:** built with the model (about 3 GB), started with `ENV=production`, `PORT=7860`, and the scheduler on, against the local database. The model loaded in about 15 s with no network call, the deep health check answered with the database and the model, the development routes were absent, and the Missing and embedding jobs ran.
- **Storage adapter, bucket copy, and restore:** tested against a stand-in of the Supabase Storage API (`test_storage.py`).
- **Deploy script:** what it uploads and the Space address (`test_deploy.py`); the workflow does nothing while its secrets are missing.
- **Database backup:** dump with `pg_dump` 17, encryption and decryption with `gpg`, restore into a scratch database. Every table had the same row count, embeddings included.
- **Web build:** with `VITE_API_URL` set, every call goes to that address.

## 9. Known Limitations and Follow-Up

- **Deployment switch-on:** waits for the owner's steps. The Space must be public, so the backend code is visible there (not the secrets). NFR-PER-01 and NFR-REL-01 are measured on it in M6, as planned.
- **AI evaluation:** the set is easy and partly tuned on itself (Section 5); a harder held-out set is planned for M6.
- **Stretch follow-ups from Increment 1 not reached:**
  - **Tailwind CSS 4:** `npm audit` still reports 3 moderate advisories in Tailwind 3's build tools, which never reach users.
  - **Backend type checker:** not added.
  - **Automated browser tests:** not added; the browser checks were done by hand.
- **Registration limit behind the Space's proxy:** with `FORWARDED_ALLOW_IPS=*` the visitor's address comes from the forwarded header, which a client could forge to avoid the limit. Accepted for the demo; narrowed if abused.
- **First ranking after a start:** the model takes about 15 s to load in the container; a ranking requested in that time waits for it.
- **Email:** tested through Mailpit; Gmail delivery is checked at switch-on.

## 10. Definition of Done

| **Item (01_Requirements Section 8)** | **Status** |
|:---|:---|
| Code merged into `main` through a pull request with CI green | Pull request opened from `increment-2`; merge after CI passes |
| Acceptance tests automated and passing; endpoints in the permission matrix | Done (Sections 3 and 1) |
| Screens in Arabic and English following the wireframes | Done (browser check, Section 4) |
| Actions write audit entries | Done: attendance records and unlocks, evaluation submit and reopen, grade update, submit, return, approve, and reopen (`test_m4_demo_scenario`, AT-WFL-07) |
| Design, API, or SRS updated where the implementation changed something | Done: [CR-08](../../Change_Requests.md), Design 1.4, API 1.3, SRS 1.5, SPMP 1.4, [02_Design.md](02_Design.md) Section 12 |
| Demo scenario runs without help | Done (Section 6) |
| Test report with the evaluation script's numbers | This document |
