<#
  Switch the pilot's listing AI (text extraction/translation AND voice notes) to Google Gemini's free tier.
  No secret passes through chat or git.

  1. Get a free key (no card): https://aistudio.google.com/apikey  -> "Create API key" (sign in with any Google account).
  2. Run in your own PowerShell, from the repo root:    .\deploy\gcp\ai_connect.ps1
     Paste the key when asked (typing is hidden).

  It checks the key, picks the newest Gemini Flash model your key can use, PROVES that text AND audio both work on your free tier,
  and only then writes these into the VM's private deploy/gcp/.env and restarts the backend:
     GEMINI_API_KEY, AI_STT_PROVIDER=gemini, AI_GEMINI_STT_MODEL, AI_LLM_BASE_URL, AI_LLM_API_KEY, AI_LISTING_LLM_MODEL
#>
param(
  [string]$Model     = "",          # leave empty to auto-pick the newest gemini-N.M-flash
  [string]$Project   = "trader-502012",
  [string]$Zone      = "asia-south1-a",
  [string]$Instance  = "pune-property",
  [string]$RemoteDir = "app",
  [switch]$Iap
)
$ErrorActionPreference = "Stop"
$base = "https://generativelanguage.googleapis.com/v1beta"

function Plain($secure) {
  $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}
function ErrText($err) {
  $msg = $err.Exception.Message
  try {
    $j = $err.ErrorDetails.Message | ConvertFrom-Json
    if ($j -is [array]) { $j = $j[0] }
    if ($j.error.message) { $msg = $j.error.message }
  } catch {}
  return $msg
}
function Call($method, $url, $key, $body) {
  $h = @{ "x-goog-api-key" = $key }
  try {
    if ($body) { Invoke-RestMethod -Method $method -Uri $url -Headers $h -ContentType "application/json" -Body ($body | ConvertTo-Json -Depth 12 -Compress) -TimeoutSec 60 }
    else { Invoke-RestMethod -Method $method -Uri $url -Headers $h -TimeoutSec 60 }
  } catch { throw "Google said: $(ErrText $_)" }
}

$key = $env:GEMINI_CONNECT_KEY   # testing hook only; normally you are prompted and typing is hidden
if (-not $key) { $key = Plain (Read-Host "Paste your Gemini API key (hidden)" -AsSecureString) }
$key = $key.Trim()
if (-not $key) { throw "A key is required" }

Write-Host "==> Checking the key and finding models" -ForegroundColor Cyan
$models = (Call GET "$base/models?pageSize=200" $key $null).models
$flash = $models | Where-Object { $_.name -match '^models/gemini-(\d+(\.\d+)?)-flash$' -and ($_.supportedGenerationMethods -contains "generateContent") } |
  ForEach-Object { [pscustomobject]@{ Id = $_.name -replace '^models/', ''; Ver = [version]([regex]::Match($_.name, 'gemini-(\d+(\.\d+)?)-flash').Groups[1].Value) } } |
  Sort-Object Ver -Descending
if ($Model) { $candidates = @($Model) } elseif ($flash) { $candidates = @($flash | Select-Object -First 5 | ForEach-Object { $_.Id }) } else { throw "No gemini-N.M-flash model is available to this key; pass -Model <id>" }
Write-Host "Flash models available: $($candidates -join ', ')"

# A brand-new model is often "503 unavailable" on the free tier; try each candidate (twice) and keep the first that passes both tests.
function TryText($m) {
  $chat = @{ model = $m; temperature = 0; response_format = @{ type = "json_object" }
             messages = @(@{ role = "system"; content = 'Reply with one JSON object with key bhk (number).' }, @{ role = "user"; content = "2 bhk upper kharadi 85 lakh" }) }
  for ($i = 1; $i -le 2; $i++) {
    try {
      $r = Invoke-RestMethod -Method POST -Uri "$base/openai/chat/completions" -Headers @{ Authorization = "Bearer $key" } -ContentType "application/json" -Body ($chat | ConvertTo-Json -Depth 8 -Compress) -TimeoutSec 60
      return @{ ok = $true; note = "$($r.choices[0].message.content)" }
    } catch { $last = ErrText $_; Start-Sleep -Seconds 3 }
  }
  return @{ ok = $false; note = $last }
}
$rate = 16000; $n = $rate; $ms = New-Object IO.MemoryStream; $bw = New-Object IO.BinaryWriter($ms)
$bw.Write([Text.Encoding]::ASCII.GetBytes("RIFF")); $bw.Write([int](36 + 2 * $n)); $bw.Write([Text.Encoding]::ASCII.GetBytes("WAVEfmt "))
$bw.Write([int]16); $bw.Write([int16]1); $bw.Write([int16]1); $bw.Write([int]$rate); $bw.Write([int]($rate * 2)); $bw.Write([int16]2); $bw.Write([int16]16)
$bw.Write([Text.Encoding]::ASCII.GetBytes("data")); $bw.Write([int](2 * $n)); $bw.Write((New-Object byte[] (2 * $n))); $bw.Flush()
$wav = [Convert]::ToBase64String($ms.ToArray())
$aud = @{ contents = @(@{ parts = @(@{ text = "Transcribe this audio. If there is no speech, output nothing." }, @{ inline_data = @{ mime_type = "audio/wav"; data = $wav } }) }) }
function TryAudio($m) {
  for ($i = 1; $i -le 2; $i++) {
    try {
      Invoke-RestMethod -Method POST -Uri "$base/models/${m}:generateContent" -Headers @{ "x-goog-api-key" = $key } -ContentType "application/json" -Body ($aud | ConvertTo-Json -Depth 12 -Compress) -TimeoutSec 60 | Out-Null
      return @{ ok = $true; note = "accepted" }
    } catch { $last = ErrText $_; Start-Sleep -Seconds 3 }
  }
  return @{ ok = $false; note = $last }
}

