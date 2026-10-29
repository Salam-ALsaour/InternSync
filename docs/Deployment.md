# InternSync – Deployment

**Version 1.2 · October 28, 2026 · Increments 2 to 4 (decision RQ-8 of Increment 2)**

This document describes the zero-cost reference deployment of System Design Section 3 and how to switch it on. Everything in the repository is ready. The deployment is switched on once the owner has done the steps in Section 3, which need accounts only the owner can create. Until then, the deployment workflows run and report that there is nothing to do.

## 1. Parts

| **Part** | **Service (free tier)** | **What runs there** |
|:---|:---|:---|
| Web app | Vercel Hobby | The static build of `frontend/`; `VITE_API_URL` points it at the API |
| API | Hugging Face Space, Docker, CPU basic | The image from `backend/Dockerfile` with the embedding model inside; port 7860 |
| Database | Supabase Free | PostgreSQL with `vector` and `pg_trgm`; the API runs the migrations at every start |
| Uploaded files | Supabase Storage | One private bucket, `internsync-files`, created by the API at start; reached only by the API |
| Email | Gmail SMTP | Sign-up, password, and notification emails, sent with an app password |
| Operations | GitHub Actions | `deploy-api.yml`, `keepalive.yml` (every 6 hours), `backup.yml` (nightly, encrypted database and files) |

The design of this deployment is in the [Increment 2 design, Section 10](Increments/Increment_2/02_Design.md).

## 2. What Is in the Repository

| **File** | **Purpose** |
|:---|:---|
| `backend/Dockerfile` | One image for the local demo and the Space. `WITH_AI=1` (the default) installs the model packages and downloads the model while the image is built, so the running API never contacts the Hugging Face Hub (`HF_HUB_OFFLINE=1`). The port comes from `PORT`. |
| `backend/app/core/storage_supabase.py` | The file storage adapter, chosen with `STORAGE_BACKEND=supabase`. Files are still served by `GET /files/{id}` after the permission check; no bucket link reaches a browser. |
| `backend/alembic/versions/0003_row_level_security.py` | Row level security on every table, so the provider's Data API cannot read them. The API connects as the table owner and is not restricted. |
| `backend/scripts/deploy_space.py` | Creates the Space if needed, copies the settings and secrets into it, and uploads the files the image is built from. |
| `frontend/vercel.json` | Build settings, the single-page-app rewrite, and security headers. |
| `.github/workflows/deploy-api.yml` | Runs the script after every change to `backend/` on `main`, or by hand. |
| `.github/workflows/keepalive.yml` | Calls `/api/v1/health?deep=true` every 6 hours: the Space sleeps after 48 hours without visits, and the free database pauses after 7 days without use. |
| `.github/workflows/backup.yml` | Nightly at 02:00 Riyadh time: a `pg_dump` of the database and a copy of the bucket (`backend/scripts/backup_files.py`), each encrypted with a passphrase and kept as an artifact of the private repository: the database for 30 days, the files for 7 days. |
| `.github/workflows/security-scan.yml` | Weekly and on request: the OWASP ZAP baseline of the web app and the API scan in safe mode, against the Docker stack with `docker-compose.check.yml` (NFR-SEC-05). A high-risk alert fails it; the reports are kept for 30 days. |
| `frontend/vercel.json` headers | Content-Security-Policy (scripts, styles, and fonts from the app only, small fonts inlined by the build as `data:`; API calls to `*.hf.space`), `frame-ancestors 'none'`, `X-Frame-Options`, `nosniff`, Referrer and Permissions policies. If the API moves to another host, add it to `connect-src` |

## 3. Owner Steps (Once)

These steps need the owner's own accounts.

1. **Hugging Face.**
   - Create a free account at huggingface.co.
   - Create an access token with write access (Settings → Access Tokens).
   - Choose the Space name, for example `<username>/internsync-api`. The workflow creates the Space.
2. **Gmail.**
   - Choose the Gmail account that sends the emails (a new one is fine).
   - Turn on 2-Step Verification.
   - Create an app password (Google Account → Security → App passwords).
3. **One decision.** A Space must be public for the web app to reach it, so the files the image is built from are visible on Hugging Face: the backend code, but never the secrets. If that is not acceptable before grading, keep the deployment off and run the local demo (Section 7).

## 4. Switching On

These steps can be done with the owner's connected Supabase, Vercel, and GitHub accounts once Section 3 is done.

1. **Supabase project.**
   - Create a free project named `internsync` in the nearest region.
   - Turn off the Data API (Project Settings → Data API). Row level security stays on as a second guard.
   - Copy three values:
     - the **Session pooler** connection string, which works over IPv4 (add `?sslmode=require`);
     - the project URL;
     - the `service_role` key.
