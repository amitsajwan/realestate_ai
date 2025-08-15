# Demo Runbook (5–7 minutes)

1) Prep
- Ensure Redis running (docker or compose)
- Start API (uvicorn) and worker (python worker.py)

2) Flow
- Register and login to get JWT
- Connect WebSocket with token (ws://.../chat/{client_id}?token=...)
- Send initial idea → receive 3 branding concepts
- Provide property details when requested
- Review final caption → confirm to post
- Show success response with post URL

3) Talk Track
- Value: faster content, consistent branding, direct posting
- Safety: no image gen, licensing-safe, fair-housing-ready roadmap
- Scale: Redis sessions, background tasks, Dockerizable
