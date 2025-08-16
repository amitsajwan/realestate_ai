# 🔧 Environment Variables Setup Guide

## 📋 **Current Status Analysis**

✅ **What You Have:**
- GROQ API Key configured
- Facebook Page ID and Page Token
- Basic application settings
- AI service tokens (Stability AI, Hugging Face)

⚠️ **What You Need:**
- Facebook App ID and App Secret (from Facebook Developer Console)
- These are different from your Page ID and Page Token

---

## 🎯 **Facebook Integration Requirements**

### **Current Setup:**
```env
FB_PAGE_ID=699986296533656  ✅ You have this
FB_PAGE_TOKEN=EAAPpYZA...    ✅ You have this
```

### **Missing for OAuth Integration:**
```env
FB_APP_ID=your_app_id_here        ❌ Need this
FB_APP_SECRET=your_app_secret_here ❌ Need this
```

---

## 🚀 **Step-by-Step Facebook Developer Setup**

### **Step 1: Access Facebook Developers**
1. Go to [https://developers.facebook.com/](https://developers.facebook.com/)
2. Log in with your Facebook account
3. Click **"My Apps"** in top navigation

### **Step 2: Create New App**
1. Click **"Create App"**
2. Choose **"Business"** as app type
3. Fill in details:
   - **App Name**: "Real Estate CRM - [Your Name]"
   - **App Contact Email**: Your email
   - **Business Account**: Create or select one

### **Step 3: Get App Credentials**
1. In your new app dashboard, go to **Settings** → **Basic**
2. You'll see:
   ```
   App ID: 1234567890123456
   App Secret: [Show] <- Click to reveal
   ```
3. **Copy both values!**

### **Step 4: Configure Facebook Login**
1. Go to **Products** → **Add Product**
2. Find **Facebook Login** → Click **Set Up**
3. Choose **Web** platform
4. In **Facebook Login Settings**:
   - **Valid OAuth Redirect URIs**: 
     ```
     http://localhost:8003/api/facebook/callback
     ```
   - **Client OAuth Settings**: Enable "Web OAuth Login"

### **Step 5: Set App Permissions**
1. Go to **App Review** → **Permissions and Features**
2. Request these permissions:
   - `pages_show_list` - List user's pages
   - `pages_manage_posts` - Post to pages
   - `pages_read_engagement` - Read page insights

---

## 📝 **Update Your .env File**

Replace these placeholder values in your `.env` file:

```env
# Replace these with your actual Facebook App credentials
FB_APP_ID=1234567890123456
FB_APP_SECRET=abcd1234efgh5678ijkl9012mnop3456
```

**Example with real values:**
```env
# Facebook Developer App Credentials
FB_APP_ID=1234567890123456
FB_APP_SECRET=abcd1234efgh5678ijkl9012mnop3456
FB_GRAPH_API_VERSION=v19.0

# Your existing Facebook Page (keep these)
FB_PAGE_ID=699986296533656
FB_PAGE_TOKEN=EAAPpYZA01aaABPAO3jrPaZCFOv1HvvUxFpbZBLbrBFouXoepvQhK89yoW4fvIfZAe520WFartuqvZBn1m4VgANyCRcGSqmssiJlejbDaIAeJUkvVMMZApECEAvbonkT43T3ljaZBYVC0bjzBYyxX6GHrZCirnZCZBT5iQmCp8VZBxDq0C9lKf1yheJBkygNW7PKLEAAwos560EbbpD5lgiiKKVPjfSTwoGYJ3Xcu8ExTNX3hZBoZD
```

---

## 🧪 **Testing Your Configuration**

### **After updating .env:**

1. **Restart your server**:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8003
   ```

2. **Open dashboard**:
   ```
   http://localhost:8003/dashboard
   ```

3. **Test Facebook connection**:
   - Look for Facebook Integration panel
   - Click "Connect Facebook"
   - Should redirect to Facebook OAuth (not error)

### **Expected Behavior:**
- ✅ No 401 error on `/api/facebook/config`
- ✅ "Connect Facebook" redirects to Facebook
- ✅ After authorization, redirects back to dashboard
- ✅ Shows connected Facebook pages

---

## 🔐 **Security Best Practices**

### **Environment File Security:**
```bash
# Add to .gitignore (if not already there)
.env
.env.local
.env.*.local
```

### **Production Considerations:**
```env
# For production, use environment variables or secure vaults
SECRET_KEY=generate-a-strong-secret-key-for-production
FB_APP_SECRET=never-commit-this-to-git
```

---

## 🎯 **Quick Checklist**

- [ ] Facebook Developer account created
- [ ] Facebook App created (Business type)
- [ ] Facebook Login product added
- [ ] OAuth redirect URI configured: `http://localhost:8003/api/facebook/callback`
- [ ] App ID and App Secret copied
- [ ] .env file updated with real credentials
- [ ] Server restarted
- [ ] Dashboard tested
- [ ] "Connect Facebook" flow tested

---

## ❓ **Common Issues & Solutions**

### **Issue**: "Invalid redirect URI"
**Solution**: Make sure redirect URI in Facebook app exactly matches:
```
http://localhost:8003/api/facebook/callback
```

### **Issue**: "App not set up for this login method"
**Solution**: Add Facebook Login product to your app

### **Issue**: Still getting 401 errors
**Solution**: Check that `FB_APP_ID` and `FB_APP_SECRET` are not placeholder values

### **Issue**: "Invalid client_id"
**Solution**: Verify your App ID is correct (numbers only, no spaces)

---

## 🎉 **Success Indicators**

When everything is working:
- Dashboard loads without Facebook API errors
- "Connect Facebook" redirects to Facebook OAuth
- After authorization, you see "Connected" status
- You can select Facebook pages to post to
- Test posts appear on your Facebook page

**You're ready to go live with Facebook integration!** 🚀
