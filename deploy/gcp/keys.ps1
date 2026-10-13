<#
  One place for the server's service keys: see which are set or empty, then add a missing one or replace an old one.
  No secret passes through chat or git: values are typed hidden here, checked against the service where a check exists, and written
  only into the VM's private deploy/gcp/.env (a backup is kept as .env.bak-keys), then the backend and worker restart.

  Run in your own PowerShell, from the repo root:
      .\deploy\gcp\keys.ps1           # shows every key (set: last 4 characters only; or empty), then lets you pick
      .\deploy\gcp\keys.ps1 -List     # only shows them
      .\deploy\gcp\keys.ps1 -Verify   # checks every key that is set against its service, on the VM (backend/scripts/keys_check.py)
  Without prompts (a script, or a test): -Set "SERPER_API_KEY=...;YOUTUBE_API_KEY=..." (add -SkipCheck to skip the service checks).

  Keys with their own guided script are shown but changed there: the text-AI keys (ai_connect.ps1, which also tests and orders the
  models), Meta (meta_connect.ps1) and WhatsApp (whatsapp_connect.ps1).
  To add a new kind of key, add one line to $Catalog below (name, what it is for, where to get it, and a check if the service has one).
#>
param(
  [switch]$List,
  [switch]$Verify,
  [string]$Set = "",                # "NAME=value;NAME=value": no prompts
  [switch]$SkipCheck,
  [string]$Project   = "trader-502012",
  [string]$Zone      = "asia-south1-a",
  [string]$Instance  = "pune-property",
  [string]$RemoteDir = "app",
  [switch]$Iap
)
$ErrorActionPreference = "Stop"

function Plain($secure) {
  $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}
function ErrText($err) {
  $msg = $err.Exception.Message
  try { $j = $err.ErrorDetails.Message | ConvertFrom-Json; if ($j.error.message) { $msg = "$($j.error.message)" } elseif ($j.message) { $msg = "$($j.message)" } } catch {}
  if ($msg.Length -gt 160) { $msg = $msg.Substring(0, 160) }
  return $msg
}

