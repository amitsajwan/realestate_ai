# PropertyAI - Technical Documentation
*Developer Guide and Architecture Reference*

## 🏗️ System Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │  Mobile App     │    │  External APIs  │
│   (Bootstrap)   │    │ (React Native)  │    │ (Facebook, AI)  │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                    ┌─────────────┴───────────┐
                    │    FastAPI Backend      │
                    │   (simple_backend.py)   │
                    └─────────────┬───────────┘
                                  │
                    ┌─────────────┴───────────┐
                    │   SQLite Database       │
                    │   (propertyai.db)       │
                    └─────────────────────────┘
```

### Core Components

#### 1. **Backend Server (simple_backend.py)**
- **Framework**: FastAPI with Uvicorn ASGI server
- **Authentication**: JWT tokens with bcrypt password hashing
- **Database**: SQLite with manual SQL queries
- **CORS**: Configured for cross-origin requests
- **Static Files**: Serves CSS, JS, and images

#### 2. **Database Layer (database_setup.py)**
- **Database**: SQLite for development, PostgreSQL for production
- **Tables**: 8 core tables for users, properties, Facebook integration
- **Migrations**: Manual schema management
- **Sample Data**: Demo users and properties for testing

#### 3. **AI Integration (genai_onboarding.py)**
- **LLM Provider**: GROQ API with Llama models
- **Content Types**: Branding, descriptions, social media posts
- **Localization**: Multi-language content generation
- **Caching**: Response caching for performance

#### 4. **Facebook Integration (facebook_integration.py)**
- **OAuth 2.0**: Complete Facebook authentication flow
- **Graph API**: Facebook API v19.0 integration
- **Token Management**: Encrypted long-term token storage
- **Page Management**: Multiple page support per user

## 🔧 Detailed Technical Specifications

### Backend API Structure

#### FastAPI Application Setup
```python
# simple_backend.py
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="PropertyAI - Real Estate CRM",
    version="1.0.0",
    description="AI-Powered Real Estate CRM with Facebook Integration"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Authentication System
```python
# JWT Token Generation
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm="HS256")

# Password Hashing
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
```

#### Database Schema Details

##### Users Table
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL,
    company TEXT DEFAULT 'Real Estate',
    role TEXT DEFAULT 'agent',
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
```

##### Agent Profiles Table
```sql
CREATE TABLE agent_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    phone TEXT,
    whatsapp TEXT,
    experience_years TEXT,
    specialization_areas TEXT,
    languages TEXT,
    profile_photo_url TEXT,
    bio TEXT,
    contact_preferences TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

##### Properties Table
```sql
CREATE TABLE properties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    address TEXT NOT NULL,
    price TEXT NOT NULL,
    property_type TEXT NOT NULL,
    bedrooms INTEGER,
    bathrooms INTEGER,
    features TEXT,
    ai_content TEXT,
    tone TEXT DEFAULT 'Professional',
    language TEXT DEFAULT 'English',
    ai_generated BOOLEAN DEFAULT 0,
    facebook_posted BOOLEAN DEFAULT 0,
    views INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

##### Facebook Integration Tables
```sql
-- Facebook Connections
CREATE TABLE facebook_connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    facebook_user_id TEXT NOT NULL,
    facebook_user_name TEXT,
    access_token TEXT NOT NULL,
    token_expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Facebook Page Tokens
CREATE TABLE facebook_page_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    page_id TEXT NOT NULL,
    page_name TEXT,
    access_token TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Facebook Posts
CREATE TABLE facebook_posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    post_id TEXT NOT NULL,
    message TEXT,
    property_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);
```

### AI Content Generation System

#### GROQ Integration
```python
# genai_onboarding.py
from groq import Groq

class GenAIOnboardingService:
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    async def generate_agent_branding(self, agent_data):
        prompt = f"""
        Create professional branding for a real estate agent:
        Name: {agent_data['name']}
        Company: {agent_data['company']}
        Experience: {agent_data['experience_years']}
        Specialization: {agent_data['specialization_areas']}
        Languages: {agent_data['languages']}
        Market: {agent_data['market']}
        
        Generate:
        1. Professional tagline (max 80 chars)
        2. About section (150-200 words)
        3. Social media bio (100 chars)
        4. Professional color scheme
        """
        
        response = self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=800
        )
        
        return self._parse_branding_response(response.choices[0].message.content)
