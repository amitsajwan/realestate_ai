<#
  Install (or remove) the nightly database backup on the pilot VM.

  Prerequisite: deploy the current code first (.\deploy\gcp\deploy.ps1) so ~/app/deploy/gcp/backup.sh exists on the VM.

  Usage (repo root):
    .\deploy\gcp\install_backup_cron.ps1 -DryRun     # prints the cron line and the commands, contacts nothing
    .\deploy\gcp\install_backup_cron.ps1             # installs the cron line, then runs one backup and lists ~/backups
    .\deploy\gcp\install_backup_cron.ps1 -Remove     # takes the cron line out again
    .\deploy\gcp\install_backup_cron.ps1 -Hour 21 -Minute 30   # VM clock is UTC: 21:30 UTC = 03:00 IST (default)

  Safe to run twice: the line is tagged and replaced, never duplicated. Backups go to ~/backups/YYYY-MM-DD.archive.gz
  (newest 14 kept), results to ~/backup.log. Nothing secret is handled by this script.
#>
param(
  [string]$Project   = "trader-502012",
  [string]$Zone      = "asia-south1-a",
  [string]$Instance  = "pune-property",
  [string]$RemoteDir = "app",
  [int]$Hour   = 21,
  [int]$Minute = 30,
  [switch]$Remove,
  [switch]$NoRunNow,
  [switch]$Iap,
  [switch]$DryRun
)
$ErrorActionPreference = "Stop"
if ($Hour -lt 0 -or $Hour -gt 23 -or $Minute -lt 0 -or $Minute -gt 59) { throw "Hour/Minute out of range" }
if ($RemoteDir -notmatch '^[A-Za-z0-9._/-]+$') { throw "RemoteDir has unexpected characters" }

$tag  = "# pune-property-backup"
$line = "$Minute $Hour * * * bash `$HOME/$RemoteDir/deploy/gcp/backup.sh >/dev/null 2>&1 $tag"
$common = @("--project", $Project, "--zone", $Zone); if ($Iap) { $common += "--tunnel-through-iap" }

# remote script: drop any previous tagged line, add the new one (unless -Remove)
$add = if ($Remove) { "" } else { "echo '$line' >> `"`$tmp`"" }
$runNow = if ($Remove -or $NoRunNow) { "" } else { "bash ~/$RemoteDir/deploy/gcp/backup.sh && ls -lh ~/backups | tail -n 5" }
$remoteSh = @"
set -e
test -f ~/$RemoteDir/deploy/gcp/backup.sh || { echo 'ERROR: backup.sh is not on the VM yet. Run .\deploy\gcp\deploy.ps1 first.'; exit 1; }
tmp=`$(mktemp)
crontab -l 2>/dev/null | grep -v '$tag' > "`$tmp" || true
$add
crontab "`$tmp"; rm -f "`$tmp"
echo 'crontab now:'; crontab -l | grep -n 'pune-property' || echo '(no pune-property lines)'
$runNow
"@

Write-Host "==> Cron line (VM time is UTC; 21:30 UTC = 03:00 IST):" -ForegroundColor Cyan
if ($Remove) { Write-Host "(removing the tagged line)" } else { Write-Host $line }

if ($DryRun) {
  Write-Host "[dry-run] gcloud compute scp $($common -join ' ') <temp script> ${Instance}:install_backup.sh" -ForegroundColor Yellow
  Write-Host "[dry-run] gcloud compute ssh $Instance $($common -join ' ') --command 'bash install_backup.sh; rm -f install_backup.sh'" -ForegroundColor Yellow
  Write-Host "[dry-run] remote script:" -ForegroundColor Yellow
  Write-Host $remoteSh
  return
}

$tmpSh = Join-Path $env:TEMP "install_backup.sh"
try {
  [IO.File]::WriteAllText($tmpSh, ($remoteSh -replace "`r`n", "`n"))
  & gcloud compute scp @common $tmpSh "${Instance}:install_backup.sh" | Out-Null; if ($LASTEXITCODE -ne 0) { throw "scp failed" }
  & gcloud compute ssh $Instance @common --command "bash install_backup.sh; rc=`$?; rm -f install_backup.sh; exit `$rc"; if ($LASTEXITCODE -ne 0) { throw "installing on the VM failed" }
} finally {
  Remove-Item $tmpSh -ErrorAction SilentlyContinue
}
Write-Host "Done." -ForegroundColor Green
