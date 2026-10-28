# Increment 3 – Design

**Status:** Approved for implementation · Oct 27, 2026; implemented Oct 27, 2026 (changes in Section 12) · Author: Salam Alsaour  
**Input:** [01_Requirements.md](01_Requirements.md), [Design 1.4](../../Design/InternSync_Design.md), [API 1.3](../../Design/InternSync_API_Spec.md), [Increment 2 design](../Increment_2/02_Design.md)

This document narrows the system design to what Increment 3 builds and records the decisions the system design leaves open. Where it says nothing, the system design, the API specification, and the earlier increment designs apply unchanged.

## 1. Modules

```
backend/app/
  similarity/      passages, the check, the decision; router (API 3.10)
  notifications/   events (the outbox writer), texts in both languages, delivery (email, push); router (3.17)
  exports/         pdf.py (fpdf2 document with the bundled fonts), grade sheet, term summary, training record; router (3.15)
  history/         router (3.18, FR-AUD-03)
  orgs/            + role transfers (FR-ORG-07)
  fonts/           Noto Naskh Arabic and Noto Sans, regular and bold, with the SIL Open Font License
frontend/public/   manifest.webmanifest, sw.js, icons
ai-eval/data/      similarity.json (10 copied and 10 original reports)
```

## 2. Data (migration `0005`)

| **Change** | **Notes** |
|:---|:---|
| `notifications` | As Design 4.3.8; partial index on rows with email or push `pending` for the delivery job |
| `push_subscriptions` | As Design 4.3.1 |
| `report_passages` | As Design 4.3.5, plus `slot_id` (copied from the version, like `university_id`) so the search can leave out every version of the same report without a join. HNSW index `halfvec_cosine_ops` |
| `similarity_checks` | As Design 4.3.5, plus `attempts` (the retry job stops after 3) |
| `similarity_matches` | As Design 4.3.5 |
| New settings | `similarity.threshold` 0.30, `similarity.passage_cosine` 0.90, `similarity.ngram_size` 5, `similarity.ngram_containment` 0.5, `notifications.reminder_hours_before` 24, `notifications.escalation_days` 3 (Design Table 4.1) |
| Row level security | On for the five new tables, as migration `0003` did for the others |

## 3. Endpoints Built

All of API Sections 3.10, 3.15, 3.17, and the history route of 3.18, and the two transfer routes of 3.2. `GET /notifications` returns each item with its text already in the caller's language (`title`, `body`), so the web app and the push service show the same words.

## 4. Similarity (Design 6.3)

1. **When.** `POST /report-slots/{id}/submit` creates the check as `pending` in the same transaction and hands the version to a background task, so the student's request does not wait (RQ-2). The `similarity_retry` job (every 5 minutes) runs checks still `pending` after 5 minutes and `failed` ones with fewer than 3 attempts.
2. **Passages.** The body text is split into sentences on `.`, `!`, `?`, `؟`, `؛`, and line breaks; a sentence shorter than 8 words joins the next one, and a sentence over 25 words is cut into 25-word pieces, so a passage is about one sentence (changed from 40–80 words, Section 12). Each passage keeps its character range. Passages are embedded with the `query: ` prefix, as both sides of the comparison are of the same kind.
3. **Candidates.** For each passage, the 5 nearest stored passages by cosine with the same `university_id` and another `slot_id` (`hnsw.iterative_scan = relaxed_order`, so the university filter never empties the result). Only submitted versions have passages.
4. **Confirm.** A passage counts for a source report when one of that report's candidates reaches `similarity.passage_cosine` and at least `similarity.ngram_containment` of the passage's word `n`-grams (normalized tokens, `n` = `similarity.ngram_size`, or the passage length if shorter) appear in that report's candidates taken together (Section 12). The side-by-side view lists the candidates that share words with the passage. The rule is one pure function (`passages.overlap`) used by the API and by the evaluation script.
5. **Score and flag.** Per source version: characters of the checked report covered by confirmed passages (overlaps merged) ÷ characters of the report. Flagged when the best source reaches `similarity.threshold`. The top 5 sources are stored with their passage pairs; the passages of the checked version are then stored for later checks.
6. **Without the model.** The check is `failed` with the reason and retried by the job; the report page says the check is not available. Nothing else waits for it.
7. **Visibility.** The assigned academic supervisor and the coordinator of the student's college see the result: score, flag, model version, and for each source its cycle, week (or "final report"), and passages. The source's author (name and student number) is added only for the coordinator of the source author's college (FR-SIM-02). The student does not see the check.
8. **Decision.** Only on a flagged check, by the assigned academic supervisor: `no_issue` or `overlap_confirmed` with a comment, audited. Nothing else changes (FR-SIM-03).

