# 🚀 Single URL Deployment Guide

## 🎯 Problem Solved

**Issue**: Frontend hardcoded to `localhost:8000` for backend calls
**Solution**: Dynamic API URL resolution that works with any single URL deployment

## ✅ Architecture Overview

### **How It Works**
1. **Frontend** detects environment and uses appropriate API URL
2. **Nginx** proxies `/api/*` requests to backend
3. **Single URL** serves both frontend and backend through reverse proxy

### **URL Resolution Logic**
```typescript
// Development (localhost:3000) → http://localhost:8000
// Docker/Production → relative paths (/api/*)
// ngrok → relative paths (/api/*)
```

## 🐳 Docker Deployment

### **1. Using Docker Compose (Recommended)**
```bash
# Start all services
docker-compose up -d

# Access via single URL
http://localhost:3000
```

### **2. Using Nginx Proxy (Production)**
```bash
# Start with nginx proxy
docker-compose --profile production up -d

# Access via single URL
http://localhost:80
```

## 🌐 ngrok Deployment

### **1. Start Backend**
```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### **2. Start Frontend**
```bash
cd frontend
npm run dev
```

### **3. Expose with ngrok**
```bash
# Option 1: Expose frontend (port 3000)
ngrok http 3000

# Option 2: Expose nginx proxy (port 80)
ngrok http 80
```

### **4. Access via ngrok URL**
```
https://abc123.ngrok-free.app
```

## 🔧 Environment Configuration

### **Frontend (.env.local)**
```env
# Use relative paths for single URL deployment
NEXT_PUBLIC_API_BASE_URL=

# Or specify custom API URL
NEXT_PUBLIC_API_BASE_URL=https://your-domain.com/api
```

### **Backend (Environment Variables)**
```env
# Allow all origins for single URL deployment
CORS_ORIGINS=*

# Or specify specific origins
CORS_ORIGINS=https://your-domain.com,https://abc123.ngrok-free.app
```

## 📊 URL Resolution Matrix

| Environment | Frontend URL | Backend URL | API Calls |
|-------------|--------------|-------------|-----------|
| **Local Dev** | localhost:3000 | localhost:8000 | Direct |
| **Docker** | localhost:3000 | localhost:8000 | Nginx Proxy |
| **ngrok** | ngrok-url | ngrok-url | Same Domain |
| **Production** | your-domain.com | your-domain.com | Same Domain |

## 🎯 API Call Examples

### **Development**
```typescript
// API calls go to: http://localhost:8000/api/v1/auth/login
fetch('/api/v1/auth/login', { ... })
```

### **Production/ngrok**
```typescript
// API calls go to: https://your-domain.com/api/v1/auth/login
fetch('/api/v1/auth/login', { ... })
```

## 🔍 Testing the Solution

### **1. Test Local Development**
```bash
# Start backend
cd backend && python -m uvicorn app.main:app --port 8000

# Start frontend
cd frontend && npm run dev

# Test API calls
curl http://localhost:3000/api/health
```

### **2. Test Docker Deployment**
```bash
# Start with Docker
docker-compose up -d

# Test single URL
curl http://localhost:3000/api/health
```

### **3. Test ngrok Deployment**
```bash
# Start services
docker-compose up -d

# Expose with ngrok
ngrok http 3000

# Test via ngrok URL
curl https://abc123.ngrok-free.app/api/health
```

## 🚀 Production Deployment

### **1. Environment Variables**
```env
# Frontend
NEXT_PUBLIC_API_BASE_URL=

# Backend
CORS_ORIGINS=https://your-domain.com
ALLOWED_ORIGINS=https://your-domain.com
```

### **2. Nginx Configuration**
```nginx
# API routes
location /api/ {
    proxy_pass http://backend:8000;
    # ... proxy headers
}

# Frontend routes
location / {
    proxy_pass http://frontend:3000;
    # ... proxy headers
}
```

### **3. SSL/HTTPS**
```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    return 301 https://$host$request_uri;
}

# HTTPS configuration
server {
    listen 443 ssl;
    # ... SSL configuration
}
```

## ✅ Benefits

1. **Single URL**: One URL for entire application
2. **No CORS Issues**: Same-origin requests
3. **Easy Deployment**: Works with any reverse proxy
4. **Environment Agnostic**: Works in dev, staging, production
5. **ngrok Compatible**: Perfect for demos and testing

## 🎉 Result

**Your application now works seamlessly with:**
- ✅ Docker Compose
- ✅ ngrok tunneling
- ✅ Production deployment
- ✅ Any reverse proxy setup
- ✅ Single URL access

**All API calls automatically resolve to the correct backend URL based on the environment!**