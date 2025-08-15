param(
    [switch]$All
)
$ErrorActionPreference = 'Stop'

# Standard artifact directories
$paths = @('.pytest_cache','playwright-report','test-results')
foreach ($p in $paths) {
  if (Test-Path $p) { Remove-Item -Recurse -Force $p; Write-Host "Removed $p" } else { Write-Host "Not found $p" }
}

# Remove all __pycache__ folders recursively
$pycaches = Get-ChildItem -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue
if ($pycaches) {
  $pycaches | Remove-Item -Recurse -Force
  Write-Host "Removed __pycache__"
} else {
  Write-Host "No __pycache__ found"
}

# Optional: deep clean (e.g., coverage, dist) if -All is specified
if ($All) {
  $deep = @('htmlcov','coverage.xml','dist','build','.coverage')
  foreach ($d in $deep) { if (Test-Path $d) { Remove-Item -Recurse -Force $d; Write-Host "Removed $d" } }
}
