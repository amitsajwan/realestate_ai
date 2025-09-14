# 🚀 PropertyAI Setup Guides

## 📋 Quick Start Options

Choose the setup method that works best for you:

| Method | Best For | Time | Complexity |
|--------|----------|------|------------|
| **Local Development** | Development, Testing | 5-10 min | Easy |
| **Docker** | Production-like, Isolation | 3-5 min | Easy |
| **ngrok** | External Testing, Demos | 2-3 min | Easy |
| **Cloud Deployment** | Production, Scalability | 15-30 min | Medium |

---

## 🖥️ Windows Setup

### Option 1: One-Click Setup
```bash
# Download and run the quick start script
quick-start-windows.bat
```

### Option 2: Manual Setup
```bash
# 1. Clone repository
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
git checkout fastapi_users

# 2. Backend setup
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.template .env
# Edit .env with your settings

# 3. Start MongoDB (install from https://www.mongodb.com/try/download/community)
# Or use MongoDB Atlas (cloud)

# 4. Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Frontend setup (new terminal)
cd frontend
npm install
copy .env.local.example .env.local
# Edit .env.local with your settings

# 6. Start frontend
npm run dev
```

### Option 3: Docker Setup
```bash
# 1. Install Docker Desktop
# Download from https://www.docker.com/products/docker-desktop/

# 2. Clone and setup
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
git checkout fastapi_users

# 3. Run Docker setup
quick-start-docker.sh
# Or manually:
docker-compose up --build -d
```

---

## 🍎 Mac Setup

### Option 1: One-Click Setup
```bash
# Make script executable and run
chmod +x quick-start-unix.sh
./quick-start-unix.sh
```

### Option 2: Manual Setup
```bash
# 1. Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install dependencies
brew install python@3.9 node mongodb-community

# 3. Clone repository
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
git checkout fastapi_users

# 4. Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
# Edit .env with your settings

# 5. Start MongoDB
brew services start mongodb-community

# 6. Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 7. Frontend setup (new terminal)
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with your settings

# 8. Start frontend
npm run dev
```

### Option 3: Docker Setup
```bash
# 1. Install Docker Desktop
brew install --cask docker

# 2. Clone and setup
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
git checkout fastapi_users

# 3. Run Docker setup
chmod +x quick-start-docker.sh
./quick-start-docker.sh
```

---

## 🐧 Linux Setup

### Option 1: One-Click Setup
```bash
# Make script executable and run
chmod +x quick-start-unix.sh
./quick-start-unix.sh
```

### Option 2: Manual Setup (Ubuntu/Debian)
```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
sudo apt install python3 python3-pip python3-venv nodejs npm mongodb git -y

# 3. Clone repository
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
git checkout fastapi_users

# 4. Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.template .env
# Edit .env with your settings

# 5. Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod

# 6. Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 7. Frontend setup (new terminal)
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with your settings

# 8. Start frontend
npm run dev
```

### Option 3: Docker Setup
```bash
# 1. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 2. Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 3. Clone and setup
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
git checkout fastapi_users

# 4. Run Docker setup
chmod +x quick-start-docker.sh
./quick-start-docker.sh
```

---

## 🌐 ngrok Setup (External Access)

### 1. Local Setup First
Follow any of the local setup methods above to get the app running locally.

### 2. Install ngrok
```bash
# Option A: npm
npm install -g ngrok

# Option B: Download binary
# Visit https://ngrok.com/download
```

### 3. Expose Application
```bash
# Expose frontend (port 3000)
ngrok http 3000

# This gives you a public URL like: https://abc123.ngrok-free.app
```

### 4. Access Your App
- **Public URL:** `https://abc123.ngrok-free.app`
- **API Documentation:** `https://abc123.ngrok-free.app/api/docs`
- **Share with anyone worldwide!**

---

## ☁️ Cloud Deployment

