#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "========================================="
echo "Temple Management Backend - Startup"
echo "========================================="
echo "Environment: ${ENV:-development}"
echo "========================================="

echo "Waiting for postgres..."

# If we have a way to check PG readiness, we would do it here. 
# For now, we rely on docker-compose healthchecks, but this script
# ensures migrations run before the app starts.

# Determine which Alembic config to use based on environment
ALEMBIC_CONFIG="${ALEMBIC_CONFIG:-alembic.ini}"

if [ "$ENV" = "production" ]; then
    ALEMBIC_CONFIG="alembic.prod.ini"
    echo "Using production Alembic configuration"
elif [ "$ENV" = "development" ]; then
    ALEMBIC_CONFIG="alembic.dev.ini"
    echo "Using development Alembic configuration"
else
    echo "Using default Alembic configuration"
fi

echo "Checking migration status..."
alembic -c "$ALEMBIC_CONFIG" heads

echo "Running database migrations..."
alembic -c "$ALEMBIC_CONFIG" upgrade head

echo "Migration complete!"
echo "========================================="
echo "Starting application..."
echo "========================================="

exec "$@"
