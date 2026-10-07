#!/usr/bin/env bash
# Proves the newest backup can actually be restored. Runs ON THE VM. Safe: it restores into a THROWAWAY database
# (restore_test_<timestamp>), compares collection counts with the live database, then drops the throwaway one.
# The live database is only read.
#
#   bash restore_test.sh               # test the newest ~/backups/*.archive.gz
#   bash restore_test.sh FILE          # test a specific archive
#   bash restore_test.sh --dry-run     # print the plan only
#
# Exit code: 0 = restored and no collection with data is missing; non-zero otherwise.
# Counts may legitimately differ a little from live (the backup is hours old): differences are shown, only a
# MISSING collection or an empty restore fails the test.
set -uo pipefail
export PATH="$PATH:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

DRY=0; FILE=""
for a in "$@"; do case "$a" in --dry-run) DRY=1;; *) FILE="$a";; esac; done
APP_DIR="${APP_DIR:-$HOME/app/deploy/gcp}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
LOG="${BACKUP_LOG:-$HOME/backup.log}"
log() { printf '%s restore_test: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG" >&2; }

cd "$APP_DIR" 2>/dev/null || { log "FAILED: cannot cd to $APP_DIR"; exit 1; }
[ -f .env ] || { log "FAILED: .env not found"; exit 1; }
envval() { grep -E "^$1=" .env | tail -n1 | cut -d= -f2- | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//" | tr -d '\r'; }
DB="${DATABASE_NAME:-$(envval DATABASE_NAME)}"; DB="${DB:-propertyai}"
case "$DB" in (*[!A-Za-z0-9_-]*|"") log "FAILED: unsafe database name"; exit 1;; esac
if [ "$(id -u)" -eq 0 ] || docker info >/dev/null 2>&1; then DC="docker compose"; else DC="sudo -n docker compose"; fi

[ -n "$FILE" ] || FILE="$(ls -1 "$BACKUP_DIR"/*.archive.gz 2>/dev/null | sort | tail -n1)"
TMPDB="restore_test_$(date +%s)"

if [ "$DRY" -eq 1 ]; then
  echo "[dry-run] archive: ${FILE:-<none found in $BACKUP_DIR>}"
  echo "[dry-run] would restore $DB.* into throwaway database $TMPDB, compare collection counts with live $DB, then drop $TMPDB"
  exit 0
fi
[ -n "$FILE" ] && [ -f "$FILE" ] || { log "FAILED: no backup archive found"; exit 1; }
gzip -t "$FILE" 2>/dev/null || { log "FAILED: $FILE is not a valid gzip file"; exit 1; }

# mongosh snippet run inside the container: prints "name<TAB>count" per non-system collection of database $DBN
COUNTS_JS='const d=db.getSiblingDB(process.env.DBN);d.getCollectionNames().filter(n=>!n.startsWith("system.")).sort().forEach(n=>print(n+"\t"+d.getCollection(n).countDocuments({})))'
counts() { # $1 = database name
  $DC exec -T mongo sh -c 'DBN="$2" mongosh --quiet -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --eval "$1"' sh "$COUNTS_JS" "$1" 2>/dev/null
}
drop_tmp() {
  $DC exec -T mongo sh -c 'DBN="$1" mongosh --quiet -u "$MONGO_INITDB_ROOT_USERNAME" -p "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --eval "db.getSiblingDB(process.env.DBN).dropDatabase().ok"' sh "$TMPDB" >/dev/null 2>&1
}
trap 'drop_tmp' EXIT

log "restoring $FILE into $TMPDB"
if ! $DC exec -T mongo sh -c 'mongorestore --username "$MONGO_INITDB_ROOT_USERNAME" --password "$MONGO_INITDB_ROOT_PASSWORD" --authenticationDatabase admin --archive --gzip --quiet --nsInclude "$1.*" --nsFrom "$1.*" --nsTo "$2.*"' sh "$DB" "$TMPDB" < "$FILE" 2>>"$LOG"; then
  log "FAILED: mongorestore returned an error (see $LOG)"; exit 1
fi

RESTORED="$(counts "$TMPDB")"
LIVE="$(counts "$DB")"
[ -n "$RESTORED" ] || { log "FAILED: the restored database has no collections (archive empty or wrong database name $DB)"; exit 1; }

BAD=0
while IFS=$'\t' read -r name rcount; do
  [ -n "$name" ] || continue
  lcount="$(printf '%s\n' "$LIVE" | awk -F'\t' -v n="$name" '$1==n{print $2}')"
  printf '  %-28s restored=%-8s live=%s\n' "$name" "$rcount" "${lcount:-absent}"
done <<< "$RESTORED"
# collections with data live but absent from the backup
while IFS=$'\t' read -r name lcount; do
  [ -n "$name" ] || continue
  if ! printf '%s\n' "$RESTORED" | awk -F'\t' -v n="$name" '$1==n{f=1} END{exit !f}'; then
    if [ "${lcount:-0}" -gt 0 ]; then echo "  MISSING from backup: $name (live has $lcount)"; BAD=1; fi
  fi
done <<< "$LIVE"

drop_tmp; trap - EXIT
if [ "$BAD" -ne 0 ]; then log "FAILED: backup $FILE is missing collections that have data"; exit 1; fi
log "OK $FILE restores cleanly ($(printf '%s\n' "$RESTORED" | wc -l | tr -d ' ') collections); throwaway database dropped"
exit 0
