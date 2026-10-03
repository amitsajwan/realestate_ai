<#
  Issue (or revoke) a pilot invite for one agent, from your laptop, in about 10 seconds.

    .\deploy\gcp\invite.ps1 -Phone 98XXXXXXXX -Label "Rahul, Baner"
    .\deploy\gcp\invite.ps1 -Phone 98XXXXXXXX -Revoke
    .\deploy\gcp\invite.ps1 -List        # people who asked for an invite on the website

  It prints the 6-digit code and a ready-to-paste WhatsApp message. Re-issuing for the same number replaces the code and clears any lockout.
  Nothing secret is stored on your laptop.
#>
param(
  [string]$Phone = "",
  [string]$Label = "",
  [switch]$Revoke,
  [switch]$List,
  [string]$Project  = "trader-502012",
  [string]$Zone     = "asia-south1-a",
  [string]$Instance = "pune-property",
  [string]$RemoteDir = "app"
)
$ErrorActionPreference = "Continue"
$common = @("--project", $Project, "--zone", $Zone)
$run = "cd ~/$RemoteDir/deploy/gcp; sudo docker compose exec -T -e PYTHONPATH=. backend python"

if ($List) {
  & gcloud compute ssh $Instance @common --command "$run scripts/invite_requests.py list" 2>&1 | Out-String | Write-Host
  return
}
if (-not $Phone) { Write-Host "Usage: .\deploy\gcp\invite.ps1 -Phone 98XXXXXXXX -Label ""Name, Area""" -ForegroundColor Yellow; return }
$digits = ($Phone -replace "\D", "")
if ($digits.Length -eq 12 -and $digits.StartsWith("91")) { $digits = $digits.Substring(2) }
if ($digits.Length -ne 10) { Write-Host "Enter a 10-digit Indian mobile number." -ForegroundColor Red; return }

if ($Revoke) {
  & gcloud compute ssh $Instance @common --command "$run scripts/invite.py revoke $digits" 2>&1 | Out-String | Write-Host
  return
}
$safe = ($Label -replace '[^A-Za-z0-9 ,.\-]', '')
$cmd = "$run scripts/invite.py issue $digits" + $(if ($safe) { " --label '$safe'" } else { "" })
& gcloud compute ssh $Instance @common --command $cmd 2>&1 | Out-String | Write-Host
Write-Host "Sign-in page: https://avasetu.in/join  (mobile number + the code above)" -ForegroundColor Green
