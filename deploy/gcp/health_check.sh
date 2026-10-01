#!/usr/bin/env bash
# Health check for the Avasetu pilot. Runs ON THE VM, every 15 minutes from cron (see install_health_cron.ps1).
#
#   bash health_check.sh               # run the checks; write ~/health.log only when something is wrong (or recovers)
#   bash health_check.sh --verbose     # also print every check result to the terminal
#   bash health_check.sh --dry-run     # run the checks, print alerts instead of sending them, change no state
#   bash health_check.sh --test-alert  # send one test alert through the configured hook and exit
#
# Checks: site (https://SITE_HOST/), API (/api/v1/health says "healthy"), disk space, the four containers, the
# Facebook/Meta Page token (asked of Meta from INSIDE the backend container; the token never leaves it and is never
# printed) and that the newest database backup is recent.
#
# Alerts are an optional hook. Put either (or both) in deploy/gcp/.env on the VM:
#   ALERT_WEBHOOK_URL=https://...   JSON POST {"text": "...", "content": "..."} (Slack, Discord, Google Chat-compatible relays, ntfy-style bridges)
#   ALERT_EMAIL=you@example.com     sent with mail/mailx/sendmail if one is installed on the VM (none by default)
# Neither set = failures are only written to ~/health.log. To avoid a message every 15 minutes, an alert is sent when the
# set of failing checks changes, repeated every 6 hours while it lasts, plus one "recovered" message.
#
# Overridable: APP_DIR, BACKUP_DIR, HEALTH_LOG (~/health.log), STATE_FILE (~/.health_state), DISK_FAIL_PCT (90),
# BACKUP_MAX_AGE_H (36), REALERT_S (21600).
set -uo pipefail
export PATH="$PATH:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

VERBOSE=0; DRY=0; TEST=0
for a in "$@"; do case "$a" in --verbose) VERBOSE=1;; --dry-run) DRY=1; VERBOSE=1;; --test-alert) TEST=1;; esac; done
APP_DIR="${APP_DIR:-$HOME/app/deploy/gcp}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"
LOG="${HEALTH_LOG:-$HOME/health.log}"
STATE="${STATE_FILE:-$HOME/.health_state}"
DISK_FAIL_PCT="${DISK_FAIL_PCT:-90}"
BACKUP_MAX_AGE_H="${BACKUP_MAX_AGE_H:-36}"
REALERT_S="${REALERT_S:-21600}"

cd "$APP_DIR" 2>/dev/null || { echo "$(date -u +%FT%TZ) FAIL config: cannot cd to $APP_DIR" >> "$LOG"; exit 1; }
[ -f .env ] || { echo "$(date -u +%FT%TZ) FAIL config: .env missing in $APP_DIR" >> "$LOG"; exit 1; }

