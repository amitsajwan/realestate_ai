<#
  Point the pilot's text AI (listing extraction, Hindi/Marathi descriptions, post polish) at OpenRouter's FREE models.
  Voice stays on Gemini (GEMINI_API_KEY is untouched). No secret passes through chat or git.

  1. Get a key: https://openrouter.ai/keys -> Create key (free; no card needed for :free models).
  2. Run in your own PowerShell, from the repo root:    .\deploy\gcp\openrouter_connect.ps1
     Paste the key when asked (typing is hidden).

  It reads OpenRouter's public model list, tests each free candidate that supports JSON output (a JSON extraction call and a plain
  text call, with timing), and only then writes AI_LLM_BASE_URL / AI_LLM_API_KEY / AI_LISTING_LLM_MODEL (the working models, in order)
  into the VM's private deploy/gcp/.env and restarts the backend. Nothing changes on the server if no model passes.

  Note: free models on OpenRouter may log prompts. We only send public listing text (never phone numbers or buyer data).
#>
param(
  [string[]]$Candidates = @(),      # override the auto-picked list, e.g. -Candidates "qwen/qwen3.8-27b:free"
  [string]$Project   = "trader-502012",
  [string]$Zone      = "asia-south1-a",
  [string]$Instance  = "pune-property",
  [string]$RemoteDir = "app",
  [switch]$Iap
)
$ErrorActionPreference = "Stop"
$base = "https://openrouter.ai/api/v1"

function Plain($secure) {
  $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}
function ErrText($err) {
  $msg = $err.Exception.Message
  try { $j = $err.ErrorDetails.Message | ConvertFrom-Json; if ($j.error.message) { $msg = "$($j.error.message)" } } catch {}
  if ($msg.Length -gt 140) { $msg = $msg.Substring(0, 140) }
  return $msg
}

$key = $env:OPENROUTER_CONNECT_KEY   # testing hook only; normally you are prompted and typing is hidden
if (-not $key) { $key = Plain (Read-Host "Paste your OpenRouter API key (hidden)" -AsSecureString) }
$key = $key.Trim()
if (-not $key) { throw "A key is required" }
$auth = @{ Authorization = "Bearer $key" }

Write-Host "==> Checking the key" -ForegroundColor Cyan
try { $null = Invoke-RestMethod -Uri "$base/auth/key" -Headers $auth -TimeoutSec 30 } catch { throw "OpenRouter rejected the key: $(ErrText $_)" }

if (-not $Candidates) {
  Write-Host "==> Reading the free model list" -ForegroundColor Cyan
  $all = (Invoke-RestMethod -Uri "$base/models" -TimeoutSec 60).data
  $Candidates = @($all | Where-Object {
      $_.id -like "*:free" -and [double]$_.pricing.prompt -eq 0 -and [double]$_.pricing.completion -eq 0 -and
      ($_.supported_parameters -contains "response_format" -or $_.supported_parameters -contains "structured_outputs") -and
      $_.id -notmatch "safety|code|lyria|omni" } |
    Sort-Object { $_.context_length } -Descending | Select-Object -First 8 | ForEach-Object { $_.id })
  $Candidates += "openrouter/free"
}
Write-Host "Candidates: $($Candidates -join ', ')"

