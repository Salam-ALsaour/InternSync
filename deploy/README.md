# InternSync – Self-Hosted Deployment (AWS Lightsail)

One server runs everything with Docker Compose, at `https://internsync.tech`:

| **Container** | **What it does** |
|:---|:---|
| `web` | Caddy: serves the built web app, forwards `/api/*` to the API, gets and renews the HTTPS certificates, redirects `www` to the bare domain |
| `api` | The image from `backend/Dockerfile` (with the embedding model). Runs the migrations at every start |
| `db` | PostgreSQL 16 with `pgvector` (no port open to the internet) |

Uploaded files are kept in the `file-data` volume and the database in `db-data`.

## First Setup

1. Run the root-only steps: `sudo bash ~/sudo_commands/01_install_docker.sh`. Then log out and back in.
2. In the Lightsail console:
   - **Networking:** attach a static IP to the instance.
   - **Firewall:** allow HTTPS (TCP 443). HTTP (TCP 80) and SSH are open by default.
3. At the domain registrar, add the A records `internsync.tech` and `www.internsync.tech`, both pointing at the static IP.
4. Create `deploy/.env` from `deploy/.env.example`, with new secrets.
5. Start the stack:

   ```bash
   docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env up -d --build
   ```

6. Create the first Platform Admin. The password is asked for on the terminal:

   ```bash
   docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env exec api \
     python -m app.cli create-platform-admin --email "<email>" --name-en "<name>" --name-ar "<name>"
   ```

7. Add the nightly backup to the ubuntu user's crontab (`crontab -e`):

   ```
   30 23 * * * /home/ubuntu/InternSync/deploy/backup.sh >> /home/ubuntu/InternSync/deploy/backups/backup.log 2>&1
   ```

## Updates

```bash
git pull
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env up -d --build
```

## Restore

```bash
dc="docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env"
$dc exec -T db pg_restore -U internsync -d internsync --clean --if-exists < deploy/backups/db-<stamp>.dump
$dc exec -T api tar -C /data/storage -xf - < deploy/backups/files-<stamp>.tar
```

The backups stay on this server. To protect against losing the whole instance, also turn on Lightsail's automatic snapshots.
