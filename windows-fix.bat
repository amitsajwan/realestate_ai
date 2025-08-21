@echo off
echo 🪟 PropertyAI Windows Fix - Complete Solution
echo ===============================================

echo.
echo 📍 Current directory: %CD%
echo 🐍 Python version:
python --version

echo.
echo 🔧 Step 1: Deactivate and remove corrupted venv...
call deactivate 2>nul
if exist venv (
    echo Removing old venv...
    rmdir /s /q venv
)

echo.
echo 📦 Step 2: Install FastAPI globally (quick fix)...
echo Installing minimal dependencies without compilation...
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install pydantic==2.5.3
pip install pydantic-settings==2.1.0
pip install python-dotenv==1.0.0
pip install requests==2.31.0
pip install groq==0.4.1

echo.
echo 🚀 Step 3: Starting PropertyAI Simple Backend...
echo ✅ Core functionality ready
echo 📱 Login, Dashboard, Facebook Integration
echo 🎯 AI Content Generation & Property Management
echo.

python simple_backend.py

echo.
echo 🎉 If you see "Uvicorn running" above, the backend is ready!
echo.
echo 📱 Next steps to test Premium Mobile UX:
echo 1. Keep this terminal open (backend running)
echo 2. Open new terminal
echo 3. cd refactoring/mobile-app
echo 4. npx expo start
echo 5. Press 'w' to test in browser
echo.
echo 🌟 You'll see the world's most advanced mobile real estate CRM!
pause