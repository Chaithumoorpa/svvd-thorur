#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Waiting for postgres..."

# If we have a way to check PG readiness, we would do it here. 
# For now, we rely on docker-compose healthchecks, but this script
# ensures migrations run before the app starts.

echo "Running database migrations..."
alembic upgrade head

echo "Starting application..."
exec "$@"
