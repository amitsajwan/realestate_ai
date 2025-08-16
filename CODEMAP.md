# Real Estate AI CRM - Code Structure Map

## 🏗️ Application Architecture

### **Primary Applications**
- **`complete_production_crm.py`** - Full-featured CRM (port 8004) with MongoDB
- **`app/main.py`** - Development server (port 8003) with in-memory storage

### **Core Components**
- **`core/config.py`** - Application settings and environment configuration
- **`core/security.py`** - Authentication, JWT tokens, password hashing
- **`db_adapter.py`** - MongoDB connection and UserRepository

### **Data Models** (`models/`)
- **`user.py`** - User authentication and profile models
- **`agent.py`** - Agent profiles with Facebook page connections
- **`crm.py`** - Lead and property management models

### **Repositories** (`repositories/`)
- **`user_repository.py`** - In-memory user storage (development)
- **`agent_repository.py`** - Agent profile management
- **`agent_repository_mongo.py`** - MongoDB agent storage

### **API Endpoints** (`api/endpoints/`)
- **`facebook_oauth.py`** - Facebook authentication and OAuth flow
- **`facebook_pages.py`** - Facebook page management and posting
- **`listing_posts.py`** - AI content generation with templates
- **`ai_localization.py`** - Multi-language AI content creation
- **`auth.py`** - User authentication endpoints
- **`leads.py`** - Lead management CRUD operations
- **`crm.py`** - Property management endpoints

### **Services** (`services/`)
- **`facebook_client.py`** - Facebook Graph API integration
- **`ai_content_service.py`** - AI content generation service

## 🌐 URL Structure

### Production CRM (port 8004)
```
GET  /                    → Login page
POST /api/login           → JWT authentication
GET  /dashboard           → Main dashboard UI
GET  /api/leads           → List leads
POST /api/leads           → Create lead
GET  /api/properties      → List properties
POST /api/properties      → Create property
GET  /api/facebook/config → Facebook connection status
POST /api/facebook/post   → Post to Facebook page
```

### Development Server (port 8003)  
```
GET  /                    → Login page
GET  /dashboard           → Dashboard UI
GET  /docs                → API documentation
GET  /api/facebook/*      → Facebook integration endpoints
POST /api/listings/*      → AI content generation
POST /ai/*                → AI localization endpoints
```

## 📁 File Organization

### **Templates & Static Files**
```
templates/
├── login.html           # User login interface
└── dashboard.html       # Main dashboard UI

static/
├── css/                 # Styles
├── js/                  # JavaScript
└── images/              # Static assets
```

### **Configuration & Deployment**
```
.env                     # Environment variables
docker-compose.crm.yml   # Production deployment
Dockerfile.crm           # Container configuration
requirements.txt         # Python dependencies
```

### **Testing**
```
tests/
├── unit/                # Unit tests by feature
├── integration/         # API integration tests
├── e2e/                 # Playwright UI tests
└── docs/                # Test documentation
```

## 🗄️ Database Architecture

### **MongoDB Collections** (Production)
- **`users`** - User accounts, authentication, Facebook tokens
- **`agent_profiles`** - Agent information and Facebook page connections
- **`leads`** - Lead information and status tracking
- **`properties`** - Property listings and details

### **In-Memory Storage** (Development)
- **Python dictionaries** for quick development and testing
- **Automatic demo data seeding** with demo@mumbai.com account

## 🔌 Integration Points

### **Facebook Graph API**
- **OAuth 2.0 flow** via `/api/facebook/connect`
- **Page management** via `/api/facebook/pages`
- **Content posting** via `/api/facebook/post`
- **Token encryption** with Fernet cipher

### **AI Services (Groq + LangChain)**
- **Content generation** via `/api/listings/generate`
- **Multi-language support** via `/ai/localize`
- **Professional templates** for real estate content

### **Authentication Flow**
- **JWT tokens** for session management
- **bcrypt hashing** for password security
- **Demo user** auto-creation for testing

## ⚙️ Configuration

### **Environment Variables**
```env
MONGO_URI=mongodb://localhost:27017/realestate_crm
GROQ_API_KEY=your_groq_api_key
FB_APP_ID=your_facebook_app_id
FB_APP_SECRET=your_facebook_app_secret
SECRET_KEY=your_secret_key
FEATURE_FACEBOOK_PERSIST=true
```

### **Feature Flags**
- **`FEATURE_FACEBOOK_PERSIST`** - Enable MongoDB token storage
- **`AI_DISABLE_IMAGE_GENERATION`** - Disable AI image features

## 🚀 Deployment Modes

### **Docker (Recommended)**
```bash
docker compose -f docker-compose.crm.yml up -d
```
- MongoDB container with persistent storage
- Production CRM with all features enabled

### **Development**
```bash
uvicorn app.main:app --reload --port 8003
```
- In-memory storage for rapid development
- Hot-reload for code changes

## 💡 Key Implementation Notes

- **MongoDB Only** - SQLite has been completely removed
- **Async/Await** - All database operations use async patterns  
- **Type Safety** - Pydantic models for data validation
- **Security First** - Encrypted tokens, hashed passwords, CSRF protection
- **API Documentation** - Auto-generated OpenAPI/Swagger documentation
