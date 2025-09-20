# API Fixes Implementation Plan

## Critical Issues Identified

### 1. Authentication Schema Mismatch

**Problem:** FastAPI Users expects `username` and `password` for login, but we're sending `email` and `password`.

**Current Login Endpoint:**
```python
# FastAPI Users default login expects:
{
    "username": "user@example.com",
    "password": "password123"
}
```

**Our Test Sends:**
```python
{
    "email": "user@example.com", 
    "password": "password123"
}
```

**Solution:** Update our test to use the correct schema, or create a custom login endpoint that accepts email.

### 2. Missing Agent Public Profile Endpoints

**Problem:** 7 endpoints are missing for agent public profiles with dynamic `{agent_slug}` routing.

**Missing Endpoints:**
- `GET /api/v1/agent/public/{agent_slug}`
- `GET /api/v1/agent/public/{agent_slug}/properties`
- `GET /api/v1/agent/public/{agent_slug}/properties/{property_id}`
- `POST /api/v1/agent/public/{agent_slug}/contact`
- `POST /api/v1/agent/public/{agent_slug}/track-contact`
- `GET /api/v1/agent/public/{agent_slug}/about`
- `GET /api/v1/agent/public/{agent_slug}/stats`

### 3. Server Errors in Agent Dashboard

**Problem:** 2 endpoints returning 500 errors:
- `PUT /api/v1/agent/dashboard/profile`
- `GET /api/v1/agent/dashboard/inquiries`

## Implementation Steps

### Step 1: Fix Authentication Test

Update the test script to use correct authentication schema:

```python
# In comprehensive_api_analysis.py, change:
login_data = {
    "email": "test@example.com",
    "password": "testpassword123"
}

# To:
login_data = {
    "username": "test@example.com",  # Use username instead of email
    "password": "testpassword123"
}
```

### Step 2: Add Missing Agent Public Endpoints

Add dynamic routing to `backend/app/api/v1/endpoints/agent_public.py`:

```python
@router.get("/{agent_slug}")
async def get_agent_public_profile(agent_slug: str):
    """Get agent public profile by slug"""
    # Implementation needed

@router.get("/{agent_slug}/properties")
async def get_agent_public_properties(agent_slug: str):
    """Get agent's public properties"""
    # Implementation needed

# ... etc for all missing endpoints
```

### Step 3: Debug Agent Dashboard Errors

Check the agent dashboard endpoints for:
- Database connection issues
- Missing dependencies
- Validation errors
- Exception handling

### Step 4: Test Authentication Fix

After fixing the schema, re-run the authentication test to verify:
- Login works with correct schema
- JWT token is generated
- Protected endpoints become accessible

## Expected Results After Fixes

- **Authentication:** 84 endpoints should become accessible
- **Missing Endpoints:** 7 endpoints should return 200 instead of 404
- **Server Errors:** 2 endpoints should return 200 instead of 500
- **Overall Success Rate:** Should increase from 18.88% to ~80%+

## Priority Order

1. **HIGH:** Fix authentication schema (affects 84 endpoints)
2. **HIGH:** Add missing agent public endpoints (7 endpoints)
3. **MEDIUM:** Debug agent dashboard server errors (2 endpoints)
4. **LOW:** Clean up duplicate endpoints and improve error handling

