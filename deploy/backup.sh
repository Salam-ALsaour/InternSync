#!/usr/bin/env bash
# Nightly backup of the database and uploaded files into deploy/backups/, keeping 14 days.
# Cron (ubuntu user): 30 23 * * * /home/ubuntu/InternSync/deploy/backup.sh >> /home/ubuntu/InternSync/deploy/backups/backup.log 2>&1
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p backups
stamp=$(date +%Y%m%d-%H%M%S)
dc="docker compose -f docker-compose.prod.yml --env-file .env"
$dc exec -T db pg_dump -U internsync -Fc internsync > "backups/db-$stamp.dump"
$dc exec -T api tar -C /data/storage -cf - . > "backups/files-$stamp.tar"
find backups -name 'db-*.dump' -mtime +14 -delete
find backups -name 'files-*.tar' -mtime +14 -delete
echo "$(date -Is) backup ok: db-$stamp.dump files-$stamp.tar"
