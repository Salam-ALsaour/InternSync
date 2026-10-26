# Increment 1 – Test Report

**Status:** Complete · Oct 24, 2026 · Author: Salam Alsaour  
**Input:** [01_Requirements.md](01_Requirements.md) (acceptance tests, Section 6; demo scenario, Section 7; Definition of Done, Section 8), [02_Design.md](02_Design.md) (test design, Section 11)  
**Build tested:** branch `increment-1`; backend Python 3.11, PostgreSQL 16; frontend Node 22, React 18, Vite 8

## 1. Summary

| **Check** | **Result** |
|:---|:---|
| Backend tests (pytest, real PostgreSQL) | **108 passed**, 0 failed |
| Backend line coverage | **95%** of `app` (gate 70%; seed, CLI, scheduler wiring, and app factory excluded by configuration) |
| Permission matrix | 107 routes listed; **494** calls by callers that are not allowed, all answered `401` or `403` |
| Acceptance tests of 01_Requirements Section 6 | **43 of 43 passed** (automated, plus the browser checks of AT-AUT-01, AT-PRF-05, and AT-LOC-01) |
| Non-functional checks of 01_Requirements Section 4.2 | 14 of 14 met; NFR-MNT-01 is confirmed when CI runs on the pull request |
| Frontend | TypeScript strict build clean; **7 Vitest tests passed** (translation keys and date format); production build succeeds |
| Lint | `ruff` clean on `app`, `tests`, `alembic`, `scripts` |
| M3 demo dry run on `docker compose up` | **10 of 10 steps passed**, twice in a row, with real emails through Mailpit |
| Dependencies shipped to users (`npm audit --omit=dev`) | 0 known vulnerabilities |
| Committed scope | 39 Must requirements delivered; 4 of 4 stretch items delivered (FR-ORG-09, FR-CYC-05, FR-VAC-05, FR-VAC-08); FR-ORG-07 deferred to Increment 3 as planned |

## 2. How to Repeat the Tests

```bash
docker compose up -d db mailpit          # PostgreSQL on 5433, Mailpit on 8025
cd backend
pip install -r requirements-dev.txt
ruff check app tests alembic scripts
pytest --cov=app                         # creates the internsync_test database on first use
cd ../frontend
npm ci
npx tsc -b && npx vitest run && npx vite build
```

The M3 rehearsal against the full stack:

```bash
docker compose up -d --build
docker compose exec api python -m app.seed --demo
python backend/scripts/demo_dry_run.py   # needs httpx (in requirements-dev.txt)
```

## 3. Acceptance Tests

Every test of 01_Requirements Section 6 has a named test in `backend/tests` (the AT ID is in the function name). "Browser" means the check was also done by hand in the running app, in Arabic and English.

