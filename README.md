# Smart Properties AI-First Real Estate CRM

## 🚀 Quick Start

### Option 1: Production CRM (Recommended)
```bash
# Start production CRM with MongoDB
docker compose -f docker-compose.crm.yml up -d

# Access at http://localhost:8004
```

### Option 2: Development Server
```bash
# Start development server
uvicorn main:app --reload --port 8003

# Access at http://localhost:8003
```

### Option 3: Manual Setup
```bash
# Set up virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set environment variables
# See Configuration section below

# Start server
python complete_production_crm.py
```

## 📱 Available Applications

### 1. Production CRM
- **URL**: http://localhost:8004
- **Features**: Full dashboard, lead management, property listings, AI content generation
- **Backend**: MongoDB database, FastAPI

### 2. Development Server
- **URL**: http://localhost:8003
- **Features**: API endpoints, Facebook integration testing
- **Backend**: In-memory database (development), FastAPI

### 3. Chat Assistant
- **URL**: http://localhost:8000/chat
- **Usage**: Type `start` to begin the assistant flow

## 🔑 Demo Credentials
- **Email**: demo@mumbai.com
- **Password**: demo123

## 🌟 Core Features

### 📊 Dashboard
- **Quick Stats**: Leads, properties, conversion rates
- **Weekly Trends**: Lead generation analytics
- **Pipeline Visualization**: Sales funnel stages
- **Lead Sources**: Distribution by channel

### 🤖 AI Content Generation
- **Property Descriptions**: AI-generated compelling listings
- **Social Media Posts**: Facebook-ready content
- **Multi-language**: 7 languages including English, Spanish, French
- **Copy to Facebook**: Seamless integration with posting workflow

### 👥 Lead Management
- **CRUD Operations**: Create, view, update, delete leads
- **Status Tracking**: Lead lifecycle management
- **Search & Filter**: Find leads by various criteria
- **Agent Assignment**: Multi-agent lead distribution

## 📱 Mobile App

### Core Features Implemented

#### 1. **Agent Onboarding Flow**
- 6-Step Comprehensive Onboarding
- Dynamic Branding System (Logo, Colors, Tags)
- Preferences & Workflow Settings

#### 2. **Dynamic Branding System**
- Real-time Brand Customization
- Custom Color Schemes
- Logo Integration

#### 3. **GROQ AI Integration**
- Lightning-fast AI Responses
- Smart Property Descriptions
- Market Analysis

#### 4. **Complete CRM System**
- Dashboard with real-time metrics
- Properties management
- Leads tracking with scoring
- AI Assistant with interactive chat

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

## 📸 Facebook Requirements

Ensure your Page has:
* ✅ `pages_manage_posts` & `pages_read_engagement`
* ✅ App has correct permissions and is live
* ✅ You are an admin of the Page

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

## 🧠 Architecture Notes

### Application Entrypoints
- **main.py** — Primary FastAPI backend for the modular AI assistant and APIs. Use this in development (uvicorn main:app --reload) and connect the React/Vite frontend to it.
- **app/main.py** — A separate lightweight modular web app for classic templates (login.html, dashboard.html). Do not run alongside main.py on the same port.
- **complete_production_crm.py** — A monolithic, all-in-one legacy app kept for reference and migration. Not recommended to run alongside the modular apps.

### Facebook Integration
- OAuth endpoints: /api/facebook/connect (redirects to Facebook) and /api/facebook/callback
- Page endpoints: /api/facebook/config, /pages, /select_page, /post
- In-memory AgentRepository stores connected_page and encrypted page tokens for demo only. Move to DB for production.

## 📌 TODO

* [ ] Auto-generate and upload logo/cover images
* [ ] Schedule Facebook posts
* [ ] Add Instagram integration
* [ ] Save user projects to database

## 📞 Support

For issues, questions, or contributions:
1. Check existing documentation in this repository
2. Review test plans in `tests/` directory
3. Follow contribution guidelines below

## 🧑‍💻 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

---

**Status**: Production-ready Real Estate AI CRM with MongoDB backend, Facebook integration, and AI-powered content generation. ✅

## 🧑‍💻 Author

**Amit Sajwan** — powered by Python, GenAI & LangGraph
