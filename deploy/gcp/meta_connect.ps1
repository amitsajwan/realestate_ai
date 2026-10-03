<#
  Connect the Facebook Page (and linked Instagram) to the pilot server WITHOUT any secret passing through chat or git.

  Run in your own PowerShell, from the repo root:
    .\deploy\gcp\meta_connect.ps1

  You are asked for two secrets (typing is hidden):
    1. the short-lived User token from Graph API Explorer (the long string in the Access Token box)
    2. the App Secret (developers.facebook.com -> your app -> App settings -> Basic -> App secret -> Show)

  What it does:
    - exchanges the User token for a long-lived one, then reads the Page access token of your Page
      (a Page token made from a long-lived User token does not expire)
    - checks the token with Meta (valid, expiry, permissions) and finds the linked Instagram business account id
    - writes META_PAGE_ID, META_PAGE_ACCESS_TOKEN, META_IG_BUSINESS_ID (if linked) and PUBLIC_MEDIA_BASE_URL into the VM's private
      deploy/gcp/.env (SOCIAL_DRY_RUN=true is set only if it is not already there), then restarts only the backend.
  It prints no secret. Nothing is written to this PC's disk except a short-lived temp file that is deleted straight after.
#>
param(
  [string]$AppId     = "1072258319113727",
  [string]$PageId    = "1361466343718313",
  [string]$Project   = "trader-502012",
  [string]$Zone      = "asia-south1-a",
  [string]$Instance  = "pune-property",
  [string]$RemoteDir = "app",
  [string]$MediaBase = "https://34-180-39-243.sslip.io",
  [string]$Version   = "v23.0",
  [switch]$Iap
)
$ErrorActionPreference = "Stop"

function Plain($secure) {
  $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}
function Graph($path, $query) {
  $qs = ($query.GetEnumerator() | ForEach-Object { "$($_.Key)=$([uri]::EscapeDataString([string]$_.Value))" }) -join "&"
  try { Invoke-RestMethod -Uri "https://graph.facebook.com/$Version/${path}?$qs" -TimeoutSec 30 }
  catch {
    $msg = $_.Exception.Message
    try { $msg = ($_.ErrorDetails.Message | ConvertFrom-Json).error.message } catch {}
    throw "Meta said: $msg"
  }
}

# Testing hook only: env vars are used when set (normally you are prompted and typing is hidden)
$userTok = $env:META_CONNECT_USER_TOKEN
$secret  = $env:META_CONNECT_APP_SECRET
if (-not $userTok) { $userTok = Plain (Read-Host "Paste the User token from Graph API Explorer (hidden)" -AsSecureString) }
if (-not $secret)  { $secret  = Plain (Read-Host "Paste the App Secret (hidden)" -AsSecureString) }
$userTok = $userTok.Trim(); $secret = $secret.Trim()
if (-not $userTok -or -not $secret) { throw "Both the token and the app secret are required" }

Write-Host "==> Exchanging for a long-lived User token" -ForegroundColor Cyan
$ex = Graph "oauth/access_token" @{ grant_type = "fb_exchange_token"; client_id = $AppId; client_secret = $secret; fb_exchange_token = $userTok }
$longUser = $ex.access_token
if (-not $longUser) { throw "No token came back from the exchange" }

Write-Host "==> Reading your Page and its Page token" -ForegroundColor Cyan
$accts = Graph "me/accounts" @{ fields = "id,name,access_token,instagram_business_account"; limit = 100; access_token = $longUser }
$page = $accts.data | Where-Object { $_.id -eq $PageId } | Select-Object -First 1
if (-not $page) { throw "Page $PageId is not in the list. Regenerate the token in Graph API Explorer and opt in to the Avasetu page." }
$pageTok = $page.access_token
Write-Host "Page found: $($page.name) ($($page.id))"

Write-Host "==> Checking the Page token with Meta" -ForegroundColor Cyan
$dbg = (Graph "debug_token" @{ input_token = $pageTok; access_token = "$AppId|$secret" }).data
$exp = if ($dbg.expires_at -eq 0) { "never expires" } else { "expires " + [DateTimeOffset]::FromUnixTimeSeconds([int64]$dbg.expires_at).ToString("yyyy-MM-dd") }
Write-Host "valid=$($dbg.is_valid)  $exp"
Write-Host "permissions: $($dbg.scopes -join ', ')"
if (-not $dbg.is_valid) { throw "Meta says the Page token is not valid" }
foreach ($need in "pages_manage_posts", "pages_read_engagement") { if ($dbg.scopes -notcontains $need) { Write-Host "MISSING permission: $need (add it in Graph API Explorer and run this again)" -ForegroundColor Yellow } }

$igId = if ($page.instagram_business_account) { $page.instagram_business_account.id } else { "" }
if ($igId) { Write-Host "Instagram business account linked: $igId" } else { Write-Host "No Instagram account linked to the Page yet (Facebook posting will work; add Instagram later and re-run)." -ForegroundColor Yellow }

Write-Host "==> Writing the values into the VM's private .env" -ForegroundColor Cyan
$lines = @("META_PAGE_ID=$PageId", "META_PAGE_ACCESS_TOKEN=$pageTok", "PUBLIC_MEDIA_BASE_URL=$MediaBase")
if ($igId) { $lines += "META_IG_BUSINESS_ID=$igId" }
$remoteSh = @'
set -e
cd ~/__DIR__/deploy/gcp
test -f .env || { echo "ERROR: deploy/gcp/.env missing on the VM"; exit 1; }
cp .env .env.bak-meta
chmod 600 .env.bak-meta
for k in $(cut -d= -f1 ~/meta.env); do sed -i "/^$k=/d" .env; done
sed -i -e '$a\' .env
cat ~/meta.env >> .env
grep -q '^SOCIAL_DRY_RUN=' .env || echo 'SOCIAL_DRY_RUN=true' >> .env
chmod 600 .env
rm -f ~/meta.env
sudo docker compose up -d backend worker  # the worker reads the same .env (background loops)
sleep 15
sudo docker compose ps backend worker --format '{{.Name}} {{.Status}}'
grep -c '^META_PAGE_ACCESS_TOKEN=' .env | sed 's/^/token lines in .env: /'
grep '^SOCIAL_DRY_RUN=' .env
'@ -replace "__DIR__", $RemoteDir
$tmpEnv = Join-Path $env:TEMP "meta.env"; $tmpSh = Join-Path $env:TEMP "meta_apply.sh"
try {
  [IO.File]::WriteAllText($tmpEnv, (($lines -join "`n") + "`n"))
  [IO.File]::WriteAllText($tmpSh, ($remoteSh -replace "`r`n", "`n"))
  $common = @("--project", $Project, "--zone", $Zone); if ($Iap) { $common += "--tunnel-through-iap" }
  & gcloud compute scp @common $tmpEnv "${Instance}:meta.env" | Out-Null; if ($LASTEXITCODE -ne 0) { throw "scp of the values failed" }
  & gcloud compute scp @common $tmpSh "${Instance}:meta_apply.sh" | Out-Null; if ($LASTEXITCODE -ne 0) { throw "scp of the script failed" }
  & gcloud compute ssh $Instance @common --command "bash meta_apply.sh; rm -f meta_apply.sh"; if ($LASTEXITCODE -ne 0) { throw "applying on the VM failed" }
} finally {
  Remove-Item $tmpEnv, $tmpSh -ErrorAction SilentlyContinue
}
Write-Host "Done. Meta is connected. Posting mode is the SOCIAL_DRY_RUN value printed above: true = test only, false = posts go public." -ForegroundColor Green
