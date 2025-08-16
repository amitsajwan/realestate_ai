# 🎯 Visual Guide: Adding Facebook Redirect URI

## Based on Your Screenshot

Looking at the Facebook Login settings page you shared, here's exactly what to do:

### ✅ **Step-by-Step Instructions**

1. **Locate the "Valid OAuth Redirect URIs" section**
   - ✅ You can see this section in your screenshot
   - It's in the middle of the page under "Client OAuth settings"

2. **Find the input field**
   - ✅ Below the "Valid OAuth redirect URIs" text, there's an empty input field
   - This is where you need to enter your callback URL

3. **Add your redirect URI**
   - Click in the empty input field
   - Type exactly: `http://localhost:8003/api/facebook/callback`
   - Make sure there are no extra spaces or characters

4. **Save the changes**
   - Scroll to the bottom of the page
   - Click the "Save Changes" button

### 🔍 **Visual Reference from Your Screenshot:**

```
Valid OAuth Redirect URIs
A manually specified redirect_uri used with Login on the web must exactly match one of the URIs listed here.

[    EMPTY INPUT FIELD    ] <- Enter your URI here
```

**Enter exactly:** `http://localhost:8003/api/facebook/callback`

### ⚠️ **Important Notes:**

- **Must match exactly** - no trailing slashes, no extra characters
- **Use HTTP (not HTTPS)** for localhost development
- **Port 8003** must match your server port

### ✅ **After Adding:**

1. Click "Save Changes"
2. Test the redirect URI validator on the same page
3. Your OAuth flow should now work without the "invalid redirect URI" error

### 🚀 **Next Step:**
Once saved, go back to your dashboard at `http://localhost:8003/dashboard` and test the "Connect Facebook" button!
