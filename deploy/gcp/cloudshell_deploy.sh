#!/usr/bin/env bash
# Deploy from Google Cloud Shell: works from a phone (shell.cloud.google.com, or the Google Cloud app > Cloud Shell), where
# gcloud is already signed in to the project. The same steps as deploy.ps1 (deploy/ files to the VM, the images of the commit,
# restart via vm_update.sh), then the public health check; if it does not pass, the commit the VM ran before is put back.
# Paste in Cloud Shell:
#   git clone -q --filter=blob:none https://github.com/amitsajwan/realestate_ai.git 2>/dev/null; cd realestate_ai && git pull -q && bash deploy/gcp/cloudshell_deploy.sh
# A commit's sha as the first argument deploys (or rolls back to) that commit; the default is the newest commit on main.
set -euo pipefail

PROJECT="${PROJECT:-trader-502012}"
ZONE="${ZONE:-asia-south1-a}"
INSTANCE="${INSTANCE:-pune-property}"
REPO="${REPO:-amitsajwan/realestate_ai}"
HEALTH_URL="${HEALTH_URL:-https://avasetu.in/api/v1/health}"
HEALTH_TRIES="${HEALTH_TRIES:-12}"
HEALTH_WAIT="${HEALTH_WAIT:-10}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE/../.."

git fetch -q origin main
SHA="${1:-$(git rev-parse origin/main)}"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "Give a full 40-character commit sha" >&2; exit 2; }
echo "==> Deploying $SHA ($(git log -1 --format=%s "$SHA" | cut -c1-70))"

if [[ -z "${SKIP_IMAGE_CHECK:-}" ]]; then
  echo "==> Checking GitHub built its images"
  built="$(curl -fsS "https://api.github.com/repos/$REPO/actions/workflows/images.yml/runs?head_sha=$SHA&status=success&per_page=1" | jq '.total_count')"
  [[ "$built" -ge 1 ]] || { echo "No successful image build for $SHA yet (GitHub > Actions > Build app images): wait for it, then run this again." >&2; exit 1; }
fi

G=(--project "$PROJECT" --zone "$ZONE" --quiet)
on_vm() { gcloud compute ssh "$INSTANCE" "${G[@]}" --command "$1"; }

# The app lives in the home of the user deploy.ps1 signs in as; Cloud Shell may sign in as another user, so find it and work
# with sudo, then give the files back to their owner.
echo "==> Finding the app on the VM"
APP="$(on_vm "sudo sh -c 'for d in /home/*/app; do [ -f \"\$d/deploy/gcp/.env\" ] && echo \"\$d\"; done' | head -1" | tr -d '\r')"
[[ "$APP" == /home/*/app ]] || { echo "Could not find ~/app/deploy/gcp/.env on the VM" >&2; exit 1; }
PREV="$(on_vm "sudo grep -m1 '^IMAGE_TAG=' $APP/deploy/gcp/.env | cut -d= -f2" | tr -d '[:space:]')"
echo "App: $APP; the VM runs ${PREV:-an unknown commit}"

ship() {
  local sha="$1" dir bundle
  dir="$(mktemp -d)"; bundle="$(mktemp --suffix=.tgz)"
  git archive "$sha" deploy | tar x -C "$dir"
  cp "$HERE/vm_update.sh" "$dir/deploy/gcp/vm_update.sh"   # a commit from before vm_update.sh existed still deploys
  tar czf "$bundle" -C "$dir" deploy
  rm -rf "$dir"
  gcloud compute scp "${G[@]}" "$bundle" "$INSTANCE:deploy-bundle.tgz"
  rm -f "$bundle"
  on_vm "set -e; owner=\$(sudo stat -c %U $APP); sudo tar xzf ~/deploy-bundle.tgz --no-same-owner -C $APP; sudo chown -R \$owner: $APP/deploy; rm -f ~/deploy-bundle.tgz; sudo bash $APP/deploy/gcp/vm_update.sh $sha"
}

healthy() {
  local i
  sleep 20
  for ((i = 1; i <= HEALTH_TRIES; i++)); do
    if curl -fsS --max-time 15 "$HEALTH_URL" 2>/dev/null | jq -e '.status == "healthy"' >/dev/null 2>&1; then return 0; fi
    sleep "$HEALTH_WAIT"
  done
  return 1
}

echo "==> Copying deploy/ and restarting on the new images"
ship "$SHA"
echo "==> Checking $HEALTH_URL"
if healthy; then echo "Deployed $SHA: healthy."; exit 0; fi

echo "!! $SHA did not pass the health check" >&2
if [[ "$PREV" =~ ^[0-9a-f]{40}$ && "$PREV" != "$SHA" ]]; then
  echo "==> Putting the previous commit $PREV back"
  ship "$PREV"
  if healthy; then echo "Rolled back to $PREV (healthy)." >&2; else echo "!! The rollback is not healthy either: the site needs a look now." >&2; fi
fi
exit 1
