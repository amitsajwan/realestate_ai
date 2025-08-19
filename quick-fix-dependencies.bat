@echo off
echo 🔧 Quick Fix for Backend Dependencies
echo =====================================

echo.
echo 📍 Current directory: %CD%
echo 🐍 Python version:
python --version

echo.
echo 🔍 Checking virtual environment...
if defined VIRTUAL_ENV (
    echo ✅ Virtual environment active: %VIRTUAL_ENV%
) else (
    echo ⚠️  Virtual environment not active - activating...
    call venv\Scripts\activate.bat
)

echo.
echo 📦 Installing missing dependencies...
echo Installing pydantic-settings...
pip install pydantic-settings==2.1.0

echo Installing other key dependencies...
pip install groq==0.4.1
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install python-dotenv==1.0.0

echo.
echo 🧪 Testing backend startup...
echo Starting PropertyAI backend...
python start.py

echo.
echo 🎉 If you see "Uvicorn running on http://0.0.0.0:8003" above, the fix worked!
echo.
echo 📱 Next steps:
echo 1. Keep this terminal open (backend running)
echo 2. Open new terminal
echo 3. cd refactoring/mobile-app
echo 4. ./start-app.sh (or: npx expo start)
echo.
echo 🌟 Your premium mobile CRM will then be ready to test!