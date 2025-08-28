# PropertyAI Authentication System Implementation Guide

## Overview

This guide provides comprehensive instructions for implementing the enhanced authentication system for PropertyAI. The system includes secure password hashing, JWT token management, real-time form validation, and production-ready security features.

## 🔧 Prerequisites

- Python 3.8+
- Node.js 18+
- MongoDB 4.4+
- Docker (optional)
- Git

## 📦 Installation Instructions

### Step 1: Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd realestate_ai
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```env
   # Database
   MONGODB_URL=mongodb://localhost:27017/propertyai
   
   # JWT Configuration
   JWT_SECRET_KEY=your-super-secret-jwt-key-here-change-in-production
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
   JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
   
   # Security
   BCRYPT_ROUNDS=12
   
   # Email Configuration (for password reset)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   
   # Application
   APP_NAME=PropertyAI
   DEBUG=False
   ENVIRONMENT=production
   ```

4. **Initialize the database:**
   ```bash
   python -c "from app.database import init_db; init_db()"
   ```

5. **Start the backend server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### Step 2: Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd nextjs-app
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment variables:**
   Create a `.env.local` file:
   ```env
   # API Configuration
   NEXT_PUBLIC_API_URL=http://localhost:8000
   
   # Application
   NEXT_PUBLIC_APP_NAME=PropertyAI
   NEXT_PUBLIC_APP_VERSION=1.0.0
   
   # Development
   NODE_ENV=development
   ```

4. **Start the frontend development server:**
   ```bash
   npm run dev
   ```

## 🧪 Testing Checklist

### Backend Testing

- [ ] **Health Check**
  ```bash
  curl http://localhost:8000/health
  ```
  Expected: `{"status": "healthy", "database": "connected"}`

- [ ] **User Registration**
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "SecurePass123!",
      "firstName": "John",
      "lastName": "Doe"
    }'
  ```

- [ ] **User Login**
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{
      "email": "test@example.com",
      "password": "SecurePass123!"
    }'
  ```

- [ ] **Protected Route Access**
  ```bash
  curl -X GET http://localhost:8000/api/v1/auth/me \
    -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
  ```

### Frontend Testing

- [ ] **Login Page Validation**
  - Navigate to `http://localhost:3000/login`
  - Test email format validation
  - Test password strength indicators
  - Test form submission with valid/invalid data

- [ ] **Registration Flow**
  - Test real-time validation feedback
  - Test password confirmation matching
  - Test successful registration redirect

- [ ] **Authentication State**
  - Test automatic token refresh
  - Test logout functionality
  - Test protected route access

### Security Testing

- [ ] **Password Security**
  - Verify bcrypt hashing (no plain text passwords in database)
  - Test password strength requirements
  - Test common password rejection

- [ ] **JWT Security**
  - Verify token expiration handling
  - Test token refresh mechanism
  - Test invalid token rejection

- [ ] **Input Validation**
  - Test SQL injection prevention
  - Test XSS prevention
  - Test malformed request handling

## 🚨 Common Issues & Solutions

### Issue 1: "Module not found" errors

**Problem:** Import errors when starting the backend

**Solution:**
```bash
# Ensure you're in the correct directory
cd realestate_ai

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue 2: Database connection errors

**Problem:** MongoDB connection failures

**Solution:**
1. Ensure MongoDB is running:
   ```bash
   # On macOS with Homebrew
   brew services start mongodb-community
   
   # On Ubuntu
   sudo systemctl start mongod
   
   # Using Docker
   docker run -d -p 27017:27017 --name mongodb mongo:latest
   ```

2. Check connection string in `.env` file
3. Verify network connectivity

### Issue 3: JWT token errors

**Problem:** "Invalid token" or "Token expired" errors

**Solution:**
1. Check JWT_SECRET_KEY in environment variables
2. Verify token expiration settings
3. Clear browser localStorage and re-login
4. Check server time synchronization

### Issue 4: CORS errors in frontend

**Problem:** Cross-origin request blocked

**Solution:**
1. Ensure backend CORS is configured:
   ```python
   # In app/main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:3000"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. Check API URL in frontend environment variables

### Issue 5: Password validation not working

**Problem:** Weak passwords being accepted

**Solution:**
1. Verify password validation in `app/utils.py`
2. Check frontend validation in `lib/validation.ts`
3. Ensure both frontend and backend validation are active

