# Increment 4 – Test Report

**Date:** Oct 28, 2026 · Author: Salam Alsaour  
**Scope:** [01_Requirements.md](01_Requirements.md) (7 Could requirements, FR-PWA-03 as changed by CR-10, and the release checks of Section 4.2) · **Design:** [02_Design.md](02_Design.md)  
**Milestone:** M6 – Testing complete (Dec 10, 2026). The build and the release checks are done; the user acceptance testing is prepared ([05_UAT_Plan.md](05_UAT_Plan.md)) and its results will be added here.

## 1. Summary

| **Check** | **Result** |
|:---|:---|
| Backend tests (pytest, real PostgreSQL) | **201 passed**, 0 failed (187 at the end of Increment 3) |
| Backend line coverage | **95%** of `app` (7,087 statements; gate 70%) |
| Permission matrix | 163 routes listed (18 new); **810** calls by callers that are not allowed, all answered `401` or `403` |
| Acceptance tests of 01_Requirements Section 6 | **12 of 13 met**. AT-AI-03 is met for matching and not for similarity: 7 of 10 copied reports of the held-out set flagged, target 9 (Section 5) |
| Browser tests (Playwright) | **34 passed** on Chromium, WebKit, a Pixel 7, and an iPhone 14; 18 skipped by design (the layout checks run once). Firefox does not start on the development laptop, which blocks its executable, so it runs in CI |
| Frontend | TypeScript strict build clean; **19 Vitest tests passed**; production build succeeds; 839 translation keys in each language |
| Security scan (OWASP ZAP) | Web app baseline: 0 high, 0 failures. API scan in safe mode: 0 high, 0 warnings after two fixes (Section 6) |
| Load test (Locust, 50 users, 5 minutes) | 7,785 requests, **0 errors**; 95th percentile **0.21 s** (limit 2 s) |
| Dependency audits | pip-audit and `npm audit --omit=dev`: no known vulnerabilities |
| AI evaluation, held-out sets | Matching top-5 **100%** (random order 35.7%); similarity **7 of 10** copied flagged, **0 of 10** originals (Section 5) |
| AI evaluation, tuning sets (unchanged) | Skill recall 97.2%; matching top-5 100%; similarity 10 of 10 and 0 of 10 |
| Backup and restore | Dump of the check database restored into a new database; every table, the new ones included, has the same row count |
| M6 demo scenario | Steps 1–5 automated through the API on the demo data (`test_m6_demo_scenario`); step 6 in the browser tests; step 7 is [Key_Results.md](../../Key_Results.md) |
| Lint | `ruff` clean on `app`, `tests`, `alembic`, `scripts`, `loadtest` |
| Committed scope | 8 of 8 requirements delivered |

## 2. How to Repeat the Tests

```bash
cd backend && pytest --cov=app                                   # 201 tests
backend/.venv/Scripts/python ai-eval/evaluate.py --heldout         # from the repository root
```

The browser tests, the load test, and the ZAP scan run against the Docker stack on its own database, as the README shows (`docker-compose.check.yml`).

## 3. Acceptance Tests

