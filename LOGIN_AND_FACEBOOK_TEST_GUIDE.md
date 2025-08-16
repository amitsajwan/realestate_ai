# 🔐 Login Guide for Your Real Estate CRM

## 🎯 **How to Login and Test Facebook Integration**

### **Step 1: Access the Login Page**

Your server is running! Go to: **http://localhost:8003/**

You'll see the login form with demo credentials already shown.

### **Step 2: Login Options**

#### **Option A: Demo Account (Recommended for Testing)**
```
Email: demo@mumbai.com
Password: demo123
```

#### **Option B: Your Account (If Configured)**
```
Email: amitsajwan@gmail.com
Password: [Your configured password]
```

### **Step 3: Complete Login Process**

1. **Open Browser**: http://localhost:8003/
2. **Enter Credentials**: Use demo@mumbai.com / demo123
3. **Click "Login to Dashboard"**: Should redirect to dashboard
4. **Dashboard Loads**: You'll see the Real Estate CRM dashboard
5. **Find Facebook Panel**: Look for "Facebook Integration" section

### **Step 4: Test Facebook Integration**

Once logged in to the dashboard:

1. **Locate Facebook Integration Panel**
2. **Check Connection Status**: Should show "Not Connected" initially  
3. **Click "Connect Facebook"**: Should redirect to Facebook OAuth
4. **Login to Facebook**: Use your Facebook account (amitsajwan@gmail.com)
5. **Authorize Your App**: Grant permissions to "RealEstateAi"
6. **Get Redirected Back**: Should show "Connected" status
7. **Test Posting**: Create a test post to your Facebook page

---

## 🔍 **Troubleshooting Login Issues**

### **If Login Doesn't Work:**

#### **Check Server Logs**
Look for error messages in your terminal where the server is running.

#### **Try Different Accounts**
If demo account doesn't work, the authentication might be configured differently.

#### **Check Browser Console**
1. Press F12 in browser
2. Go to Console tab
3. Try login again
4. Look for error messages

#### **Verify API Endpoint**
Test the login endpoint directly:

```bash
curl -X POST http://localhost:8003/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo@mumbai.com","password":"demo123"}'
```

---

## 🎯 **What Should Happen After Login**

### **Successful Login Flow:**
1. ✅ Login form submits successfully
2. ✅ Token stored in localStorage
3. ✅ Redirected to `/dashboard`
4. ✅ Dashboard loads with various panels
5. ✅ Facebook Integration panel visible
6. ✅ No more 401 errors on Facebook API calls

### **Expected Dashboard Elements:**
- **Leads Management Panel**
- **Properties Panel**  
- **Facebook Integration Panel** ⭐ (This is what we want!)
- **System Status/Information**

---

## 🚀 **Quick Test Commands**

### **Test Login API Directly:**
```powershell
.\.venv\Scripts\python.exe -c "
import requests
import json

# Test login
login_data = {'email': 'demo@mumbai.com', 'password': 'demo123'}
response = requests.post('http://localhost:8003/api/login', json=login_data)

print(f'Login Status: {response.status_code}')
if response.status_code == 200:
    print('✅ Login successful!')
    token = response.json().get('token')
    print(f'Token received: {token[:20]}...' if token else 'No token')
else:
    print(f'❌ Login failed: {response.text}')
"
```

### **Test Authenticated Facebook Config:**
```powershell
# After successful login, test Facebook config with token
.\.venv\Scripts\python.exe -c "
import requests

# First login to get token
login_data = {'email': 'demo@mumbai.com', 'password': 'demo123'}
login_response = requests.post('http://localhost:8003/api/login', json=login_data)

if login_response.status_code == 200:
    token = login_response.json().get('token')
    
    # Test Facebook config with authentication
    headers = {'Authorization': f'Bearer {token}'}
    fb_response = requests.get('http://localhost:8003/api/facebook/config', headers=headers)
    
    print(f'Facebook Config Status: {fb_response.status_code}')
    if fb_response.status_code == 200:
        print('✅ Facebook integration ready!')
        print(f'Response: {fb_response.json()}')
    else:
        print(f'Facebook config: {fb_response.text}')
else:
    print('❌ Could not login to test Facebook config')
"
```

---

## 🎊 **Summary: Your Complete Test Flow**

### **Step-by-Step Testing:**

1. **Login**: http://localhost:8003/ with demo@mumbai.com / demo123
2. **Dashboard**: Should load at http://localhost:8003/dashboard  
3. **Facebook Panel**: Look for Facebook Integration section
4. **Connect Facebook**: Click button, should redirect to Facebook
5. **OAuth Flow**: Login with amitsajwan@gmail.com, authorize app
6. **Back to Dashboard**: Should show "Connected to Facebook"
7. **Post Test**: Create and post test content to Facebook

### **Success Indicators:**
- ✅ Login works without errors
- ✅ Dashboard loads completely
- ✅ Facebook Integration panel visible
- ✅ No 401 errors in browser console
- ✅ "Connect Facebook" redirects to Facebook OAuth
- ✅ After OAuth, shows connected status

**Your Facebook integration is ready to test once you login! 🚀**
