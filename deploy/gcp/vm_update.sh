#!/usr/bin/env bash
# Runs ON THE VM, from the unpacked deploy/ bundle: point the app at the images of one commit, pull them and restart.
# The same steps as the remote command in deploy.ps1 (no -Build); used by the automatic deploy (.github/workflows/deploy.yml).
# Keep the two in step.
#   bash ~/app/deploy/gcp/vm_update.sh <40-character commit sha>
# The secrets in deploy/gcp/.env are kept; only IMAGE_TAG changes.
set -euo pipefail

SHA="${1:-}"
[[ "$SHA" =~ ^[0-9a-f]{40}$ ]] || { echo "usage: vm_update.sh <40-character commit sha>" >&2; exit 2; }

cd "$(dirname "$0")"   # deploy/gcp
test -f .env || { echo 'ERROR: deploy/gcp/.env missing on the VM'; exit 1; }

# grep -v ends the file with a newline; "cat >" keeps the .env's permissions
set_tag() {
  grep -v '^IMAGE_TAG=' .env > /tmp/env.new || true
  echo "IMAGE_TAG=$1" >> /tmp/env.new
  cat /tmp/env.new > .env
  rm -f /tmp/env.new
}
OLD_TAG="$(grep -m1 '^IMAGE_TAG=' .env | cut -d= -f2 || true)"
set_tag "$SHA"

sudo gcloud auth configure-docker asia-south1-docker.pkg.dev --quiet >/dev/null 2>&1 || true
# room for the new images first (2026-10-22: the disk was 97% full): images no container uses and the build cache. The images
# the site runs now are in use, so they stay, and a rollback to them needs no download.
df -h / | tail -1
sudo docker image prune -a -f >/dev/null || true
sudo docker builder prune -a -f >/dev/null 2>&1 || true
df -h / | tail -1
# a failed pull (no space, registry down) leaves the site as it is: .env goes back to the commit it runs
if ! sudo docker compose pull backend conversations newsroom media embedder qdrant frontend; then
  [[ -n "$OLD_TAG" ]] && set_tag "$OLD_TAG"
  echo "ERROR: could not pull the images of $SHA; nothing was restarted (IMAGE_TAG back to ${OLD_TAG:-unset})" >&2
  df -h / | tail -1
  exit 1
fi
# a second "up -d" starts any service the first one left stopped (2026-10-15: a deploy left the backend down for ~3 minutes)
sudo docker compose up -d --no-build --remove-orphans || { echo 'first up failed, retrying'; sleep 10; sudo docker compose up -d --no-build; }
sleep 8
sudo docker compose up -d --no-build
sudo docker compose ps
sudo docker image prune -a -f --filter until=72h >/dev/null || true
rm -f ~/pune-property.tgz
echo "IMAGE_TAG=$SHA"
