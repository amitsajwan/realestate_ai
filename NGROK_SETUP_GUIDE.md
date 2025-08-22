# Local Development & ngrok Setup Guide (Free Version)

## 1. Start ngrok (Free)
- Run: `ngrok http 8003`
- Copy the HTTPS forwarding URL (it will change each time you start ngrok).

## 2. Update Environment Variables
- In your `.env` file, set:
  ```
  MODULAR_PROXY_TARGET=<your-ngrok-url>
  BASE_URL=<your-ngrok-url>
  FB_APP_ID=<your-facebook-app-id>
  FB_APP_SECRET=<your-facebook-app-secret>
  FB_OAUTH_BASE=https://www.facebook.com/v19.0/dialog/oauth?
  FB_DOCS_BASE=https://developers.facebook.com/docs/facebook-login/web?state=
  ```
- Paste the new ngrok URL each time you restart ngrok.

## 3. Start the Application
- Run your backend:
  - `python simple_backend.py`
  - or `uvicorn simple_backend:app --reload`

## 4. Run Tests
- Run unit/integration tests: `pytest`
- Run Playwright/E2E tests: `pytest tests/e2e/`

## 5. Validate Facebook Integration
- Go to your ngrok URL in a browser.
- Test Facebook login, page connection, and posting.

## 6. Troubleshooting
- If any test fails, check logs and environment variables.
- Update `.env` or code as needed.

---
**Note:** With the free ngrok plan, your URL will change every time you restart ngrok. Always update your `.env` and Facebook app settings with the new URL.