| **Test** | **How** | **Result** |
|:---|:---|:--:|
| AT-CER-01 | `test_at_cer_01_only_a_final_grade_gets_a_certificate`: refused before Final; 26-character code; the PDF text holds the code, the name, and the company and no grade; the QR code read back from the PDF (zxing) equals the page address; a second valid one refused; the file only for the student and the coordinator | Pass |
| AT-CER-02 | `test_at_cer_02_public_check_valid_revoked_and_altered` (fields exactly as FR-CER-02 lists; dashes and lower case accepted); browser test `public.spec.ts` on four engines | Pass |
| AT-CER-03 | `test_at_cer_03_revoke_needs_a_reason_then_a_new_one_can_be_issued` | Pass |
| AT-EVL-05 | `test_at_evl_05_…`: opens at the training end date (and with a Final grade, `test_feedback_opens_with_the_final_grade…`), once only, the coordinator sees it and the averages, and the company supervisor, Company Admin, academic supervisor, another coordinator, another student, and the Platform Admin are refused on every path | Pass |
| AT-DSH-03 | `test_at_dsh_03_job_offer_rate_is_yes_over_answers`: 3 Yes of 4 answers is 75.0%; a student who skipped is not counted; Pending changed to Yes | Pass |
| AT-DSH-04 | `test_at_dsh_04_leniency_alert_from_five_final_evaluations` (4.8 against 3.6 alerts) and `…four_evaluations_raise_no_alert` | Pass |
| AT-PRV-04 | `test_at_prv_04_anonymize_after_the_retention_period`: refused while open and before the period; afterwards no name, email, student number, CV file, report text, comment, or certificate file can be retrieved; the audit log is masked; the student still in another open cycle is skipped; the four statistics answers are identical before and after; the cycle cannot be reopened. The demo data repeats it (`test_m6_demo_scenario`) | Pass |
| AT-PWA-03 | Unit tests `offline.test.ts` (what the copy keeps and leaves out, another user, sign-out, idle time, draft expiry); browser test `offline.spec.ts` on four engines: saved copy with its time, the not-saved notice, the draft typed offline saved after reconnecting, nothing left after sign-out | Pass |
| AT-SEC-05 | ZAP baseline and API scan (Section 6); dependency audits | Pass |
| AT-PER-01 | Locust, 50 users (Section 4) | Pass on the local stack |
| AT-PRT-01 | Browser tests on Chromium, WebKit, Pixel 7, iPhone 14; no horizontal scrolling at 360, 768, 1366, and 1920 px | Pass; Firefox in CI, real phones in the UAT |
| AT-USA-04 | axe contrast check on 12 pages; keyboard-only browser test (sign in, open the reports, save a draft) | Pass |
| AT-AI-03 | Held-out sets run once (Section 5) | Matching met; similarity **not met** |

## 4. Release Checks (Section 4.2)

| **ID** | **Result** | **Status** |
|:---|:---|:--:|
| NFR-SEC-05 | ZAP: 0 high-risk findings (Section 6); audits clean | Met |
| NFR-PER-01 | Local Docker stack on the development laptop, 50 users, spawn 5 per second, 5 minutes: 7,785 requests, 0 failures; 95th percentile 0.21 s over all requests. By kind: dashboard 0.14 s, placement list 0.52 s (the slowest), report slots 0.13 s, attendance 0.19 s, vacancies 0.29 s, draft save 0.20 s, sign-in 0.83 s (Argon2 on purpose). Slowest single request 1.9 s | Met on the local stack; repeated on the reference deployment after the switch-on |
| NFR-PRT-01 | Browser tests (Section 3) | Met for four engines and sizes; Firefox in CI; phones in the UAT |
| NFR-USA-03 | No horizontal scrolling at the four widths on 11 pages (sign-in, five of the student, five of the coordinator) | Met |
| NFR-USA-04 | No contrast failure on 12 pages after one fix (Section 7); the main task done with the keyboard alone | Met |
| NFR-AI-03 | Held-out sets in the repository, the script reproduces the numbers | Met; the similarity target is not (Section 5) |
| NFR-REL-02 | Restore of a dump of the check database: identical row counts in every table, `certificates`, `company_evaluations`, and `outcome_surveys` included | Met |
| NFR-USA-01 | UAT plan, task cards, consent text, and result sheet ready | Pending: run by the owner |

## 5. Held-out AI Evaluation (RQ-6)

The sets were written on Oct 28, after the settings of CR-09 were frozen, and labelled before the first run. They ran once; no setting was changed afterwards.

| **Set** | **Result** | **Random order** | **Target** |
|:---|:---|:---|:---|
| Matching: 10 profiles, 15 vacancies with one listed skill each, all open to every profile | Top-5 **100%**; top-1 **60%**; mean reciprocal rank **0.767** | 35.7%; 7.3%; 0.232 | 80% top-5 |
| Similarity: 4 sources, 10 copied reports (48–78% copied), 10 originals on the same topics | **7 of 10** copied flagged: all 7 copied word for word, none of the 3 reworded (HC04, HC05, HC10, score 0); **0 of 10** originals flagged | – | 9 of 10; at most 1 |

**What this shows:**

- **Matching** holds on a harder set: the model ranks the right vacancy high even when the vacancy names one skill only.
- **Similarity** finds copied text reliably and never accused an original report, but a report reworded sentence by sentence escapes the word 5-gram rule entirely.
- **The 9-of-10 target** (O5) was written for "copied" reports. It is met for text copied word for word (7 of 7 here, 10 of 10 on the tuning set) and not for paraphrase.
- **The flag is advisory** and the supervisor decides (NFR-AI-01). The test report records the limit instead of retuning the setting on this set, which would make it a tuning set again.
- **Possible remedy:** a rule on the embedding similarity alone. It would also flag original reports on the same topic, so it needs its own evaluation. It is listed for after the project (Section 8).