$extractSystem = 'Extract real-estate facts. Reply with ONE JSON object using only keys: bhk (number), price_inr (integer rupees; 85 lakh = 8500000), locality, city. Omit unknown keys.'
$passed = @()
foreach ($m in $Candidates) {
  Write-Host "==> Testing $m" -ForegroundColor Cyan
  $t0 = Get-Date
  try {
    $body = @{ model = $m; temperature = 0; response_format = @{ type = "json_object" }
               messages = @(@{ role = "system"; content = $extractSystem }, @{ role = "user"; content = "2 bhk upper kharadi 85 lk pune" }) }
    $r = Invoke-RestMethod -Method POST -Uri "$base/chat/completions" -Headers $auth -ContentType "application/json" -Body ($body | ConvertTo-Json -Depth 8 -Compress) -TimeoutSec 60
    $txt = "$($r.choices[0].message.content)"
    $j = $txt -replace '(?s)^.*?(\{.*\}).*$', '$1' | ConvertFrom-Json
    $ok = ($j.bhk -eq 2) -and ([int64]$j.price_inr -eq 8500000)
    $secs = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
    if (-not $ok) { Write-Host "  JSON parsed but wrong values: $txt" -ForegroundColor Yellow; continue }
    Write-Host "  JSON extraction OK (${secs}s): bhk=$($j.bhk) price=$($j.price_inr) locality=$($j.locality)" -ForegroundColor Green
    if ($secs -gt 25) { Write-Host "  too slow for a listing screen (>25s), skipping" -ForegroundColor Yellow; continue }
    $t1 = Get-Date
    $body2 = @{ model = $m; temperature = 0.4; messages = @(@{ role = "system"; content = "Rewrite the post warmer, keep all numbers and words like INTERESTED unchanged. Output only the post." },
                                                        @{ role = "user"; content = "2 BHK apartment in Kharadi, Pune - Rs 85 Lakh. Comment INTERESTED for details." }) }
    $r2 = Invoke-RestMethod -Method POST -Uri "$base/chat/completions" -Headers $auth -ContentType "application/json" -Body ($body2 | ConvertTo-Json -Depth 8 -Compress) -TimeoutSec 60
    $t = "$($r2.choices[0].message.content)".Trim()
    if ($t -match "85" -and $t -match "INTERESTED") { Write-Host "  text OK ($([math]::Round(((Get-Date) - $t1).TotalSeconds,1))s): $($t.Substring(0, [Math]::Min(90, $t.Length)))" -ForegroundColor Green; $passed += $m }
    else { Write-Host "  text changed a protected fact: $t" -ForegroundColor Yellow }
  } catch { Write-Host "  failed: $(ErrText $_)" -ForegroundColor Yellow }
  Start-Sleep -Seconds 2
}
if (-not $passed) { throw "No free model passed both tests right now (free models are often busy). Nothing was changed on the server. Try again in a few minutes." }
$chain = ($passed | Select-Object -First 5) -join ","
Write-Host "Model order on the server: $chain" -ForegroundColor Green

Write-Host "==> Writing the settings into the VM's private .env" -ForegroundColor Cyan
$lines = @("AI_LLM_BASE_URL=$base", "AI_LLM_API_KEY=$key", "AI_LISTING_LLM_MODEL=$chain")
$remoteSh = @'
set -e
cd ~/__DIR__/deploy/gcp
test -f .env || { echo "ERROR: deploy/gcp/.env missing on the VM"; exit 1; }
cp .env .env.bak-or
chmod 600 .env.bak-or
for k in $(cut -d= -f1 ~/or.env); do sed -i "/^$k=/d" .env; done
sed -i -e '$a\' .env
cat ~/or.env >> .env
chmod 600 .env
rm -f ~/or.env
sudo docker compose up -d backend worker  # the worker reads the same .env (background loops)
sleep 15
sudo docker compose ps backend worker --format '{{.Name}} {{.Status}}'
grep -E '^(AI_STT_PROVIDER|AI_LLM_BASE_URL|AI_LISTING_LLM_MODEL)=' .env
'@ -replace "__DIR__", $RemoteDir
$tmpEnv = Join-Path $env:TEMP "or.env"; $tmpSh = Join-Path $env:TEMP "or_apply.sh"
try {
  [IO.File]::WriteAllText($tmpEnv, (($lines -join "`n") + "`n"))
  [IO.File]::WriteAllText($tmpSh, ($remoteSh -replace "`r`n", "`n"))
  $common = @("--project", $Project, "--zone", $Zone); if ($Iap) { $common += "--tunnel-through-iap" }
  & gcloud compute scp @common $tmpEnv "${Instance}:or.env" | Out-Null; if ($LASTEXITCODE -ne 0) { throw "scp of the values failed" }
  & gcloud compute scp @common $tmpSh "${Instance}:or_apply.sh" | Out-Null; if ($LASTEXITCODE -ne 0) { throw "scp of the script failed" }
  & gcloud compute ssh $Instance @common --command "bash or_apply.sh; rm -f or_apply.sh"; if ($LASTEXITCODE -ne 0) { throw "applying on the VM failed" }
} finally {
  Remove-Item $tmpEnv, $tmpSh -ErrorAction SilentlyContinue
}
Write-Host "Done. Text AI now uses OpenRouter free models ($chain). Voice still uses Gemini." -ForegroundColor Green
