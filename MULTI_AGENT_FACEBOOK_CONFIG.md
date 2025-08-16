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

Update `core/config.py` to support agent-specific configs:
