#!/bin/sh
set -e

echo "Starting GrandLedger API..."

# Run database migrations (don't fail if migration already applied or tables exist)
echo "Running migrations..."
if alembic upgrade head 2>&1; then
    echo "Migrations completed successfully"
else
    echo "WARNING: Migration encountered an issue, attempting to continue..."
    # Check if DB is reachable
    if python -c "from sqlmodel import Session
from src.database import engine
from sqlmodel import text
session = Session(engine)
session.exec(text('SELECT 1'))
session.close()
print('DB OK')" 2>/dev/null; then
        echo "Database is reachable, proceeding with startup"
    else
        echo "ERROR: Database not reachable, exiting"
        exit 1
    fi
fi

echo "Starting uvicorn..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
