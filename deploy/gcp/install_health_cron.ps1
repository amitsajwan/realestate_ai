<#
  Install (or remove) the 15-minute health check on the pilot VM.

  Prerequisite: deploy the current code first (.\deploy\gcp\deploy.ps1) so ~/app/deploy/gcp/health_check.sh exists on the VM.
  Install the backup cron too (install_backup_cron.ps1): the health check also warns when backups stop.

  Usage (repo root):
    .\deploy\gcp\install_health_cron.ps1 -DryRun     # prints the cron line and the commands, contacts nothing
    .\deploy\gcp\install_health_cron.ps1             # installs the cron line, then runs one verbose check so you see the result
    .\deploy\gcp\install_health_cron.ps1 -Remove     # takes the cron line out again
    .\deploy\gcp\install_health_cron.ps1 -EveryMinutes 5

  Optional alerts: add ALERT_WEBHOOK_URL=... and/or ALERT_EMAIL=... to the VM's deploy/gcp/.env (this script never asks for or
  handles them). Without them, failures are just written to ~/health.log. Safe to run twice (the line is tagged and replaced).
#>
param(
  [string]$Project   = "trader-502012",
  [string]$Zone      = "asia-south1-a",
  [string]$Instance  = "pune-property",
  [string]$RemoteDir = "app",
  [int]$EveryMinutes = 15,
  [switch]$Remove,
  [switch]$NoRunNow,
  [switch]$Iap,
  [switch]$DryRun
)
$ErrorActionPreference = "Stop"
if ($EveryMinutes -lt 1 -or $EveryMinutes -gt 59) { throw "EveryMinutes must be 1-59" }
if ($RemoteDir -notmatch '^[A-Za-z0-9._/-]+$') { throw "RemoteDir has unexpected characters" }

$tag  = "# pune-property-health"
$line = "*/$EveryMinutes * * * * bash `$HOME/$RemoteDir/deploy/gcp/health_check.sh >/dev/null 2>&1 $tag"
$common = @("--project", $Project, "--zone", $Zone); if ($Iap) { $common += "--tunnel-through-iap" }

$add = if ($Remove) { "" } else { "echo '$line' >> `"`$tmp`"" }
$runNow = if ($Remove -or $NoRunNow) { "" } else { "bash ~/$RemoteDir/deploy/gcp/health_check.sh --verbose || echo '(some check failed: see the lines above; also ~/health.log)'" }
$remoteSh = @"
set -e
test -f ~/$RemoteDir/deploy/gcp/health_check.sh || { echo 'ERROR: health_check.sh is not on the VM yet. Run .\deploy\gcp\deploy.ps1 first.'; exit 1; }
tmp=`$(mktemp)
crontab -l 2>/dev/null | grep -v '$tag' > "`$tmp" || true
$add
crontab "`$tmp"; rm -f "`$tmp"
echo 'crontab now:'; crontab -l | grep -n 'pune-property' || echo '(no pune-property lines)'
set +e
$runNow
exit 0
"@

Write-Host "==> Cron line:" -ForegroundColor Cyan
if ($Remove) { Write-Host "(removing the tagged line)" } else { Write-Host $line }

if ($DryRun) {
  Write-Host "[dry-run] gcloud compute scp $($common -join ' ') <temp script> ${Instance}:install_health.sh" -ForegroundColor Yellow
  Write-Host "[dry-run] gcloud compute ssh $Instance $($common -join ' ') --command 'bash install_health.sh; rm -f install_health.sh'" -ForegroundColor Yellow
  Write-Host "[dry-run] remote script:" -ForegroundColor Yellow
  Write-Host $remoteSh
  return
}

$tmpSh = Join-Path $env:TEMP "install_health.sh"
try {
  [IO.File]::WriteAllText($tmpSh, ($remoteSh -replace "`r`n", "`n"))
  & gcloud compute scp @common $tmpSh "${Instance}:install_health.sh" | Out-Null; if ($LASTEXITCODE -ne 0) { throw "scp failed" }
  & gcloud compute ssh $Instance @common --command "bash install_health.sh; rc=`$?; rm -f install_health.sh; exit `$rc"; if ($LASTEXITCODE -ne 0) { throw "installing on the VM failed" }
} finally {
  Remove-Item $tmpSh -ErrorAction SilentlyContinue
}
Write-Host "Done." -ForegroundColor Green
