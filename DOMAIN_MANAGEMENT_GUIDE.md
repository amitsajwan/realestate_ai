# 🌐 Domain Management Guide

## 🎯 **Answer: Will it work with any domain?**

### **Current Configuration: LIMITED**
- ✅ **ngrok URLs**: Will work (all tiers)
- ✅ **Localhost**: Will work
- ✅ **Production domains**: Will work (if configured)
- ❌ **New ngrok URLs**: Won't work (until you update config)
- ❌ **Custom domains**: Won't work (until you add them)
- ❌ **Other tunneling services**: Won't work (until you add them)

## 🔧 **Solutions for Dynamic Domains**

### **Option 1: Update CORS Configuration (RECOMMENDED)**

When you get a new ngrok URL or domain, update the nginx config:

```nginx
# Add your new domain to the CORS whitelist
map $http_origin $cors_origin {
    default "";
    "~^https://your-domain\.com$" $http_origin;
    "~^https://.*\.ngrok-free\.app$" $http_origin;
    "~^https://.*\.ngrok\.io$" $http_origin;
    "~^https://.*\.ngrok\.app$" $http_origin;
    "~^https://your-new-ngrok-url\.ngrok-free\.app$" $http_origin;  # Add new URL
    "~^http://localhost:3000$" $http_origin;
}
```

### **Option 2: Use Dynamic CORS (DEVELOPMENT ONLY)**

For development/testing, use the dynamic CORS configuration:

```bash
# Copy the dynamic CORS config
cp docker/nginx-dynamic-cors.conf docker/nginx.conf

# Restart Docker
docker-compose down
docker-compose up -d
```

**⚠️ WARNING**: This allows ANY domain to access your API. Only use for development!

### **Option 3: Environment-Based CORS**

Create different nginx configs for different environments:

```bash
# Development (allows any domain)
cp docker/nginx-dynamic-cors.conf docker/nginx.conf

# Production (restricted domains)
cp docker/nginx.conf docker/nginx-production.conf
```

## 🚀 **Quick Fix for ngrok URL Changes**

### **Step 1: Get Your New ngrok URL**
```bash
ngrok http 80
# Copy the new URL: https://abc123.ngrok-free.app
```

### **Step 2: Update nginx.conf**
```nginx
# Add the new URL to the CORS whitelist
"~^https://abc123\.ngrok-free\.app$" $http_origin;
```

### **Step 3: Restart Docker**
```bash
docker-compose down
docker-compose up -d
```

## 📋 **Supported Domains (Current)**

### **✅ Will Work**
- `https://your-domain.com` (production)
- `https://*.your-domain.com` (subdomains)
- `https://*.ngrok-free.app` (ngrok free tier)
- `https://*.ngrok.io` (ngrok paid tier)
- `https://*.ngrok.app` (ngrok new domains)
- `https://*.localtunnel.me` (localtunnel)
- `https://*.serveo.net` (serveo)
- `https://*.loca.lt` (loca)
- `http://localhost:3000` (local development)
- `http://127.0.0.1:3000` (local development)

### **❌ Won't Work**
- New ngrok URLs (until added to config)
- Custom domains (until added to config)
- Other tunneling services (until added to config)

## 🔄 **Automated Domain Management**

### **Script to Update ngrok URL**
```bash
#!/bin/bash
# update-ngrok-url.sh

# Get current ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url')

# Update nginx config
sed -i "s/ngrok-free\.app.*/ngrok-free\.app$" $http_origin;\n    \"~^$NGROK_URL$\" $http_origin;/" docker/nginx.conf

# Restart Docker
docker-compose down
docker-compose up -d

echo "Updated nginx config with new ngrok URL: $NGROK_URL"
```

### **Environment Variables for Domains**
```env
# .env
ALLOWED_DOMAINS="your-domain.com,*.ngrok-free.app,*.ngrok.io,localhost:3000"
```

## 🎯 **Best Practices**

### **For Development**
- Use dynamic CORS configuration
- Allow all domains for testing
- Use environment variables for domain management

### **For Production**
- Use strict CORS whitelist
- Only allow specific domains
- Regularly audit allowed domains
- Use environment-specific configurations

### **For ngrok Testing**
- Use ngrok paid tier for static domains
- Update CORS config when URLs change
- Consider using environment variables

## 🚨 **Security Considerations**

### **Dynamic CORS (Development)**
```nginx
# Allows ANY domain - SECURITY RISK!
add_header Access-Control-Allow-Origin $http_origin always;
```

### **Whitelist CORS (Production)**
```nginx
# Only allows specific domains - SECURE
map $http_origin $cors_origin {
    default "";
    "~^https://your-domain\.com$" $http_origin;
}
add_header Access-Control-Allow-Origin $cors_origin always;
```

## 📝 **Quick Reference**

### **Add New Domain**
1. Edit `docker/nginx.conf`
2. Add domain to CORS whitelist
3. Run `docker-compose restart nginx`

### **Allow All Domains (Dev Only)**
1. Copy `docker/nginx-dynamic-cors.conf` to `docker/nginx.conf`
2. Run `docker-compose restart nginx`

### **Check Current Domains**
```bash
# View current nginx config
cat docker/nginx.conf | grep -A 10 "map \$http_origin"
```

## 🎉 **Summary**

**Current Status**: Limited to whitelisted domains
**ngrok URLs**: Will work if added to whitelist
**Custom Domains**: Will work if added to whitelist
**Dynamic Domains**: Use dynamic CORS config for development

**Recommendation**: Use environment-specific configurations for different deployment scenarios.