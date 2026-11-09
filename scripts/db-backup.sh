#!/bin/bash
# Backup script for GrandLedger PostgreSQL database
# Usage: ./scripts/db-backup.sh [--encrypt-key <key>] [--retention-days <N>]
#
# Environment:
#   DATABASE_URL          PostgreSQL connection string
#   BACKUP_DIR            Backup directory (default: ./backups)
#   ENCRYPT_KEY           AES-256 encryption key (optional but recommended)
#   RETENTION_DAYS        Days to keep daily backups (default: 7)
#   RETENTION_WEEKS       Weeks to keep weekly backups (default: 4)
#   RETENTION_MONTHS      Months to keep monthly backups (default: 12)

set -euo pipefail

ENCRYPT_KEY=""
RETENTION_DAYS="${RETENTION_DAYS:-7}"
RETENTION_WEEKS="${RETENTION_WEEKS:-4}"
RETENTION_MONTHS="${RETENTION_MONTHS:-12}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --encrypt-key)
            ENCRYPT_KEY="$2"
            shift 2
            ;;
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_HOST="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/grandledger}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DATE=$(date +%Y-%m-%d)
WEEK=$(date +%G-W%V)
MONTH=$(date +%Y-%m)

mkdir -p "$BACKUP_DIR/daily" "$BACKUP_DIR/weekly" "$BACKUP_DIR/monthly"

BACKUP_FILE="$BACKUP_DIR/daily/grandledger_$TIMESTAMP.sql"

echo "[$(date -Iseconds)] Starting backup to $BACKUP_FILE..."
pg_dump "$DB_HOST" > "$BACKUP_FILE"

if [ -n "$ENCRYPT_KEY" ]; then
    echo "[$(date -Iseconds)] Encrypting backup..."
    openssl enc -aes-256-cbc -salt -pbkdf2 -in "$BACKUP_FILE" -out "$BACKUP_FILE.enc" -k "$ENCRYPT_KEY"
    rm "$BACKUP_FILE"
    BACKUP_FILE="$BACKUP_FILE.enc"
    echo "[$(date -Iseconds)] Encrypted backup: $BACKUP_FILE"
else
    echo "[$(date -Iseconds)] Backup complete (unencrypted): $BACKUP_FILE"
fi

# Copy to weekly rotation (first day of week = Monday)
if [[ $(date +%u) == "1" ]]; then
    cp "$BACKUP_FILE" "$BACKUP_DIR/weekly/grandledger_$WEEK$( [[ -n "$ENCRYPT_KEY" ]] && echo ".enc" || echo ".sql")"
    echo "[$(date -Iseconds)] Weekly backup created: $WEEK"
fi

# Copy to monthly rotation (1st of month)
if [[ $(date +%d) == "01" ]]; then
    cp "$BACKUP_FILE" "$BACKUP_DIR/monthly/grandledger_$MONTH$( [[ -n "$ENCRYPT_KEY" ]] && echo ".enc" || echo ".sql")"
    echo "[$(date -Iseconds)] Monthly backup created: $MONTH"
fi

# Cleanup old backups
echo "[$(date -Iseconds)] Cleaning old backups (daily > $RETENTION_DAYS days, weekly > $RETENTION_WEEKS weeks, monthly > $RETENTION_MONTHS months)..."
find "$BACKUP_DIR/daily" -name "grandledger_*" -mtime +$((RETENTION_DAYS)) -delete 2>/dev/null || true
find "$BACKUP_DIR/weekly" -name "grandledger_*" -mtime +$((RETENTION_WEEKS * 7)) -delete 2>/dev/null || true
find "$BACKUP_DIR/monthly" -name "grandledger_*" -mtime +$((RETENTION_MONTHS * 30)) -delete 2>/dev/null || true

echo "[$(date -Iseconds)] Backup rotation complete."
echo "Current backup size:"
ls -lh "$BACKUP_FILE"
