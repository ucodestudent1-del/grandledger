#!/bin/bash
# Dev SMTP server for local email testing
# Runs MailHog-style catch-all SMTP on port 1025, web UI on port 8025

set -e

IMAGE="${SMTP_DEV_IMAGE:-mailhog/mailhog:latest}"
PORT="${SMTP_DEV_PORT:-1025}"
UI_PORT="${SMTP_DEV_UI_PORT:-8025}"

echo "Starting dev SMTP server (MailHog)..."
echo "SMTP: localhost:${PORT}"
echo "Web UI: http://localhost:${UI_PORT}"

docker run --rm \
  --name grandledger-smtp-dev \
  -p "${PORT}:1025" \
  -p "${UI_PORT}:8025" \
  "${IMAGE}"
