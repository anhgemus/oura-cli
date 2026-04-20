#!/usr/bin/env bash
# Append yesterday's summary to a dated JSONL archive. Put in a cron.
set -euo pipefail

ARCHIVE_DIR="${HOME}/.oura-archive"
mkdir -p "$ARCHIVE_DIR"
DATE=$(date -d "yesterday" +%F)

oura summary --date "$DATE" --json >> "${ARCHIVE_DIR}/summaries.jsonl"
oura export --days 2 --out "${ARCHIVE_DIR}/raw/${DATE}" >/dev/null
echo "✓ archived $DATE"