# read one KEY from .env without sourcing it
envval() { grep -E "^$1=" .env | tail -n1 | cut -d= -f2- | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//" | tr -d '\r'; }
if [ "$(id -u)" -eq 0 ] || docker info >/dev/null 2>&1; then DC="docker compose"; else DC="sudo -n docker compose"; fi

FAILS=()     # "name: detail" lines
say()  { [ "$VERBOSE" -eq 1 ] && echo "$*"; return 0; }
ok()   { say "ok    $1${2:+: $2}"; }
bad()  { FAILS+=("$1: $2"); say "FAIL  $1: $2"; }

# ---------------------------------------------------------------- notification hook
notify() { # $1 = message
  local msg="$1" sent=0
  local hook mail; hook="$(envval ALERT_WEBHOOK_URL)"; mail="$(envval ALERT_EMAIL)"
  if [ "$DRY" -eq 1 ]; then
    echo "[dry-run] alert would be sent (webhook configured: $([ -n "$hook" ] && echo yes || echo no), email configured: $([ -n "$mail" ] && echo yes || echo no)): $msg"; return 0
  fi
  if [ -n "$hook" ]; then
    local json; json="$(python3 -c 'import json,sys; m=sys.argv[1]; print(json.dumps({"text":m,"content":m}))' "$msg" 2>/dev/null)"
    [ -n "$json" ] || json="{\"text\":\"health alert\",\"content\":\"health alert\"}"
    if curl -fsS -m 15 -o /dev/null -H 'Content-Type: application/json' -d "$json" "$hook" 2>/dev/null; then sent=1
    else echo "$(date -u +%FT%TZ) NOTIFY webhook delivery failed" >> "$LOG"; fi
  fi
  if [ -n "$mail" ]; then
    if command -v mail >/dev/null 2>&1;    then printf '%s\n' "$msg" | mail -s "Avasetu: health alert" "$mail" && sent=1
    elif command -v mailx >/dev/null 2>&1;  then printf '%s\n' "$msg" | mailx -s "Avasetu: health alert" "$mail" && sent=1
    elif command -v sendmail >/dev/null 2>&1; then printf 'Subject: Avasetu: health alert\n\n%s\n' "$msg" | sendmail "$mail" && sent=1
    else echo "$(date -u +%FT%TZ) NOTIFY ALERT_EMAIL is set but no mail/mailx/sendmail on this VM (use ALERT_WEBHOOK_URL instead)" >> "$LOG"; fi
  fi
  return 0
}

if [ "$TEST" -eq 1 ]; then
  notify "Test alert from pune-property health_check.sh at $(date -u +%FT%TZ). If you can read this, alerts work."
  echo "test alert handed to the configured hook(s) (nothing configured = nothing sent)"; exit 0
fi

# ---------------------------------------------------------------- checks
HOST="$(envval SITE_HOST)"
if [ -z "$HOST" ]; then bad config "SITE_HOST is not set in .env"; else
  if curl -fsS -m 15 -o /dev/null "https://$HOST/" 2>/dev/null; then ok site "https://$HOST/"; else bad site "https://$HOST/ did not answer with a success status"; fi
  if curl -fsS -m 15 "https://$HOST/api/v1/health" 2>/dev/null | grep -q '"healthy"'; then ok api; else bad api "/api/v1/health did not report healthy"; fi
fi

PCT="$(df --output=pcent / 2>/dev/null | tail -n1 | tr -dc '0-9')"
if [ -z "$PCT" ]; then bad disk "could not read disk usage"
elif [ "$PCT" -ge "$DISK_FAIL_PCT" ]; then bad disk "root disk is ${PCT}% full (limit ${DISK_FAIL_PCT}%)"
else ok disk "${PCT}% used"; fi

PS="$($DC ps --format '{{.Service}} {{.State}} {{.Health}}' 2>/dev/null)"
for svc in mongo backend frontend caddy; do
  line="$(printf '%s\n' "$PS" | awk -v s="$svc" '$1==s{print; exit}')"
  if [ -z "$line" ]; then bad "container $svc" "not found"
  elif [ "$(echo "$line" | awk '{print $2}')" != "running" ]; then bad "container $svc" "state is $(echo "$line" | awk '{print $2}')"
  elif echo "$line" | awk '{print $3}' | grep -qx unhealthy; then bad "container $svc" "running but unhealthy"
  else ok "container $svc"; fi
done

# Facebook Page token: debug_token answered by Meta. The script below runs inside the backend container and reads the
# token from that container's environment; it prints ONLY one status word (and a short Meta error code/message).
TOKEN_PY='
import json, os, sys, urllib.request, urllib.parse, urllib.error
t = os.environ.get("META_PAGE_ACCESS_TOKEN", "").strip()
v = os.environ.get("META_GRAPH_VERSION", "v23.0") or "v23.0"
if not t:
    print("NOTOKEN"); sys.exit(0)
q = urllib.parse.urlencode({"input_token": t, "access_token": t})
try:
    r = json.load(urllib.request.urlopen("https://graph.facebook.com/%s/debug_token?%s" % (v, q), timeout=20))
    d = r.get("data", {})
    if d.get("is_valid"): print("VALID")
    else: print("INVALID %s" % str(d.get("error", {}).get("message", "token not valid")).replace(t, "***")[:160])
except urllib.error.HTTPError as e:
    try: err = json.load(e).get("error", {})
    except Exception: err = {}
    code = err.get("code", e.code)
    print(("INVALID code %s %s" if code in (190, 102) else "UNKNOWN code %s %s") % (code, str(err.get("message", ""))[:120].replace(t, "***")))
except Exception as e:
    print("UNKNOWN network %s" % type(e).__name__)
'
TOK="$(printf '%s\n' "$TOKEN_PY" | $DC exec -T backend python - 2>/dev/null | tail -n1)"
case "$TOK" in
  VALID)    ok facebook-token ;;
  NOTOKEN)  say "skip  facebook-token: META_PAGE_ACCESS_TOKEN not configured" ;;
  INVALID*) bad facebook-token "Meta rejected the Page token (${TOK#INVALID }). Reconnect with meta_connect.ps1 (docs/META_SETUP.md H4)" ;;
  UNKNOWN*) say "warn  facebook-token: could not ask Meta right now (${TOK#UNKNOWN }); not counted as a failure" ;;
  *)        bad facebook-token "could not run the check in the backend container" ;;
