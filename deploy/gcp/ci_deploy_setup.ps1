<#
  Turn on the automatic deploy (.github/workflows/deploy.yml): every commit pushed to main goes live by itself once GitHub has
  built its images, and the previous commit is put back if the site's health check does not pass. Run once, from the repo
  root, with gcloud signed in to the project and gh signed in to GitHub (repository admin).

  What it does:
    1. checks the VM takes ssh keys from metadata (not OS Login) and lists the firewall rules that open port 22,
    2. makes a new ssh key ON THE VM (nothing is written on this PC), for the same VM user deploy.ps1 uses (so the same ~/app),
    3. adds its public half to the VM's own ssh keys (instance metadata; existing keys are kept, an older GitHub key is replaced),
    4. stores the private half as the repository secret DEPLOY_SSH_KEY, and DEPLOY_SSH_USER, DEPLOY_SSH_HOST (the VM's address),
       DEPLOY_KNOWN_HOSTS (the VM's host key, so GitHub only ever talks to this VM) and AUTO_DEPLOY=true as repository variables.

  Usage:
    .\deploy\gcp\ci_deploy_setup.ps1 -DryRun   # checks and prints every step, changes nothing
    .\deploy\gcp\ci_deploy_setup.ps1           # turns it on (running it again makes a new key and drops the old one)
    .\deploy\gcp\ci_deploy_setup.ps1 -Off      # turns it off: AUTO_DEPLOY=false, the key leaves the VM and GitHub
  Manual deploys with deploy.ps1 keep working either way.
#>
param(
  [string]$Project  = "trader-502012",
  [string]$Zone     = "asia-south1-a",
  [string]$Instance = "pune-property",
  [string]$Repo     = "",
  [switch]$Iap,
  [switch]$Off,
  [switch]$DryRun
)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path (Split-Path $PSScriptRoot))   # repo root

$Comment = "github-deploy"   # marks our key in the VM's ssh keys
function Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }
function Check($what) { if ($LASTEXITCODE -ne 0) { throw "failed: $what" } }
$common = @("--project", $Project, "--zone", $Zone)
$sshFlags = $common + $(if ($Iap) { @("--tunnel-through-iap") } else { @() })

foreach ($tool in "gcloud", "gh") { if (-not (Get-Command $tool -ErrorAction SilentlyContinue)) { throw "$tool is not installed" } }
if (-not $Repo) { $Repo = gh repo view --json nameWithOwner -q .nameWithOwner; Check "gh repo view (is gh signed in?)" }
Write-Host "Repository: $Repo   VM: $Instance ($Project, $Zone)"

# The VM's own ssh keys (instance metadata), without our old GitHub key; a temp file keeps the newlines exact.
function OtherKeys() {
  $vm = gcloud compute instances describe $Instance @common --format json | ConvertFrom-Json; Check "describe $Instance"
  $item = $vm.metadata.items | Where-Object { $_.key -eq "ssh-keys" }
  $lines = if ($item) { $item.value -split "`n" } else { @() }
  return @($lines | Where-Object { $_.Trim() -and -not $_.TrimEnd().EndsWith(" $Comment") })
}
function WriteKeys($lines) {
  $file = Join-Path $env:TEMP "avasetu-ssh-keys.txt"
  [IO.File]::WriteAllText($file, (($lines -join "`n") + "`n"))
  if ($DryRun) { Write-Host "[dry-run] gcloud compute instances add-metadata $Instance --metadata-from-file ssh-keys=<$($lines.Count) keys>" -ForegroundColor Yellow }
  else { gcloud compute instances add-metadata $Instance @common --metadata-from-file "ssh-keys=$file"; Check "add-metadata ssh-keys" }
  Remove-Item $file -ErrorAction SilentlyContinue
}
function SetVar($name, $value) {
  if ($DryRun) { Write-Host "[dry-run] gh variable set $name" -ForegroundColor Yellow; return }
  gh variable set $name --repo $Repo --body $value; Check "gh variable set $name"
}

if ($Off) {
  Step "Turning the automatic deploy off"
  SetVar "AUTO_DEPLOY" "false"
  Step "Removing GitHub's key from the VM"
  WriteKeys (OtherKeys)
  if ($DryRun) { Write-Host "[dry-run] gh secret delete DEPLOY_SSH_KEY" -ForegroundColor Yellow }
  else { gh secret delete DEPLOY_SSH_KEY --repo $Repo; if ($LASTEXITCODE -ne 0) { Write-Host "(no DEPLOY_SSH_KEY secret to delete)" } }
  Write-Host "Off. Deploy by hand with .\deploy\gcp\deploy.ps1" -ForegroundColor Green
  return
}

