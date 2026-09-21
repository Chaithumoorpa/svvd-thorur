#!/usr/bin/env bash
# Runs on the EC2 instance to deploy the latest `development` branch.
# Invoked two ways:
#   - manually: bash deploy/aws/deploy.sh
#   - by GitHub Actions over SSH, via a forced command in authorized_keys
#     scoped to this exact path - see DEPLOY_AWS.md's CI/CD section.
set -euo pipefail

cd /home/ubuntu/svvd-thorur

git pull origin development
docker compose -f docker-compose.yml -f docker-compose.prod.yml build
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
# Always restart the frontend, even if only the backend image changed: it
# holds long-lived connections to the backend container's IP, which changes
# whenever that container is recreated - otherwise it keeps proxying to a
# now-dead IP until something else bounces it. Cheap relative to a rebuild.
docker compose -f docker-compose.yml -f docker-compose.prod.yml restart frontend

echo "Deployed $(git rev-parse --short HEAD) at $(date -u +%FT%TZ)"
