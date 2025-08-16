# Facebook Integration Setup Guide

## 🎯 Current Status (August 2025)
- ✅ **Facebook OAuth implementation complete** 
- ✅ **Dashboard integration working**
- ✅ **Encrypted token storage system**
- ✅ **Multi-page posting support**
- ✅ **Server running with Facebook routes loaded**

## 🚀 Quick Setup (Production Ready)

### 1. Create Facebook Developer App
1. Go to https://developers.facebook.com/
2. Create new app → Business → Real Estate AI CRM  
3. Add "Facebook Login" product
4. Add "Instagram Basic Display" (if needed)

### 2. Configure OAuth Settings
```
Valid OAuth Redirect URIs:
http://localhost:8003/api/facebook/callback
https://yourdomain.com/api/facebook/callback
```

### 3. Update Environment Variables
```bash
# .env file
FB_APP_ID=your_facebook_app_id_here
FB_APP_SECRET=your_facebook_app_secret_here  
FB_GRAPH_API_VERSION=v19.0
FEATURE_FACEBOOK_PERSIST=false
```

### 4. Test Integration
```bash
# Start server
uvicorn app.main:app --reload --port 8003

# Test endpoints
curl http://localhost:8003/api/facebook/config
curl http://localhost:8003/docs  # View API documentation
```

### 5. Complete OAuth Flow
1. Open http://localhost:8003/dashboard
2. Login with demo@mumbai.com/demo123  
3. Click "Connect Facebook" in Facebook Integration section
4. Complete Facebook authorization
5. Select Facebook page for posting
6. Test posting functionality

## 🔧 Technical Implementation

### API Endpoints Available:
- `GET /api/facebook/config` - Connection status
- `GET /api/facebook/connect` - Start OAuth flow
- `GET /api/facebook/callback` - OAuth callback
- `GET /api/facebook/pages` - List connected pages
- `POST /api/facebook/select_page` - Select active page  
- `POST /api/facebook/post` - Post to Facebook page

### Security Features:
- Fernet encryption for access tokens
- OAuth state verification (CSRF protection)
- User-scoped token storage
- Secure token retrieval system

### Database Integration:
- In-memory storage (development)
- MongoDB support (production) via FEATURE_FACEBOOK_PERSIST flag
- Encrypted token storage in both modes

## 🧪 Testing

### Manual Testing:
1. Dashboard UI loads Facebook integration panel
2. Connection status displays correctly
3. OAuth flow completes successfully  
4. Page selection works
5. Posting to Facebook succeeds

### API Testing:
```bash
# Test connection status
curl http://localhost:8003/api/facebook/config

# Test posting (after OAuth)
curl -X POST http://localhost:8003/api/facebook/post \
  -H "Content-Type: application/json" \
  -d '{"message": "Test post from Real Estate AI CRM!"}'
```

## 🚨 Troubleshooting

### Common Issues:

**401 Unauthorized Error:**
- Ensure FB_APP_ID and FB_APP_SECRET are set correctly
- Verify OAuth redirect URI matches exactly
- Check Facebook app is in Development/Live mode

**Connection Status "Not Connected":**
- Complete OAuth flow first via dashboard
- Ensure user has Facebook pages with admin access
- Check encrypted tokens are stored correctly

**Posting Fails:**
- Verify selected page has posting permissions
- Ensure page access token is valid and not expired
- Check Facebook page allows API posting

## 📱 Facebook App Requirements

### Required Products:
- Facebook Login (for OAuth)
- Instagram Basic Display (optional)

### Required Permissions:
- pages_show_list (to list user's pages)  
- pages_read_engagement (to read page info)
- pages_manage_posts (to post to pages)
- publish_to_groups (optional)

### App Review:
- Most permissions work in Development mode
- Submit for review before production deployment
- Test thoroughly with test pages first

## 🎯 Next Steps
1. Create Facebook Developer app with real credentials
2. Test complete OAuth flow
3. Verify posting works with real Facebook pages
4. Deploy to production with proper domain OAuth redirect
5. Submit Facebook app for review (if needed for permissions)
