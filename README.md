# 🏠 PropertyAI - AI-Powered Real Estate Platform

A modern, full-stack real estate platform with AI-powered property management, lead generation, and agent profiles.

## 🌟 Features

- **🤖 AI-Powered**: Content generation, market insights, property suggestions
- **👥 Multi-User**: Agent profiles, client management, lead tracking
- **🌍 Multi-Language**: Internationalization support
- **📱 Responsive**: Mobile-friendly design
- **🔐 Secure**: JWT authentication, CORS protection
- **🚀 Scalable**: Microservices architecture with Docker support
- **🌐 Single URL**: Deploy frontend and backend with one URL

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│           Frontend (Next.js)        │
│  - React 18 + TypeScript            │
│  - Tailwind CSS                     │
│  - Responsive Design                │
└─────────────────────────────────────┘
                    │
┌─────────────────────────────────────┐
│         Nginx Reverse Proxy         │
│  - Single URL Deployment            │
│  - CORS Management                  │
│  - Load Balancing                   │
└─────────────────────────────────────┘
                    │
┌─────────────────────────────────────┐
│         Backend (FastAPI)           │
│  - Python 3.8+                     │
│  - MongoDB Database                 │
│  - JWT Authentication               │
└─────────────────────────────────────┘
```

## 📋 Prerequisites

### Required Software
- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **MongoDB** ([Download](https://www.mongodb.com/try/download/community) or [Atlas](https://www.mongodb.com/atlas))
- **Git** ([Download](https://git-scm.com/downloads))

### Optional Software
- **Docker Desktop** ([Download](https://www.docker.com/products/docker-desktop/))
- **ngrok** ([Download](https://ngrok.com/download))

## 🚀 Quick Start

### Option 1: Local Development (Recommended)

#### 1. Clone Repository
```bash
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
git checkout fastapi_users
```

#### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.template .env
```

**Configure Backend Environment (`.env`):**
```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=real_estate_platform

# Security
SECRET_KEY=your-super-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Features (Optional - Get from https://console.groq.com/)
GROQ_API_KEY=your-groq-api-key-here

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]
```

#### 3. Start MongoDB
```bash
# Option A: Local MongoDB
mongod

# Option B: MongoDB Atlas (Cloud)
# Just update MONGODB_URL in .env to your Atlas connection string
```

#### 4. Start Backend
```bash
# From backend directory
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**✅ Backend running at:** `http://localhost:8000`  
**✅ API Documentation:** `http://localhost:8000/docs`

#### 5. Frontend Setup
```bash
# Open new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.local.example .env.local
```

**Configure Frontend Environment (`.env.local`):**
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

#### 6. Start Frontend
```bash
# From frontend directory
npm run dev
```

**✅ Frontend running at:** `http://localhost:3000`

#### 7. Verify Setup
1. Open browser: `http://localhost:3000`
2. Register a new user
3. Login and explore the platform
4. Add properties and manage your agent profile

---

### Option 2: Docker Development

#### 1. Clone Repository
```bash
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
git checkout fastapi_users
```

#### 2. Configure Environment
```bash
# Copy environment template
cp .env.template .env

# Edit .env file with your settings
# MONGODB_URL=mongodb://mongodb:27017
# SECRET_KEY=your-secret-key
# GROQ_API_KEY=your-groq-key
```

#### 3. Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**✅ Services running:**
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- MongoDB: `localhost:27017`
- Nginx: `http://localhost:80` (Single URL)

#### 4. Access Application
- **Single URL:** `http://localhost:80` (Recommended)
- **Direct Frontend:** `http://localhost:3000`
- **Direct Backend:** `http://localhost:8000`

---

### Option 3: Production Deployment

#### 1. Prepare Production Environment
```bash
# Clone repository
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
git checkout fastapi_users

# Configure production environment
cp .env.template .env.production
```

**Production Environment (`.env.production`):**
```env
# Database
MONGODB_URL=mongodb://your-production-mongodb-url
DATABASE_NAME=real_estate_platform_prod

# Security
SECRET_KEY=your-super-secure-production-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Features
GROQ_API_KEY=your-production-groq-api-key

# CORS
ALLOWED_ORIGINS=["https://your-domain.com"]
```

#### 2. Build and Deploy
```bash
# Build Docker images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

#### 3. Configure Domain
Update `docker/nginx.conf` with your domain:
```nginx
# Replace 'your-domain.com' with your actual domain
"~^https://your-domain\.com$" $http_origin;
"~^https://.*\.your-domain\.com$" $http_origin;
```

---

### Option 4: ngrok Testing (External Access)

#### 1. Local Setup
Follow **Option 1** to get local development running.

#### 2. Install ngrok
```bash
# Install ngrok
npm install -g ngrok

