# CODEMAP

This document maps major features to files and endpoints.

## Apps
- complete_production_crm.py: Production CRM (HTML UI + API) on port 8004
- main.py: Assistant backend / API-only

## Core
- core/config.py: Settings (MONGO_URI, SECRET_KEY, URLs)
- core/security.py: Password hashing and JWT helpers
- db_adapter.py: MongoDB client, UserRepository

## UI/Routes (complete_production_crm.py)
- GET /           -> Login page
- POST /api/login -> Authenticates demo/real users (JWT)
- GET /dashboard  -> Dashboard with nav and JS
- GET/POST /api/leads
- GET/POST /api/properties
- Facebook mock routes: /api/facebook/* and /auth/facebook/*

## Tests
- tests/ui: Playwright UI tests
- tests/smoke_check.py: Minimal backend smoke test

## Docker
- Dockerfile.crm + docker-compose.crm.yml: Mongo + CRM at :8004

## Known Gotchas
- Inline JS in HTML strings: escape newlines (use \\n) and attach global funcs via window.
- DB mode is driven by db_adapter.MONGO_URI -> DB_MODE
