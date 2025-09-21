# 🪟 PropertyAI - Windows Setup Guide

Complete step-by-step guide to set up PropertyAI on Windows.

## 🎯 Quick Start (Recommended for Windows)

### Prerequisites
- **Windows 10/11** (64-bit)
- **Docker Desktop for Windows** ([Download](https://www.docker.com/products/docker-desktop/))
- **Git for Windows** ([Download](https://git-scm.com/download/win))
- **Groq API Key** ([Get from console.groq.com](https://console.groq.com/))

### One-Command Setup
```cmd
# Open Command Prompt or PowerShell as Administrator
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai

# Copy and configure environment
copy .env.production.template .env.production
notepad .env.production

# Deploy with one command
deploy.sh production
```

**✅ Your application will be running at:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

## 🔧 Manual Windows Setup

### Step 1: Install Prerequisites

#### 1.1 Install Docker Desktop
1. Download from [docker.com](https://www.docker.com/products/docker-desktop/)
2. Run the installer
3. Enable WSL 2 integration when prompted
4. Restart your computer
5. Verify installation:
   ```cmd
   docker --version
   docker-compose --version
   ```

#### 1.2 Install Git
1. Download from [git-scm.com](https://git-scm.com/download/win)
2. Run installer with default settings
3. Verify installation:
   ```cmd
   git --version
   ```

#### 1.3 Install Python (for development)
1. Download Python 3.11+ from [python.org](https://www.python.org/downloads/)
2. **Important**: Check "Add Python to PATH" during installation
3. Verify installation:
   ```cmd
   python --version
   pip --version
   ```

#### 1.4 Install Node.js (for development)
1. Download Node.js 18+ from [nodejs.org](https://nodejs.org/)
2. Run installer with default settings
3. Verify installation:
   ```cmd
   node --version
   npm --version
   ```

### Step 2: Clone and Setup Project

```cmd
# Clone repository
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai

# Check current branch
git branch
```

### Step 3: Configure Environment

```cmd
# Copy environment template
copy .env.production.template .env.production

# Edit environment file
notepad .env.production
```

**Configure these essential settings in `.env.production`:**
```env
# AI Features (Required)
GROQ_API_KEY=your-groq-api-key-here

# Security (Generate secure keys)
JWT_SECRET_KEY=your-super-secure-jwt-secret-key
MONGO_ROOT_PASSWORD=your-secure-mongodb-password
REDIS_PASSWORD=your-secure-redis-password

# Domain Configuration
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

### Step 4: Deploy with Docker

#### Option A: Production Deployment (Recommended)
```cmd
# Deploy with monitoring
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps

# View logs
docker-compose -f docker-compose.production.yml logs -f
```

#### Option B: Development Deployment
```cmd
# Deploy development environment
docker-compose -f docker-compose.dev.yml up -d

# Check status
docker-compose -f docker-compose.dev.yml ps
```

#### Option C: With Monitoring Stack
```cmd
# Deploy with Prometheus and Grafana
docker-compose -f docker-compose.production.yml --profile monitoring up -d

# Access monitoring
# Grafana: http://localhost:3001 (admin/admin123)
# Prometheus: http://localhost:9090
```

### Step 5: Verify Installation

#### 5.1 Check Services
```cmd
# Check if containers are running
docker ps

# Check service health
curl http://localhost:8000/api/v1/health
curl http://localhost:3000
```

#### 5.2 Run Tests
```cmd
# Run comprehensive test suite
python comprehensive_test.py
```

Expected output:
```
🎯 TEST SUMMARY
Total Tests: 20
✅ Passed: 18
❌ Failed: 2
⚠️ Errors: 0
Success Rate: 90.0%

🎉 EXCELLENT! Platform is in great shape!
```

---

## 🌐 ngrok Setup (External Access)

### Step 1: Install ngrok
```cmd
# Download from https://ngrok.com/download
# Or install via npm:
npm install -g ngrok
```

### Step 2: Get ngrok Auth Token
1. Sign up at [ngrok.com](https://ngrok.com/)
2. Get your auth token from the dashboard
3. Configure ngrok:
   ```cmd
   ngrok config add-authtoken YOUR_AUTH_TOKEN
   ```

### Step 3: Deploy with ngrok
```cmd
# Deploy with ngrok configuration
docker-compose -f docker-compose.ngrok.yml up -d

# In another terminal, expose the application
ngrok http 80
```

**✅ Your app is now accessible worldwide at the ngrok URL!**

### Step 4: Update Environment (if needed)
If you need to update the ngrok URL in your environment:
```cmd
# The application automatically detects ngrok URLs
# No manual configuration needed!
```

---

## 🧪 Development Setup (Windows)

### Backend Development
```cmd
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.template .env
notepad .env

# Start MongoDB (if using local)
# Download MongoDB from https://www.mongodb.com/try/download/community
# Install and start MongoDB service

# Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Development
```cmd
# Open new Command Prompt
cd frontend

# Install dependencies
npm install

# Configure environment
copy .env.local.example .env.local
notepad .env.local

# Start frontend
npm run dev
```

---

## 🔧 Windows-Specific Troubleshooting

### Port Conflicts
```cmd
# Check if ports are in use
netstat -an | findstr :3000
netstat -an | findstr :8000

# Kill processes using ports
netstat -ano | findstr :3000
# Note the PID and kill it:
taskkill /PID <PID> /F
```

### Docker Issues
```cmd
# Restart Docker Desktop
# Right-click Docker Desktop icon in system tray
# Select "Restart Docker Desktop"

# Reset Docker if needed
# Docker Desktop > Settings > Reset > Reset to factory defaults
```

### Python/Virtual Environment Issues
```cmd
# If Python not found:
# 1. Reinstall Python with "Add to PATH" checked
# 2. Restart Command Prompt
# 3. Try: py -m venv venv (instead of python -m venv venv)

# If pip issues:
python -m pip install --upgrade pip
```

### Node.js/npm Issues
```cmd
# Clear npm cache
npm cache clean --force

# Reinstall dependencies
rmdir /s node_modules
del package-lock.json
npm install
```

### MongoDB Issues
```cmd
# Start MongoDB service
net start MongoDB

# Or install MongoDB as Windows Service
# Download from https://www.mongodb.com/try/download/community
# Choose "Install MongoDB as a Service"
```

### WSL2 Issues (if using Docker Desktop)
```cmd
# Enable WSL2 in Docker Desktop
# Docker Desktop > Settings > General > Use WSL 2 based engine

# Update WSL2
wsl --update
```

---

## 📊 Monitoring on Windows

### Access Monitoring Dashboards
- **Grafana**: http://localhost:3001 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Application Health**: http://localhost:8000/api/v1/health

### View Logs
```cmd
# Docker logs
docker-compose -f docker-compose.production.yml logs -f

# Backend logs (if running locally)
tail -f backend/logs/app.log

# Frontend logs (if running locally)
npm run dev
```

### Performance Monitoring
```cmd
# Run performance tests
python qa/performance_test.py

# Check system resources
# Task Manager > Performance tab
```

---

## 🚀 Production Deployment on Windows

### Step 1: Prepare Production Environment
```cmd
# Configure production environment
copy .env.production.template .env.production
notepad .env.production
```

### Step 2: Generate Secure Keys
```cmd
# Generate secure JWT secret
python -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_urlsafe(32))"

# Generate MongoDB password
python -c "import secrets; print('MONGO_ROOT_PASSWORD=' + secrets.token_urlsafe(16))"

# Generate Redis password
python -c "import secrets; print('REDIS_PASSWORD=' + secrets.token_urlsafe(16))"
```

### Step 3: Deploy Production
```cmd
# Deploy with monitoring
docker-compose -f docker-compose.production.yml --profile monitoring up -d

# Verify deployment
docker-compose -f docker-compose.production.yml ps
```

### Step 4: Configure Domain (Optional)
1. Update `docker/nginx/nginx.conf` with your domain
2. Set up SSL certificates in `docker/nginx/ssl/`
3. Update environment variables with your domain

---

## 🎯 Success Verification

After setup, you should have:

✅ **Docker containers running**  
✅ **Frontend accessible at http://localhost:3000**  
✅ **Backend API at http://localhost:8000**  
✅ **API documentation at http://localhost:8000/docs**  
✅ **MongoDB database connected**  
✅ **Redis cache running**  
✅ **Monitoring dashboards accessible**  
✅ **90%+ test success rate**  

**Your PropertyAI platform is now running on Windows! 🎉**

---

## 🆘 Need Help?

- **Check logs**: `docker-compose logs -f`
- **Run diagnostics**: `python comprehensive_test.py`
- **Restart services**: `docker-compose restart`
- **Full reset**: `docker-compose down -v && docker-compose up --build`

For more help, see the main [README.md](README.md) or [COMPREHENSIVE_GUIDE.md](COMPREHENSIVE_GUIDE.md).