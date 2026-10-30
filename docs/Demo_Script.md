# InternSync – Final Demonstration Script

**Version 1.0 · Oct 29, 2026 · Milestone M7 (Dec 15, 2026)**

A 15-minute demonstration that shows one function of each increment, on the local Docker stack with fresh demo data. All demo accounts use the password `Demo-2026-pass`.

## 1. Preparation (the day before and 30 minutes before)

1. **Fresh demo data.** These commands delete everything stored in the local demo and load the demo data again:

   ```bash
   docker compose down
   docker volume rm internsync_db-data internsync_file-data
   docker compose up -d --build
   docker compose exec api python -m app.seed --demo
   ```

2. **Wait for the model.** The API log shows `embedding model loaded` (about 15 s after start): `docker compose logs api | findstr "model loaded"`.
3. **Browser windows** (one per role, so nobody signs in during the demo):
   - a normal window for the student;
   - private windows for the academic supervisor and the coordinator;
   - a second browser for the company.

   Set each to the language of the audience.
4. **A phone** on the same Wi-Fi network, to scan the certificate's QR code. Find the laptop's address with `ipconfig`; the phone opens `http://<address>:5173`.
5. **Copy to the clipboard** the former student's paragraph (README, "To show a similarity flag").
6. **Open beside the demo:**
   - [Key_Results.md](Key_Results.md) for the numbers;
   - the [slides](https://claude.ai/artifact/3KnHXL8q7QgWXN1xwaynKp) (or their PowerPoint download, if there may be no internet).

## 2. The Demonstration (15 minutes)

| **Time** | **Who** | **What to show** | **What to say** |
|:--:|:---|:---|:---|
| 0:00 | – | Slides 1–4 | The problem, the five users, and the solution in one picture |
| 2:00 | Student `s1@iau.edu.sa` | Training opportunities, Recommended tab: the fit score, matched and missing skills, Advisory label, development plan | Matching uses a multilingual model on our own server; it advises, the student decides (Increment 2) |
| 3:30 | Student | My reports: open this week's report, paste the former student's paragraph into "Tasks performed", fill the rest, Submit | Deadlines in Riyadh time; Late is computed by the server (Increment 1) |
| 4:30 | Academic supervisor `f.alharbi@iau.edu.sa` | Home: the similarity flag; open the report: score, passages side by side; record "Overlap confirmed" with a comment | Compared only with reports of the same university; advisory (Increment 3) |
| 6:00 | Company `sara@nakheel.example` | Trainees, then the trainee: record this week's attendance, open the periodic evaluation on the rubric | One rubric for every company (Increment 2) |
| 7:00 | Coordinator `coordinator@iau.edu.sa` | Cycles, Summer 2025 (demo), Statistics: the leniency alert, the job-offer rate, the companies' ratings | Information for the coordinator only; the company never sees the students' answers (Increment 4) |
| 8:30 | Coordinator | Certificates: open Lama Al-Harbi's certificate PDF; scan its QR code with the phone: Valid, no grade | Code of 128 random bits; the public page never shows the grade |
| 9:30 | Coordinator | Exports: the grade sheet in Excel and PDF (Arabic names joined correctly) | 100 students in about 1 s (Excel) and 2–5 s (PDF) |
| 10:30 | Student (phone or the student window) | Turn off Wi-Fi (or the browser's offline mode): the saved copy with its time; type next week's report; turn Wi-Fi on: the draft is saved | Offline mode (CR-10); submitting still needs the connection |
| 11:30 | Coordinator | The summer cycle page, Data retention: the counts, then "Anonymize personal data"; the statistics stay the same | Privacy after the retention period (NFR-PRV-04) |
| 12:30 | – | Slides on quality, AI accuracy, and speed (Key Results) | 201 automated backend tests, 810 refused permission checks, the honest held-out result |
| 14:00 | – | Lessons, open items, thanks | UAT and the online deployment are the open items |

## 3. If Something Fails

| **Problem** | **What to do** |
|:---|:---|
| Docker Desktop does not start | Quit it fully, then start it again. If it reports a socket file that "cannot be accessed by the system", move the folder named in the message aside (for example `%LOCALAPPDATA%\Docker\run`) and start again. **Never choose "Reset to factory defaults" before the demo:** it deletes the demo data |
| The similarity result shows "pending" | The model is still loading; wait 30 s and reload. The retry job also runs every 5 minutes |
| No network for the phone | Show the certificate page in a laptop browser at `/verify` and type the code |
| The anonymization was already run | Show the cycle's statistics and the anonymized names instead; reset the data after the demo |
| A screen is in the wrong language | The language button at the top switches it for that account |

## 4. Likely Questions

| **Question** | **Where the answer is** |
|:---|:---|
| How do you know the matching works? | Key Results, Section 3; [Increment 2 test report](Increments/Increment_2/04_Test_Report.md), Section 5 |
| What does the similarity check miss? | Reworded copies: Key Results, Section 3; [Increment 4 test report](Increments/Increment_4/04_Test_Report.md), Section 5 |
| How is access controlled? | Design 7.2 and the permission matrix (163 endpoints × every role) |
| What does it cost to run? | Nothing: [Deployment](Deployment.md), Section 7 |
| What changed from the plan? | [Change requests](Change_Requests.md) CR-01 to CR-11; [Final report](Final_Report.md), Section 5 |
| Which requirements are tested? | [Requirements status](Requirements_Status.md) |
