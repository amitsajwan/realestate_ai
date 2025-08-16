# 🏠 Real Estate AI CRM

AI-powered Real Estate CRM with Facebook integration, automated content generation, and comprehensive lead management for modern real estate agents.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB (for data storage)
- Optional: Docker (for containerized deployment)

### Option 1: Production CRM (Recommended)

**Full-featured CRM with MongoDB:**
```bash
docker compose -f docker-compose.crm.yml up -d --build
```
- 🌐 **CRM Interface**: http://localhost:8004
- 📊 **Complete Dashboard**: Leads, Properties, AI Tools
- 🗄️ **Persistent Storage**: MongoDB

Stop:
```bash
docker compose -f docker-compose.crm.yml down -v
```

### Option 2: Development Server

**Lightweight development with in-memory storage:**
```bash
# Install dependencies
pip install -r requirements.txt

# Start development server  
uvicorn app.main:app --reload --port 8003
```
- 🌐 **Dashboard**: http://localhost:8003/dashboard
- 🧪 **Development Mode**: In-memory data storage

### Option 3: Manual Setup

1. **Clone and setup:**
   ```bash
   git clone <repository>
   cd realestate_ai
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # macOS/Linux
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   # Copy .env.example to .env and configure:
   MONGO_URI=mongodb://localhost:27017/realestate_crm
   GROQ_API_KEY=your_groq_api_key
   FB_APP_ID=your_facebook_app_id
   FB_APP_SECRET=your_facebook_app_secret
   ```

3. **Start application:**
   ```bash
   # Development mode (port 8003)
   uvicorn app.main:app --reload --port 8003
   
   # OR Production mode (port 8004)  
   python complete_production_crm.py
   ```

## 🎯 Available Applications

| Application | URL | Purpose | Database |
|-------------|-----|---------|----------|
| **Production CRM** | http://localhost:8004 | Full-featured CRM with persistent storage | MongoDB |
| **Development Server** | http://localhost:8003 | Lightweight development and testing | In-memory |
| **API Documentation** | http://localhost:8003/docs | Interactive API documentation | - |
| **Health Check** | http://localhost:8003/ | Server status verification | - |

## 🔑 Demo Credentials

**Login:** demo@mumbai.com  
**Password:** demo123

## 🏗️ Core Features

### 📊 Dashboard
- **5-Tab Interface**: Dashboard, Leads, Properties, AI Tools, Settings
- **Real-time Updates**: Connection status, lead metrics, activity feed
- **Responsive Design**: Mobile-friendly interface

### 📘 Facebook Integration
- **OAuth Authentication**: Secure Facebook account connection
- **Multi-page Support**: Manage multiple Facebook business pages
- **Direct Posting**: Post content directly to Facebook from dashboard
- **Encrypted Storage**: Secure token storage with Fernet encryption

### 🤖 AI Content Generation
- **LangChain + Groq**: Advanced AI content creation
- **Professional Templates**: Just Listed, Open House, Price Drop, Sold
- **Multi-language**: 7 languages including English, Spanish, French
- **Copy to Facebook**: Seamless integration with posting workflow

### 👥 Lead Management
- **CRUD Operations**: Create, view, update, delete leads
- **Status Tracking**: Lead lifecycle management
- **Search & Filter**: Find leads by various criteria
- **Agent Assignment**: Multi-agent lead distribution

## �️ Technical Stack

### Backend
- **Framework**: FastAPI with async/await
- **Database**: MongoDB (production) / In-memory (development)
- **Authentication**: JWT tokens with bcrypt password hashing
- **AI Integration**: LangChain with Groq LLM API

### APIs
- **Facebook Graph API**: v19.0 for social media integration
- **Groq API**: AI content generation and localization
- **RESTful Endpoints**: Standard HTTP API design

### Security
- **Encryption**: Fernet encryption for sensitive tokens
- **CSRF Protection**: OAuth state verification
- **Password Hashing**: bcrypt with salt
- **Environment Variables**: Secure configuration management

```
ws://localhost:8000/chat
```