| **Test** | **Automated test(s)** | **Result** |
|:---|:---|:--:|
| AT-AUT-01 | `test_at_aut_01_each_role_logs_in_with_its_role`; browser: each role's menu, the team page only for the Company Admin | Pass |
| AT-AUT-02 | `test_at_aut_02_registration_kinds_and_single_use_confirmation`, `test_at_aut_02_expired_confirmation_link`, `test_resend_confirmation` | Pass |
| AT-AUT-03 | `test_at_aut_03_idle_timeout_and_logout`, `test_session_max_lifetime` | Pass |
| AT-AUT-04 | `test_at_aut_04_password_reset`, `test_at_aut_04_expired_reset_link` | Pass |
| AT-AUT-05 | `test_every_route_is_in_the_matrix_and_nothing_else`, `test_at_aut_05_disallowed_callers_are_refused`, `test_allowed_callers_pass_the_role_gates`; scope cases in the module suites | Pass |
| AT-AUT-06 | `test_at_aut_06_deactivation`, `test_deactivated_user_session_ends`, `test_company_suspend_and_reactivate` | Pass |
| AT-ORG-01 | `test_at_org_01_new_college_appears_and_deactivated_does_not`, `test_registration_refused_for_inactive_college` | Pass |
| AT-ORG-02 | `test_at_org_02_unverified_accounts_are_limited` | Pass |
| AT-ORG-03 | `test_at_org_03_one_coordinator_per_college` | Pass |
| AT-ORG-04 | `test_at_org_04_company_verification` | Pass |
| AT-ORG-05 | `test_at_org_05_student_verification_enrols`, `test_student_request_waits_without_open_cycle` | Pass |
| AT-ORG-06 | `test_at_org_06_invited_supervisor_joins_the_college`, `test_at_org_06_expired_invitation_and_resend`, `test_company_admin_invites_colleague` | Pass |
| AT-ORG-08 | `test_at_org_08_document_access_and_purge` (clock moved 29 and 31 days) | Pass |
| AT-ORG-09 | `test_at_org_09_resubmission_after_rejection` | Pass |
| AT-CYC-01 | `test_at_cyc_01_unit_weeks_follow_weekday_and_time`, `test_at_cyc_01_api_creates_twelve_weeks`, `test_unit_partial_last_week_counts_only_days_in_the_cycle` | Pass |
| AT-CYC-02 | `test_at_cyc_02_weights_must_total_100` | Pass |
| AT-CYC-03 | `test_at_cyc_03_locked_rubric_cannot_change` | Pass |
| AT-CYC-04 | `test_at_cyc_04_unit_synonym_matches_and_shows_canonical_name`, `test_skill_catalog_admin` | Pass |
| AT-CYC-05 | `test_at_cyc_05_closed_cycle_is_read_only`, `test_closed_cycle_freezes_reports` | Pass |
| AT-PRF-02 | `test_at_prf_02_verified_student_cannot_edit_academic_fields`, `test_pending_student_can_correct_academic_fields` | Pass |
| AT-PRF-03 | `test_at_prf_03_size_and_type_limits_and_versions` | Pass |
| AT-PRF-04 | `test_at_prf_04_unit_full_dictionary_on_sample_cvs`, `test_at_prf_04_extracted_skills_are_only_candidates`, `test_arabic_docx_cv_extraction` | Pass |
| AT-PRF-05 | `test_at_prf_05_image_only_pdf`; browser: the message and the empty editable list | Pass |
| AT-VAC-01 | `test_at_vac_01_create_and_validate` | Pass |
| AT-VAC-02 | `test_at_vac_02_visibility` | Pass |
| AT-VAC-03 | `test_at_vac_03_filters` | Pass |
| AT-VAC-04 | `test_at_vac_04_application_rules` (duplicate, wrong training type, after deadline, sixth application), `test_unit_eligibility_reasons` | Pass |
| AT-VAC-05 | `test_at_vac_05_withdraw_frees_a_slot` | Pass |
| AT-VAC-06 | `test_at_vac_06_applicants_and_decisions` | Pass |
| AT-VAC-07 | `test_at_vac_07_placement_rules`, `test_placement_with_another_company_supervisor` | Pass |
| AT-VAC-08 | `test_at_vac_08_change_supervisor_and_cancel` | Pass |
| AT-REP-01 | `test_at_rep_01_slots_and_deadlines` | Pass |
| AT-REP-02 | `test_at_rep_02_attachment_limits`, `test_weekly_report_needs_all_fields`, `test_final_report_needs_a_main_document` | Pass |
| AT-REP-03 | `test_at_rep_03_drafts_private_and_submission_final` | Pass |
| AT-REP-04 | `test_at_rep_04_unit_deadline_minute_is_inclusive`, `test_at_rep_04_on_time_late_and_missing` | Pass |
| AT-REP-05 | `test_at_rep_05_revision_cycle_keeps_versions` | Pass |
| AT-REP-06 | `test_at_rep_06_comments` | Pass |
| AT-REP-07 | `test_at_rep_07_closed_slot_refuses_submission` | Pass |
| AT-WFL-01 | `test_at_wfl_01_every_allowed_transition_passes`, `test_at_wfl_01_disallowed_transitions_from_each_state_are_rejected` | Pass |
| AT-LOC-01 | `test_language_is_saved_and_used_for_errors`; browser: every Increment 1 page in both languages, right to left in Arabic and left to right in English | Pass |
| AT-LOC-02 | `frontend/src/i18n/keys.test.ts` (same keys in both files, every key used in the code exists, placeholders match); 506 keys | Pass |
| AT-AUD-01 | `test_m3_demo_scenario_and_at_aud_01`; dry-run step 10 | Pass |
| AT-AUD-02 | `test_at_aud_02_no_endpoint_changes_audit_entries`, `test_at_aud_02_database_refuses_update_and_delete`, `test_at_aud_02_filters_and_scope` | Pass |

## 4. Non-Functional Checks

| **ID** | **Evidence** | **Result** |
|:---|:---|:--:|
| NFR-SEC-02 | Argon2id hashing (`app/core/security.py`); `test_weak_password_refused` | Met |
| NFR-SEC-03 | `test_lockout_after_five_failures` (locked, then open again after 16 minutes); registration limit `test_registration_rate_limit` | Met |
| NFR-SEC-04 | Type detected from content (`test_at_prf_03…` refuses a PNG named `.pdf`, a ZIP named `.docx`, and text); files stored under random keys outside the web root; `403` without permission (`test_at_org_08…`, `test_cv_file_visible_to_company_only_after_application`); downloads send `nosniff` | Met |
| NFR-PRV-01 | `test_consent_gate`; privacy notice page at first login | Met |
| NFR-PRV-02 | Text extraction and skill matching run inside the API (`app/ai`); no outside service is called | Met |
| NFR-PRV-03 | Permission matrix; the Platform Admin is refused on CV, report, and placement routes; audit entries of the college only for its coordinator (`test_at_aud_02_filters_and_scope`) | Met |
| NFR-REL-04 | A refused attachment (too large or wrong type) leaves the draft and its other files unchanged (`test_at_rep_02_attachment_limits`) | Met |
| NFR-L10N-01 | Browser check of every page in both languages and directions | Met |
| NFR-L10N-02 | Deadlines stored in UTC and shown in Asia/Riyadh as DD/MM/YYYY HH:mm (`format.test.ts`); 1 minute before is on time, 1 minute after is late (`test_at_rep_04_unit_deadline_minute_is_inclusive`) | Met |
| NFR-MNT-01 | `.github/workflows/ci.yml` runs lint, tests with the 70% gate, and the frontend checks on every pull request; local coverage 95% | Met locally; CI run on the pull request |
| NFR-MNT-02 | OpenAPI generated by FastAPI; the frontend types are generated from it, and CI fails if either committed copy is out of date | Met |
| NFR-MNT-03 | Link validity, session timeout, lockout, application limit, file sizes, attachment count, and purge days are read from `system_settings` (`test_majors_and_settings`, `test_at_vac_05…` changes the limit) | Met |
| NFR-PRT-02 | `docker compose up -d --build` starts database, API (migrations and reference data on start), web app, and Mailpit; the dry run ran against it | Met |
| NFR-USA-03 | Checked at 375 px (phone, the sidebar stacks above the content) and 1280 px | Met |

