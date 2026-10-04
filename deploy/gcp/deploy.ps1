<#
  Redeploy the pilot to the single GCP VM (Caddy + frontend + backend + worker + MongoDB via docker compose).

  What it does:
    1. Bundles the TRACKED files of deploy/, backend/ and frontend/ from git HEAD (so no .env, node_modules or uploads ever leave your PC).
    2. Copies the bundle to the VM and unpacks it into $RemoteDir (the VM's own deploy/gcp/.env with the secrets is untouched).
    3. Rebuilds and restarts the containers, then checks the public health address.

  Usage (from the repo root, with your changes COMMITTED):
    .\deploy\gcp\deploy.ps1 -DryRun     # prints every step, contacts nothing, still builds the local bundle to prove it works
    .\deploy\gcp\deploy.ps1             # does it for real
    .\deploy\gcp\deploy.ps1 -Iap        # use IAP tunnelling for ssh/scp (once SSH is restricted to IAP)
    .\deploy\gcp\deploy.ps1 -ContactEmail you@example.com
        # also sets NEXT_PUBLIC_CONTACT_EMAIL in the VM's private .env (shown on /privacy, /terms, /data-deletion; never committed to git)

  Assumptions to confirm the first time (defaults come from the deployment notes): project, zone, instance name, and that the app lives in
  ~/app on the VM. Override with -RemoteDir if the VM uses a different folder.
#>
param(
  [string]$Project   = "trader-502012",
  [string]$Zone      = "asia-south1-a",
  [string]$Instance  = "pune-property",
  [string]$RemoteDir = "app",
  [string]$HealthUrl = "https://avasetu.in/api/v1/health",
  [string]$ContactEmail = "",
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
Write-Host "Deploying commit $head"

Step "Building the bundle from git HEAD (tracked files only)"
$bundle = Join-Path $env:TEMP "pune-property-$head.tgz"
git archive --format=tar.gz -o $bundle HEAD deploy backend frontend -- ":!frontend/screenshots" ":!frontend/e2e"
if ($LASTEXITCODE -ne 0) { throw "git archive failed" }
$mb = [math]::Round((Get-Item $bundle).Length / 1MB, 1)
Write-Host "Bundle: $bundle ($mb MB)"

$iapFlag = if ($Iap) { " --tunnel-through-iap" } else { "" }
$target = "$Instance"
$common = "--project $Project --zone $Zone$iapFlag"

Step "Copying the bundle to the VM"
Run "gcloud compute scp $common `"$bundle`" ${target}:pune-property.tgz"

Step "Unpacking and rebuilding on the VM (secrets in deploy/gcp/.env are kept)"
$setEmail = ""
if ($ContactEmail) { $setEmail = "sed -i '/^NEXT_PUBLIC_CONTACT_EMAIL=/d' .env; sed -i -e '`$a\' .env; echo 'NEXT_PUBLIC_CONTACT_EMAIL=$ContactEmail' >> .env; " }
# Unpacking over the old tree keeps files deleted from git, and they get built in (a removed Next.js route once broke the
# build). Code files in the code folders that the bundle no longer has are removed; .env files, backups and assets are kept.
$prune = "cd $RemoteDir; tar tzf ~/pune-property.tgz | sort > /tmp/deploy-new.txt; find backend/app backend/scripts backend/tests frontend/app frontend/components frontend/lib frontend/__tests__ -type f \( -name '*.py' -o -name '*.ts' -o -name '*.tsx' -o -name '*.js' -o -name '*.jsx' -o -name '*.mjs' -o -name '*.css' \) -not -path '*/node_modules/*' -not -path '*/__pycache__/*' 2>/dev/null | sort | comm -23 - /tmp/deploy-new.txt > /tmp/deploy-stale.txt; echo stale code files removed:; wc -l /tmp/deploy-stale.txt; xargs -r -a /tmp/deploy-stale.txt rm -f; cd ~; "
$remote = "set -e; mkdir -p $RemoteDir; tar xzf ~/pune-property.tgz -C $RemoteDir; $prune cd $RemoteDir/deploy/gcp; test -f .env || { echo 'ERROR: deploy/gcp/.env missing on the VM'; exit 1; }; ${setEmail}sudo docker compose up -d --build; sudo docker compose ps; rm -f ~/pune-property.tgz"
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