Then type `start` to begin the assistant flow.

---

## 🚀 Example Flow

1. Assistant asks branding questions.
2. You reply with branding preferences.
3. Assistant generates:

   * Brand name + tagline
   * Logo and cover image prompts
   * About section
4. You enter property details (location, price, etc.)
5. Assistant generates:

   * Base post + 3 variants
6. You confirm posting to Facebook Page.
7. Assistant posts using image `images/building.png`.

---

## 📸 Facebook Requirements

Ensure your Page has:

* ✅ `pages_manage_posts` & `pages_read_engagement`
* ✅ App has correct permissions and is live
* ✅ You are an admin of the Page

---

## 🧠 Powered by

* [LangGraph](https://github.com/langchain-ai/langgraph)
* [FastAPI](https://fastapi.tiangolo.com/)
* [Groq LLM via LangChain](https://python.langchain.com/docs/integrations/llms/groq)

---

## 📌 TODO

* [ ] Auto-generate and upload logo/cover images
* [ ] Schedule Facebook posts
* [ ] Add Instagram integration
* [ ] Save user projects to database

---

## 📁 Documentation

### Essential Guides
- **[CURRENT_STATUS.md](CURRENT_STATUS.md)** - Current implementation overview
- **[FACEBOOK_SETUP_GUIDE.md](FACEBOOK_SETUP_GUIDE.md)** - Facebook integration setup
- **[USER_MANUAL.md](USER_MANUAL.md)** - End user guide for CRM features
- **[PRODUCTION_GUIDE.md](PRODUCTION_GUIDE.md)** - Deployment and production setup

### Development
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Developer guidelines and workflow
- **[CODEMAP.md](CODEMAP.md)** - Code structure and architecture
- **[tests/](tests/)** - Comprehensive test plans and setup guides

### Architecture
- **[docs/architecture/](docs/architecture/)** - Technical design documents
- **[specs/](specs/)** - Feature specifications and requirements

## 🧪 Testing

### Test Organization
```
tests/
├── unit/           # Unit tests for core functionality
├── integration/    # API and service integration tests  
├── e2e/           # End-to-end Playwright tests
└── docs/          # Test documentation and plans
```

### Running Tests
```bash
# Unit tests
pytest tests/unit/

# Integration tests (requires running server)
pytest tests/integration/

# E2E tests (requires Playwright setup)
npm run test:e2e
```

## 🚀 Deployment

### Docker (Recommended)
```bash
# Start production CRM with MongoDB
docker compose -f docker-compose.crm.yml up -d

# Access at http://localhost:8004
```

### Manual Deployment
```bash
# Set environment variables
export MONGO_URI=mongodb://localhost:27017/realestate_crm
export GROQ_API_KEY=your_groq_key
export FB_APP_ID=your_fb_app_id
export FB_APP_SECRET=your_fb_app_secret

# Start production server
python complete_production_crm.py
```

## 🔧 Configuration

### Required Environment Variables
```env
# Database
MONGO_URI=mongodb://localhost:27017/realestate_crm

# AI Services  
GROQ_API_KEY=your_groq_api_key

# Facebook Integration
FB_APP_ID=your_facebook_app_id
FB_APP_SECRET=your_facebook_app_secret

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_key
```

### Optional Configuration
```env
# Feature Flags
FEATURE_FACEBOOK_PERSIST=true
AI_DISABLE_IMAGE_GENERATION=false

# External Services
STABILITY_API_KEY=your_stability_key
HUGGINGFACE_API_TOKEN=your_hf_token
```

## 📞 Support

For issues, questions, or contributions:
1. Check existing documentation in this repository
2. Review test plans in `tests/` directory
3. Consult `CURRENT_STATUS.md` for implementation details
4. Follow contribution guidelines in `CONTRIBUTING.md`

---

**Status**: Production-ready Real Estate AI CRM with MongoDB backend, Facebook integration, and AI-powered content generation. ✅

## 🧑‍💻 Author

**Amit Sajwan** — powered by Python, GenAI & LangGraph
