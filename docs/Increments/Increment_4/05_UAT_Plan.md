# Increment 4 – User Acceptance Testing Plan

**Status:** Ready Oct 28, 2026; sessions run by the project owner before Dec 10, 2026 · Author: Salam Alsaour  
**Requirement:** NFR-USA-01 (O8): at least 8 participants covering all five roles; at least 80% of the scenarios completed without help. **Also:** the device check of NFR-PRT-01 and FR-PWA-01 – 03 on real phones (Section 7).

## 1. Participants

| **Role** | **People** | **Who (SRS D-06)** |
|:---|:--:|:---|
| Student | 3 | Students of the college, at least one using a phone only |
| Company supervisor | 2 | Faculty with industry experience act as company supervisors; one of them is the Company Admin |
| Academic supervisor | 1 | A faculty member |
| Coordinator | 1 | A faculty member who knows the co-op process |
| Platform Admin | 1 | A student or staff member from IT |
| **Total** | **8** | |

A participant does the scenarios of one role. Nobody in the project team takes part as a participant.

## 2. Set-up

1. Start the local demo with fresh demo data. The new database is created when the API starts. The second command deletes everything stored in the local demo, so keep anything needed first:

   ```bash
   docker compose down
   docker volume rm internsync_db-data internsync_file-data
   docker compose up -d --build
   docker compose exec api python -m app.seed --demo
   ```

2. Each participant uses the demo account of their role (password `Demo-2026-pass`). Two participants of the same role do their sessions one after the other, with the data reset between them, or use the second account of the role.
3. The participant chooses Arabic or English at the start; the moderator notes the choice.
4. One session lasts about 20 minutes. It can run in person or online with screen sharing.

## 3. Consent (read to the participant)

> This session tests the InternSync system, not you. You will do a few tasks while I watch, and I will note whether each task was done without help. No name or personal data of yours is recorded: only your role, the language you chose, and the results. You can stop at any time. Do you agree to take part?

The moderator records "agreed" and the date in the result sheet. No recording is made.

## 4. How a Scenario Is Scored

| **Result** | **Meaning** |
|:---|:---|
| Done without help | Finished correctly with no hint from the moderator |
| Done with help | Finished after one or more hints |
| Not done | Not finished, or finished wrongly, within 5 minutes |

The moderator gives a hint only when the participant asks or has been stuck for 2 minutes, and notes what was unclear. **The share** is the number of "Done without help" divided by all the scenarios run, over all participants. The target is 80% or more.

After the session, the participant answers one question: "How easy was the system to use?" on a scale from 1 (very hard) to 5 (very easy).

## 5. Scenario Cards

The moderator hands the card, in the participant's language, and does not explain the screens.

### Student (accounts `s1@iau.edu.sa`; `s10@iau.edu.sa` for ST-4)

| **ID** | **Task given to the participant** | **Done when** |
|:--:|:---|:---|
| ST-1 | "Find the training opportunities that suit you best and see why the first one is recommended." | The recommendation list is open and the matched and missing skills of one vacancy are shown |
| ST-2 | "Write this week's report and submit it." | The report shows Submitted |
| ST-3 | "Turn off the internet (airplane mode), open your reports, and write next week's report. Then turn the internet back on." | The text is saved as a draft after reconnecting |
| ST-4 | "Your training has ended. Evaluate the company and answer whether they offered you a job." | Both answers are saved |

### Company supervisor (accounts `sara@nakheel.example`, `omar@nakheel.example`)

| **ID** | **Task** | **Done when** |
|:--:|:---|:---|
| CS-1 | "Record this week's attendance of your trainee: one day absent, with a note." | The week shows as recorded |
| CS-2 | "Fill in the periodic evaluation of your trainee and submit it." | The evaluation shows Submitted |
| CS-3 | (Company Admin) "Publish a new training opportunity for two students." | The vacancy shows Published |

### Academic supervisor (account `f.alharbi@iau.edu.sa`)

| **ID** | **Task** | **Done when** |
|:--:|:---|:---|
| AS-1 | "Review the last report your student submitted and ask for a revision with a comment." | The report shows Revision requested |
| AS-2 | "Check whether any report was flagged as similar to another report, and record your decision." | The decision is saved with a comment |

### Coordinator (account `coordinator@iau.edu.sa`)

| **ID** | **Task** | **Done when** |
|:--:|:---|:---|
| CO-1 | "Confirm the placement of the student waiting for one and assign an academic supervisor." | The placement is confirmed |
| CO-2 | "Export the grade sheet of the current cycle as Excel." | The file is downloaded and opens |
| CO-3 | "Issue the completion certificate of Fahad Al-Dosari (summer 2025) and check it with a phone camera." | The public page shows Valid |
| CO-4 | "Find which company of summer 2025 gives evaluations well above the others." | The participant names Nakheel Digital Solutions |

### Platform Admin (account `admin@internsync.example`)

| **ID** | **Task** | **Done when** |
|:--:|:---|:---|
| PA-1 | "Approve the pending verification request." | The request shows Approved |
| PA-2 | "Add a new skill, Kotlin Multiplatform, to the skill dictionary." | The skill is in the list |

## 6. Result Sheet

The sheet is [uat_results_template.csv](uat_results_template.csv): one row per scenario per participant, with the columns `participant, role, language, device, scenario, result, hints, note, ease`. The share of Section 4 is computed with a formula over the `result` column. The filled sheet and the summary go into this increment's test report.

## 7. Device Check (same sessions, on the participants' phones or the team's)

| **Check** | **Android (Chrome)** | **iPhone (Safari)** |
|:---|:--:|:--:|
| The app installs from the browser (Add to Home Screen) and opens full screen (FR-PWA-01) | ☐ | ☐ |
| With notifications allowed, a push arrives when a report is accepted (FR-PWA-02; on iPhone only for the installed app) | ☐ | ☐ |
| In airplane mode the app opens, shows the offline notice and the saved copy, and its action buttons are disabled (FR-PWA-03) | ☐ | ☐ |
| The main task of the role works (NFR-PRT-01) | ☐ | ☐ |

The local demo is reached from a phone on the same Wi-Fi network at `http://<laptop address>:5173`. Install and push need HTTPS outside `localhost`, so they are checked on the reference deployment once it is switched on ([Deployment](../../Deployment.md)), or with a phone browser's "localhost" port forwarding over USB.
