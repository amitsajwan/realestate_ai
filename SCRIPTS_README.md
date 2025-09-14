# 🚀 Real Estate AI Platform - Startup Scripts

## Overview
This project includes optimized startup scripts for different environments and use cases.

## 📁 Available Scripts

### **For Windows PowerShell (Recommended)**
- **`start-local.ps1`** - Local development with separate terminal windows
- **`start-docker.ps1`** - Docker-based deployment

### **For Unix/Linux**
- **`setup.sh`** - Complete environment setup
- **`start_app_improved.sh`** - Enhanced startup script

## 🖥️ Windows PowerShell Usage

### Local Development (Recommended)
```powershell
# Start all services in separate terminal windows
.\start-local.ps1

# Start only backend
.\start-local.ps1 -Action backend

# Start only frontend  
.\start-local.ps1 -Action frontend

# Check service status
.\start-local.ps1 -Action status

# Stop all services
.\start-local.ps1 -Action stop

# Restart all services
.\start-local.ps1 -Action restart
```

### Docker Deployment
```powershell
# Start with Docker
.\start-docker.ps1

# Check container status
.\start-docker.ps1 -Action status

# View logs
.\start-docker.ps1 -Action logs

# Stop containers
.\start-docker.ps1 -Action stop

# Clean up everything
.\start-docker.ps1 -Action clean
```

## 🐧 Unix/Linux Usage

### First Time Setup
```bash
# Complete environment setup
./setup.sh
```

### Daily Development
```bash
# Start all services
./start_app_improved.sh

# Stop services (Ctrl+C in the terminal)
```

## 🌐 Access URLs

Once started, access your application at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔧 Prerequisites

### Windows
- PowerShell 5.1+ (included in Windows 10/11)
- Python 3.8+ with virtual environment support
- Node.js 16+ with npm
- Docker Desktop (for Docker deployment)

### Unix/Linux
- Python 3.8+
- Node.js 16+
- MongoDB (optional, will use mock database if not available)

## 📝 Notes

- **Windows users**: Use `start-local.ps1` for the best development experience
- **Docker users**: Use `start-docker.ps1` for production-like deployment
- **Unix/Linux users**: Use `setup.sh` first, then `start_app_improved.sh`
- All scripts include error handling and health checks
- Services run in separate terminals for better debugging visibility

## 🆘 Troubleshooting

1. **Port conflicts**: Scripts automatically detect and resolve port conflicts
2. **Missing dependencies**: Run `setup.sh` first to install all requirements
3. **Docker issues**: Ensure Docker Desktop is running
4. **Permission errors**: Run PowerShell as Administrator if needed

## 📞 Support

If you encounter issues:
1. Check the script output for error messages
2. Verify all prerequisites are installed
3. Try the status command to see what's running
4. Check the logs for detailed error information