# Or download from https://ngrok.com/download
```

#### 3. Expose Application
```bash
# Expose frontend
ngrok http 3000

# This gives you a public URL like: https://abc123.ngrok-free.app
```

#### 4. Update Configuration
The application automatically detects ngrok URLs and works seamlessly!

**✅ Your app is now accessible worldwide at the ngrok URL!**

---

## 🧪 Testing

### Run Test Suite
```bash
# Complete user journey test
python test_complete_user_journey.py

# E2E verification test
python test_e2e_verification.py

# CORS functionality test
python test_cors_functionality.py

# Single URL deployment test
python test_single_url_deployment.py
```

### Test Results
```
🎯 JOURNEY COMPLETE: 14/14 tests passed
🎉 BULLETPROOF SUCCESS! Complete user journey working perfectly!
```

---

## 🔧 Troubleshooting

### Common Issues

#### Port Conflicts
```bash
# Check if ports are in use
netstat -an | findstr :3000
netstat -an | findstr :8000

# Kill processes using ports
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Mac/Linux:
lsof -ti:3000 | xargs kill -9
```

#### MongoDB Connection Issues
```bash
# Check MongoDB status
# Windows:
net start MongoDB

# Mac/Linux:
sudo systemctl start mongod

# Or use MongoDB Atlas (cloud)
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

#### Environment Variables
- Check `.env` files exist and are properly configured
- Ensure no trailing spaces in environment values
- Restart services after changing environment variables

### Getting Help

1. **Check logs:**
   ```bash
   # Backend logs
   tail -f backend/logs/app.log
   
   # Frontend logs
   npm run dev
   
   # Docker logs
   docker-compose logs -f
   ```

2. **Verify services:**
   ```bash
   # Check if services are running
   curl http://localhost:8000/docs
   curl http://localhost:3000
   ```

3. **Reset everything:**
   ```bash
   # Stop all services
   docker-compose down
   
   # Remove containers and volumes
   docker-compose down -v
   
   # Rebuild and start
   docker-compose up --build
   ```

---

## 📁 Project Structure

```
realestate_ai/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core functionality
│   │   ├── models/         # Database models
│   │   └── main.py         # FastAPI app
│   ├── requirements.txt    # Python dependencies
│   └── .env.template       # Environment template
├── frontend/               # Next.js frontend
│   ├── app/                # Next.js app directory
│   ├── components/         # React components
│   ├── lib/                # Utilities and API client
│   ├── package.json        # Node.js dependencies
│   └── .env.local.example  # Environment template
├── docker/                 # Docker configurations
│   └── nginx.conf          # Nginx reverse proxy
├── docker-compose.yml      # Docker Compose config
├── test_*.py              # Test suites
└── README.md              # This file
```

---

## 🌐 Domain Management

### Supported Domains
- **Local Development:** `localhost:3000`, `127.0.0.1:3000`
- **ngrok:** `*.ngrok-free.app`, `*.ngrok.io`, `*.ngrok.app`
- **Tunneling Services:** `*.localtunnel.me`, `*.serveo.net`, `*.loca.lt`
- **Production:** `your-domain.com`, `*.your-domain.com`

### Adding New Domains
Edit `docker/nginx.conf`:
```nginx
map $http_origin $cors_origin {
    default "";
    "~^https://your-new-domain\.com$" $http_origin;
    # Add more domains here
}
```

---

## 🚀 Deployment Options

### 1. Single Server Deployment
- Use Docker Compose
- Single URL for frontend and backend
- Nginx reverse proxy
- MongoDB database

### 2. Cloud Deployment
- **AWS:** EC2 + RDS + S3
- **Google Cloud:** Compute Engine + Cloud SQL
- **Azure:** App Service + Cosmos DB
- **DigitalOcean:** Droplet + Managed Database

### 3. Container Orchestration
- **Kubernetes:** For large-scale deployments
- **Docker Swarm:** For simpler orchestration
- **AWS ECS:** Managed container service

---

## 📊 Monitoring & Maintenance

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# Complete system test
python test_e2e_verification.py
```

### Logs
```bash
# Application logs
tail -f logs/app.log

# Docker logs
docker-compose logs -f

# System logs
journalctl -u your-service
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🆘 Support

- **Documentation:** Check this README and inline code comments
- **Issues:** Create an issue on GitHub
- **Discussions:** Use GitHub Discussions for questions

---

## 🎉 Success!

If you've followed this guide, you should now have:

✅ **A fully functional Real Estate AI Platform**  
✅ **Frontend and backend running locally**  
✅ **Database connected and working**  
✅ **Authentication system operational**  
✅ **Property management features working**  
✅ **Agent profiles functional**  
✅ **AI features ready (with Groq key)**  
✅ **Mobile-responsive design**  
✅ **Production-ready architecture**  

**Happy coding! 🚀**