```

#### Content Localization
```python
# Multi-language support
SUPPORTED_LANGUAGES = {
    "English": "en",
    "Hindi": "hi", 
    "Marathi": "mr",
    "Gujarati": "gu"
}

def generate_localized_content(property_data, language="English", tone="Professional"):
    language_prompts = {
        "Hindi": "हिंदी में लिखें",
        "Marathi": "मराठीत लिहा", 
        "Gujarati": "ગુજરાતીમાં લખો"
    }
    
    prompt = f"""
    Create a {tone.lower()} property listing in {language}:
    Property: {property_data['property_type']} at {property_data['address']}
    Price: {property_data['price']}
    Features: {property_data['features']}
    
    {language_prompts.get(language, "")}
    """
```

### Facebook Integration Details

#### OAuth Flow Implementation
```python
# facebook_integration.py
class FacebookIntegration:
    def get_oauth_url(self, user_id: str, redirect_uri: str) -> str:
        state = secrets.token_urlsafe(32)
        self._save_oauth_state(user_id, state)
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': redirect_uri,
            'scope': 'pages_read_engagement,pages_manage_posts,pages_show_list',
            'response_type': 'code',
            'state': state
        }
        
        return f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"
    
    async def handle_oauth_callback(self, code: str, state: str, redirect_uri: str):
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                f"{self.base_url}/oauth/access_token",
                data={
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                    'redirect_uri': redirect_uri,
                    'code': code
                }
            )
            
            token_data = token_response.json()
            access_token = token_data['access_token']
            
            # Get user info and save connection
            user_response = await client.get(
                f"{self.base_url}/me",
                params={'access_token': access_token, 'fields': 'id,name'}
            )
            
            return user_response.json()
```

#### Token Encryption
```python
# Secure token storage
from cryptography.fernet import Fernet

def _setup_encryption(self):
    key = os.getenv("ENCRYPTION_KEY")
    if not key:
        key = Fernet.generate_key()
        # Store key securely in production
    self.cipher_suite = Fernet(key)

def _encrypt_token(self, token: str) -> str:
    return self.cipher_suite.encrypt(token.encode()).decode()

def _decrypt_token(self, encrypted_token: str) -> str:
    return self.cipher_suite.decrypt(encrypted_token.encode()).decode()
```

### Frontend Architecture

#### Modern Onboarding Flow
```javascript
// templates/modern_onboarding.html
class ModernOnboarding {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 7;
        this.formData = {};
        this.facebookConfig = {
            option: null,
            connected: false
        };
    }
    
    async generateBranding() {
        const userData = this.collectUserData();
        
        const response = await fetch('/api/ai/generate-branding', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(userData)
        });
        
        const result = await response.json();
        this.displayBrandingResults(result.branding);
    }
    
    async testFacebookConfig() {
        const appId = document.querySelector('input[name="facebook_app_id"]').value;
        const appSecret = document.querySelector('input[name="facebook_app_secret"]').value;
        const pageId = document.querySelector('input[name="facebook_page_id"]').value;
        
        const response = await fetch('/api/facebook/test-config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({app_id: appId, app_secret: appSecret, page_id: pageId})
        });
        
        return response.json();
    }
}
```

#### Property Management System
```javascript
// Dashboard property functions
async function generateAIContent() {
    const propertyData = this.getFormData();
    
    const response = await fetch('/api/listings/generate', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            ...propertyData,
            template: "just_listed",
            tone: propertyData.tone || "Professional",
            language: propertyData.language || "English"
        })
    });
    
    const aiContent = await response.json();
    this.showContentPreview(aiContent);
}

