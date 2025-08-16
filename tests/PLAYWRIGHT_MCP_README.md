# Playwright MCP-style Setup (Real App Compatible)

This setup lets you run Playwright E2E tests against:
- a locally started server (default), or
- a real/staging system already running (no local server started)

## Quick start

- Local default (starts Python app):

```powershell
$env:BASE_URL = 'http://127.0.0.1:8004'
npm run test:e2e
```

- Target a real system (do not start any web server):

```powershell
$env:PW_NO_SERVER = '1'
$env:BASE_URL = 'https://your-real-host.example.com'
# Optional, if you already have a JWT token
# $env:AUTH_TOKEN = '<jwt>'
npm run test:e2e
```

## MCP-style fixtures

See `tests/ui/fixtures/mcp.ts` which provides a lightweight plugin bus with hooks:
- `beforeAuth`, `afterAuth(token)`
- `beforeNavigate(path)`, `onApiResponse(url, status)`

You can attach custom logic per suite without coupling tests to any backend detail.

## Example real run

```powershell
$env:PW_NO_SERVER = '1'
$env:BASE_URL = 'http://127.0.0.1:8003'
# Automatically obtains token via /api/login if AUTH_TOKEN not provided
npx playwright test tests/ui/real-login-and-nav.spec.ts --reporter=list
```

## Notes
- Config injects `Authorization` header for API requests when `AUTH_TOKEN` is set.
- UI flow still performs a visible login to catch regressions.
- Network listener records `/api/` responses for quick triage.
