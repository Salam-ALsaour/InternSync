# InternSync – Key Results

**Updated Oct 28, 2026, at the end of Increment 4** · Author: Salam Alsaour

Every measured result of the project in one place, for the final presentation. Each number is copied from a test report or a run of a script in the repository, with its target and the way to repeat it. Numbers measured on the local Docker stack (a laptop) say so; they are repeated on the reference deployment once it is switched on ([Deployment](Deployment.md)).

## 1. Headline Numbers

| **What** | **Result** | **Target** |
|:---|:---|:---|
| Automated tests | **201 backend tests**, **19 frontend unit tests**, **34 browser tests** on four browser engines and sizes, all passing | All pass |
| Code covered by the backend tests | **95%** | 70% |
| Permission checks | **810** calls by users who must be refused, over **163** endpoints: **0** got through | 0 (O1) |
| Matching: a relevant vacancy in the top 5 | **100%** of profiles on the tuning set and **100%** on the held-out set (a random order: 80% and 36%) | 80% (O2) |
| Skills found in CVs | **97.2%** (English 97.4%, Arabic 96.9%) | 70% |
| Copied reports flagged | **10 of 10** on the tuning set; **7 of 10** on the held-out set: all 7 copied word for word, none of the 3 reworded | 9 of 10 (O5) |
| Original reports wrongly flagged | **0 of 10** on both sets | At most 1 of 10 |
| 50 users at once | **95%** of requests within **0.21 s**, 0 errors in 7,785 requests | Within 2 s (NFR-PER-01) |
| Grade sheet of 100 students | **1.0–1.3 s** Excel, **2.4–4.6 s** PDF | Under 60 s (O6) |
| Similarity result with 10,000 stored reports | **0.35–0.42 s** | Within 2 minutes |
| Security scan (OWASP ZAP) | **0** high-risk findings; the API scan clean after two fixes | 0 high (NFR-SEC-05) |
| Known vulnerable dependencies | **0** (pip-audit, npm audit) | 0 critical |
| Screens in both languages | **100%**: 839 texts in Arabic and in English, right to left and left to right | 100% (O7) |
| Running cost | **0** (free tiers only) | 0 (CR-01) |

## 2. Quality and Testing

| **Check** | **Result** | **Repeat with** | **Source** |
|:---|:---|:---|:---|
| Backend tests on a real PostgreSQL | 108 → 158 → 187 → **201** passing at the end of Increments 1 to 4 | `pytest --cov=app` in `backend/` | Test reports 1–4, Section 1 |
| Backend line coverage | 95% at the end of every increment | same | same |
| Permission matrix | 107 → 129 → 145 → **163** endpoints; **810** refused calls checked, none allowed | same (`tests/permissions`) | same |
| Acceptance tests | Increment 1: 43 of 43 · Increment 2: 27 of 27 · Increment 3: 21 of 21 · Increment 4: 12 of 13; AT-AI-03 is met for matching and not for reworded copies (7 of 10 flagged, target 9) | same | Test reports, Section 3 |
| Demo scenarios automated end to end | M4, M5, and M6 scenarios run through the API in the test suite | `pytest tests/test_demo_m*.py` | `backend/tests` |
| Browser tests | **34 passed** on Chromium, WebKit (the Safari engine), an Android phone size, and an iPhone size, including a keyboard-only task; Firefox runs in CI | `npx playwright test` in `frontend/` | Test report 4, Section 4 |
| Frontend | TypeScript strict build clean; 19 unit tests; production build succeeds | `npx tsc -b && npx vitest run && npx vite build` | same |

## 3. AI Accuracy

All sets are synthetic and labelled by the author (SRS C-09). The tuning sets were used to choose the settings; the **held-out sets** were written after the settings were frozen and run once, so they are the honest numbers.

| **Measure** | **Tuning set** | **Held-out set** | **Target** |
|:---|:---|:---|:---|
| Skill extraction recall (20 CVs, Arabic and English) | 97.2% | – | 70% |
| Matching, relevant vacancy in the top 5 | 100% (9 eligible vacancies per profile; random order 79.7%) | 100% (15 eligible per profile, one skill per vacancy; random order 35.7%) | 80% |
| Matching, relevant vacancy first | 100% | 60% (random order 7.3%) | – |
| Similarity, copied reports flagged | 10 of 10 (44–54% copied) | 7 of 10: 7 of 7 copied word for word, 0 of 3 reworded sentence by sentence | 9 of 10 |
| Similarity, original reports flagged | 0 of 10 | 0 of 10 | At most 1 |

