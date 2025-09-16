# Authentication Module

## Overview

The Authentication Module is a modular, self-contained authentication system for the real estate platform. It provides user management, JWT-based authentication, and seamless integration with the main application.

## Architecture

```
backend/modules/auth/
├── __init__.py              # Module exports
├── config.py                # Configuration settings
├── integration.py           # Integration with main app
├── models/
│   ├── __init__.py
│   └── user.py             # User models (User, UserCreate, UserRead, UserUpdate)
├── services/
│   ├── __init__.py
│   └── auth_service.py     # Authentication service logic
├── api/
│   ├── __init__.py
│   └── auth_router.py      # Authentication API endpoints
├── tests/
│   ├── __init__.py
│   └── test_auth_module.py # Module tests
└── README.md               # This file
```

## Features

- **User Management**: Complete user lifecycle management
- **JWT Authentication**: Secure token-based authentication
- **MongoDB Integration**: Beanie ODM for database operations
- **Frontend Compatibility**: Consistent API responses for frontend
- **Modular Design**: Self-contained and reusable
- **Configuration Management**: Environment-based configuration
- **Comprehensive Testing**: Unit tests for all components

## Components

### Models (`models/user.py`)

- **User**: Main user document model
- **UserCreate**: User creation schema
- **UserRead**: User read schema with frontend compatibility
- **UserUpdate**: User update schema

### Services (`services/auth_service.py`)

- **AuthService**: Main authentication service
- **UserManager**: Custom user manager for FastAPI Users
- **Password Helper**: Secure password handling

### API (`api/auth_router.py`)

- **GET /me**: Get current user information
- **POST /register**: Register new user
- **GET /health**: Health check endpoint
- **JWT Authentication**: Login/logout endpoints

### Configuration (`config.py`)

- JWT settings (secret key, algorithm, expiration)
- Password requirements
- CORS configuration
- Database settings

## Usage

### 1. Import the Module

```python
from modules.auth import User, UserCreate, UserRead, AuthService, auth_router
```

### 2. Initialize in Main App

```python
from modules.auth.integration import integrate_auth_module, get_auth_config

# Get configuration
auth_config = get_auth_config()

# Integrate with FastAPI app
integrate_auth_module(app, auth_config)
```

### 3. Use in Endpoints

```python
from modules.auth.models.user import User
from modules.auth.services.auth_service import get_current_user_id

@router.get("/protected")
async def protected_endpoint(current_user: User = Depends(current_active_user)):
    user_id = get_current_user_id(current_user)
    return {"user_id": user_id, "message": "Access granted"}
```

## Configuration

The module uses environment variables with the `AUTH_` prefix:

```bash
# JWT Settings
AUTH_JWT_SECRET_KEY=your-secret-key-change-in-production
AUTH_JWT_ALGORITHM=HS256
AUTH_JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Password Settings
AUTH_PASSWORD_MIN_LENGTH=8

# Database Settings
AUTH_DATABASE_URL=mongodb://localhost:27017
AUTH_DATABASE_NAME=realestate_ai
```

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/jwt/login` - Login with email/password
- `POST /api/v1/auth/jwt/logout` - Logout
- `GET /api/v1/auth/me` - Get current user info
- `GET /api/v1/auth/health` - Health check

### Request/Response Examples

#### Register User

```json
POST /api/v1/auth/register
{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "company": "Real Estate Co"
}

Response:
{
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "company": "Real Estate Co",
    "onboarding_completed": false,
    "onboarding_step": 0,
    "onboardingCompleted": false,
    "onboardingStep": 0,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer"
}
```

#### Get Current User

```json
GET /api/v1/auth/me
Authorization: Bearer <token>

Response:
{
  "id": "507f1f77bcf86cd799439011",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "company": "Real Estate Co",
  "onboarding_completed": true,
  "onboarding_step": 6,
  "onboardingCompleted": true,
  "onboardingStep": 6,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## Testing

Run the module tests:

```bash
python -m pytest backend/modules/auth/tests/
```

## Integration with Main App

The authentication module is designed to work alongside the existing authentication system. It provides:

1. **Modular Structure**: Self-contained authentication logic
2. **Consistent API**: Same endpoints and responses as before
3. **Easy Migration**: Gradual migration from existing system
4. **Team Assignment**: Can be assigned to a dedicated developer
5. **Code Review**: Module lead can review authentication changes
6. **Architect Approval**: Final integration approved by architect

## Benefits

- **Maintainability**: Clear separation of concerns
- **Scalability**: Easy to extend and modify
- **Team Development**: Multiple developers can work on different modules
- **Testing**: Isolated testing of authentication logic
- **Code Review**: Focused review process for authentication changes
- **Documentation**: Comprehensive documentation for the module

## Next Steps

1. **Team Assignment**: Assign authentication module to a dedicated developer
2. **Code Review**: Implement module lead review process
3. **Integration Testing**: Test with the main application
4. **Performance Testing**: Ensure module performs well under load
5. **Security Audit**: Review authentication security measures
6. **Documentation**: Keep documentation updated with changes

## Support

For questions or issues with the authentication module, contact the module lead or refer to the main project documentation.