## 6. Security Scan (NFR-SEC-05)

| **Target** | **Findings** | **Action** |
|:---|:---|:---|
| Web app (development server), ZAP baseline | Medium: no Content-Security-Policy, no anti-clickjacking header. Low: COEP, COOP, CORP, Permissions-Policy, `nosniff`. Informational only otherwise | The hosted app is served by Vercel with `vercel.json`. It already sent `nosniff`, `X-Frame-Options`, Referrer-Policy, and Permissions-Policy. **It sent no Content-Security-Policy although the design said so (defect 3)**: added with COOP. The production preview now sends the same headers, and a run in the browser showed no blocked resource |
| API, ZAP API scan in safe mode from the OpenAPI document | Low: `X-Content-Type-Options` and `Cross-Origin-Resource-Policy` missing on JSON answers | Both added to every answer (`test_every_answer_has_the_release_check_headers`); the rescan passed 120 rules with 0 warnings |

The workflow `security-scan.yml` repeats both scans every week and fails on a high-risk alert.

## 7. Defects Found and Fixed

| **Defect** | **Found by** | **Fix** |
|:---|:---|:---|
| 1. The server's 30-minute idle limit never ended a session while a window stayed open: the notification count asks the API every minute | Design review of the offline idle limit | The app counts idle time from the last key, click, or touch and ends the session itself, online and offline (CR-11) |
| 2. The saved copy was written at most once a second, so a page opened just before a reload was missing offline | Browser test `offline.spec.ts` | The copy is also written when the page is left or reloaded |
| 3. `vercel.json` sent no Content-Security-Policy, although Design 7.1 relies on one | ZAP baseline | Strict policy added. A browser run then showed that the build inlines small fonts as `data:` URLs, so `font-src` allows `data:` |
| 4. API answers without `nosniff` and a resource policy | ZAP API scan | Middleware adds both |
| 5. The demo clock buttons (development only) had a contrast of 3.86:1 | axe check | White text |
| 6. The registration audit entry stored the email address, which an anonymization could not remove from the append-only log | Design of NFR-PRV-04 | The entry keeps the kind only; older entries are masked when read |
| 7. Certificates listed in a changing order when two had the same time | Test with the frozen clock | The valid certificate first, then the newest |

## 8. Limitations and Notes

- **Similarity and paraphrase:** Section 5. Students are told that the check is advisory; a supervisor reading the passages decides.
- **The held-out sets were written by the author**, like the tuning sets, because no second person was available (RQ-6). They are independent of the settings, not of the author.
- **The load test ran on the development laptop.** The free Space has 2 CPU cores, so the numbers there will be higher. The same script runs against it after the switch-on.
- **Offline copy and app restarts:** the copy lives as long as the window, so closing the installed app ends it. This is chosen for privacy on shared devices (RQ-2).
- **Firefox:** covered by CI on Linux. On the development laptop Windows blocks the downloaded Firefox build.
- **Docker Desktop on the development laptop** crashed twice during this increment, after being stopped by force. Leftover socket files blocked its start until they were moved aside. This was a laptop problem, not a project problem, but it is noted because the demo runs on Docker.

## 9. Pending for M6

| **Item** | **Owner** | **Plan** |
|:---|:---|:---|
| UAT with at least 8 participants (O8) | Project owner | [05_UAT_Plan.md](05_UAT_Plan.md); results into this report |
| Device check on an Android phone and an iPhone | Project owner | Same sessions (UAT plan, Section 7) |
| Firefox browser tests | CI | First run on this pull request |
| NFR-PER-01 and ZAP on the reference deployment | After the switch-on | Same scripts |

## 10. Definition of Done

| **Criterion** | **Status** |
|:---|:---|
| Code merged through a pull request with CI green | On this pull request |
| Acceptance tests automated and passing, or checked in the browser; endpoints in the permission matrix | Done, except the similarity part of AT-AI-03 (Section 5) |
| Screens in Arabic and English, following the wireframes or the existing layout | Done (`Verify_Mobile`; the other screens follow the existing pages) |
| Actions audited | Issue, revoke, evaluation of the company, survey, retention, anonymization |
| Documents updated | SRS 1.6, Design 1.6, API 1.5, SPMP 1.6, Deployment 1.2, CR-10, CR-11, README, Key_Results |
| Release checks with results here and in Key_Results | Done |
| UAT materials ready | Done; the sessions are pending |
