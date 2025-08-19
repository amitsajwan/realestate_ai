@echo off
echo 🪟 PropertyAI Windows Quick Start
echo =================================

echo.
echo 📍 Current directory: %CD%
echo 🐍 Python version:
python --version

echo.
echo 📥 Step 1: Pull latest changes...
git pull origin main

echo.
echo 🔧 Step 2: Fix virtual environment...
echo Deactivating current venv...
call deactivate 2>nul

echo Removing corrupted venv...
if exist venv rmdir /s /q venv

echo Creating fresh virtual environment...
python -m venv venv

echo Activating new virtual environment...
call venv\Scripts\activate.bat

echo.
echo 📦 Step 3: Install minimal dependencies...
python -m pip install --upgrade pip
pip install -r requirements-minimal.txt

echo.
echo 🚀 Step 4: Starting PropertyAI backend...
echo ✅ Backend will start on http://localhost:8003
echo 📱 Premium Mobile UX features enabled
echo.

python start.py

pause