## 5. Notifications (Design 5.3 and Table 5.6)

- **Outbox (RQ-3).** `notify(db, users, event, params, link, key)` inserts one row per recipient in the caller's transaction; a repeated idempotency key is ignored (`ON CONFLICT DO NOTHING`), so a job that runs twice sends nothing twice (NFR-REL-03).
- **Texts.** `notifications/texts.py` holds the title and body of each event in Arabic and English, filled from `params`. The in-app list, the email, and the push use the recipient's current language (FR-NOT-06).
- **Delivery.** `deliver_notifications` (every minute) sends the email of each `pending` row (retry up to 5 times, then `failed`) and the push to each subscription of the user. Push is `skipped` when VAPID keys are not configured or the user has no subscription. A subscription answered with 404 or 410 is deleted. The push payload is `{title, link}` only (NFR-PRV-03).
- **Scheduled events.**
  - `send_reminders` (15 min): slots in `draft` or `revision_requested` of active placements due within `notifications.reminder_hours_before` hours; key `reminder:{slot}`.
  - `flag_missing` (existing): now also notifies the student and the academic supervisor; key `missing:{slot}:{user}`.
  - `escalate_overdue` (15 min): reports not submitted, attendance weeks not recorded, and evaluations not submitted, `notifications.escalation_days` days after their deadline, to the coordinator of the student's college; key `escalation:{type}:{id}`.
- **Event hooks.** Every event of Design Table 5.6 except `invitation.sent` (still a direct email) and `certificate.issued` (FR-CER, Could) is written by the service that makes the change.
- **Dashboard.** The coordinator gets `escalations` (open escalation items) and the academic supervisor `similarity_flags` (flagged checks without a decision).

## 6. Web Push and the App Shell

- **Keys (RQ-4).** `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, and `VAPID_SUBJECT` from the environment; `python -m app.cli vapid-keys` prints a new pair. The deploy script copies them to the Space when present.
- **Manifest.** `manifest.webmanifest`: name, short name, `start_url` `/`, `display: standalone`, theme and background colours of the design system, icons 192 and 512 px (also maskable), Arabic as the main language with `dir: auto`.
- **Service worker (RQ-5).** `sw.js`:
  - It caches the app shell (`/`, `index.html`, the manifest, the icons) at install, and the built files under `/assets/` on first use.
  - Pages are fetched network first, falling back to the cached `index.html`.
  - `/api/` is never cached.
  - It shows push notifications and opens their link when clicked.
  - It is registered in production builds only, so the development server is not affected.
- **Offline.** An online/offline hook drives a banner in the layout, and every action button is disabled while offline (FR-PWA-03).
- **Push settings.** The notification page offers "Turn on push notifications" when the browser supports it; the subscription is sent to `POST /push/subscriptions` and removed with `DELETE` when turned off.

## 7. Exports (Design 5.6, changed by RQ-1)

- **PDF.** fpdf2 with HarfBuzz shaping and the bundled fonts: Noto Sans with Noto Naskh Arabic as fallback, so mixed Arabic and English text renders in one line. Percentages use the Arabic percent sign in Arabic, and the footer keeps the page number and the time in separate cells so the directions never mix.
  - In Arabic the page runs right to left: the title is right-aligned, and the table columns are in reverse order.
  - Values are taken from the same services as the screens: grades from `grades.service`, statistics from `dashboard.service`.
- **Excel.** openpyxl, one row per placement, a header row, and the sheet set right to left in Arabic. Text cells that start with `=`, `+`, `-`, or `@` get a leading `'` (formula injection).
- **Files.** Streamed as attachments with names such as `grade-sheet-<cycle>.xlsx`; each export writes an `export` audit entry (who exported what).
- **Speed (NFR-PER-05).** The rows are built with the same functions as the grade screens, a few queries per row; 100 rows take about 1 s for Excel and 2.5 s for the PDF.

## 8. History (FR-AUD-03)

`GET /history/{entity_type}/{entity_id}` for `report_slot`, `evaluation`, and `grade`: the caller must be allowed to view the record (the rules of its own endpoint). The answer lists the record's audit entries, oldest first: time, action, the user's name and role (or "system"), the old and new status, and the reason. The report page, each evaluation, and the grade tab get a "History" panel.

