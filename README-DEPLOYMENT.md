# 🚀 Simple Deployment Guide

This guide provides **two simple ways** to run your PropertyAI application without the complexity of ngrok or manual configuration.

## 🎯 Quick Start

### Option 1: Local Development (Recommended for Development)
```powershell
# Start everything locally
.\start-local.ps1

# Check status
.\start-local.ps1 -Action status

# Stop services
.\start-local.ps1 -Action stop
```

### Option 2: Docker Deployment (Recommended for Production-like Testing)
```powershell
# Start with Docker
.\start-docker.ps1

# Check status
.\start-docker.ps1 -Action status

# Stop containers
.\start-docker.ps1 -Action stop
```

## 📋 Prerequisites

### For Local Development:
- ✅ **Node.js** (v18 or higher)
- ✅ **Python** (v3.8 or higher)
- ✅ **MongoDB** (running locally)
- ✅ **PowerShell** (Windows)

### For Docker Deployment:
- ✅ **Docker Desktop** (running)
- ✅ **PowerShell** (Windows)

## 🔧 Local Development Setup

### 1. Start MongoDB
```bash
# Windows (if installed as service)
net start MongoDB

# Or start manually
mongod

# macOS
brew services start mongodb-community

# Linux
sudo systemctl start mongod
```

### 2. Run the Application
```powershell
# Start all services
.\start-local.ps1
```

### 3. Access Your Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 🐳 Docker Deployment Setup

### 1. Start with Docker
```powershell
# Start all containers
.\start-docker.ps1
```

### 2. Access Your Application
- **Application**: http://localhost
- **API Documentation**: http://localhost/docs

## 🛠️ Available Commands

### Local Development Commands
```powershell
.\start-local.ps1 -Action start      # Start all services
.\start-local.ps1 -Action stop       # Stop all services
.\start-local.ps1 -Action restart    # Restart all services
.\start-local.ps1 -Action status     # Check service status
.\start-local.ps1 -Action logs       # Show recent logs
.\start-local.ps1 -SkipMongo         # Start without MongoDB
```

### Docker Commands
```powershell
.\start-docker.ps1 -Action start     # Start containers
.\start-docker.ps1 -Action stop      # Stop containers
.\start-docker.ps1 -Action restart   # Restart containers
.\start-docker.ps1 -Action build     # Build Docker images
.\start-docker.ps1 -Action status    # Check container status
.\start-docker.ps1 -Action logs      # Show container logs
.\start-docker.ps1 -Action clean     # Clean up resources
.\start-docker.ps1 -Force            # Force rebuild images
```

## 🔧 Configuration

### Environment Variables
The scripts automatically use the correct configuration for each environment:

- **Local Development**: Uses `localhost` URLs
- **Docker**: Uses container networking

### Facebook OAuth (Optional)
For Facebook integration, update these files:
- `env.local` (for local development)
- `docker/env.production` (for Docker)

## 🐛 Troubleshooting

### Local Development Issues

**MongoDB not starting:**
```powershell
# Check if MongoDB service is running
Get-Service MongoDB

# Start MongoDB service
Start-Service MongoDB
```

**Port already in use:**
```powershell
# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# Kill the process
taskkill /PID <PID> /F
```

**Python dependencies issues:**
```powershell
# Recreate virtual environment
cd backend
Remove-Item .venv -Recurse -Force
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Docker Issues

**Docker not running:**
- Start Docker Desktop
- Wait for it to fully start

**Port conflicts:**
```powershell
# Check what's using port 80
netstat -ano | findstr :80

# Stop conflicting services or change port in docker-compose.yml
```

**Container build failures:**
```powershell
# Clean and rebuild
.\start-docker.ps1 -Action clean -Force
.\start-docker.ps1 -Action build
```

## 📊 Monitoring

### Check Service Status
```powershell
# Local development
.\start-local.ps1 -Action status

# Docker deployment
.\start-docker.ps1 -Action status
```

### View Logs
```powershell
# Local development
.\start-local.ps1 -Action logs

# Docker deployment
.\start-docker.ps1 -Action logs
```

## 🎉 Success Indicators

### Local Development
- ✅ MongoDB running on port 27017
- ✅ Backend running on port 8000
- ✅ Frontend running on port 3000
- ✅ Can access http://localhost:3000

### Docker Deployment
- ✅ All 4 containers running (mongodb, backend, frontend, nginx)
- ✅ Can access http://localhost
- ✅ Health check passes

## 🔄 Switching Between Modes

### From Local to Docker
```powershell
# Stop local services
.\start-local.ps1 -Action stop

# Start Docker
.\start-docker.ps1
```

### From Docker to Local
```powershell
# Stop Docker containers
.\start-docker.ps1 -Action stop

# Start local services
.\start-local.ps1
```

## 📝 Notes

- **Local Development**: Best for active development and debugging
- **Docker Deployment**: Best for production-like testing and deployment
- **No ngrok required**: Both modes work without external tunneling
- **Facebook OAuth**: Configure separately if needed for external access
- **Database**: MongoDB data persists between restarts

## 🆘 Getting Help

If you encounter issues:

1. **Check the status**: `.\start-local.ps1 -Action status` or `.\start-docker.ps1 -Action status`
2. **View logs**: `.\start-local.ps1 -Action logs` or `.\start-docker.ps1 -Action logs`
3. **Restart services**: `.\start-local.ps1 -Action restart` or `.\start-docker.ps1 -Action restart`
4. **Clean and rebuild**: `.\start-docker.ps1 -Action clean -Force`

---

**Happy coding! 🚀**