**What the numbers mean:**

- The similarity check finds copied text, not copied ideas. A report reworded sentence by sentence is not flagged. This is the expected limit of the word n-gram rule (Design 6.3).
- The flag is advisory: a supervisor decides, and nothing changes automatically (NFR-AI-01).

**Repeat with:**

```bash
backend/.venv/Scripts/python ai-eval/evaluate.py             # tuning sets
backend/.venv/Scripts/python ai-eval/evaluate.py --heldout   # held-out sets
```

## 4. Speed

| **Requirement** | **Measured** | **Limit** | **Where** | **Source** |
|:---|:---|:---|:---|:---|
| NFR-PER-01: ordinary requests, 50 users at once | 95th percentile **0.21 s** over 7,785 requests in 5 minutes; slowest kind (placement list) 0.52 s; 0 errors | 2 s | Local Docker stack | Test report 4, Section 4 |
| NFR-PER-02: ranked vacancies, 1,000 open | 95th percentile **0.83 s** with the model, 0.76 s rule-based | 5 s | Test database | Test report 2 |
| NFR-PER-03: skills from a 5 MB CV | **2–6 s** (94 s before the fix found in testing) | 30 s | Test database | Test report 2 |
| NFR-PER-04: similarity with 10,000 stored reports | **0.35–0.42 s** | 2 minutes | Test database | Test report 3 |
| NFR-PER-05: grade sheet of 100 students | **1.0–1.3 s** Excel, **2.4–4.6 s** PDF | 60 s each | Test database | Test report 3 |

## 5. Security and Privacy

| **Check** | **Result** |
|:---|:---|
| OWASP ZAP baseline of the web app | 0 high; medium findings only for headers that the development server does not send. The hosted app sends them (`vercel.json`), and the Content-Security-Policy was added in this increment |
| OWASP ZAP scan of the API (safe mode, 120 rules) | 0 high; two low findings fixed (`nosniff`, resource policy), then 0 warnings |
| Dependency audits in CI | 0 known vulnerabilities (pip-audit, npm audit) |
| Passwords and sign-in | Argon2id; lockout after 5 failures; 30-minute idle limit, also on the device offline |
| Who sees what | Every endpoint checked for every role (Section 2); the company never sees the student's evaluation of it; the grade is never on the certificate page |
| Privacy | Consent notice at first login; push messages carry a title only; anonymization of closed cycles after the retention period, with the statistics unchanged; offline copies deleted at sign-out |

## 6. Languages, Devices, and Accessibility

| **Check** | **Result** |
|:---|:---|
| Two languages | 839 texts in each of Arabic and English, checked equal by a test; Arabic right to left; Arabic PDFs with joined letters |
| Screen widths | No horizontal scrolling at 360, 768, 1366, and 1920 px on the main pages of the student and the coordinator (browser tests) |
| Contrast | No text below 4.5:1 on the main pages (automated axe check); one dev-only failure fixed |
| Installable app and offline mode | Installs as an app; offline, pages opened earlier stay readable and drafts typed offline are saved after reconnecting (browser test on four engines) |

## 7. Scope Delivered

| **Priority** | **Delivered** |
|:---|:---|
| Must (Increments 1 and 2) | All |
| Should (Increment 3, plus the changed FR-PWA-03 in Increment 4) | All |
| Could (Increment 4): certificates, evaluation of the company, job-offer survey, leniency alert, anonymization | All |
| Product functions F1 to F19 of the Proposal | 19 of 19 |

## 8. Still to Measure

| **What** | **When** |
|:---|:---|
| User acceptance testing, at least 8 participants, 80% of scenarios without help (O8) | Sessions run by the owner before Dec 10 ([plan](Increments/Increment_4/05_UAT_Plan.md)) |
| Install, push, and airplane mode on real Android and iPhone devices | In the UAT sessions |
| NFR-PER-01 and the ZAP scan on the reference deployment | After the switch-on ([Deployment](Deployment.md)) |

## Revision History

| **Date** | **Change** |
|:--:|:---|
| Oct 28, 2026 | First version, at the end of Increment 4 |
