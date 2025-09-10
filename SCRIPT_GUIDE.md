# PropertyAI - Script Usage Guide

## 🎯 **Which Script to Use When?**

### **For Development (Recommended)**
```powershell
# Start all services with separate terminal windows
.\start-local.ps1

# Start individual services
.\start-local.ps1 -Action backend
.\start-local.ps1 -Action frontend
.\start-local.ps1 -Action mongo
```

### **For Production/Testing**
```powershell
# Docker deployment
.\start-docker.ps1

# Full build and deploy
.\startup-fixed.ps1 -Mode full-deploy
```

### **For Linux/Mac**
```bash
# Start services
./start_app.sh

# Stop services
./stop_app.sh
```

## 🔧 **Script Comparison**

| Script | Purpose | Terminal Type | Best For |
|--------|---------|---------------|----------|
| `start-local.ps1` | Development | Separate Windows | Daily development |
| `startup-fixed.ps1` | Build/Deploy | Current Terminal | Production builds |
| `start-docker.ps1` | Docker Deploy | Current Terminal | Container testing |
| `start_app.sh` | Linux/Mac Dev | Background | Cross-platform dev |

## 🖥️ **IDE Terminal Integration**

### **VS Code Tasks (Ctrl+Shift+P → "Tasks: Run Task")**
- **Start All Services** - Opens separate terminals
- **Start Backend Only** - Backend in IDE terminal
- **Start Frontend Only** - Frontend in IDE terminal
- **Stop All Services** - Stops everything
- **Check Status** - Shows service status

### **Why Separate Windows vs IDE Terminals?**

#### **Separate Windows (Default)**
✅ **Pros:**
- Services run independently
- Won't close accidentally
- Clear separation of logs
- Better for debugging
- Hot reload works perfectly

❌ **Cons:**
- More windows to manage
- Takes up screen space

#### **IDE Terminals**
✅ **Pros:**
- Integrated with VS Code
- Easy to switch between
- Less screen clutter

❌ **Cons:**
- Can close accidentally
- May interfere with each other
- Hot reload might not work as well

## 🚀 **Quick Start Commands**

### **Development (Most Common)**
```powershell
# Start everything
.\start-local.ps1

# Check status
.\start-local.ps1 -Action status

# Stop everything
.\start-local.ps1 -Action stop
```

### **Production Testing**
```powershell
# Build and deploy with Docker
.\startup-fixed.ps1 -Mode full-deploy

# Run tests
.\startup-fixed.ps1 -Mode test-playwright
.\startup-fixed.ps1 -Mode test-backend
```

### **Docker Only**
```powershell
# Start Docker services
.\start-docker.ps1

# Stop Docker services
.\start-docker.ps1 -Action stop
```

## 🔍 **Troubleshooting**

### **Backend Won't Start**
1. Check if port 8000 is free: `netstat -an | findstr :8000`
2. Check MongoDB is running: `.\start-local.ps1 -Action mongo`
3. Check Python dependencies: `cd backend && pip install -r requirements.txt`

### **Frontend Won't Start**
1. Check if port 3000 is free: `netstat -an | findstr :3000`
2. Install dependencies: `cd frontend && npm install`
3. Clear cache: `cd frontend && npm run clean`

### **Docker Issues**
1. Check Docker is running: `docker info`
2. Check Docker Compose: `docker-compose --version`
3. Rebuild images: `.\startup-fixed.ps1 -Mode build-images`

## 📝 **Environment Variables**

Make sure these are set in your environment:
- `MONGODB_URL` - MongoDB connection string
- `SECRET_KEY` - JWT secret key
- `NEXT_PUBLIC_API_URL` - Frontend API URL

## 🎯 **Recommendations**

1. **For daily development**: Use `start-local.ps1` (separate windows)
2. **For testing**: Use VS Code tasks (IDE terminals)
3. **For production**: Use `startup-fixed.ps1` or `start-docker.ps1`
4. **For team sharing**: Use Docker approach
