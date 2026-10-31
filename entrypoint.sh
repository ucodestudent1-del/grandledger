#!/bin/sh
set -e

echo "Starting GrandLedger API..."
echo "DATABASE_URL: ${DATABASE_URL:-not set}"
echo "REDIS_URL: ${REDIS_URL:-not set}"

# Run database migrations (retry on connection failure)
echo "Running migrations..."
MAX_ATTEMPTS=30
ATTEMPT=0
while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    if alembic upgrade head 2>&1; then
        echo "Migrations completed successfully"
        break
    fi
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo "ERROR: Migration failed after $MAX_ATTEMPTS attempts"
        exit 1
    fi
    echo "Waiting for database (attempt $ATTEMPT/$MAX_ATTEMPTS)..."
    sleep 2
done

echo "Starting uvicorn..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
