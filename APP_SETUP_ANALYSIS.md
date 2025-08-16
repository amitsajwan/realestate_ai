# Facebook API Testing - App Setup Fix

The issue is that your `app/main.py` doesn't include the Facebook routes. You have two options:

## Option 1: Use the Main Backend App (Recommended)

Your main.py in the root directory has all the Facebook integration. Run this instead:

```powershell
cd C:\Users\code\realestate_ai
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8003
```

Then visit: `http://localhost:8003/agents/demo` or create a dashboard route.

## Option 2: Add Facebook Routes to Modular App

Add Facebook routes to your app/main.py:

```python
# Add to app/main.py after existing routes
try:
    # ... existing routes ...
    from api.endpoints import facebook_oauth, facebook_pages  # type: ignore
    app.include_router(facebook_oauth.router, prefix="/api/facebook", tags=["facebook"])
    app.include_router(facebook_pages.router, prefix="/api/facebook", tags=["facebook"])
except Exception as e:
    print(f"Facebook routes not available: {e}")
```

## Current Status Check

Let me verify which files have the dashboard with Facebook integration:
