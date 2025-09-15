# 🚀 **DEVELOPMENT SETUP GUIDE: Multi-Post Management System**

## 📋 **Development Environment Setup**

### **Prerequisites**
- **Node.js**: v18.0.0 or higher
- **Python**: v3.9 or higher
- **MongoDB**: v5.0 or higher
- **Redis**: v6.0 or higher
- **Git**: Latest version
- **Docker**: v20.0 or higher (optional)

## 🔧 **Backend Development Setup**

### **Environment Configuration**
```bash
# Clone the repository
git clone <repository-url>
cd real-estate-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Set up environment variables
cp .env.template .env
# Edit .env with your configuration
```

### **Environment Variables**
```env
# Database Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=real_estate_platform
TEST_DATABASE_NAME=real_estate_platform_test

# Redis Configuration
REDIS_URL=redis://localhost:6379

# AI Service Configuration
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama3-8b-8192

# Social Media APIs
FACEBOOK_APP_ID=your_facebook_app_id
FACEBOOK_APP_SECRET=your_facebook_app_secret
INSTAGRAM_ACCESS_TOKEN=your_instagram_token
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret

# JWT Configuration
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Configuration
DEBUG=True
ENABLE_MULTILANGUAGE=True
CORS_ORIGINS=http://localhost:3000
```

### **Database Setup**
```bash
# Start MongoDB
mongod --dbpath /path/to/your/db

# Create database and collections
python -m backend.app.utils.database_init

# Run migrations
python -m backend.app.utils.migration
```

### **Development Server**
```bash
# Start the backend server
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# The API will be available at http://localhost:8000
# API documentation at http://localhost:8000/docs
```

## 🎨 **Frontend Development Setup**

### **Environment Configuration**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.local.template .env.local
# Edit .env.local with your configuration
```

### **Environment Variables**
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_VERSION=v1

# Application Configuration
NEXT_PUBLIC_APP_NAME=Real Estate Platform
NEXT_PUBLIC_APP_VERSION=1.0.0

# Feature Flags
NEXT_PUBLIC_ENABLE_MULTILANGUAGE=true
NEXT_PUBLIC_ENABLE_AI_FEATURES=true
NEXT_PUBLIC_ENABLE_ANALYTICS=true

# External Services
NEXT_PUBLIC_GROQ_API_KEY=your_groq_api_key_here
NEXT_PUBLIC_FACEBOOK_APP_ID=your_facebook_app_id
```

### **Development Server**
```bash
# Start the frontend development server
npm run dev

# The application will be available at http://localhost:3000
```

## 🐳 **Docker Development Setup**

### **Docker Compose Configuration**
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  mongodb:
    image: mongo:5.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      MONGO_INITDB_DATABASE: real_estate_platform

  redis:
    image: redis:6.0
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - REDIS_URL=redis://redis:6379
    depends_on:
      - mongodb
      - redis
    volumes:
      - ./backend:/app
      - /app/venv

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  mongodb_data:
  redis_data:
```

### **Docker Commands**
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f

# Stop all services
docker-compose -f docker-compose.dev.yml down

# Rebuild services
docker-compose -f docker-compose.dev.yml up --build
```

## 🧪 **Testing Setup**

### **Backend Testing**
```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-mock

# Run tests
pytest backend/tests/ -v

# Run tests with coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Run specific test file
pytest backend/tests/test_post_management.py -v
```

### **Frontend Testing**
```bash
# Install test dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom jest

# Run tests
npm test

# Run tests with coverage
npm test -- --coverage

# Run specific test file
npm test -- PostManagement.test.tsx
```

### **End-to-End Testing**
```bash
# Install Playwright
npm install --save-dev @playwright/test

# Run E2E tests
npx playwright test

# Run E2E tests in headed mode
npx playwright test --headed
```

## 📊 **Development Tools**

### **Code Quality Tools**
```bash
# Backend - Black for code formatting
pip install black isort flake8 mypy

# Format code
black backend/
isort backend/

# Lint code
flake8 backend/
mypy backend/

# Frontend - Prettier and ESLint
npm install --save-dev prettier eslint

# Format code
npm run format

# Lint code
npm run lint
```