$passed = @()
$audioNote = ""
foreach ($m in $candidates) {
  Write-Host "==> Testing $m (text, then audio with 1 second of silence)" -ForegroundColor Cyan
  $t = TryText $m
  if (-not $t.ok) { Write-Host "  text failed: $($t.note)" -ForegroundColor Yellow; continue }
  Write-Host "  text OK: $($t.note)" -ForegroundColor Green
  $a = TryAudio $m
  if (-not $a.ok) { Write-Host "  audio failed: $($a.note)" -ForegroundColor Yellow; $audioNote = $a.note; continue }
  Write-Host "  audio OK: Gemini accepted an audio request on your key" -ForegroundColor Green
  $passed += $m
  if ($passed.Count -ge 3) { break }
}
if (-not $passed) { throw "No candidate model passed both the text and audio tests (last audio message: '$audioNote'). Nothing was changed on the server. Try again in a few minutes, or tell Claude the messages above." }
# The free tier gives every model its own small DAILY quota, so the server tries them in this order and moves on when one is used up or busy.
# Models that did not pass today (for example quota already used) stay at the end of the list; they recover tomorrow and a retired one just fails over.
$chain = @($passed) + @($candidates | Where-Object { $passed -notcontains $_ })
$pick = $chain -join ","
Write-Host "Model order on the server: $pick"

Write-Host "==> Writing the settings into the VM's private .env" -ForegroundColor Cyan
$lines = @("GEMINI_API_KEY=$key", "AI_STT_PROVIDER=gemini", "AI_GEMINI_STT_MODEL=$pick", "AI_LLM_BASE_URL=$base/openai", "AI_LLM_API_KEY=$key", "AI_LISTING_LLM_MODEL=$pick")
$remoteSh = @'
set -e
cd ~/__DIR__/deploy/gcp
test -f .env || { echo "ERROR: deploy/gcp/.env missing on the VM"; exit 1; }
cp .env .env.bak-ai
chmod 600 .env.bak-ai
for k in $(cut -d= -f1 ~/ai.env); do sed -i "/^$k=/d" .env; done
sed -i -e '$a\' .env
cat ~/ai.env >> .env
chmod 600 .env
rm -f ~/ai.env
sudo docker compose up -d backend
sleep 15
sudo docker compose ps backend --format '{{.Name}} {{.Status}}'
grep -E '^(AI_STT_PROVIDER|AI_GEMINI_STT_MODEL|AI_LLM_BASE_URL|AI_LISTING_LLM_MODEL)=' .env
'@ -replace "__DIR__", $RemoteDir
$tmpEnv = Join-Path $env:TEMP "ai.env"; $tmpSh = Join-Path $env:TEMP "ai_apply.sh"
try {
  [IO.File]::WriteAllText($tmpEnv, (($lines -join "`n") + "`n"))
  [IO.File]::WriteAllText($tmpSh, ($remoteSh -replace "`r`n", "`n"))
  $common = @("--project", $Project, "--zone", $Zone); if ($Iap) { $common += "--tunnel-through-iap" }
  & gcloud compute scp @common $tmpEnv "${Instance}:ai.env" | Out-Null; if ($LASTEXITCODE -ne 0) { throw "scp of the values failed" }
  & gcloud compute scp @common $tmpSh "${Instance}:ai_apply.sh" | Out-Null; if ($LASTEXITCODE -ne 0) { throw "scp of the script failed" }
  & gcloud compute ssh $Instance @common --command "bash ai_apply.sh; rm -f ai_apply.sh"; if ($LASTEXITCODE -ne 0) { throw "applying on the VM failed" }
} finally {
  Remove-Item $tmpEnv, $tmpSh -ErrorAction SilentlyContinue
}
Write-Host "Done. Listing AI and voice now use Gemini ($pick)." -ForegroundColor Green
