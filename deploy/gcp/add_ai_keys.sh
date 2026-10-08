#!/usr/bin/env bash
# Add free AI provider keys to the VM's deploy/gcp/.env, one provider at a time (Mistral first).
# For each provider: opens the key page, asks for the key (hidden), checks it against the provider, then saves it.
# Empty input skips a provider. Keys never go into git, the shell history or a command line.
#   bash deploy/gcp/add_ai_keys.sh
set -euo pipefail

PROJECT=trader-502012
ZONE=asia-south1-a
INSTANCE=pune-property
REMOTE_ENV='app/deploy/gcp/.env'

# name | env var | key page | check url | auth style (bearer|query)
PROVIDERS=(
  "Mistral|MISTRAL_API_KEY|https://console.mistral.ai/api-keys|https://api.mistral.ai/v1/models|bearer"
  "Gemini (Google AI Studio)|GEMINI_API_KEY|https://aistudio.google.com/app/apikey|https://generativelanguage.googleapis.com/v1beta/models|query"
  "Cerebras|CEREBRAS_API_KEY|https://cloud.cerebras.ai|https://api.cerebras.ai/v1/models|bearer"
  "SambaNova|SAMBANOVA_API_KEY|https://cloud.sambanova.ai/apis|https://api.sambanova.ai/v1/models|bearer"
  "NVIDIA (build.nvidia.com)|NVIDIA_API_KEY|https://build.nvidia.com/settings/api-keys|https://integrate.api.nvidia.com/v1/models|bearer"
  "GitHub Models (optional)|GITHUB_MODELS_TOKEN|https://github.com/settings/personal-access-tokens/new|https://models.github.ai/catalog/models|bearer"
)

open_url() { explorer.exe "$1" >/dev/null 2>&1 || xdg-open "$1" >/dev/null 2>&1 || open "$1" >/dev/null 2>&1 || true; }

check_key() {  # url style key -> prints HTTP status
  if [ "$2" = query ]; then
    curl -s -o /dev/null -w '%{http_code}' --config - <<<"url = \"$1?key=$3\""
  else
    curl -s -o /dev/null -w '%{http_code}' --config - <<<"url = \"$1\"
header = \"Authorization: Bearer $3\""
  fi
}

tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

for p in "${PROVIDERS[@]}"; do
  IFS='|' read -r name var page url style <<<"$p"
  echo
  echo "=== $name ==="
  echo "Key page: $page"
  read -r -p "Open it in the browser? [Y/n] " yn
  [[ "$yn" =~ ^[Nn] ]] || open_url "$page"
  while true; do
    read -r -s -p "Paste the $name key (Enter to skip): " key; echo
    key=$(printf '%s' "$key" | tr -d '[:space:]')
    [ -z "$key" ] && { echo "Skipped $name."; break; }
    code=$(check_key "$url" "$style" "$key")
    if [ "$code" = 200 ]; then
      echo "OK: the key works."
      printf '%s=%s\n' "$var" "$key" >>"$tmp"
      break
    fi
    echo "The provider answered HTTP $code (not 200). Check the key and try again."
  done
done

if [ ! -s "$tmp" ]; then echo; echo "No keys to save."; exit 0; fi

echo
echo "Saving $(wc -l <"$tmp") key(s) to the VM ($REMOTE_ENV); a backup goes to .env.bak first."
gcloud compute scp --project "$PROJECT" --zone "$ZONE" "$tmp" "$INSTANCE:ai_keys.tmp"
gcloud compute ssh "$INSTANCE" --project "$PROJECT" --zone "$ZONE" --command "set -e; f=$REMOTE_ENV; cp \$f \$f.bak; \
while IFS='=' read -r k v; do [ -n \"\$k\" ] || continue; grep -v \"^\$k=\" \$f > \$f.new || true; mv \$f.new \$f; echo \"\$k=\$v\" >> \$f; echo \"saved \$k\"; done < ~/ai_keys.tmp; \
chmod 600 \$f; rm -f ~/ai_keys.tmp"
echo "Done. The keys take effect on the next deploy."
