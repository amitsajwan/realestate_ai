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
grep -v '^IMAGE_TAG=' .env > /tmp/env.new || true
echo "IMAGE_TAG=$SHA" >> /tmp/env.new
cat /tmp/env.new > .env
rm -f /tmp/env.new

sudo gcloud auth configure-docker asia-south1-docker.pkg.dev --quiet >/dev/null 2>&1 || true
sudo docker compose pull backend conversations newsroom media embedder qdrant frontend
# a second "up -d" starts any service the first one left stopped (2026-10-15: a deploy left the backend down for ~3 minutes)
sudo docker compose up -d --no-build --remove-orphans || { echo 'first up failed, retrying'; sleep 10; sudo docker compose up -d --no-build; }
sleep 8
sudo docker compose up -d --no-build
sudo docker compose ps
sudo docker image prune -a -f --filter until=72h >/dev/null || true
rm -f ~/pune-property.tgz
echo "IMAGE_TAG=$SHA"
