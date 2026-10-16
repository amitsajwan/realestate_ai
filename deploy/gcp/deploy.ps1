<#
  Redeploy the pilot to the single GCP VM (Caddy + frontend + backend + worker roles + MongoDB via docker compose).

  What it does (default): the app images are built on GitHub (.github/workflows/images.yml) for every push, so a deploy
    1. waits until GitHub has built the images of git HEAD (HEAD must be pushed),
    2. copies the TRACKED files of deploy/ to the VM (compose file, Caddyfile, scripts; the VM's own deploy/gcp/.env with the
       secrets is untouched) and sets IMAGE_TAG in that .env to the commit,
    3. pulls the images and restarts the containers (no build on the VM), then checks the public health address.
  Old images unused for 3 days are removed from the VM (any of them can be pulled again from Artifact Registry).

  Usage (from the repo root, with your changes COMMITTED and PUSHED):
    .\deploy\gcp\deploy.ps1 -DryRun     # prints every step, contacts nothing
    .\deploy\gcp\deploy.ps1             # does it for real
    .\deploy\gcp\deploy.ps1 -Tag <sha>  # roll back (or forward) to the images of another commit, already built
    .\deploy\gcp\deploy.ps1 -Build      # the fallback: bundle backend/ and frontend/ too and build on the VM (slow)
    .\deploy\gcp\deploy.ps1 -Iap        # use IAP tunnelling for ssh/scp (once SSH is restricted to IAP)
    .\deploy\gcp\deploy.ps1 -ContactEmail you@example.com
        # also sets NEXT_PUBLIC_CONTACT_EMAIL in the VM's private .env (shown on /privacy, /terms, /data-deletion; never committed to
        # git). With images built on GitHub it must also be the repository variable of the same name (gh variable set).
#>
param(
  [string]$Project   = "trader-502012",
  [string]$Zone      = "asia-south1-a",
  [string]$Instance  = "pune-property",
  [string]$RemoteDir = "app",
  [string]$HealthUrl = "https://avasetu.in/api/v1/health",
  [string]$ContactEmail = "",
  [string]$Tag = "",
  [switch]$Build,
  [switch]$Iap,
  [switch]$DryRun
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path (Split-Path $PSScriptRoot))   # repo root

function Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }
function Run($cmd) { if ($DryRun) { Write-Host "[dry-run] $cmd" -ForegroundColor Yellow } else { Invoke-Expression $cmd; if ($LASTEXITCODE -ne 0) { throw "failed: $cmd" } } }

if ($ContactEmail -and $ContactEmail -notmatch '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$') { throw "ContactEmail does not look like an email address" }

Step "Checking the working tree"
$dirty = git status --porcelain --untracked-files=no
if ($dirty) { throw "You have uncommitted changes to tracked files. Commit them first (the bundle is built from git HEAD):`n$dirty" }
$head = git rev-parse --short HEAD
$sha = if ($Tag) { $Tag } else { git rev-parse HEAD }
Write-Host "Deploying commit $head$(if ($Tag) { " with the images of $Tag" })"

if (-not $Build -and -not $Tag) {
  Step "Waiting for GitHub to build the images of $head"
  if (-not (git branch -r --contains $sha)) { throw "Commit $head is not pushed: push it (GitHub builds the images on push), or deploy with -Build" }
  if ($DryRun) { Write-Host "[dry-run] gh run watch (images.yml, $sha)" -ForegroundColor Yellow }
  else {
    $run = $null
    foreach ($i in 1..18) {   # a push starts the build within seconds; give it 3 minutes to appear
      $run = gh run list --workflow images.yml --commit $sha --json databaseId,status,conclusion --limit 1 | ConvertFrom-Json | Select-Object -First 1
      if ($run) { break }
      Start-Sleep -Seconds 10
    }
    if (-not $run) { throw "GitHub has no image build for $head (Actions > Build app images > Run workflow), or deploy with -Build" }
    if ($run.status -ne "completed") { gh run watch $run.databaseId --exit-status | Out-Null }
    $run = gh run view $run.databaseId --json conclusion | ConvertFrom-Json
    if ($run.conclusion -ne "success") { throw "The image build for $head did not succeed ($($run.conclusion)): gh run view --log-failed" }
    Write-Host "Images built: $sha"
  }
}

Step "Building the bundle from git HEAD (tracked files only)"
$bundle = Join-Path $env:TEMP "pune-property-$head.tgz"
if ($Build) { git archive --format=tar.gz -o $bundle HEAD deploy backend frontend -- ":!frontend/screenshots" ":!frontend/e2e" }
else { git archive --format=tar.gz -o $bundle HEAD deploy }
if ($LASTEXITCODE -ne 0) { throw "git archive failed" }
$mb = [math]::Round((Get-Item $bundle).Length / 1MB, 1)
Write-Host "Bundle: $bundle ($mb MB)"

