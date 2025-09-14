@echo off
echo 🚀 PropertyAI Quick Start for Windows
echo =====================================

echo.
echo 📋 Checking prerequisites...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✅ Python found

:: Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js not found. Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)
echo ✅ Node.js found

:: Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Git not found. Please install Git from https://git-scm.com/downloads
    pause
    exit /b 1
)
echo ✅ Git found

echo.
echo 🔧 Setting up backend...

:: Navigate to backend directory
cd backend

:: Create virtual environment
echo Creating Python virtual environment...
python -m venv venv

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

:: Create environment file
echo Creating environment configuration...
if not exist .env (
    copy .env.template .env
    echo ✅ Environment file created. Please edit .env with your settings.
) else (
    echo ✅ Environment file already exists.
)

echo.
echo ⚛️ Setting up frontend...

:: Navigate to frontend directory
cd ..\frontend

:: Install Node.js dependencies
echo Installing Node.js dependencies...
npm install

:: Create environment file
echo Creating frontend environment configuration...
if not exist .env.local (
    copy .env.local.example .env.local
    echo ✅ Frontend environment file created.
) else (
    echo ✅ Frontend environment file already exists.
)

echo.
echo 🎯 Starting services...

:: Start backend in new window
echo Starting backend server...
start "PropertyAI Backend" cmd /k "cd /d %~dp0backend && call venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait a moment for backend to start
timeout /t 5 /nobreak >nul

:: Start frontend in new window
echo Starting frontend server...
start "PropertyAI Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo 🎉 Setup complete!
echo.
echo ✅ Backend running at: http://localhost:8000
echo ✅ Frontend running at: http://localhost:3000
echo ✅ API Documentation: http://localhost:8000/docs
echo.
echo 📝 Next steps:
echo 1. Make sure MongoDB is running (install from https://www.mongodb.com/try/download/community)
echo 2. Edit backend/.env with your MongoDB URL and secret key
echo 3. Open http://localhost:3000 in your browser
echo 4. Register a new user and start using the platform!
echo.
echo Press any key to open the application in your browser...
pause >nul

:: Open browser
start http://localhost:3000

echo.
echo 🚀 PropertyAI is now running! Check the terminal windows for any errors.
echo.
pause