2. **GitHub secrets** (repository Settings → Secrets and variables → Actions → Secrets). With the GitHub CLI, `gh secret set NAME` reads the value without showing it.

   | **Secret** | **Value** |
   |:---|:---|
   | `HF_TOKEN` | The Hugging Face token |
   | `DATABASE_URL` | The Session pooler string; `postgresql://…` is accepted as it is |
   | `JWT_SECRET` | A random value of at least 32 characters: `python -c "import secrets; print(secrets.token_urlsafe(48))"`. The API refuses to start in production without one |
   | `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | The project URL and the `service_role` key |
   | `SMTP_USER`, `SMTP_PASSWORD` | The Gmail address and its app password |
   | `DATABASE_URL_BACKUP` | The same Session pooler string |
   | `BACKUP_PASSPHRASE` | A long passphrase kept outside GitHub as well; without it the backups cannot be opened |
   | `VAPID_PRIVATE_KEY` | The private half of the web push key pair: `python -m app.cli vapid-keys` (from `backend/`) prints both halves. Without the pair, notifications go by email only |

3. **GitHub variables** (same page, Variables tab).

   | **Variable** | **Value** |
   |:---|:---|
   | `HF_SPACE` | `<username>/internsync-api` |
   | `API_URL` | `https://<username>-internsync-api.hf.space` (lower case; `_` and `.` become `-`) |
   | `WEB_URL` | The Vercel production address, after step 5 |
   | `VAPID_PUBLIC_KEY` | The public half of the web push key pair |
   | `VAPID_SUBJECT` | `mailto:` and the Gmail address that sends the emails |

4. **Deploy the API.**
   - Run Actions → Deploy API → Run workflow. The first image build on the Space takes about ten minutes.
   - Then check:
     - `API_URL/api/v1/health?deep=true` answers `"database": "ok"`;
     - `API_URL/api/v1/version` names the embedding model.
5. **Web app.**
   - Import the repository in Vercel with the root directory `frontend`.
   - Add the environment variable `VITE_API_URL` with the value of `API_URL`, then deploy.
   - Put the production address in `WEB_URL` and run Deploy API again, so that the API accepts calls from the web app (`CORS_ORIGINS`) and the email links open it (`FRONTEND_BASE_URL`).
6. **First Platform Admin.** From `backend/` on the owner's computer, with the Session pooler string, run:

   ```bash
   DATABASE_URL="<session pooler string>" python -m app.cli create-platform-admin --email "<email>" --name-en "<name>" --name-ar "<name>"
   ```

   The password is asked for on the terminal.
7. **Checks.**
   - Run Keep alive and Backup by hand once each.
   - Restore the backup once into a scratch database and a scratch bucket (Section 6).
   - Sign in, register a test student, and confirm the email arrives.

The settings the script sets on the Space, which are not secret, are `ENV=production`, `PORT=7860`, `STORAGE_BACKEND=supabase`, `SCHEDULER_ENABLED=true`, the Gmail SMTP host and port with TLS, and `FORWARDED_ALLOW_IPS=*`, so that the registration limit sees the visitor's address behind the Space's proxy.

## 5. Updates

- **API:** a merge to `main` that changes `backend/` deploys it. Migrations run when the new image starts.
- **Web app:** Vercel builds every push to `main` and shows a preview for each pull request.
- **Secrets:** change the GitHub secret and run Deploy API.

## 6. Restore

1. Download the artifacts `database-backup` and `files-backup` of a Backup run (Actions → Backup → the run → Artifacts).
2. Decrypt them with the passphrase:

   ```bash
   gpg --decrypt --output internsync.dump internsync-<stamp>.dump.gpg
   gpg --decrypt --output files.tar files-<stamp>.tar.gpg
   ```

3. Restore the database into an empty database with `pg_restore` 17 or later:

   ```bash
   pg_restore --no-owner --dbname="<target connection string>" internsync.dump
   ```

4. Put the files back into the bucket, from `backend/`:

   ```bash
   SUPABASE_URL="<url>" SUPABASE_SERVICE_KEY="<key>" python scripts/backup_files.py --restore files.tar
   ```

The database procedure was rehearsed on October 26, 2026 with the local demo database: dump, encryption, decryption, and restore into a scratch database, with the same row counts in every table checked, embeddings included. The copy and restore of files is covered by an automated test against a stand-in of the Storage API, and is repeated against the real bucket in the switch-on checks (Section 4, step 7). Restoring into the local PostgreSQL 16 gives one harmless error for a setting that only version 17 knows (`transaction_timeout`); the hosted database runs version 17.

## 7. Limits and Fallback

- **Free tiers.**
  - **Space:** sleeps after 48 hours without visits; its disk is not kept, which is why files live in Supabase Storage.
  - **Supabase Free:** 500 MB of database and 1 GB of files; pauses after 7 days of low activity.
  - **Vercel Hobby:** non-commercial use only.
  - **GitHub Actions:** 2,000 minutes a month for a private repository. CI, keep-alive (about 120 runs a month), and backups stay well under it. The browser tests run on pull requests only (about 15 minutes each) and the ZAP scan once a week (about 15 minutes), so 20 pull requests a month and the weekly scan add about 360 minutes. Artifact storage is limited to 500 MB: 30 database copies and 7 file copies fit while the files stay under about 60 MB. If they grow beyond that, shorten the file retention in `backup.yml`.
  - **Gmail:** about 500 emails a day.
- **Fallback:** if a provider is unavailable, run the same containers locally with `docker compose up` (README). The local demo with demo accounts is also how the milestone demos run: demo accounts are refused when `ENV=production`.

## Revision History

| **Version** | **Date** | **Change** |
|:--:|:--:|:---|
| 1.0 | Oct 26, 2026 | First version (Increment 2, RQ-8) |
| 1.1 | Oct 27, 2026 | Web push keys (Increment 3, FR-PWA-02): one secret and two variables, copied to the Space by the deploy script |
| 1.2 | Oct 28, 2026 | Increment 4: the weekly ZAP scan workflow, the Content-Security-Policy in `vercel.json`, and the Actions minutes of the browser tests and the scan |
