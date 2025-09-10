@echo off
title PropertyAI Backend - FastAPI Server
echo ================================================================================
echo   PropertyAI Backend - FastAPI Server
echo ================================================================================
echo.
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
cd /d "C:\Users\code\realestate_ai\backend"
call .venv\Scripts\activate.bat
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
