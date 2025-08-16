# 🏢 Multi-Agent Facebook Configuration Guide

## 🎯 **Problem**: Multiple Real Estate Agents, One Application

Your application serves **multiple real estate agents**, each needing their own:
- Facebook Business Page
- Facebook App credentials
- Independent posting capabilities
- Separate OAuth tokens

## 🔧 **Solution Options**

### **Option 1: Agent-Specific Environment Files (Recommended)**

Create separate environment files for each agent:

```bash
# Directory structure
├── .env.defaults          # Default/shared settings
├── .env.agent1           # John Smith's Facebook app
├── .env.agent2           # Jane Doe's Facebook app
├── .env.agent3           # Mike Johnson's Facebook app
└── agents/
    ├── john-smith/
    ├── jane-doe/
    └── mike-johnson/
```

### **Option 2: Database-Based Agent Configuration (Production)**

Store Facebook app credentials in database per agent:

```sql
agents_facebook_config
├── agent_id (Primary Key)
├── fb_app_id
├── fb_app_secret  (encrypted)
├── fb_page_id
├── created_at
└── updated_at
```

### **Option 3: Single Facebook App, Multiple Pages (Simplest)**

One Facebook app that manages multiple pages for different agents.

---

## 🚀 **Implementation: Option 1 (Agent-Specific Configs)**

### Step 1: Create Agent Environment Files

**.env.defaults** (Shared settings):
```env
# Shared Application Settings
SECRET_KEY=your_shared_secret_key
BASE_URL=http://localhost:8003
FRONTEND_URL=http://localhost:3000
MONGO_URI=mongodb://localhost:27017/
REDIS_HOST=localhost
REDIS_PORT=6379
GROQ_API_KEY=your_groq_api_key

# Facebook API Version (same for all agents)
FB_GRAPH_API_VERSION=v19.0
FEATURE_FACEBOOK_PERSIST=true
```

**.env.agent1** (John Smith):
```env
# Agent: John Smith
AGENT_ID=john-smith
AGENT_NAME=John Smith
AGENT_BRAND=Smith Real Estate

# John's Facebook App
FB_APP_ID=123456789012345
FB_APP_SECRET=john_smith_facebook_app_secret
FB_PAGE_ID=john_smith_page_id
```

**.env.agent2** (Jane Doe):
```env
# Agent: Jane Doe  
AGENT_ID=jane-doe
AGENT_NAME=Jane Doe
AGENT_BRAND=Doe Properties

# Jane's Facebook App
FB_APP_ID=678901234567890
FB_APP_SECRET=jane_doe_facebook_app_secret
FB_PAGE_ID=jane_doe_page_id
```

### Step 2: Update Configuration System

I've created a new multi-agent configuration system for you:

**Files Created:**
- `core/multi_agent_config.py` - Enhanced configuration system
- `api/endpoints/facebook_multi_agent.py` - Multi-agent Facebook endpoints
- `.env.defaults` - Shared application settings
- `.env.john-smith` - Example agent configuration
- `.env.jane-doe` - Example agent configuration

### Step 3: Update Your Application

**Option A: Use New Multi-Agent Endpoints**

Add to your `app/main.py`:

```python
# Add multi-agent Facebook routes
from api.endpoints import facebook_multi_agent
app.include_router(facebook_multi_agent.router, prefix="/api/facebook", tags=["facebook-multi-agent"])
```

**Option B: Keep Current System + Agent Selection**

Update your existing Facebook endpoints to accept an `agent_id` parameter.

---

## 🎯 **Usage Examples**

### For Agent "john-smith":

1. **Create Facebook Developer App** for John Smith
2. **Update `.env.john-smith`** with real credentials
3. **Agent Dashboard**: `http://localhost:8003/agents/john-smith`
4. **Facebook Config**: `GET /api/facebook/config/john-smith`
5. **Connect Facebook**: `GET /api/facebook/connect/john-smith`
6. **Post Content**: `POST /api/facebook/post/john-smith`

### For Agent "jane-doe":

1. **Create separate Facebook Developer App** for Jane Doe
2. **Update `.env.jane-doe`** with her credentials  
3. **Agent Dashboard**: `http://localhost:8003/agents/jane-doe`
4. **Facebook Config**: `GET /api/facebook/config/jane-doe`

---

## 🚀 **Implementation Strategy**

### **Phase 1: Single Agent Testing (Current)**
Use your existing setup with one agent to test Facebook integration:

```env
# Current .env file
FB_APP_ID=your_test_facebook_app_id
FB_APP_SECRET=your_test_facebook_app_secret
FB_GRAPH_API_VERSION=v19.0
```

### **Phase 2: Multi-Agent Rollout** 
1. Each agent creates their own Facebook Business account
2. Each agent creates their own Facebook Developer app
3. Each agent gets their own `.env.{agent-id}` file
4. Application automatically loads the right config based on agent context

---

## 📋 **Agent Onboarding Checklist**

For each new agent joining your platform:

### **Agent Setup:**
- [ ] Create Facebook Business account
- [ ] Create Facebook Business page
- [ ] Create Facebook Developer account  
- [ ] Create Facebook app for their business
- [ ] Configure OAuth redirect URIs
- [ ] Get App ID and App Secret

### **System Configuration:**
- [ ] Create `.env.{agent-id}` file
- [ ] Add agent's Facebook credentials
- [ ] Set up agent branding/info
- [ ] Test Facebook connection
- [ ] Verify posting works

### **Go-Live:**
- [ ] Agent tests dashboard access
- [ ] Agent connects their Facebook account
- [ ] Agent posts test content
- [ ] Monitor for any issues

---

## 🔐 **Security Considerations**

### **Environment File Security:**
```bash
# Add to .gitignore
.env*
!.env.example
!.env.defaults
```

### **Production Deployment:**
- Store credentials in secure vault (Azure Key Vault, AWS Secrets Manager)
- Use environment-specific configurations
- Rotate secrets regularly
- Monitor for suspicious access

---

## 🎯 **Quick Start for Testing**

### **Right Now (Single Agent):**
1. Keep using your current `.env` file
2. Create one Facebook Developer app
3. Test with current setup
4. Once working, expand to multi-agent

### **Later (Multi-Agent):**
1. Each agent creates their Facebook app
2. Create agent-specific `.env.{agent-id}` files
3. Switch to multi-agent endpoints
4. Each agent has independent Facebook integration

---

## 🤝 **Recommended Approach**

**For Your Current Testing:**
```env
# Use your existing .env file
FB_APP_ID=your_single_test_facebook_app_id
FB_APP_SECRET=your_single_test_facebook_app_secret
FB_GRAPH_API_VERSION=v19.0
```

**For Production with Multiple Agents:**
```env
# .env.defaults (shared)
FB_GRAPH_API_VERSION=v19.0
FEATURE_MULTI_AGENT=true

# .env.agent1 (John's Facebook app)
FB_APP_ID=john_facebook_app_id
FB_APP_SECRET=john_facebook_app_secret

# .env.agent2 (Jane's Facebook app) 
FB_APP_ID=jane_facebook_app_id
FB_APP_SECRET=jane_facebook_app_secret
```

This way each agent has **complete control** over their Facebook integration while sharing the same application infrastructure!
