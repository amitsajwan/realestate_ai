# 🧪 **Facebook Testing Guide - No Business Setup Required**

## 🎯 **Testing Facebook Integration Without Business Setup**

You can test Facebook integration using **Facebook's Developer Tools** without needing a business account. Here's how:

## 🚀 **Option 1: Facebook Developer App (Recommended)**

### **Step 1: Create Facebook Developer Account**
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Click **"Get Started"** or **"My Apps"**
3. Use your **personal Facebook account** (no business required)
4. Accept Facebook Developer Terms

### **Step 2: Create a Test App**
```bash
# In Facebook Developer Console:
1. Click "Create App"
2. Choose "Consumer" or "Other" (not Business)
3. App Name: "PropertyAI Test"
4. App Contact Email: your-email@example.com
```

### **Step 3: Configure Facebook Login**
```bash
# In your Facebook App:
1. Go to "Facebook Login" → "Settings"
2. Add Valid OAuth Redirect URIs:
   - http://localhost:8000/api/v1/facebook/callback
   - https://your-ngrok-url.ngrok-free.app/api/v1/facebook/callback
3. Save changes
```

### **Step 4: Get App Credentials**
```bash
# From Facebook App Dashboard:
1. Go to "Settings" → "Basic"
2. Copy "App ID" → FB_APP_ID
3. Copy "App Secret" → FB_APP_SECRET
```

## 🧪 **Option 2: Mock Facebook Service (Development)**

### **Create Mock Facebook Service**
```python
# backend/app/services/mock_facebook_service.py
class MockFacebookService:
    """Mock Facebook service for development testing"""
    
    def __init__(self):
        self.test_users = {
            "test_user_1": {
                "id": "123456789",
                "name": "Test User",
                "email": "test@example.com",
                "access_token": "mock_access_token_123"
            }
        }
    
    async def mock_oauth_callback(self, code: str):
        """Mock OAuth callback"""
        return {
            "access_token": "mock_access_token_123",
            "user_id": "123456789",
            "expires_in": 3600
        }
    
    async def mock_get_user_info(self, access_token: str):
        """Mock user info retrieval"""
        return {
            "id": "123456789",
            "name": "Test User",
            "email": "test@example.com",
            "picture": {"data": {"url": "https://via.placeholder.com/150"}}
        }
```

## 🔧 **Option 3: Environment-Based Testing**

### **Development Environment Setup**
```bash
# .env.development
ENVIRONMENT=development
FB_APP_ID=your_test_app_id
FB_APP_SECRET=your_test_app_secret
FB_PAGE_ID=test_page_id
FB_PAGE_TOKEN=test_page_token
USE_MOCK_FACEBOOK=true
```

### **Update Facebook Service for Testing**
```python
# backend/app/services/facebook_service.py
class FacebookService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.use_mock = os.getenv("USE_MOCK_FACEBOOK", "false").lower() == "true"
        
        if self.use_mock:
            self.client_id = "mock_app_id"
            self.client_secret = "mock_app_secret"
        else:
            self.client_id = os.getenv("FB_APP_ID", settings.FB_APP_ID)
            self.client_secret = os.getenv("FB_APP_SECRET", settings.FB_APP_SECRET)
```

## 🎮 **Testing Scenarios**

### **1. OAuth Flow Testing**
```bash
# Test OAuth without real Facebook
curl -X GET "http://localhost:8000/api/v1/facebook/auth" \
  -H "Authorization: Bearer your_test_token"

# Expected Response:
{
  "auth_url": "https://www.facebook.com/v19.0/dialog/oauth?client_id=...",
  "state": "random_state_string"
}
```

### **2. Callback Testing**
```bash
# Test callback with mock data
curl -X GET "http://localhost:8000/api/v1/facebook/callback?code=mock_code&state=test_state"

# Expected Response:
{
  "success": true,
  "message": "Facebook connected successfully",
  "user": {
    "id": "123456789",
    "name": "Test User",
    "email": "test@example.com"
  }
}
```

### **3. Post Creation Testing**
```bash
# Test post creation
curl -X POST "http://localhost:8000/api/v1/facebook/posts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_test_token" \
  -d '{
    "message": "Test property post",
    "property_id": "test_property_123"
  }'
```

## 🛠️ **Quick Setup Commands**

### **1. Start with Mock Facebook**
```powershell
# Set environment for testing
$env:USE_MOCK_FACEBOOK="true"
$env:FB_APP_ID="mock_app_id"
$env:FB_APP_SECRET="mock_app_secret"

# Start local development
.\start-local.ps1
```

### **2. Test Facebook Endpoints**
```powershell
# Test Facebook auth
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/facebook/auth" -Method GET

# Test Facebook callback
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/facebook/callback?code=test&state=test" -Method GET
```

## 📱 **Facebook Test Users (If Using Real App)**

### **Create Test Users**
```bash
# In Facebook Developer Console:
1. Go to "Roles" → "Test Users"
2. Click "Add Test Users"
3. Create 2-3 test users
4. Use these for testing OAuth flow
```

### **Test User Permissions**
```bash
# Test users can:
- Login to your app
- Test OAuth flow
- Create posts (if page connected)
- Test all Facebook features
```

## 🎯 **Testing Checklist**

### **✅ OAuth Flow**
- [ ] Facebook login URL generation
- [ ] OAuth callback handling
- [ ] Access token exchange
- [ ] User info retrieval

### **✅ Post Management**
- [ ] Create property posts
- [ ] Edit post content
- [ ] Delete posts
- [ ] Post scheduling

### **✅ Campaign Management**
- [ ] Create ad campaigns
- [ ] Set budgets and targeting
- [ ] Monitor campaign performance
- [ ] Pause/resume campaigns

## 🚀 **Production vs Development**

### **Development (Testing)**
```bash
# Use mock service or test app
USE_MOCK_FACEBOOK=true
FB_APP_ID=test_app_id
FB_APP_SECRET=test_app_secret
```

### **Production (Real Business)**
```bash
# Use real business app
USE_MOCK_FACEBOOK=false
FB_APP_ID=real_business_app_id
FB_APP_SECRET=real_business_app_secret
FB_PAGE_ID=real_business_page_id
FB_PAGE_TOKEN=real_business_page_token
```

## 🎉 **Summary**

**You can test Facebook integration without a business setup by:**

1. **Using Facebook Developer App** (personal account)
2. **Creating mock services** for development
3. **Using test users** for OAuth testing
4. **Environment-based configuration** for different stages

**No business account required for development and testing!** 🚀