async function postToFacebook() {
    const response = await fetch('/api/facebook/post', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            property_id: currentProperty.id,
            message: aiGeneratedContent.caption,
            tone: currentProperty.tone,
            language: currentProperty.language
        })
    });
    
    return response.json();
}
```

## 🧪 Testing Framework

### Playwright Test Structure
```typescript
// tests/modern-onboarding-flow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Modern Onboarding Flow', () => {
    test('Complete 7-step onboarding process', async ({ page }) => {
        await page.goto('http://localhost:8003/modern-onboarding');
        
        // Step 1: Personal Information
        await page.fill('input[name="name"]', 'Test Agent');
        await page.fill('input[name="email"]', `test-${Date.now()}@example.com`);
        await page.click('#nextBtn');
        
        // Step 2: Company Details
        await page.selectOption('select[name="experience_years"]', '3-5 years');
        await page.fill('input[name="specialization_areas"]', 'Mumbai, Bandra');
        await page.click('#nextBtn');
        
        // Continue through all steps...
        // Step 5: Facebook Integration
        await page.click('text=Quick Start (Recommended)');
        await expect(page.locator('.facebook-option.selected')).toBeVisible();
        
        // Step 7: Completion
        await expect(page.locator('text=Congratulations!')).toBeVisible();
    });
});
```

### API Testing
```typescript
// tests/facebook-config-test.spec.ts
test('Facebook configuration validation', async ({ page }) => {
    const response = await page.request.post('/api/facebook/test-config', {
        data: {
            app_id: 'test123',
            app_secret: 'test456',
            page_id: 'test789'
        }
    });
    
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.success).toBe(false);
    expect(data.error).toContain('Invalid App ID or App Secret');
});
```

## 📦 Deployment Configuration

### Environment Setup
```bash
# .env file
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxx
FB_APP_ID=123456789012345
FB_APP_SECRET=abcdef123456789abcdef123456789ab
FB_REDIRECT_URI=https://yourdomain.com/api/facebook/callback
JWT_SECRET_KEY=your-super-secret-jwt-key
ENCRYPTION_KEY=your-fernet-encryption-key
DATABASE_URL=postgresql://user:password@localhost:5432/propertyai
```

### Production Deployment
```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8003

CMD ["python", "simple_backend.py"]
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8003:8003"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/propertyai
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      POSTGRES_DB: propertyai
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

## 🔍 Performance Optimization

### Database Optimization
```sql
-- Indexes for common queries
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_properties_user_id ON properties(user_id);
CREATE INDEX idx_facebook_connections_user_id ON facebook_connections(user_id);
CREATE INDEX idx_agent_profiles_user_id ON agent_profiles(user_id);
```

### API Response Caching
```python
from functools import lru_cache
import asyncio

@lru_cache(maxsize=128)
def cached_ai_generation(property_hash: str):
    # Cache AI-generated content for similar properties
    pass

# Async caching for API responses
async def get_facebook_pages_cached(user_id: int):
    cache_key = f"fb_pages_{user_id}"
    cached = await redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    pages = await facebook_integration.get_user_pages(user_id)
    await redis_client.setex(cache_key, 300, json.dumps(pages))
    return pages
```

### Frontend Optimization
```javascript
// Lazy loading for large datasets
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            loadMoreProperties();
        }
    });
});

// Debounced search
const debouncedSearch = debounce((query) => {
    searchProperties(query);
}, 300);

// Image optimization
function optimizeImage(url, width = 400) {
    return url + `?w=${width}&q=80&fm=webp`;
}
```

## 🔐 Security Implementation

### Authentication Security
```python
# Rate limiting for login attempts
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, user_data: UserLogin):
    # Login implementation with rate limiting
    pass
```

### Data Validation
```python
from pydantic import BaseModel, EmailStr, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v
```

### SQL Injection Prevention
```python
# Parameterized queries
def get_user_properties(user_id: int):
    cursor.execute("""
        SELECT * FROM properties 
        WHERE user_id = ? AND is_active = 1
        ORDER BY created_at DESC
    """, (user_id,))
    return cursor.fetchall()
```

---

*PropertyAI Technical Documentation - Version 1.0*

