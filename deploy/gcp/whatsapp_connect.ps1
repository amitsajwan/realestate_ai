<#
  Connect the WhatsApp number (Meta test number first) to the pilot server WITHOUT any secret passing through chat or git.

  Run in your own PowerShell, from the repo root:
    .\deploy\gcp\whatsapp_connect.ps1 -PhoneNumberId 123456789012345
    .\deploy\gcp\whatsapp_connect.ps1 -PhoneNumberId 123456789012345 -Live      # replies are really sent (only after testing)

  You are asked for two secrets (typing is hidden):
    1. the permanent access token of the System User (Business Settings -> Users -> System users -> Generate new token)
    2. the App Secret (developers.facebook.com -> PuneProperties app -> App settings -> Basic -> App secret -> Show)

  What it does:
    - checks the token with Meta: reads the phone number's display number and name, and lists the token's permissions
      (whatsapp_business_messaging is required); this also proves the app secret is right
    - makes a new random webhook Verify token and prints ONLY that (you paste it into Meta's webhook settings)
    - optionally subscribes the app to your WhatsApp Business Account (-WabaId), so messages reach the webhook
    - writes WHATSAPP_ENABLED, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN, WHATSAPP_APP_SECRET, WHATSAPP_VERIFY_TOKEN,
      WHATSAPP_OWNER_AGENT_ID (if given) and WHATSAPP_DRY_RUN (true, or false with -Live) into the VM's private deploy/gcp/.env,
      then restarts only the backend.
  It prints no token or secret. Nothing is written to this PC's disk except a short-lived temp file that is deleted straight after.
#>
param(
  [string]$PhoneNumberId = "",
  [string]$WabaId        = "",
  [string]$OwnerAgentId  = "",
  [string]$PublicNumber  = "",   # optional: the number buyers see on the website button (NEXT_PUBLIC_WHATSAPP_NUMBER, needs a frontend rebuild)
  [string]$AppId     = "1072258319113727",
  [string]$Project   = "trader-502012",
  [string]$Zone      = "asia-south1-a",
  [string]$Instance  = "pune-property",
  [string]$RemoteDir = "app",
  [string]$SiteHost  = "34-180-39-243.sslip.io",
  [string]$Version   = "v23.0",
  [switch]$Live,
  [switch]$Iap
)
$ErrorActionPreference = "Stop"

function Plain($secure) {
  $b = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try { [Runtime.InteropServices.Marshal]::PtrToStringBSTR($b) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($b) }
}
function Graph($method, $path, $query, $token) {
  $qs = ($query.GetEnumerator() | ForEach-Object { "$($_.Key)=$([uri]::EscapeDataString([string]$_.Value))" }) -join "&"
  $headers = @{}
  if ($token) { $headers["Authorization"] = "Bearer $token" }
  try { Invoke-RestMethod -Method $method -Uri "https://graph.facebook.com/$Version/${path}?$qs" -Headers $headers -TimeoutSec 30 }
  catch {
    $msg = $_.Exception.Message
    try { $msg = ($_.ErrorDetails.Message | ConvertFrom-Json).error.message } catch {}
    throw "Meta said: $msg"
  }
}

if (-not $PhoneNumberId) { $PhoneNumberId = (Read-Host "Phone number ID (WhatsApp -> API Setup, under the From number)").Trim() }
if ($PhoneNumberId -notmatch '^\d{6,20}$') { throw "The Phone number ID is a long number (digits only), not the phone number itself" }

# Testing hook only: env vars are used when set (normally you are prompted and typing is hidden)
$token  = $env:WA_CONNECT_ACCESS_TOKEN
$secret = $env:WA_CONNECT_APP_SECRET
if (-not $token)  { $token  = Plain (Read-Host "Paste the System User access token (hidden)" -AsSecureString) }
if (-not $secret) { $secret = Plain (Read-Host "Paste the App Secret (hidden)" -AsSecureString) }
$token = $token.Trim(); $secret = $secret.Trim()
if (-not $token -or -not $secret) { throw "Both the token and the app secret are required" }

Write-Host "==> Checking the token against your WhatsApp number" -ForegroundColor Cyan
$info = Graph "GET" $PhoneNumberId @{ fields = "display_phone_number,verified_name,quality_rating" } $token
Write-Host "Number: $($info.display_phone_number)   Name: $($info.verified_name)   Quality: $($info.quality_rating)"

Write-Host "==> Checking the token's permissions (this also checks the app secret)" -ForegroundColor Cyan
$dbg = (Graph "GET" "debug_token" @{ input_token = $token; access_token = "$AppId|$secret" } $null).data
$exp = if ($dbg.expires_at -eq 0) { "never expires" } else { "expires " + [DateTimeOffset]::FromUnixTimeSeconds([int64]$dbg.expires_at).ToString("yyyy-MM-dd") }
Write-Host "valid=$($dbg.is_valid)  $exp"
Write-Host "permissions: $($dbg.scopes -join ', ')"
if (-not $dbg.is_valid) { throw "Meta says the token is not valid" }
if ($dbg.scopes -notcontains "whatsapp_business_messaging") { throw "The token is missing whatsapp_business_messaging. Generate it again with that permission ticked." }
if ($dbg.scopes -notcontains "whatsapp_business_management") { Write-Host "Note: whatsapp_business_management is not ticked (needed for -WabaId and later number changes)." -ForegroundColor Yellow }
if ($dbg.expires_at -ne 0) { Write-Host "This token expires. Use a System User token with 'Never' expiry for the pilot." -ForegroundColor Yellow }

if ($WabaId) {
  Write-Host "==> Subscribing the app to WhatsApp Business Account $WabaId" -ForegroundColor Cyan
  $sub = Graph "POST" "$WabaId/subscribed_apps" @{} $token
  Write-Host "subscribed: $($sub.success)"
}

$bytes = New-Object byte[] 24
[Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$verify = "pp-" + (($bytes | ForEach-Object { $_.ToString("x2") }) -join "")

Write-Host "==> Writing the values into the VM's private .env" -ForegroundColor Cyan
$dry = if ($Live) { "false" } else { "true" }
$lines = @("WHATSAPP_ENABLED=true", "WHATSAPP_PHONE_NUMBER_ID=$PhoneNumberId", "WHATSAPP_ACCESS_TOKEN=$token", "WHATSAPP_APP_SECRET=$secret",
           "WHATSAPP_VERIFY_TOKEN=$verify", "WHATSAPP_GRAPH_VERSION=$Version", "WHATSAPP_DRY_RUN=$dry")
if ($OwnerAgentId) { $lines += "WHATSAPP_OWNER_AGENT_ID=$OwnerAgentId" }
if ($PublicNumber) { $lines += "NEXT_PUBLIC_WHATSAPP_NUMBER=$(($PublicNumber -replace '\D', ''))" }
$remoteSh = @'
set -e
cd ~/__DIR__/deploy/gcp
test -f .env || { echo "ERROR: deploy/gcp/.env missing on the VM"; exit 1; }
cp .env .env.bak-whatsapp
chmod 600 .env.bak-whatsapp
for k in $(cut -d= -f1 ~/wa.env); do sed -i "/^$k=/d" .env; done
sed -i -e '$a\' .env
cat ~/wa.env >> .env
chmod 600 .env
rm -f ~/wa.env
sudo docker compose up -d backend
sleep 15
sudo docker compose ps backend --format '{{.Name}} {{.Status}}'
grep -c '^WHATSAPP_ACCESS_TOKEN=' .env | sed 's/^/token lines in .env: /'
grep '^WHATSAPP_DRY_RUN=' .env
grep -q '^WHATSAPP_OWNER_AGENT_ID=' .env || echo 'NOTE: WHATSAPP_OWNER_AGENT_ID is not set; chats will use INTEREST_OWNER_AGENT_ID / ENGAGE_OWNER_AGENT_ID'
'@ -replace "__DIR__", $RemoteDir
$tmpEnv = Join-Path $env:TEMP "wa.env"; $tmpSh = Join-Path $env:TEMP "wa_apply.sh"
try {
  [IO.File]::WriteAllText($tmpEnv, (($lines -join "`n") + "`n"))
  [IO.File]::WriteAllText($tmpSh, ($remoteSh -replace "`r`n", "`n"))
  $common = @("--project", $Project, "--zone", $Zone); if ($Iap) { $common += "--tunnel-through-iap" }
  & gcloud compute scp @common $tmpEnv "${Instance}:wa.env" | Out-Null; if ($LASTEXITCODE -ne 0) { throw "scp of the values failed" }
  & gcloud compute scp @common $tmpSh "${Instance}:wa_apply.sh" | Out-Null; if ($LASTEXITCODE -ne 0) { throw "scp of the script failed" }
  & gcloud compute ssh $Instance @common --command "bash wa_apply.sh; rm -f wa_apply.sh"; if ($LASTEXITCODE -ne 0) { throw "applying on the VM failed" }
} finally {
  Remove-Item $tmpEnv, $tmpSh -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "Done. Now in Meta (WhatsApp -> Configuration -> Webhook -> Edit):" -ForegroundColor Green
Write-Host "  Callback URL : https://$SiteHost/api/v1/whatsapp/webhook"
Write-Host "  Verify token : $verify"
Write-Host "Then Verify and save, and subscribe to the 'messages' field."
Write-Host "Reply mode is the WHATSAPP_DRY_RUN value printed above: true = test only (nothing is sent), false = replies are sent."