Step "Checking the VM takes ssh keys from metadata"
$vm = gcloud compute instances describe $Instance @common --format json | ConvertFrom-Json; Check "describe $Instance"
$proj = gcloud compute project-info describe --project $Project --format json | ConvertFrom-Json; Check "project-info describe"
$osl = @($vm.metadata.items) + @($proj.commonInstanceMetadata.items) | Where-Object { $_.key -eq "enable-oslogin" -and "$($_.value)".ToUpper() -eq "TRUE" }
if ($osl) { throw "OS Login is on for this VM or project: metadata ssh keys are ignored there. Ask for the OS Login variant of this setup." }
$ip = $vm.networkInterfaces[0].accessConfigs[0].natIP
if (-not $ip) { throw "The VM has no external address for GitHub to reach" }
Write-Host "VM address: $ip"

Step "Firewall rules that open ssh (port 22): GitHub's machines connect from changing addresses"
gcloud compute firewall-rules list --project $Project --filter "direction=INGRESS AND disabled=false" --format "table(name,sourceRanges.list(),allowed[].map().firewall_rule().list())"
Check "firewall-rules list"
Write-Host "GitHub needs port 22 open to 0.0.0.0/0 (the key is the lock). If ssh is limited to your address or to IAP, the deploy cannot connect." -ForegroundColor Yellow

Step "Making a new ssh key on the VM (the private half goes straight to GitHub, never to a file here)"
# one remote command; no double quotes inside, and `$ keeps PowerShell from expanding the remote shell's variables
$remote = "set -e; d=`$(mktemp -d); ssh-keygen -q -t ed25519 -N '' -C $Comment -f `$d/k; echo USER=`$(whoami); echo PUB=`$(cat `$d/k.pub); echo HOSTKEY=`$(cut -d' ' -f1,2 /etc/ssh/ssh_host_ed25519_key.pub); cat `$d/k; rm -rf `$d"
if ($DryRun) {
  Write-Host "[dry-run] gcloud compute ssh $Instance --command `"$remote`"" -ForegroundColor Yellow
  $user = "<vm user>"; $pub = "ssh-ed25519 AAAA... $Comment"; $hostKey = "ssh-ed25519 AAAA..."; $private = "<private key>"
} else {
  $out = gcloud compute ssh $Instance @sshFlags --command $remote; Check "gcloud compute ssh (make the key)"
  $user = (($out | Where-Object { $_ -like "USER=*" }) -replace '^USER=', '').Trim()
  $pub = (($out | Where-Object { $_ -like "PUB=*" }) -replace '^PUB=', '').Trim()
  $hostKey = (($out | Where-Object { $_ -like "HOSTKEY=*" }) -replace '^HOSTKEY=', '').Trim()
  $begin = [array]::IndexOf($out, ($out | Where-Object { $_ -like "-----BEGIN OPENSSH PRIVATE KEY-----*" } | Select-Object -First 1))
  $end = [array]::IndexOf($out, ($out | Where-Object { $_ -like "-----END OPENSSH PRIVATE KEY-----*" } | Select-Object -First 1))
  if (-not $user -or -not $pub -or -not $hostKey -or $begin -lt 0 -or $end -le $begin) { throw "Could not read the new key from the VM's answer" }
  $private = ($out[$begin..$end] | ForEach-Object { $_.TrimEnd() }) -join "`n"
}
Write-Host "VM user: $user"

Step "Adding the key to the VM's own ssh keys (other keys kept)"
WriteKeys (@(OtherKeys) + @("${user}:$pub"))

Step "Storing the key and the VM's details in GitHub ($Repo)"
if ($DryRun) { Write-Host "[dry-run] gh secret set DEPLOY_SSH_KEY" -ForegroundColor Yellow }
else { gh secret set DEPLOY_SSH_KEY --repo $Repo --body $private; Check "gh secret set DEPLOY_SSH_KEY" }   # --body: a pipe would add CRLF
$private = $null
SetVar "DEPLOY_SSH_USER" $user
SetVar "DEPLOY_SSH_HOST" $ip
SetVar "DEPLOY_KNOWN_HOSTS" "$ip $hostKey"
SetVar "AUTO_DEPLOY" "true"

Write-Host ""
Write-Host "On. The next push to main deploys itself once its images are built (Actions > Deploy)." -ForegroundColor Green
Write-Host "To put main live now: gh workflow run deploy.yml --repo $Repo   (then: gh run watch)"
Write-Host "Roll back to an older commit: gh workflow run deploy.yml --repo $Repo -f sha=<40-character sha>"
Write-Host "Turn it off: .\deploy\gcp\ci_deploy_setup.ps1 -Off"
