#!/usr/bin/env bash
# The automatic deploy (.github/workflows/deploy.yml), run on GitHub's machine after the images of a commit are built:
#   1. remembers the commit the VM runs now (IMAGE_TAG in its .env),
#   2. copies deploy/ of the new commit to the VM and runs deploy/gcp/vm_update.sh there (pull the images, restart),
#   3. checks the public health address; if it does not pass, puts the previous commit back the same way and fails, so the
#      owner gets GitHub's failure email and the site keeps running the last good version.
# Needs (set once by deploy/gcp/ci_deploy_setup.ps1): an ssh key for the VM user in ~/.ssh/deploy_key, the VM's host key in
# ~/.ssh/known_hosts, and DEPLOY_SSH_USER, DEPLOY_SSH_HOST in the environment.
#   SHA=<commit> bash deploy/gcp/ci_deploy.sh
set -euo pipefail

: "${SHA:?SHA (the commit to deploy) is required}"
: "${DEPLOY_SSH_USER:?}"
: "${DEPLOY_SSH_HOST:?}"
REMOTE_DIR="${REMOTE_DIR:-app}"
HEALTH_URL="${HEALTH_URL:-https://avasetu.in/api/v1/health}"
HEALTH_TRIES="${HEALTH_TRIES:-12}"
HEALTH_WAIT="${HEALTH_WAIT:-10}"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "SHA must be a full 40-character commit" >&2; exit 2; }
HERE="$(cd "$(dirname "$0")" && pwd)"

SSH_OPTS=(-i "$HOME/.ssh/deploy_key" -o IdentitiesOnly=yes -o UserKnownHostsFile="$HOME/.ssh/known_hosts" -o StrictHostKeyChecking=yes -o ConnectTimeout=20 -o ServerAliveInterval=15)
TARGET="$DEPLOY_SSH_USER@$DEPLOY_SSH_HOST"
# shellcheck disable=SC2029  # the commands are built here on purpose (sha and folder are checked above)
vm() { ssh "${SSH_OPTS[@]}" "$TARGET" "$@"; }

# Copy deploy/ of one commit to the VM and switch to that commit's images. The bundle always carries this checkout's
# vm_update.sh: a commit from before the automatic deploy has none, and a rollback must still work.
ship() {
  local sha="$1" bundle dir
  bundle="$(mktemp --suffix=.tgz)"
  dir="$(mktemp -d)"
  git archive "$sha" deploy | tar x -C "$dir"
  cp "$HERE/vm_update.sh" "$dir/deploy/gcp/vm_update.sh"
  tar czf "$bundle" -C "$dir" deploy
  rm -rf "$dir"
  scp "${SSH_OPTS[@]}" "$bundle" "$TARGET:pune-property.tgz"
  rm -f "$bundle"
  vm "set -e; mkdir -p $REMOTE_DIR; tar xzf ~/pune-property.tgz -C $REMOTE_DIR; bash $REMOTE_DIR/deploy/gcp/vm_update.sh $sha"
}

healthy() {
  local i body
  sleep 20
  for ((i = 1; i <= HEALTH_TRIES; i++)); do
    body="$(curl -fsS --max-time 15 "$HEALTH_URL" 2>/dev/null || true)"
    if jq -e '.status == "healthy"' >/dev/null 2>&1 <<<"$body"; then return 0; fi
    sleep "$HEALTH_WAIT"
  done
  return 1
}

# a failed connection stops here, before anything on the VM changed
PREV="$(vm "grep -m1 '^IMAGE_TAG=' $REMOTE_DIR/deploy/gcp/.env | cut -d= -f2 || true")" \
  || { echo "::error::Cannot reach $TARGET over ssh: nothing was changed"; exit 1; }
PREV="$(echo "$PREV" | tr -d '[:space:]')"
echo "The VM runs ${PREV:-an unknown commit}; deploying $SHA"
if [[ "$PREV" == "$SHA" ]]; then echo "Already on $SHA: restarting it anyway"; fi

ship "$SHA"
if healthy; then
  echo "::notice::Deployed $SHA, healthy at $HEALTH_URL"
  exit 0
fi

echo "::error::$SHA did not pass the health check at $HEALTH_URL"
if [[ "$PREV" =~ ^[0-9a-f]{40}$ && "$PREV" != "$SHA" ]]; then
  echo "Putting the previous commit $PREV back"
  if ship "$PREV" && healthy; then
    echo "::error::Rolled back to $PREV (healthy). Fix $SHA and push again."
  else
    echo "::error::Rollback to $PREV did not pass the health check either: the site needs a look now."
  fi
else
  echo "::error::No previous commit to go back to (IMAGE_TAG was '${PREV}')."
fi
exit 1
