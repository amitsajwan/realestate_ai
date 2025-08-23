# URL Configuration Guide

## Overview

PropertyAI now uses a centralized, environment-based URL configuration system to ensure consistency across development, testing, and production environments.

## URL Strategy

### Development (Default)
- **Base URL**: `http://localhost:8003`
- **Testing**: All tests run against localhost
- **Facebook OAuth**: Callbacks still use ngrok for external access

### Production/ngrok
- **Base URL**: `https://8400abb81098.ngrok-free.app`
- **Testing**: Can be configured to test against ngrok
- **Facebook OAuth**: Callbacks use the same ngrok URL

## Configuration Files

### 1. `app/config.py`
Central configuration management with environment detection.

```python
from app.config import settings

# Get appropriate base URL
base_url = settings.get_base_url()

# Get specific URLs for OAuth callbacks
dashboard_url = settings.get_dashboard_url()
login_url = settings.get_login_url()

# Get Facebook OAuth callback (always ngrok)
callback_url = settings.get_facebook_callback_url()
```

### 2. Environment Variables

```bash
# Development (default)
USE_NGROK=false
TEST_BASE_URL=http://localhost:8003

# Production/ngrok
USE_NGROK=true
TEST_BASE_URL=https://8400abb81098.ngrok-free.app
NGROK_BASE_URL=https://8400abb81098.ngrok-free.app
```

### 3. Playwright Configuration

```typescript
// playwright.config.ts
baseURL: process.env.TEST_BASE_URL || 'http://localhost:8003'
```

## Usage Examples

### Running Tests Locally
```bash
# Default: localhost
npx playwright test

# Explicit: localhost
TEST_BASE_URL=http://localhost:8003 npx playwright test
```

### Running Tests Against ngrok
```bash
# Test against ngrok
TEST_BASE_URL=https://8400abb81098.ngrok-free.app npx playwright test
```

### Facebook OAuth
Facebook OAuth callbacks always use the ngrok URL for external access, regardless of the base URL setting.

## Benefits

1. **Consistency**: All URLs managed from one place
2. **Flexibility**: Easy switch between localhost and ngrok
3. **Facebook OAuth**: Always works with external callbacks
4. **Testing**: Can test against any environment
5. **Maintenance**: Single source of truth for URL configuration

## Migration Notes

- Old hardcoded URLs have been replaced with configuration-based URLs
- Facebook OAuth continues to work as expected
- Tests now use environment variables for flexibility
- Development workflow remains unchanged (localhost by default)
