<#
  Configure Groq as the primary text/voice provider and OpenRouter as its independent text fallback.
  OpenRouter free models are probed with the supplied key and working models are ordered first.
  Gemini fallback is disabled because a stale/invalid key causes pointless 401s.
  No secret passes through chat or git.

  1. Create fresh keys at https://console.groq.com/keys and https://openrouter.ai/keys.
  2. Run from the repo root; both keys are requested with hidden input.
#>
param(
  [string[]]$Models = @("openai/gpt-oss-120b", "openai/gpt-oss-20b"),
  [string]$Project = "trader-502012",
  [string]$Zone = "asia-south1-a",
  [string]$Instance = "pune-property",
  [string]$RemoteDir = "app",
  [switch]$Iap
)
$ErrorActionPreference = "Stop"
$base = "https://api.groq.com/openai/v1"
$routerBase = "https://openrouter.ai/api/v1"

function Plain($secure) {
  $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}
function ErrText($err) {
  $msg = $err.Exception.Message
  try {
    $j = $err.ErrorDetails.Message | ConvertFrom-Json
    if ($j.error.message) { $msg = $j.error.message }
  } catch {}
  if ($msg.Length -gt 160) { $msg = $msg.Substring(0, 160) }
  return $msg
}

$groqKey = $env:GROQ_CONNECT_KEY   # testing hook only; normally prompted with hidden input
if (-not $groqKey) { $groqKey = Plain (Read-Host "Paste your NEW Groq API key (hidden)" -AsSecureString) }
$groqKey = $groqKey.Trim()
if (-not $groqKey) { throw "A Groq key is required" }
$groqAuth = @{ Authorization = "Bearer $groqKey" }

$routerKey = $env:OPENROUTER_CONNECT_KEY   # testing hook only; normally prompted with hidden input
if (-not $routerKey) { $routerKey = Plain (Read-Host "Paste your NEW OpenRouter API key (hidden)" -AsSecureString) }
$routerKey = $routerKey.Trim()
if (-not $routerKey) { throw "An OpenRouter key is required" }
$routerAuth = @{ Authorization = "Bearer $routerKey" }

Write-Host "==> Checking Groq key" -ForegroundColor Cyan
try { $null = Invoke-RestMethod -Uri "$base/models" -Headers $groqAuth -TimeoutSec 30 }
catch { throw "Groq rejected the key: $(ErrText $_)" }

$passed = @()
foreach ($m in $Models) {
  Write-Host "==> Testing $m with a JSON extraction request" -ForegroundColor Cyan
  try {
    $body = @{ model = $m; temperature = 0; response_format = @{ type = "json_object" }
               messages = @(@{ role = "system"; content = 'Reply with one JSON object with key bhk (number).' },
                            @{ role = "user"; content = "2 bhk upper kharadi 85 lakh" }) }
    $r = Invoke-RestMethod -Method POST -Uri "$base/chat/completions" -Headers $groqAuth -ContentType "application/json" `
      -Body ($body | ConvertTo-Json -Depth 8 -Compress) -TimeoutSec 45
    $result = "$($r.choices[0].message.content)" | ConvertFrom-Json
    if ($result.bhk -ne 2) { throw "model returned invalid test JSON" }
    Write-Host "  OK" -ForegroundColor Green
    $passed += $m
    if ($passed.Count -ge 3) { break }
  } catch { Write-Host "  failed: $(ErrText $_)" -ForegroundColor Yellow }
}
if (-not $passed) { throw "No Groq model passed the test. Nothing was changed on the server." }
$groqPick = $passed -join ","
Write-Host "Groq primary model order: $groqPick" -ForegroundColor Green

Write-Host "==> Checking OpenRouter key and discovering free fallback models" -ForegroundColor Cyan
try {
  $null = Invoke-RestMethod -Uri "$routerBase/auth/key" -Headers $routerAuth -TimeoutSec 30
  $available = (Invoke-RestMethod -Uri "$routerBase/models" -Headers $routerAuth -TimeoutSec 60).data
} catch { throw "OpenRouter rejected the key or model-list request failed: $(ErrText $_)" }
$routerCandidates = @($available | Where-Object {
    $_.id -like "*:free" -and [double]$_.pricing.prompt -eq 0 -and [double]$_.pricing.completion -eq 0 -and
    ($_.supported_parameters -contains "response_format" -or $_.supported_parameters -contains "structured_outputs") -and
    $_.id -notmatch "safety|code|lyria|omni" } |
  Sort-Object { $_.context_length } -Descending | Select-Object -First 5 | ForEach-Object { $_.id })
$routerCandidates += "openrouter/free"
$routerCandidates = @($routerCandidates | Select-Object -Unique)
Write-Host "Testing OpenRouter candidates: $($routerCandidates -join ', ')" -ForegroundColor Cyan
$routerPassed = @()
foreach ($m in $routerCandidates) {
  Write-Host "==> Testing OpenRouter $m" -ForegroundColor Cyan
  try {
    $body = @{ model = $m; temperature = 0; response_format = @{ type = "json_object" }
               messages = @(@{ role = "system"; content = 'Reply with one JSON object with key bhk (number).' },
                            @{ role = "user"; content = "2 bhk upper kharadi 85 lakh" }) }
    $r = Invoke-RestMethod -Method POST -Uri "$routerBase/chat/completions" -Headers $routerAuth -ContentType "application/json" `
      -Body ($body | ConvertTo-Json -Depth 8 -Compress) -TimeoutSec 45
    $result = "$($r.choices[0].message.content)" | ConvertFrom-Json
    if ($result.bhk -ne 2) { throw "model returned invalid test JSON" }
    Write-Host "  OK" -ForegroundColor Green
    $routerPassed += $m
    if ($routerPassed.Count -ge 3) { break }
  } catch { Write-Host "  failed: $(ErrText $_)" -ForegroundColor Yellow }
}
if (-not $routerPassed) { throw "No OpenRouter free model passed the live test. Nothing was changed on the server." }
$routerOrder = @($routerPassed) + @($routerCandidates | Where-Object { $routerPassed -notcontains $_ })
$routerPick = $routerOrder -join ","
Write-Host "OpenRouter fallback model order: $routerPick" -ForegroundColor Green

Write-Host "==> Writing the settings into the VM's private .env" -ForegroundColor Cyan
$lines = @("AI_LLM_BASE_URL=$base", "AI_LLM_API_KEY=$groqKey", "AI_LISTING_LLM_MODEL=$groqPick", "AI_LLM_FALLBACK_BASE_URL=$routerBase", "AI_LLM_FALLBACK_API_KEY=$routerKey", "AI_LLM_PROVIDER_FALLBACK_MODEL=$routerPick", "AI_LLM_FALLBACK=off", "AI_STT_PROVIDER=groq", "AI_STT_BASE_URL=$base", "AI_STT_API_KEY=$groqKey")
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
grep -E '^(AI_LLM_BASE_URL|AI_LISTING_LLM_MODEL|AI_LLM_FALLBACK_BASE_URL|AI_LLM_PROVIDER_FALLBACK_MODEL|AI_LLM_FALLBACK|AI_STT_PROVIDER|AI_STT_BASE_URL)=' .env
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
Write-Host "Done. Groq ($groqPick) is primary; OpenRouter is the text fallback; Groq handles voice notes." -ForegroundColor Green