### AWS Deployment
```bash
# 1. Create EC2 instance
# 2. Install Docker
# 3. Clone repository
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
git checkout fastapi_users

# 4. Configure environment
cp .env.template .env
# Edit .env with AWS RDS MongoDB URL

# 5. Deploy
docker-compose up --build -d

# 6. Configure security groups
# Allow ports 80, 443, 3000, 8000
```

### Google Cloud Deployment
```bash
# 1. Create Compute Engine instance
# 2. Install Docker
# 3. Clone and setup
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
git checkout fastapi_users

# 4. Deploy
docker-compose up --build -d

# 5. Configure firewall rules
gcloud compute firewall-rules create allow-propertyai --allow tcp:80,tcp:443,tcp:3000,tcp:8000
```

### DigitalOcean Deployment
```bash
# 1. Create Droplet
# 2. Install Docker
# 3. Clone and setup
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
git checkout fastapi_users

# 4. Deploy
docker-compose up --build -d

# 5. Configure domain
# Point your domain to the droplet IP
```

---

## 🔧 Environment Configuration

### Backend Environment (.env)
```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=real_estate_platform

# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Features (Optional)
GROQ_API_KEY=your-groq-api-key-here

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]
```

### Frontend Environment (.env.local)
```env
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

# Application URL
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Feature Flags
NEXT_PUBLIC_ENABLE_MULTILANGUAGE=true
NEXT_PUBLIC_ENABLE_FACEBOOK_INTEGRATION=true
NEXT_PUBLIC_ENABLE_AI_FEATURES=true
NEXT_PUBLIC_ENABLE_ANALYTICS=true

# Development Settings
NEXT_PUBLIC_DEBUG=true
NEXT_PUBLIC_ENABLE_DEV_TOOLS=true
```

---

## 🧪 Testing Your Setup

### Run Test Suite
```bash
# Complete user journey test
python test_complete_user_journey.py

# E2E verification test
python test_e2e_verification.py

# CORS functionality test
python test_cors_functionality.py
```

### Manual Testing
1. **Open browser:** `http://localhost:3000`
2. **Register a new user**
3. **Login with your credentials**
4. **Complete onboarding**
5. **Add a property**
6. **View your dashboard**
7. **Check agent public profile**

---

## 🆘 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check if ports are in use
netstat -an | grep :3000
netstat -an | grep :8000

# Kill processes using ports
# Linux/Mac:
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

#### MongoDB Issues
```bash
# Check MongoDB status
# Linux:
sudo systemctl status mongod
sudo systemctl start mongod

# Mac:
brew services start mongodb-community

# Windows:
net start MongoDB
```

#### Docker Issues
```bash
# Reset Docker containers
docker-compose down -v
docker-compose up --build -d

# Check Docker logs
docker-compose logs -f

# Clean up Docker
docker system prune -a
```

#### Dependencies Issues
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

---

## 📊 Performance Optimization

### Production Optimizations
```bash
# Build optimized frontend
cd frontend
npm run build
npm start

# Use production Docker images
docker-compose -f docker-compose.prod.yml up -d

# Enable caching
# Configure Redis for session storage
# Use CDN for static assets
```

### Monitoring
```bash
# Check service health
curl http://localhost:8000/health
curl http://localhost:3000

# Monitor logs
tail -f logs/app.log
docker-compose logs -f

# Check resource usage
docker stats
htop
```

---

## 🎉 Success Checklist

After setup, you should have:

- ✅ **Frontend running** at `http://localhost:3000`
- ✅ **Backend running** at `http://localhost:8000`
- ✅ **API Documentation** at `http://localhost:8000/docs`
- ✅ **Database connected** and working
- ✅ **Authentication system** operational
- ✅ **Property management** features working
- ✅ **Agent profiles** functional
- ✅ **Mobile-responsive** design
- ✅ **All tests passing**

**Congratulations! Your PropertyAI platform is ready to use! 🚀**