esac

NEWEST="$(ls -1t "$BACKUP_DIR"/*.archive.gz 2>/dev/null | head -n1)"
if [ -z "$NEWEST" ]; then bad backup "no backup found in $BACKUP_DIR (is the backup cron installed?)"
else
  AGE_H=$(( ( $(date +%s) - $(stat -c %Y "$NEWEST") ) / 3600 ))
  if [ "$AGE_H" -gt "$BACKUP_MAX_AGE_H" ]; then bad backup "newest backup is ${AGE_H}h old (limit ${BACKUP_MAX_AGE_H}h): $(basename "$NEWEST")"
  else ok backup "$(basename "$NEWEST"), ${AGE_H}h old"; fi
fi

# ---------------------------------------------------------------- log + alert with de-duplication
NOW="$(date +%s)"; STAMP="$(date -u +%FT%TZ)"
SIG=""; [ "${#FAILS[@]}" -gt 0 ] && SIG="$(printf '%s\n' "${FAILS[@]}" | cut -d: -f1 | sort | tr '\n' ',')"
PREV_SIG=""; PREV_T=0
[ -f "$STATE" ] && { PREV_SIG="$(sed -n 1p "$STATE")"; PREV_T="$(sed -n 2p "$STATE")"; PREV_T="${PREV_T:-0}"; }

if [ "${#FAILS[@]}" -gt 0 ]; then
  if [ "$DRY" -eq 0 ]; then for f in "${FAILS[@]}"; do echo "$STAMP FAIL $f" >> "$LOG"; done; fi
  if [ "$SIG" != "$PREV_SIG" ] || [ $(( NOW - PREV_T )) -ge "$REALERT_S" ]; then
    notify "pune-property ALERT ($STAMP): $(printf '%s; ' "${FAILS[@]}")"
    [ "$DRY" -eq 0 ] && printf '%s\n%s\n' "$SIG" "$NOW" > "$STATE"
  fi
  RC=1
else
  if [ -n "$PREV_SIG" ]; then
    [ "$DRY" -eq 0 ] && echo "$STAMP OK recovered (was failing: $PREV_SIG)" >> "$LOG"
    notify "pune-property recovered ($STAMP): all checks pass again"
    [ "$DRY" -eq 0 ] && : > "$STATE"
  fi
  say "all checks passed"
  RC=0
fi

# keep the log bounded
if [ "$DRY" -eq 0 ] && [ -f "$LOG" ] && [ "$(wc -l < "$LOG")" -gt 5000 ]; then tail -n 2000 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"; fi
exit $RC
