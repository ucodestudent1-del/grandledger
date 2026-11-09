#!/bin/bash
# Restore script for GrandLedger PostgreSQL database
# Usage: ./scripts/db-restore.sh <backup_file> [--decrypt-key <key>]
#
# Environment:
#   DATABASE_URL          PostgreSQL connection string
#   DB_HOST               PostgreSQL host (alternative to DATABASE_URL)

set -euo pipefail

DECRYPT_KEY=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --decrypt-key)
            DECRYPT_KEY="$2"
            shift 2
            ;;
        *)
            if [[ -z "${BACKUP_FILE:-}" ]]; then
                BACKUP_FILE="$1"
            else
                echo "Unknown option: $1" >&2
                exit 1
            fi
            shift
            ;;
    esac
done

if [[ -z "${BACKUP_FILE:-}" ]]; then
    echo "Usage: $0 <backup_file> [--decrypt-key <key>]" >&2
    exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "Backup file not found: $BACKUP_FILE" >&2
    exit 1
fi

DB_HOST="${DATABASE_URL:-postgresql://postgres:postgres@localhost:5432/grandledger}"
RESTORE_FILE="$BACKUP_FILE"

# Decrypt if needed
if [[ "$BACKUP_FILE" == *.enc ]]; then
    if [[ -z "$DECRYPT_KEY" ]]; then
        echo "Encrypted backup requires --decrypt-key" >&2
        exit 1
    fi
    DECRYPTED_FILE="${BACKUP_FILE%.enc}"
    echo "Decrypting backup..."
    openssl enc -d -aes-256-cbc -pbkdf2 -in "$BACKUP_FILE" -out "$DECRYPTED_FILE" -k "$DECRYPT_KEY"
    RESTORE_FILE="$DECRYPTED_FILE"
fi

echo "Restoring database from $RESTORE_FILE..."
echo "WARNING: This will DROP and RECREATE all data in the target database."
read -p "Type 'RESTORE' to confirm: " confirm
if [[ "$confirm" != "RESTORE" ]]; then
    echo "Aborted."
    rm -f "$DECRYPTED_FILE"
    exit 1
fi

# Drop and recreate database
dbname=$(echo "$DB_HOST" | sed 's/.*\///')
echo "Dropping and recreating database: $dbname"
dropdb --if-exists "$dbname" || true
createdb "$dbname"

# Restore
psql "$DB_HOST" < "$RESTORE_FILE"

# Cleanup decrypted temp file
if [[ -n "${DECRYPTED_FILE:-}" && -f "$DECRYPTED_FILE" ]]; then
    rm -f "$DECRYPTED_FILE"
fi

echo "Restore complete."