$iapFlag = if ($Iap) { " --tunnel-through-iap" } else { "" }
$target = "$Instance"
$common = "--project $Project --zone $Zone$iapFlag"

Step "Copying the bundle to the VM"
Run "gcloud compute scp $common `"$bundle`" ${target}:pune-property.tgz"

$setEmail = ""
# no "$" in these remote commands: Run() re-reads the string, so PowerShell expands it again ("sed '$a\'" became "sed '\'" and
# stopped the first image deploy, 2026-10-16). grep -v ends the file with a newline; "cat >" keeps the .env's permissions.
function SetEnv($name, $value) { "grep -v '^${name}=' .env > /tmp/env.new || true; echo '${name}=${value}' >> /tmp/env.new; cat /tmp/env.new > .env; rm -f /tmp/env.new; " }
if ($ContactEmail) { $setEmail = SetEnv "NEXT_PUBLIC_CONTACT_EMAIL" $ContactEmail }
# a second "up -d" starts any service the first one left stopped (2026-10-15: a deploy left the backend down for ~3 minutes)
if ($Build) {
  Step "Unpacking and rebuilding on the VM (secrets in deploy/gcp/.env are kept)"
  # Unpacking over the old tree keeps files deleted from git, and they get built in (a removed Next.js route once broke the
  # build). Code files in the code folders that the bundle no longer has are removed; .env files, backups and assets are kept.
  $prune = "cd $RemoteDir; tar tzf ~/pune-property.tgz | sort > /tmp/deploy-new.txt; find backend/app backend/scripts backend/tests frontend/app frontend/components frontend/lib frontend/__tests__ frontend/hooks frontend/store frontend/types frontend/utils frontend/styles frontend/tests -type f \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.mjs' -o -name '*.css' \) -not -path '*/node_modules/*' -not -path '*/__pycache__/*' 2>/dev/null | sort | comm -23 - /tmp/deploy-new.txt > /tmp/deploy-stale.txt; echo stale code files removed:; wc -l /tmp/deploy-stale.txt; xargs -r -a /tmp/deploy-stale.txt rm -f; cd ~; "
  $remote = "set -e; mkdir -p $RemoteDir; tar xzf ~/pune-property.tgz -C $RemoteDir; $prune cd $RemoteDir/deploy/gcp; test -f .env || { echo 'ERROR: deploy/gcp/.env missing on the VM'; exit 1; }; ${setEmail}sudo docker compose up -d --build --remove-orphans || { echo first up failed, retrying; sleep 10; sudo docker compose up -d; }; sleep 8; sudo docker compose up -d; sudo docker compose ps; rm -f ~/pune-property.tgz"
} else {
  Step "Unpacking deploy/, pulling the images of $sha and restarting (secrets in deploy/gcp/.env are kept)"
  $setTag = SetEnv "IMAGE_TAG" $sha
  $login = "sudo gcloud auth configure-docker asia-south1-docker.pkg.dev --quiet >/dev/null 2>&1; "
  $remote = "set -e; mkdir -p $RemoteDir; tar xzf ~/pune-property.tgz -C $RemoteDir; cd $RemoteDir/deploy/gcp; test -f .env || { echo 'ERROR: deploy/gcp/.env missing on the VM'; exit 1; }; ${setEmail}${setTag}${login}sudo docker compose pull backend conversations newsroom media frontend; sudo docker compose up -d --no-build --remove-orphans || { echo first up failed, retrying; sleep 10; sudo docker compose up -d --no-build; }; sleep 8; sudo docker compose up -d --no-build; sudo docker compose ps; sudo docker image prune -a -f --filter until=72h >/dev/null; rm -f ~/pune-property.tgz"
}
Run "gcloud compute ssh $target $common --command `"$remote`""

Step "Checking the public health address"
if ($DryRun) { Write-Host "[dry-run] curl $HealthUrl" -ForegroundColor Yellow }
else {
  Start-Sleep -Seconds 20
  $ok = $false
  foreach ($i in 1..10) {
    try { $r = Invoke-RestMethod -Uri $HealthUrl -TimeoutSec 15; if ($r.status -eq "healthy") { $ok = $true; break } } catch { Start-Sleep -Seconds 10 }
  }
  if ($ok) { Write-Host "Healthy: $HealthUrl" -ForegroundColor Green } else { throw "Health check did not pass; check: gcloud compute ssh $target $common --command 'cd $RemoteDir/deploy/gcp; sudo docker compose logs --tail 80 backend'" }
}
Remove-Item $bundle -ErrorAction SilentlyContinue
Write-Host "Done." -ForegroundColor Green
