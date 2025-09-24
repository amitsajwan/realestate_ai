# Authentication System Setup Guide

## Overview

The authentication system has been updated to provide proper JWT-based authentication with development support. The system now uses a hybrid approach in development mode that tries real authentication first and falls back to mock authentication if needed.

## Current Implementation

### Environment-Based Authentication

- **Development Mode**: Hybrid authentication (real JWT with mock fallback)
- **Production Mode**: Full JWT authentication only

### Key Components

1. **Authentication Backend** (`app/core/auth_backend.py`)
   - FastAPI Users integration
   - JWT strategy with proper token handling
   - Environment-aware authentication flow

2. **Development Auth Service** (`app/services/development_auth_service.py`)
   - Manages development user creation
   - Generates development tokens
   - Handles development authentication

3. **Development Endpoints** (`app/api/v1/endpoints/auth.py`)
   - `/api/v1/auth/dev/tokens` - Get development tokens
   - `/api/v1/auth/dev/login` - Login with development credentials
   - `/api/v1/auth/dev/setup-user` - Setup development user

## Setup Instructions

### 1. Environment Configuration

Set the following environment variables:

```bash
# Required
ENVIRONMENT=development
JWT_SECRET_KEY=your-secret-key-here-change-in-production

# Optional (with defaults)
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=propertyai
```

### 2. Initialize Development Authentication

Run the setup script:

```bash
cd backend
python scripts/setup_development_auth.py
```

This will:
- Initialize the database
- Create a development user (`test@example.com`)
- Generate development tokens
- Display setup information

### 3. Start the Application

```bash
cd backend
python -m uvicorn app.main:app --reload
```

## Usage

### Development Authentication

#### Option 1: Use Development Tokens Endpoint

```bash
# Get development tokens
curl -X GET "http://localhost:8000/api/v1/auth/dev/tokens"

# Response includes access_token and user info
```

#### Option 2: Use Development Login

```bash
# Login with development credentials
curl -X POST "http://localhost:8000/api/v1/auth/dev/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "test123"}'
```

#### Option 3: Use Mock Authentication (Automatic Fallback)

The system automatically falls back to mock authentication if JWT validation fails in development mode.

### Production Authentication

In production mode (`ENVIRONMENT=production`), use the standard FastAPI Users endpoints:

```bash
# Register new user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123", "first_name": "John", "last_name": "Doe"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/jwt/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

## Authentication Flow

### Development Mode

1. **Real Authentication Attempt**: System tries to validate JWT token
2. **Fallback to Mock**: If JWT validation fails, uses mock user
3. **Consistent User**: Mock user has consistent ID and properties

### Production Mode

1. **JWT Validation Only**: System validates JWT tokens
2. **No Fallback**: Returns 401 if authentication fails
3. **Secure**: No mock authentication available

## API Endpoints

### Standard Authentication (All Environments)

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/jwt/login` - Login with credentials
- `GET /api/v1/auth/me` - Get current user info
- `PUT /api/v1/auth/me` - Update current user
- `GET /api/v1/auth/health` - Authentication health check

### Development Authentication (Development Only)

- `GET /api/v1/auth/dev/tokens` - Get development tokens
- `POST /api/v1/auth/dev/login` - Login with development credentials
- `POST /api/v1/auth/dev/setup-user` - Setup development user

## Troubleshooting

### Common Issues

1. **"Using mock authentication for development"**
   - This is expected in development mode
   - The system will try real authentication first, then fall back to mock

2. **401 Unauthorized Errors**
   - Check if JWT token is properly formatted
   - Verify token hasn't expired
   - In development, system should fall back to mock

3. **Database Connection Issues**
   - Ensure MongoDB is running
   - Check MONGODB_URL configuration
   - Run the setup script to initialize

### Debug Information

Check the authentication health endpoint:

```bash
curl -X GET "http://localhost:8000/api/v1/auth/health"
```

Response includes:
- Authentication service status
- Current environment
- Authentication mode (hybrid/production)

## Security Notes

### Development Mode
- Mock authentication is only available in development
- Development endpoints are automatically disabled in production
- JWT tokens are still generated and validated when possible

### Production Mode
- Full JWT authentication required
- No mock authentication available
- Strong JWT secret key required

## Migration from Old System

The new system is backward compatible:

1. **Existing Users**: Continue to work with new JWT system
2. **Frontend**: No changes required for standard authentication
3. **Development**: Enhanced with proper token generation
4. **Production**: Secure JWT-only authentication

## Next Steps

1. **Test Authentication**: Use the development endpoints to test
2. **Update Frontend**: Use development tokens for testing
3. **Deploy Production**: Set `ENVIRONMENT=production` for deployment
4. **Monitor**: Use health endpoints to monitor authentication status
