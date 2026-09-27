#!/usr/bin/env bash
# Runs on the EC2 instance to deploy the latest `development` branch.
# Invoked two ways:
#   - manually: bash deploy/aws/deploy.sh
#   - by GitHub Actions over SSH, via a forced command in authorized_keys
#     scoped to this exact path - see DEPLOY_AWS.md's CI/CD section.
set -euo pipefail

cd /home/ubuntu/svvd-thorur

# Pull, then run the freshly pulled copy of this script: bash keeps executing
# the copy it already opened, so otherwise a change to the steps below would
# only take effect on the deploy after next.
if [ "${DEPLOY_SCRIPT_PULLED:-}" != "1" ]; then
  git pull origin development
  DEPLOY_SCRIPT_PULLED=1 exec bash deploy/aws/deploy.sh
fi

compose() {
  docker compose -f docker-compose.yml -f docker-compose.prod.yml "$@"
}

compose build
compose up -d
# Always restart the frontend, even if only the backend image changed: it
# holds long-lived connections to the backend container's IP, which changes
# whenever that container is recreated - otherwise it keeps proxying to a
# now-dead IP until something else bounces it. Cheap relative to a rebuild.
compose restart frontend

# `up -d` returns as soon as the containers start, before the backend's
# entrypoint has applied migrations - a migration that crash-loops the
# backend would otherwise still report a successful deploy. /health only
# answers once migrations and app startup have both succeeded.
echo "Waiting for the backend to become healthy..."
for _ in $(seq 1 60); do
  if curl -fsS --max-time 3 http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "Backend healthy. Deployed $(git rev-parse --short HEAD) at $(date -u +%FT%TZ)"
    exit 0
  fi
  sleep 2
done

echo "DEPLOY FAILED: backend not healthy after 2 minutes. Recent backend logs:" >&2
compose ps >&2 || true
compose logs backend --tail=80 >&2 || true
exit 1
