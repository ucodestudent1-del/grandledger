#!/bin/bash
# Backup script for GrandLedger PostgreSQL database
# Usage: ./scripts/db-backup.sh [--encrypt-key <key>]

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_HOST="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/grandledger}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

BACKUP_FILE="$BACKUP_DIR/grandledger_$TIMESTAMP.sql"

echo "Starting backup to $BACKUP_FILE..."
pg_dump "$DB_HOST" > "$BACKUP_FILE"

if [ -n "${ENCRYPT_KEY:-}" ]; then
    echo "Encrypting backup..."
    openssl enc -aes-256-cbc -salt -in "$BACKUP_FILE" -out "$BACKUP_FILE.enc" -k "$ENCRYPT_KEY"
    rm "$BACKUP_FILE"
    BACKUP_FILE="$BACKUP_FILE.enc"
    echo "Encrypted backup: $BACKUP_FILE"
else
    echo "Backup complete: $BACKUP_FILE"
fi

# Cleanup old backups (keep last 7 days)
find "$BACKUP_DIR" -name "grandledger_*.sql*" -mtime +7 -delete 2>/dev/null || true
find "$BACKUP_DIR" -name "grandledger_*.sql.enc" -mtime +7 -delete 2>/dev/null || true

echo "Old backups cleaned. Current backup size:"
ls -lh "$BACKUP_FILE"
