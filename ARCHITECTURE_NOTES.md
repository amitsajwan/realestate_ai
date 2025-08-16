# Architecture Notes (Entrypoints and Facebook Integration)

This repo contains multiple apps/scripts; here’s how they relate:

- main.py — Primary FastAPI backend for the modular AI assistant and APIs. Use this in development (uvicorn main:app --reload) and connect the React/Vite frontend to it.
- app/main.py — A separate lightweight modular web app for classic templates (login.html, dashboard.html). Do not run alongside main.py on the same port.
- complete_production_crm.py — A monolithic, all-in-one legacy app kept for reference and migration. Not recommended to run alongside the modular apps.

Recommended usage
- Prefer main.py as the single backend service. It exposes:
  - /api/facebook/*: OAuth connect, config, pages, select_page, and post endpoints
  - /api/listings/*, /api/ai-localization/* and more
- The React frontend (frontend/) connects to main.py via CORS.
- The app/templates dashboard is a light demo. Use one UI at a time to avoid confusion.

Facebook integration (current state)
- OAuth endpoints: /api/facebook/connect (redirects to Facebook) and /api/facebook/callback
- Page endpoints: /api/facebook/config, /pages, /select_page, /post
- In-memory AgentRepository stores connected_page and encrypted page tokens for demo only. Move to DB for production.
- services/facebook_client.py uses settings.FB_GRAPH_API_VERSION for Graph versioning.

Next steps to productionize
- Persist connected_page + tokens in your DB (Mongo) with encryption
- Page selection UI when multiple Pages are available
- Photo publishing via /photos edge, media library, and scheduled posts
- Webhooks for comments/messages -> lead capture
