# Environment Architecture Guide

## Overview

This document outlines the architectural approach to handling environment variables and configuration across different deployment contexts in the Real Estate AI CRM application.

## Architecture Principles

### 1. Environment Detection
- **Development**: Direct localhost connections for faster development
- **Docker/Container**: Service names and relative paths through proxy
- **Production**: Secure configurations with strict CORS policies

### 2. Configuration Hierarchy
1. Environment variables (highest priority)
2. Runtime detection (hostname-based)
3. Sensible defaults (lowest priority)

## Component Configuration

### Frontend (Next.js)

#### API Base URL Resolution
```typescript
// Smart environment detection in api.ts and onboarding.ts
if (envUrl === '') {
  return ''; // Use relative paths (Docker/nginx proxy)
}
if (envUrl) {
  return envUrl; // Use explicit URL
}
// Auto-detect: localhost = direct connection, others = relative paths
```

#### Configuration Options
- `NEXT_PUBLIC_API_BASE_URL=""` → Relative paths (Docker/Production)
- `NEXT_PUBLIC_API_BASE_URL="http://localhost:8000"` → Direct connection (Development)
- `NEXT_PUBLIC_API_BASE_URL="https://api.yourdomain.com"` → Custom API endpoint

### Backend (FastAPI)

#### Database Connection
```python
# Smart service name resolution
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
```

#### CORS Configuration
```python
# Environment-based CORS policies
if os.getenv("ENVIRONMENT") == "production":
    # Strict origin checking with regex patterns
else:
    # Permissive for development
```

## Deployment Contexts

### Local Development
```bash
# .env
ENVIRONMENT=development
MONGODB_URL=mongodb://localhost:27017
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

**Characteristics:**
- Direct database connection to localhost
- Frontend connects directly to backend
- Permissive CORS for development ease

### Docker Development
```yaml
# docker-compose.yml
environment:
  ENVIRONMENT: production
  MONGODB_URL: mongodb://admin:password123@mongodb:27017/real_estate_crm?authSource=admin
  NEXT_PUBLIC_API_BASE_URL: ""
```

**Characteristics:**
- Uses Docker service names (mongodb, backend, frontend)
- Frontend uses relative paths through nginx proxy
- Simulates production environment locally

### Production Deployment
```bash
# .env
ENVIRONMENT=production
MONGODB_URL=mongodb://admin:secure_password@mongodb:27017/real_estate_crm?authSource=admin
NEXT_PUBLIC_API_BASE_URL=""
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SECRET_KEY=very-secure-production-key
```

**Characteristics:**
- Secure database credentials
- Strict CORS policies
- Relative paths through production proxy
- Production-grade secrets

## Network Architecture

### Development Flow
```
Browser → http://localhost:3000 (Frontend)
       → http://localhost:8000 (Backend API)
       → mongodb://localhost:27017 (Database)
```

### Docker/Production Flow
```
Browser → http://domain.com (Nginx)
       → /api/* → backend:8000 (Backend API)
       → /* → frontend:3000 (Frontend)
       → mongodb://mongodb:27017 (Database)
```

## Security Considerations

### CORS Policies
- **Development**: Permissive (`allow_origins=["*"]`)
- **Production**: Strict regex patterns for ngrok and custom domains

### Environment Variables
- Never commit secrets to version control
- Use different secrets for each environment
- Rotate production secrets regularly

### Database Security
- Use authentication in production
- Separate databases for different environments
- Use Docker secrets for sensitive data

## Troubleshooting

### Common Issues

1. **Frontend can't connect to backend**
   - Check `NEXT_PUBLIC_API_BASE_URL` configuration
   - Verify network connectivity between containers
   - Ensure nginx proxy configuration is correct

2. **CORS errors**
   - Verify `ENVIRONMENT` variable is set correctly
   - Check `CORS_ORIGINS` for custom domains
   - Ensure origin matches expected patterns

3. **Database connection failed**
   - Verify `MONGODB_URL` uses correct service name
   - Check database container health
   - Verify authentication credentials

### Debug Commands

```bash
# Check container connectivity
docker exec crm_frontend curl http://backend:8000/health

# Verify environment variables
docker exec crm_backend env | grep MONGODB_URL
docker exec crm_frontend env | grep NEXT_PUBLIC_API_BASE_URL

# Check nginx configuration
docker exec crm_nginx nginx -t
```

## Best Practices

1. **Use environment detection over hardcoded values**
2. **Prefer relative paths in containerized environments**
3. **Keep development and production configurations documented**
4. **Test configuration changes in Docker before production**
5. **Use meaningful defaults that work in most scenarios**
6. **Validate environment variables at application startup**

This architecture ensures the application works seamlessly across all deployment contexts while maintaining security and flexibility.