# ---- the keys ----------------------------------------------------------------------------------------------------------------------
# Check: a script block given the value; it throws when the service refuses the key. File: the value is read from a file you pick
# (stored base64). Owner: another script manages it (shown only).
$Catalog = @(
  @{ Name = "SERPER_API_KEY"; For = "Google search results for hot projects: top projects per area, who markets them"
     Get = "https://serper.dev -> sign up -> API key (2,500 free searches)"
     Check = { param($v) $null = Invoke-RestMethod -Method POST -Uri "https://google.serper.dev/search" -Headers @{ "X-API-KEY" = $v } `
                 -ContentType "application/json" -Body '{"q":"new launch projects in Kharadi Pune","gl":"in","num":1}' -TimeoutSec 30 } }
  @{ Name = "YOUTUBE_API_KEY"; For = "YouTube videos about hot projects (official YouTube Data API)"
     Get = "https://console.cloud.google.com/apis/credentials -> Create credentials -> API key; enable 'YouTube Data API v3'"
     Check = { param($v) $null = Invoke-RestMethod -Uri "https://www.googleapis.com/youtube/v3/search?part=snippet&type=video&maxResults=1&q=Pune%20flats&key=$v" -TimeoutSec 30 } }
  @{ Name = "GOOGLE_TTS_API_KEY"; For = "Reel voice-overs (Google Cloud Text-to-Speech)"
     Get = "https://console.cloud.google.com/apis/credentials -> API key restricted to 'Cloud Text-to-Speech API'"
     Check = { param($v) $null = Invoke-RestMethod -Uri "https://texttospeech.googleapis.com/v1/voices?languageCode=hi-IN&key=$v" -TimeoutSec 30 } }
  @{ Name = "GEMINI_API_KEY"; For = "Gemini (voice and fallback AI)"
     Get = "https://aistudio.google.com/apikey"
     Check = { param($v) $null = Invoke-RestMethod -Uri "https://generativelanguage.googleapis.com/v1beta/models?pageSize=1&key=$v" -TimeoutSec 30 } }
  @{ Name = "GSC_SA_KEY_B64"; For = "Search Console reader (which project pages Google shows)"; File = $true
     Get = "Google Cloud -> IAM -> Service accounts -> Keys -> Add key (JSON); add its email in Search Console as a Restricted user"
     Check = { param($v) $j = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($v)) | ConvertFrom-Json
               if (-not ($j.client_email -and $j.private_key -and $j.token_uri)) { throw "this is not a service-account key file" } } }
  @{ Name = "AI_LLM_API_KEY"; For = "Text AI"; Owner = "ai_connect.ps1" }
  @{ Name = "GROQ_API_KEY"; For = "Text AI (Groq)"; Owner = "ai_connect.ps1" }
  @{ Name = "AI_LLM_FALLBACK_API_KEY"; For = "Text AI fallback"; Owner = "ai_connect.ps1" }
  @{ Name = "AI_STT_API_KEY"; For = "Speech to text"; Owner = "ai_connect.ps1" }
  @{ Name = "AI_VISION_API_KEY"; For = "Photo review (vision)"; Owner = "ai_connect.ps1" }
  @{ Name = "AI_VISION_FALLBACK_API_KEY"; For = "Photo review fallback"; Owner = "ai_connect.ps1" }
  @{ Name = "META_PAGE_ACCESS_TOKEN"; For = "Facebook and Instagram posting"; Owner = "meta_connect.ps1" }
  @{ Name = "WHATSAPP_ACCESS_TOKEN"; For = "WhatsApp"; Owner = "whatsapp_connect.ps1" }
)

$common = @("--project", $Project, "--zone", $Zone); if ($Iap) { $common += "--tunnel-through-iap" }

function Show-Status {
  $names = ($Catalog | ForEach-Object { $_.Name }) -join " "
  # prints "NAME SET abcd" or "NAME EMPTY": only the last 4 characters ever leave the VM
  # no double quotes inside: Windows PowerShell 5.1 splits a native argument at embedded quotes (gcloud: unrecognized arguments)
  $sh = "cd ~/$RemoteDir/deploy/gcp && for k in $names; do v=`$(grep -m1 ^`$k= .env | cut -d= -f2-); " +
        "if [ `${#v} -gt 0 ]; then echo `$k SET `${v: -4}; else echo `$k EMPTY; fi; done"
  $out = & gcloud compute ssh $Instance @common --command $sh
  if ($LASTEXITCODE -ne 0) { throw "could not read the VM's .env" }
  $state = @{}
  foreach ($line in $out) { $p = "$line".Trim() -split " "; if ($p.Count -ge 2) { $state[$p[0]] = $p } }
  Write-Host ""
  for ($i = 0; $i -lt $Catalog.Count; $i++) {
    $k = $Catalog[$i]; $s = $state[$k.Name]
    $tag = if ($s -and $s[1] -eq "SET") { "set (...$($s[2]))" } else { "EMPTY" }
    $color = if ($tag -eq "EMPTY") { "Yellow" } else { "Green" }
    $who = if ($k.Owner) { "   [change with $($k.Owner)]" } else { "" }
    Write-Host ("{0,3}. {1,-26} {2,-14} {3}{4}" -f ($i + 1), $k.Name, $tag, $k.For, $who) -ForegroundColor $color
  }
  Write-Host ""
}

function Test-Keys {
  # runs inside the backend container, which has the .env loaded: the keys are checked where they live and never leave the VM
  Write-Host "==> Checking every key with its service (on the VM)" -ForegroundColor Cyan
  & gcloud compute ssh $Instance @common --command "cd ~/$RemoteDir/deploy/gcp && sudo docker compose exec -T backend python scripts/keys_check.py"
  if ($LASTEXITCODE -eq 0) { Write-Host "All set keys work." -ForegroundColor Green }
  else { Write-Host "Some keys FAILED (see above): replace them with this script, or with the script named next to them." -ForegroundColor Yellow }
}

if ($Verify) { Test-Keys; return }
Write-Host "==> Reading which keys the server has" -ForegroundColor Cyan
Show-Status
if ($List) { return }

$changes = [ordered]@{}
foreach ($pair in ($Set -split ";" | Where-Object { $_ })) {
  $name, $value = $pair -split "=", 2
  $k = $Catalog | Where-Object { $_.Name -eq $name.Trim() }
  if (-not $k -or $k.Owner) { throw "$name is not a key this script sets" }
  $value = "$value".Trim()
  if (-not $value -or $value -match "[\s`"'`$\\]") { throw "$name has an empty or unusable value" }
  if ($k.Check -and -not $SkipCheck) { try { & $k.Check $value } catch { throw "the service refused $($name): $(ErrText $_)" } }
  $changes[$k.Name] = $value
}
while (-not $Set) {
  $pick = Read-Host "Number of a key to add or replace (Enter when done)"
  if (-not $pick) { break }
  $n = 0
  if (-not [int]::TryParse($pick, [ref]$n) -or $n -lt 1 -or $n -gt $Catalog.Count) { Write-Host "  no such number" -ForegroundColor Yellow; continue }
  $k = $Catalog[$n - 1]
  if ($k.Owner) { Write-Host "  $($k.Name) is set by $($k.Owner) (it also tests and configures the service); run that instead." -ForegroundColor Yellow; continue }
  Write-Host "  $($k.For). Get it: $($k.Get)"
  if ($k.File) {
    $path = (Read-Host "  Path to the key file").Trim('"', ' ')
    if (-not (Test-Path $path)) { Write-Host "  file not found" -ForegroundColor Yellow; continue }
    $value = [Convert]::ToBase64String([IO.File]::ReadAllBytes($path))
  } else {
    $value = (Plain (Read-Host "  Paste $($k.Name) (hidden)" -AsSecureString)).Trim()
  }
  if (-not $value) { Write-Host "  empty, skipped" -ForegroundColor Yellow; continue }
  if ($value -match "[\s`"'`$\\]") { Write-Host "  the value has spaces, quotes or `$ in it: not a key, skipped" -ForegroundColor Yellow; continue }
  if ($k.Check) {
    try { & $k.Check $value; Write-Host "  checked with the service: OK" -ForegroundColor Green }
    catch {
      Write-Host "  the service refused it: $(ErrText $_)" -ForegroundColor Yellow
      if ((Read-Host "  Save it anyway? (y/N)") -ne "y") { continue }
    }
  }
  $changes[$k.Name] = $value
  Write-Host "  will save $($k.Name) (...$($value.Substring([Math]::Max(0, $value.Length - 4))))" -ForegroundColor Green
}
if ($changes.Count -eq 0) { Write-Host "Nothing to change."; return }

Write-Host "==> Writing $($changes.Count) key(s) into the VM's private .env" -ForegroundColor Cyan
$lines = $changes.GetEnumerator() | ForEach-Object { "$($_.Key)=$($_.Value)" }
$remoteSh = @'
set -e
cd ~/__DIR__/deploy/gcp
test -f .env || { echo "ERROR: deploy/gcp/.env missing on the VM"; exit 1; }
cp .env .env.bak-keys
chmod 600 .env.bak-keys
for k in $(cut -d= -f1 ~/keys.env); do sed -i "/^$k=/d" .env; done
sed -i -e '$a\' .env
cat ~/keys.env >> .env
chmod 600 .env
rm -f ~/keys.env
sudo docker compose up -d backend worker  # both read the same .env
sleep 15
sudo docker compose ps backend worker --format '{{.Name}} {{.Status}}'
'@ -replace "__DIR__", $RemoteDir
$tmpEnv = Join-Path ([IO.Path]::GetTempPath()) "keys.env"; $tmpSh = Join-Path ([IO.Path]::GetTempPath()) "keys_apply.sh"
try {
  [IO.File]::WriteAllText($tmpEnv, (($lines -join "`n") + "`n"))
  [IO.File]::WriteAllText($tmpSh, ($remoteSh -replace "`r`n", "`n"))
  & gcloud compute scp @common $tmpEnv "${Instance}:keys.env" | Out-Null; if ($LASTEXITCODE -ne 0) { throw "scp of the values failed" }
  & gcloud compute scp @common $tmpSh "${Instance}:keys_apply.sh" | Out-Null; if ($LASTEXITCODE -ne 0) { throw "scp of the script failed" }
  & gcloud compute ssh $Instance @common --command "bash keys_apply.sh; rm -f keys_apply.sh"; if ($LASTEXITCODE -ne 0) { throw "applying on the VM failed" }
} finally {
  Remove-Item $tmpEnv, $tmpSh -ErrorAction SilentlyContinue
}
Write-Host "==> Now" -ForegroundColor Cyan
Show-Status
Test-Keys
Write-Host "Done. The old file is kept on the VM as deploy/gcp/.env.bak-keys." -ForegroundColor Green
