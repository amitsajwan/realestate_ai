# PowerShell script to automate Playwright browser path setup and installation
$browserPath = "C:\Users\code\playwright-browsers"
$env:PLAYWRIGHT_BROWSERS_PATH = $browserPath
Write-Host "Setting PLAYWRIGHT_BROWSERS_PATH to $browserPath"

# Create the directory if it doesn't exist
if (!(Test-Path $browserPath)) {
    New-Item -ItemType Directory -Path $browserPath | Out-Null
    Write-Host "Created browser path directory: $browserPath"
}

# Install Playwright browsers
Write-Host "Installing Playwright browsers..."
npx playwright install
Write-Host "Playwright browser installation complete."
