#!/usr/bin/env bash
# Nightly Postgres backup: dump -> gzip -> upload to S3, with a short local
# retention window as a fast-restore cache. Meant to run from cron on the
# EC2 host - see the "Backups" section of DEPLOY_AWS.md for the crontab
# line and the one-time IAM/S3 setup this depends on.
#
# Uses the backend container's own boto3 + instance-role credentials for the
# S3 upload (the same ones StorageService already uses for gallery/tickets/
# receipts) rather than installing a separate AWS CLI on the host.
set -euo pipefail

cd /home/ubuntu/svvd-thorur
COMPOSE="docker compose -f docker-compose.yml -f docker-compose.prod.yml"

DATE=$(date +%F)
DUMP_DIR=/home/ubuntu/backups
mkdir -p "$DUMP_DIR"
DUMP_FILE="$DUMP_DIR/$DATE.sql.gz"

$COMPOSE exec -T postgres pg_dump -U "${POSTGRES_USER:-templeuser}" "${POSTGRES_DB:-templedb}" \
  | gzip > "$DUMP_FILE"

$COMPOSE cp "$DUMP_FILE" backend:/tmp/backup.sql.gz
$COMPOSE exec -T backend python -c "
import boto3, os
s3 = boto3.client('s3', region_name=os.environ['AWS_REGION'],
                   endpoint_url=f\"https://s3.{os.environ['AWS_REGION']}.amazonaws.com\")
s3.upload_file('/tmp/backup.sql.gz', os.environ['S3_BUCKET_NAME'], 'backups/$DATE.sql.gz')
print('Uploaded backups/$DATE.sql.gz')
"
$COMPOSE exec -T backend rm -f /tmp/backup.sql.gz

# Keep the last 14 days on-instance for a quick restore; S3's own lifecycle
# rule (see DEPLOY_AWS.md) handles longer-term, off-instance retention.
find "$DUMP_DIR" -name '*.sql.gz' -mtime +14 -delete

echo "Backup complete: $DATE"