## 5. M3 Demo Dry Run

Run with `backend/scripts/demo_dry_run.py` against `docker compose up` on Oct 24, 2026. Emails were read from Mailpit, and the demo clock was moved past the week 2 deadline for step 8.

| **Step** | **Result** |
|:---|:---|
| 1. Platform Admin adds a college and a skill | Pass |
| 2. Coordinator registers with an appointment letter, confirms the email, is approved | Pass |
| 3. 12-week Co-op cycle with 12 deadlines, weights 40/30/30, a rubric; invited academic supervisor joins | Pass |
| 4. Company registers and is approved; Company Admin invites a colleague; vacancy published for the university | Pass |
| 5. Student registers, sees the pending status, completes the profile, uploads a CV (6 skills suggested), confirms the skills | Pass |
| 6. Coordinator approves and enrols the student; the filtered list shows the vacancy; the student applies | Pass |
| 7. Company accepts; coordinator confirms the placement; 13 report slots appear | Pass |
| 8. Week 1 submitted late, revision requested, resubmitted (2 versions kept), accepted; week 2 closed as Missing | Pass |
| 9. Language switched to English and back, saved on the account | Pass |
| 10. Coordinator's audit log shows the student's 14 entries covering every step | Pass |

The same steps were also done by hand in the browser for the student (writing and submitting a report) and the academic supervisor (requesting a revision), and every page of the coordinator, company, and Platform Admin was opened in both languages.

## 6. Defects Found and Fixed

| **Defect** | **Found by** | **Fix** |
|:---|:---|:---|
| Sessions ended at once when the server's clock and the application clock differed (token issue time checked by the JWT library) | `test_at_aut_01…` | Expiry checked against the application clock only |
| Error messages ignored the user's saved language | `test_language_is_saved_and_used_for_errors` | Language kept on the request and applied when the error is written |
| Publishing a vacancy in the request that created it failed | Demo seed | Database session flushes pending rows before queries |
| A failed job could leave its lock held on a pooled connection, so the job never ran again | `test_job_failure_is_recorded_and_releases_the_lock` | Transaction-level advisory lock |
| The API container stopped at start with a plain `CORS_ORIGINS` value | `docker compose up` | Comma-separated values accepted; `test_config.py` |
| The Missing flag waited 15 minutes after every restart | Dry run on Docker | First run 30 seconds after start |
| Fractions such as `3.10 / 5.00` were reversed on Arabic pages | Browser check | Shown left to right |
| Single-word synonyms such as "rest", "spring", and "العربية" matched ordinary CV text | Review of the skill vocabulary | Removed; "Go" and "R" renamed |

## 7. Known Limitations and Follow-Up

- **Development tooling advisories:** `npm audit` reports 3 moderate advisories in Tailwind CSS 3 and its PostCSS helpers, which run only while the site is built. The fix is the move to Tailwind 4, planned for Increment 2. Vite and Vitest were upgraded in this increment for the same reason.
- **Backend type checking:** the frontend is type-checked in strict mode; the backend relies on `ruff` and the tests. A type checker for the backend is planned for Increment 2.
- **Browser tests:** the end-to-end checks of this increment were done by hand. Automated browser tests are planned with the Increment 2 screens.
- **Skill extraction accuracy** is measured at M4 on labelled CVs (decision RQ-4).
- **Performance and HTTPS** are checked on the free-tier deployment at the start of Increment 2 (decision RQ-7).
- **Email delivery** is tested through Mailpit; the real SMTP account is configured with the deployment.

## 8. Definition of Done

| **Item (01_Requirements Section 8)** | **Status** |
|:---|:---|
| Code merged into `main` through a pull request with CI green | Pull request opened from `increment-1`; merge after CI passes |
| Acceptance tests automated and passing; endpoints in the permission matrix | Done (Sections 3 and 1) |
| Screens in Arabic and English following the wireframes | Done |
| Actions write audit entries | Done (AT-AUD-01) |
| Design, API, or SRS updated where the implementation changed something | Done: [CR-07](../../Change_Requests.md), Design 1.3, API 1.2, [02_Design.md](02_Design.md) Section 12 |
| Demo scenario runs without help | Done (Section 5) |
