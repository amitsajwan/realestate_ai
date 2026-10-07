#!/usr/bin/env bash
# Nightly MongoDB backup for the Avasetu pilot. Runs ON THE VM (normally from cron, see install_backup_cron.ps1).
#
#   bash backup.sh            # dump -> ~/backups/YYYY-MM-DD.archive.gz, keep the newest 14
#   bash backup.sh --dry-run  # print what it would do, touch nothing
#
# The dump is taken inside the mongo container; the database password is read there from the container's own
# environment, so no secret is on this script's command line, in a file, or in the log.
# Exit code: 0 ok, non-zero on any failure (health_check.sh also flags a missing/stale backup).
#
# Overridable through the environment: APP_DIR (default ~/app/deploy/gcp), BACKUP_DIR (~/backups), KEEP (14),
# DATABASE_NAME (default: value in .env, else propertyai), BACKUP_LOG (~/backup.log).
set -uo pipefail
export PATH="$PATH:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1
APP_DIR="${APP_DIR:-$HOME/app/deploy/gcp}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
KEEP="${KEEP:-14}"
LOG="${BACKUP_LOG:-$HOME/backup.log}"

log() { printf '%s backup: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG" >&2; }
fail() { log "FAILED: $*"; [ -n "${TMP:-}" ] && rm -f "$TMP"; exit 1; }

cd "$APP_DIR" 2>/dev/null || fail "cannot cd to $APP_DIR"
[ -f .env ] || fail ".env not found in $APP_DIR"

# read one KEY from .env without sourcing it (values may contain shell-special characters)
envval() { grep -E "^$1=" .env | tail -n1 | cut -d= -f2- | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//" | tr -d '\r'; }

DB="${DATABASE_NAME:-$(envval DATABASE_NAME)}"; DB="${DB:-propertyai}"
case "$DB" in (*[!A-Za-z0-9_-]*|"") fail "unsafe database name";; esac

if [ "$(id -u)" -eq 0 ] || docker info >/dev/null 2>&1; then DC="docker compose"; else DC="sudo -n docker compose"; fi

OUT="$BACKUP_DIR/$(date +%F).archive.gz"
TMP="$OUT.partial"

if [ "$DRY" -eq 1 ]; then
  echo "[dry-run] would run in $APP_DIR: $DC exec -T mongo mongodump --db $DB --archive --gzip (password from container env)"
  echo "[dry-run] would write $OUT (via $TMP, then rename), keep the newest $KEEP in $BACKUP_DIR, log to $LOG"
  exit 0
fi

mkdir -p "$BACKUP_DIR" && chmod 700 "$BACKUP_DIR" || fail "cannot create $BACKUP_DIR"

$DC ps --status running --services 2>/dev/null | grep -qx mongo || fail "mongo container is not running"

# mongodump writes the archive to stdout; the shell inside the container expands the password from ITS env.
if ! $DC exec -T mongo sh -c 'mongodump --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --db "$1" --archive --gzip --quiet' sh "$DB" > "$TMP" 2>>"$LOG"; then
  fail "mongodump returned an error (see $LOG)"
fi

# sanity: a non-trivial, valid gzip stream
SIZE="$(wc -c < "$TMP" | tr -d ' ')"
[ "${SIZE:-0}" -gt 100 ] || fail "dump is suspiciously small ($SIZE bytes)"
gzip -t "$TMP" 2>/dev/null || fail "dump is not a valid gzip stream"

chmod 600 "$TMP"
mv -f "$TMP" "$OUT" || fail "could not move the dump into place"

# retention: keep the newest $KEEP dated archives (names sort chronologically)
ls -1 "$BACKUP_DIR"/*.archive.gz 2>/dev/null | sort | head -n "-$KEEP" | while read -r old; do rm -f -- "$old" && log "pruned $old"; done
rm -f "$BACKUP_DIR"/*.archive.gz.partial 2>/dev/null

COUNT="$(ls -1 "$BACKUP_DIR"/*.archive.gz 2>/dev/null | wc -l | tr -d ' ')"
log "OK $OUT ($SIZE bytes, database $DB, $COUNT kept)"
exit 0
