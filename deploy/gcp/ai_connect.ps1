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
if ($Model) { $pick = $Model } elseif ($flash) { $pick = $flash[0].Id } else { throw "No gemini-N.M-flash model is available to this key; pass -Model <id>" }
Write-Host "Flash models available: $((($flash | Select-Object -First 5).Id) -join ', ')"
Write-Host "Using: $pick"

Write-Host "==> Test 1: text (JSON reply, the way listing extraction uses it)" -ForegroundColor Cyan
$chat = @{ model = $pick; temperature = 0; response_format = @{ type = "json_object" }
           messages = @(@{ role = "system"; content = 'Reply with one JSON object with key bhk (number).' }, @{ role = "user"; content = "2 bhk upper kharadi 85 lakh" }) }
try {
  $r = Invoke-RestMethod -Method POST -Uri "$base/openai/chat/completions" -Headers @{ Authorization = "Bearer $key" } -ContentType "application/json" -Body ($chat | ConvertTo-Json -Depth 8 -Compress) -TimeoutSec 60
  Write-Host "text OK: $($r.choices[0].message.content)" -ForegroundColor Green
} catch { throw "Text test failed: $(ErrText $_)" }

Write-Host "==> Test 2: audio (1 second of silence; proves audio is allowed on your free tier)" -ForegroundColor Cyan
$rate = 16000; $n = $rate; $ms = New-Object IO.MemoryStream; $bw = New-Object IO.BinaryWriter($ms)
$bw.Write([Text.Encoding]::ASCII.GetBytes("RIFF")); $bw.Write([int](36 + 2 * $n)); $bw.Write([Text.Encoding]::ASCII.GetBytes("WAVEfmt "))
$bw.Write([int]16); $bw.Write([int16]1); $bw.Write([int16]1); $bw.Write([int]$rate); $bw.Write([int]($rate * 2)); $bw.Write([int16]2); $bw.Write([int16]16)
$bw.Write([Text.Encoding]::ASCII.GetBytes("data")); $bw.Write([int](2 * $n)); $bw.Write((New-Object byte[] (2 * $n))); $bw.Flush()
$wav = [Convert]::ToBase64String($ms.ToArray())
$aud = @{ contents = @(@{ parts = @(@{ text = "Transcribe this audio. If there is no speech, output nothing." }, @{ inline_data = @{ mime_type = "audio/wav"; data = $wav } }) }) }
$null = Call POST "$base/models/${pick}:generateContent" $key $aud
Write-Host "audio OK: Gemini accepted an audio request on your key" -ForegroundColor Green

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
