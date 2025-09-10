# PropertyAI Backend - FastAPI Server
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "  PropertyAI Backend - FastAPI Server" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting FastAPI server on http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Set-Location "C:\Users\code\realestate_ai\backend"
& .\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