## 🚀 Production Deployment

### Backend Deployment

1. **Environment Configuration:**
   ```env
   # Production .env
   MONGODB_URL=mongodb://your-production-db-url
   JWT_SECRET_KEY=your-super-secure-production-key
   DEBUG=False
   ENVIRONMENT=production
   ALLOWED_HOSTS=your-domain.com,www.your-domain.com
   ```

2. **Using Docker:**
   ```dockerfile
   # Dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   
   EXPOSE 8000
   CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
   ```

3. **Build and run:**
   ```bash
   docker build -t propertyai-backend .
   docker run -p 8000:8000 --env-file .env propertyai-backend
   ```

### Frontend Deployment

1. **Build for production:**
   ```bash
   cd nextjs-app
   npm run build
   ```

2. **Environment variables:**
   ```env
   # Production .env.local
   NEXT_PUBLIC_API_URL=https://api.your-domain.com
   NODE_ENV=production
   ```

3. **Deploy to Vercel:**
   ```bash
   npm install -g vercel
   vercel --prod
   ```

### Database Setup (Production)

1. **MongoDB Atlas (Recommended):**
   - Create cluster at https://cloud.mongodb.com
   - Configure network access
   - Create database user
   - Get connection string

2. **Indexes for Performance:**
   ```javascript
   // MongoDB shell commands
   db.users.createIndex({ "email": 1 }, { unique: true })
   db.users.createIndex({ "createdAt": 1 })
   db.users.createIndex({ "isActive": 1 })
   ```

### SSL/HTTPS Configuration

1. **Backend (using nginx):**
   ```nginx
   server {
       listen 443 ssl;
       server_name api.your-domain.com;
       
       ssl_certificate /path/to/certificate.crt;
       ssl_certificate_key /path/to/private.key;
       
       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

2. **Frontend:** Automatically handled by Vercel/Netlify

## 📊 Monitoring & Logging

### Backend Monitoring

1. **Health Check Endpoint:**
   ```python
   # Monitor this endpoint
   GET /health
   ```

2. **Log Analysis:**
   ```bash
   # View application logs
   tail -f logs/app.log
   
   # Monitor authentication attempts
   grep "auth" logs/app.log
   ```

### Frontend Monitoring

1. **Error Tracking:**
   - Integrate Sentry for error monitoring
   - Monitor authentication failures
   - Track API response times

2. **Analytics:**
   - Monitor login success rates
   - Track user registration flow
   - Analyze form validation errors

## 🔒 Security Best Practices

### Password Security
- ✅ Bcrypt with 12 rounds
- ✅ Password strength validation
- ✅ Common password prevention
- ✅ No password storage in logs

### JWT Security
- ✅ Short access token expiry (30 minutes)
- ✅ Secure refresh token mechanism
- ✅ Token blacklisting on logout
- ✅ Proper token validation

### API Security
- ✅ Rate limiting
- ✅ Input validation and sanitization
- ✅ CORS configuration
- ✅ HTTPS enforcement

### Database Security
- ✅ Connection encryption
- ✅ User access controls
- ✅ Regular backups
- ✅ Index optimization

## 📝 Maintenance Tasks

### Daily
- [ ] Monitor error logs
- [ ] Check authentication success rates
- [ ] Verify system health endpoints

### Weekly
- [ ] Review security logs
- [ ] Update dependencies (if needed)
- [ ] Database performance analysis

### Monthly
- [ ] Security audit
- [ ] Backup verification
- [ ] Performance optimization review
- [ ] User feedback analysis

## 🆘 Support & Troubleshooting

### Log Locations
- Backend: `logs/app.log`
- Frontend: Browser console
- Database: MongoDB logs

### Debug Mode
```bash
# Enable debug logging
export DEBUG=True
uvicorn app.main:app --reload --log-level debug
```

### Performance Monitoring
```bash
# Monitor API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/api/v1/auth/me
```

## 📞 Getting Help

If you encounter issues not covered in this guide:

1. Check the application logs
2. Verify environment variables
3. Test with minimal configuration
4. Review the authentication flow step by step
5. Check network connectivity and firewall settings

---

**Last Updated:** January 2024  
**Version:** 1.0.0  
**Compatibility:** Python 3.8+, Node.js 18+, MongoDB 4.4+