## 9. Role Transfer (FR-ORG-07)

- **Coordinator.** `POST /colleges/{id}/coordinator/transfer {user_id, reason}`: the new holder must be an active academic supervisor of the same college. In one transaction, the previous coordinator becomes an academic supervisor and the new one becomes the verified coordinator, in that order, because one college has one coordinator.
- **Company Admin.** `POST /companies/{id}/admin/transfer {user_id, reason}`: the new holder must be an active company supervisor of the same company; the flag moves the same way.
- **Common.** A reason is required. The change is audited with both users, both are notified (`role.transferred`), and rights follow at once, because the role is read from the database on every request.
- **Screen.** The Platform Admin's organization page gets a "Transfer" action next to the coordinator and the Company Admin.

## 10. Frontend

| **Area** | **Screens** |
|:---|:---|
| All roles | Bell with the unread count in the header; notification page (mark read, mark all read, push on or off); offline banner; installable app |
| Academic supervisor | Similarity panel on the report review (`AS_ReportReview`): Advisory label, score, sources, passages side by side, decision form; dashboard item for flagged checks |
| Coordinator | Exports page (`CO_Exports`): grade sheet in Excel and PDF, term summary; training record on the placement page; similarity result with the source author; escalations on the dashboard |
| Academic supervisor and coordinator | Training record download on the placement page |
| Platform Admin | Transfer dialogs on the organization page |
| Reports, evaluations, grades | History panel |

## 11. Test Design

- **Similarity:** unit tests for the passage splitter and the n-gram containment; API tests with the stand-in embedder for AT-SIM-01 – 03 (another university seeded with the same text); a timed test with 10,000 stored reports (AT-PER-04); the evaluation script on the 20-report set.
- **Notifications:** each event of FR-NOT-05 driven through the API, then the outbox checked for the right recipient and language; the jobs run twice to prove no duplicates; delivery with the memory mail backend and a stand-in push sender (payload inspected, 410 handling).
- **Exports:** the Excel file read back with openpyxl and the PDF text read back with pypdf, compared with the stored values; a timed test with 100 placements (AT-PER-05).
- **History, transfers:** API tests, including the refusals.
- **PWA:** a unit test of the manifest (required fields, icon sizes); the install and the offline behaviour checked in the browser on a production build.
- **Permission matrix:** the new routes are added.
- **Demo data:** the seed adds a former student of a closed spring cycle with an accepted week 1 report, so the demo can show a similarity flag; the check of that report runs during the seed (or later by the retry job).

## 12. Changes During Implementation

Recorded as [CR-09](../../Change_Requests.md); the system design (1.5) and the API specification (1.4) were updated in the same pull request. The test results are in [04_Test_Report.md](04_Test_Report.md).

| **Change** | **Why** |
|:---|:---|
| Passages of about one sentence (8–25 words) instead of 40–80 words | With realistic copying (about half of a report), the evaluation set found 4 of 10 copied reports with long passages and 10 of 10 with sentence passages; originals: none flagged either way |
| A passage is compared with the source report's nearby passages taken together | A copied passage often spans two source passages, so neither alone reached half of its word sequences |
| The side-by-side view lists only source passages that share words with the passage | All five neighbours were shown at first, most of them unrelated |
| `report_passages.slot_id`, `similarity_checks.attempts` and `created_at` | Leave out every version of the same report without a join; let the retry job stop after 3 attempts and find stale pending checks |
| Escalation filter named `type`, as in the API specification | It was `kind` in the first build |
| The backend dependency audit fails on any known vulnerability, not only critical ones (RQ-9) | `pip-audit` has no severity filter; the frontend audit keeps the `critical` level |
| Former student with an accepted report in the demo data | The demo shows a similarity flag without preparing data by hand |

Defects found by the tests, the evaluation, and the browser and visual checks, and fixed before the pull request:

- **Similarity:** the two changes above, found by the evaluation script once the copied share was lowered to the 40% of the acceptance criterion (it was over 70% in the first version of the set, which hid the problem).
- **PDF layout, found by rendering the exported files:**
  - Component weights printed as "30.00".
  - In Arabic, the footer mixed the date and the page number in the wrong order, and the total page count left a gap, because it is filled in after shaping; the footer now shows the page number alone.
  - The percent sign is the Arabic one in Arabic.
  - The cycle name and its dates were on one line and reordered each other.
- **Web app:**
  - The history arrow pointed backwards in English.
  - "11 أيام" was not correct Arabic, so overdue days are now a number under a "days overdue" header.