### **API Testing**
```bash
# Install HTTPie for API testing
pip install httpie

# Test API endpoints
http GET localhost:8000/api/v1/posts
http POST localhost:8000/api/v1/posts title="Test Post" content="Test Content"
```

### **Database Tools**
```bash
# Install MongoDB Compass for database management
# Download from: https://www.mongodb.com/products/compass

# Install Redis Commander for Redis management
npm install -g redis-commander
redis-commander
```

## 🔄 **Development Workflow**

### **Git Workflow**
```bash
# Create feature branch
git checkout -b feature/post-management

# Make changes and commit
git add .
git commit -m "feat: implement post management API"

# Push to remote
git push origin feature/post-management

# Create pull request
# Merge after code review
```

### **Code Review Process**
1. **Create Pull Request**: Include description of changes
2. **Assign Reviewers**: Backend Dev 1 reviews Backend Dev 2's code
3. **Review Checklist**: Use provided checklist for thorough review
4. **Address Feedback**: Make requested changes
5. **Approval**: Get approval from at least one reviewer
6. **Merge**: Merge after all checks pass

### **Testing Workflow**
1. **Unit Tests**: Write tests for new functionality
2. **Integration Tests**: Test API integration
3. **E2E Tests**: Test complete user workflows
4. **Performance Tests**: Test performance requirements
5. **Security Tests**: Test security measures

## 📝 **Development Guidelines**

### **Backend Guidelines**
- **Code Style**: Follow PEP 8 and Black formatting
- **Type Hints**: Use type hints for all functions
- **Documentation**: Document all public functions and classes
- **Error Handling**: Implement comprehensive error handling
- **Logging**: Use structured logging for debugging
- **Testing**: Write tests for all new functionality

### **Frontend Guidelines**
- **Code Style**: Follow ESLint and Prettier configuration
- **TypeScript**: Use TypeScript for type safety
- **Components**: Create reusable, composable components
- **State Management**: Use appropriate state management patterns
- **Performance**: Optimize for performance and accessibility
- **Testing**: Write tests for all components and hooks

### **API Guidelines**
- **RESTful Design**: Follow REST principles
- **Versioning**: Use API versioning for backward compatibility
- **Validation**: Validate all input data
- **Error Responses**: Use consistent error response format
- **Documentation**: Keep API documentation up to date
- **Rate Limiting**: Implement rate limiting for API endpoints

## 🚨 **Troubleshooting**

### **Common Issues**

#### **Backend Issues**
```bash
# MongoDB connection issues
# Check if MongoDB is running
sudo systemctl status mongod

# Check MongoDB logs
sudo journalctl -u mongod

# Redis connection issues
# Check if Redis is running
sudo systemctl status redis

# Check Redis logs
sudo journalctl -u redis
```

#### **Frontend Issues**
```bash
# Node modules issues
rm -rf node_modules package-lock.json
npm install

# Build issues
npm run build

# TypeScript issues
npm run type-check
```

#### **Database Issues**
```bash
# Reset database
mongo real_estate_platform --eval "db.dropDatabase()"

# Restore from backup
mongorestore --db real_estate_platform backup/
```

### **Performance Issues**
```bash
# Check API response times
http GET localhost:8000/api/v1/posts --timeout 5

# Check database performance
mongo real_estate_platform --eval "db.property_posts.explain().find()"

# Check Redis performance
redis-cli --latency
```

## 📚 **Useful Resources**

### **Documentation**
- **FastAPI**: https://fastapi.tiangolo.com/
- **Next.js**: https://nextjs.org/docs
- **MongoDB**: https://docs.mongodb.com/
- **Redis**: https://redis.io/documentation
- **Groq API**: https://console.groq.com/docs

### **Development Tools**
- **Postman**: API testing
- **MongoDB Compass**: Database management
- **Redis Commander**: Redis management
- **VS Code**: Code editor with extensions
- **GitHub**: Version control and collaboration

### **Learning Resources**
- **FastAPI Tutorial**: https://fastapi.tiangolo.com/tutorial/
- **Next.js Tutorial**: https://nextjs.org/learn
- **MongoDB Tutorial**: https://docs.mongodb.com/manual/tutorial/
- **React Testing**: https://testing-library.com/docs/react-testing-library/intro/

---

**Setup Guide Version**: 1.0  
**Last Updated**: 2024-01-15  
**Next Update**: 2024-01-22