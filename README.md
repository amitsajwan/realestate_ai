# 🏠 PropertyAI - AI-Powered Real Estate Platform

A comprehensive, production-ready real estate platform with AI-powered content generation, social media publishing, and advanced analytics.

## 🌟 Key Features

- **🤖 AI-Powered Content**: Groq AI integration for property descriptions and social media posts
- **📱 Social Publishing**: Multi-platform publishing (Facebook, Instagram, Website)
- **👥 Multi-User System**: Agent profiles, client management, team collaboration
- **📊 Business Analytics**: Comprehensive dashboard with real-time metrics
- **🌍 Multi-Language Support**: Internationalization ready
- **🔐 Enterprise Security**: JWT authentication, CORS protection, rate limiting
- **🚀 Production Ready**: Docker containerization, monitoring, CI/CD pipeline
- **📈 Scalable Architecture**: Microservices with MongoDB and Redis

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend API   │    │   Database      │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   (MongoDB)     │
│   Port: 3000    │    │   Port: 8000    │    │   Port: 27017   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   Redis Cache   │    │   Monitoring    │
│   (Reverse      │    │   Port: 6379    │    │   (Prometheus   │
│    Proxy)       │    │                 │    │    + Grafana)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** ([Download](https://www.docker.com/products/docker-desktop/))
- **Git** ([Download](https://git-scm.com/downloads))
- **Groq API Key** ([Get from console.groq.com](https://console.groq.com/))

### Option 1: One-Command Docker Setup (Recommended)

```bash
# Clone the repository
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai

# Configure environment
cp .env.production.template .env.production
# Edit .env.production with your Groq API key and settings

# Deploy with one command
./deploy.sh production
```

**✅ Access your application:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Monitoring**: http://localhost:3001 (Grafana)

### Option 2: Windows Development Setup

#### 1. Clone Repository
```bash
git clone https://github.com/amitsajwan/realestate_ai.git
cd realestate_ai
```

#### 2. Backend Setup
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.template .env
# Edit .env with your settings
```

**Configure Backend Environment (`.env`):**
```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=propertyai

# Security
SECRET_KEY=your-super-secret-key-here-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Features (Required for content generation)
GROQ_API_KEY=your-groq-api-key-here

# CORS
ALLOWED_ORIGINS=["http://localhost:3000"]
```

#### 3. Start MongoDB
```bash
# Option A: Install MongoDB locally
# Download from https://www.mongodb.com/try/download/community
# Then start: mongod

# Option B: Use MongoDB Atlas (Cloud)
# Update MONGODB_URL in .env to your Atlas connection string
```

#### 4. Start Backend
```bash
# From backend directory
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 5. Frontend Setup
```bash
# Open new terminal, navigate to frontend
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.local.example .env.local
# Edit .env.local with your settings
```

**Configure Frontend Environment (`.env.local`):**
```env
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Feature Flags
NEXT_PUBLIC_ENABLE_MULTILANGUAGE=true
NEXT_PUBLIC_ENABLE_FACEBOOK_INTEGRATION=true
NEXT_PUBLIC_ENABLE_AI_FEATURES=true
NEXT_PUBLIC_ENABLE_ANALYTICS=true
```

#### 6. Start Frontend
```bash
# From frontend directory
npm run dev
```

### Option 3: ngrok External Access

#### 1. Complete Local Setup
Follow **Option 1** or **Option 2** to get the application running locally.

#### 2. Install ngrok
```bash
# Download from https://ngrok.com/download
# Or install via npm:
npm install -g ngrok
```

#### 3. Expose Application
```bash
# For Docker setup:
docker-compose -f docker-compose.ngrok.yml up -d

# For local setup:
ngrok http 3000
```

#### 4. Automatic Configuration
The application automatically detects ngrok URLs and configures CORS appropriately!

**✅ Your app is now accessible worldwide at the ngrok URL!**

## 🧪 Testing

### Run Comprehensive Test Suite
```bash
# Test all functionality
python comprehensive_test.py

# Run performance tests
python qa/performance_test.py

# Run backend tests
cd backend
python -m pytest tests/ -v
```

### Expected Test Results
```
🎯 TEST SUMMARY
Total Tests: 20
✅ Passed: 18
❌ Failed: 2
⚠️ Errors: 0
Success Rate: 90.0%

🎉 EXCELLENT! Platform is in great shape!
```

## 🐳 Docker Deployment Options

### Development
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### Production
```bash
docker-compose -f docker-compose.production.yml up -d
```

### ngrok (External Access)
```bash
docker-compose -f docker-compose.ngrok.yml up -d
```

### With Monitoring
```bash
docker-compose -f docker-compose.production.yml --profile monitoring up -d
```

## 🌐 Domain Management

### Supported Domains
- **Local Development**: `localhost:3000`, `127.0.0.1:3000`
- **ngrok**: `*.ngrok-free.app`, `*.ngrok.io`, `*.ngrok.app`
- **Tunneling Services**: `*.localtunnel.me`, `*.serveo.net`, `*.loca.lt`
- **Production**: `your-domain.com`, `*.your-domain.com`

### Adding Custom Domains
Edit `docker/nginx/nginx.conf`:
```nginx
# Add your domain to the CORS configuration
add_header Access-Control-Allow-Origin "https://your-domain.com";
```

## 🔧 Troubleshooting

### Common Issues

#### Port Conflicts (Windows)
```cmd
# Check if ports are in use
netstat -an | findstr :3000
netstat -an | findstr :8000

# Kill processes using ports
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

#### MongoDB Connection Issues
```bash
# Check MongoDB status
# Windows: net start MongoDB
# Mac/Linux: sudo systemctl start mongod

# Or use MongoDB Atlas (cloud)
```

#### Docker Issues
```bash
# Stop all services
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Rebuild and start
docker-compose up --build
```

#### Environment Variables
- Ensure `.env` files exist and are properly configured
- No trailing spaces in environment values
- Restart services after changing environment variables

### Getting Help

1. **Check logs:**
   ```bash
   # Docker logs
   docker-compose logs -f
   
   # Backend logs
   tail -f backend/logs/app.log
   ```

2. **Verify services:**
   ```bash
   # Check if services are running
   curl http://localhost:8000/docs
   curl http://localhost:3000
   ```

3. **Run diagnostics:**
   ```bash
   # Comprehensive system test
   python comprehensive_test.py
   ```

## 📁 Project Structure

```
realestate_ai/
├── backend/                 # FastAPI backend
│   ├── app/
│   │   ├── api/            # API routes and endpoints
│   │   ├── core/           # Core functionality (auth, database, security)
│   │   ├── models/         # Database models
│   │   ├── services/       # Business logic services
│   │   └── main.py         # FastAPI application
│   ├── modules/            # Modular components (auth module)
│   ├── tests/              # Test suites
│   ├── requirements.txt    # Python dependencies
│   └── .env.template       # Environment template
├── frontend/               # Next.js frontend
│   ├── app/                # Next.js app directory
│   ├── components/         # React components
│   ├── lib/                # Utilities and API client
│   ├── hooks/              # React hooks
│   ├── types/              # TypeScript type definitions
│   ├── package.json        # Node.js dependencies
│   └── .env.local.example  # Environment template
├── docker/                 # Docker configurations
│   ├── nginx/              # Nginx configurations
│   └── monitoring/         # Monitoring stack configs
├── qa/                     # Quality assurance
│   └── performance_test.py # Performance testing
├── .github/                # CI/CD workflows
├── docker-compose*.yml     # Docker Compose configurations
├── deploy.sh              # One-command deployment script
├── comprehensive_test.py   # Comprehensive test suite
└── README.md              # This file
```

## 🚀 Deployment Options

### 1. Single Server (Recommended)
- Use Docker Compose
- Single URL for frontend and backend
- Nginx reverse proxy
- MongoDB database
- Redis caching

### 2. Cloud Deployment
- **AWS**: EC2 + RDS + S3
- **Google Cloud**: Compute Engine + Cloud SQL
- **Azure**: App Service + Cosmos DB
- **DigitalOcean**: Droplet + Managed Database

### 3. Container Orchestration
- **Kubernetes**: For large-scale deployments
- **Docker Swarm**: For simpler orchestration
- **AWS ECS**: Managed container service

## 📊 Monitoring & Analytics

### Built-in Monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Visualization dashboards
- **Health Checks**: Automated service monitoring
- **Business Analytics**: Real-time KPI tracking

### Access Monitoring
- **Grafana Dashboard**: http://localhost:3001 (admin/admin123)
- **Prometheus Metrics**: http://localhost:9090
- **Application Health**: http://localhost:8000/api/v1/health

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`python comprehensive_test.py`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and [COMPREHENSIVE_GUIDE.md](COMPREHENSIVE_GUIDE.md)
- **Issues**: Create an issue on [GitHub](https://github.com/amitsajwan/realestate_ai/issues)
- **Discussions**: Use [GitHub Discussions](https://github.com/amitsajwan/realestate_ai/discussions)

## 🎉 Success Checklist

If you've followed this guide, you should now have:

✅ **A fully functional PropertyAI Platform**  
✅ **Frontend and backend running**  
✅ **Database connected and working**  
✅ **Authentication system operational**  
✅ **Property management features working**  
✅ **AI-powered content generation**  
✅ **Social media publishing**  
✅ **Business analytics dashboard**  
✅ **Production-ready architecture**  
✅ **Monitoring and health checks**  

**Happy coding! 🚀**

---

*For detailed technical documentation, see [COMPREHENSIVE_GUIDE.md](COMPREHENSIVE_GUIDE.md)*