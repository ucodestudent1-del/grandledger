#!/bin/sh
set -e

echo "Starting GrandLedger API..."
echo "DATABASE_URL: ${DATABASE_URL:-not set}"
echo "REDIS_URL: ${REDIS_URL:-not set}"

# Force correct DATABASE_URL for Docker networking if localhost is detected
if echo "${DATABASE_URL:-}" | grep -q "localhost\|127.0.0.1\|::1"; then
    echo "WARNING: DATABASE_URL contains localhost - replacing with Docker service name"
    export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's/localhost/postgres/g; s/127.0.0.1/postgres/g; s/::1/postgres/g')
    echo "DATABASE_URL (corrected): $DATABASE_URL"
fi

# Normalize postgresql:// to postgresql+psycopg:// for psycopg v3 driver
if echo "${DATABASE_URL:-}" | grep -q "^postgresql://"; then
    export DATABASE_URL=$(echo "$DATABASE_URL" | sed 's|^postgresql://|postgresql+psycopg://|')
    echo "DATABASE_URL (driver normalized): $DATABASE_URL"
fi

# Force correct REDIS_URL for Docker networking if localhost is detected
if echo "${REDIS_URL:-}" | grep -q "localhost\|127.0.0.1\|::1"; then
    echo "WARNING: REDIS_URL contains localhost - replacing with Docker service name"
    export REDIS_URL=$(echo "$REDIS_URL" | sed 's/localhost/redis/g; s/127.0.0.1/redis/g; s/::1/redis/g')
    echo "REDIS_URL (corrected): $REDIS_URL"
fi

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
