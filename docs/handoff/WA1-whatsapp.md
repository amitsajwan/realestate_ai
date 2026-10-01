# WA1: WhatsApp buyer assistant (handoff)

Branch base: `ddc3f87`. Commits: `15deaa4` (backend modules), `570eaef` (tests), `55f3426` (frontend), `eea98f6` (setup guide + connect script), plus this handoff.

## What it does
A buyer messages the PUNE Property WhatsApp number (Meta test number first). The assistant answers with the **website chat engine** and
**grounded knowledge** (same honesty rules: no invented facts or prices, sample homes labelled, unknowns handed to a person), in the buyer's
language (English, Hindi, Marathi, Hinglish, romanised Marathi). The buyer becomes a **lead** in `contacts` (source `whatsapp`) with the
requirement the engine extracts, and the agent gets an **in-app notification** (Studio home badge). Only free replies inside the 24-hour
window the buyer opened; no paid templates; starts in dry run.

## Files
Backend (new; nothing else imports them):
- `backend/app/modules/whatsapp/config.py`: env settings (below). Secrets are `repr=False`.
- `.../whatsapp/graph.py`: Cloud API client (`send_text`, `mark_read`, `phone_info`). Token in the `Authorization: Bearer` header, never in
  URLs; every error text goes through `social.publisher.sanitize` with the token, app secret and verify token.
- `.../whatsapp/router.py`: `GET /whatsapp/webhook` (hub challenge, constant-time compare), `POST /whatsapp/webhook` (HMAC-SHA256 of the raw
  body with the app secret vs `X-Hub-Signature-256`, constant time, 403 on missing/wrong; 200 at once; new messages handled in a
  `BackgroundTasks` task; statuses update delivery), `GET /whatsapp/conversations` (bearer, agent scoped, number masked).
- `.../whatsapp/service.py`: idempotent intake (`whatsapp_messages`, _id = Meta message id), routing, STOP/START, media/location replies,
  conversation state per `<phone_number_id>:<wa_id>` (last 20 messages) in `whatsapp_conversations`, 24-hour window (from the message's own
  timestamp, so a late retry cannot reopen it), dry run, per-buyer hourly cap (30), lead upsert, notifications, mark-as-read.
- `.../whatsapp/adapters.py`: the only coupling to chat engine, knowledge, interest links, tracking requirement merge, contacts and
  notifications. **No edits to chat/engine or knowledge were needed**: WhatsApp pre-fills the engine state with the buyer's number and
  WhatsApp profile name (`phone`, `consent_shown`, `lead_done=True`), so the engine never asks for the number and never makes its own lead;
  the adapter writes the lead (dedupe by agent + phone, so a website-chat lead with the same number is updated, not duplicated).
  It uses `knowledge.reply._localise` (private) for translating vetted KB answers when an LLM is configured; without an LLM those stay in English.
- `.../whatsapp/lang.py`: Hindi/Marathi/Hinglish/romanised-Marathi versions of the engine's fixed sentences and our own lines (data-use
  notice, STOP, START, media, location).
- `backend/app/modules/notifications/`: `notify(db, agent_id, kind, summary, ref)`, `GET /notifications?unread=true`,
  `POST /notifications/{id}/read` (agent scoped). Kinds used: `new_whatsapp_lead`, `whatsapp_needs_you`. TODO hook for paid WhatsApp
  utility-template alerts is in `notifications/service.py::notify`.

Frontend:
- `frontend/components/site/WhatsAppButton.tsx`: "Chat on WhatsApp" -> `https://wa.me/<n>?text=Hi, I am interested in <title> (ref <code>)`;
  renders only when `NEXT_PUBLIC_WHATSAPP_NUMBER` is set; an agent's own number only when `show_whatsapp === true` is passed.
- Placed under "I am interested" on `/go` (each item with a code) and `/i/[code]` (reads optional `show_whatsapp` / `agent_whatsapp`
  from the interest view if the backend ever adds them; it does not today).
- `frontend/lib/app/whatsapp.ts`: Studio client (conversations, notifications, mark read); fixture mode returns empty lists.
- `frontend/app/studio/interest/page.tsx`: "WhatsApp chats" section (WhatsApp label, summary, last 6 messages with send status, STOP and
  needs-you notes); viewing it marks WhatsApp notifications read.
- `frontend/app/studio/page.tsx`: green badge "N new WhatsApp leads and chats" linking to the Interest tab.

Ops/docs: `docs/WHATSAPP_SETUP.md` (owner click-by-click, coexistence, real number, cost table), `deploy/gcp/whatsapp_connect.ps1`.

## Wiring (integrator)
`backend/app/api/v1/router.py`:
```python
from app.modules.whatsapp.router import router as whatsapp_router
from app.modules.notifications.router import router as notifications_router
api_router.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
```
Website button (optional; keep off while on the test number): add a build arg like the existing ones
- `frontend/Dockerfile`: `ARG NEXT_PUBLIC_WHATSAPP_NUMBER=` and add `NEXT_PUBLIC_WHATSAPP_NUMBER=$NEXT_PUBLIC_WHATSAPP_NUMBER` to the `ENV` line.
- `deploy/gcp/docker-compose.yml` frontend `args`: `NEXT_PUBLIC_WHATSAPP_NUMBER: ${NEXT_PUBLIC_WHATSAPP_NUMBER:-}`.

Suggested Mongo indexes: `whatsapp_conversations {agent_id:1, updated_at:-1}`, `notifications {agent_id:1, read:1, created_at:-1}`
(`whatsapp_messages` uses `_id`, so duplicates are rejected by Mongo itself).

## Environment (backend, `deploy/gcp/.env`; the connect script writes these)
| Variable | Default | Meaning |
|---|---|---|
| `WHATSAPP_ENABLED` | false | webhook accepts signed POSTs but does nothing until true |
| `WHATSAPP_DRY_RUN` | true | replies stored, not sent; only an explicit false sends |
| `WHATSAPP_PHONE_NUMBER_ID` | | platform number's Phone number ID |
| `WHATSAPP_ACCESS_TOKEN` | | System User token (whatsapp_business_messaging, whatsapp_business_management) |
| `WHATSAPP_VERIFY_TOKEN` | | random; pasted into Meta's webhook settings |
| `WHATSAPP_APP_SECRET` | | Meta app secret (signature check); missing = every POST 403 |
| `WHATSAPP_OWNER_AGENT_ID` | falls back to `INTEREST_OWNER_AGENT_ID`, `ENGAGE_OWNER_AGENT_ID` | receives chats that name no agent |
| `WHATSAPP_NUMBER_AGENTS` | `{}` | JSON `{"<phone_number_id>": "<agent_id>"}` for agents' own (coexistence) numbers |
| `WHATSAPP_GRAPH_VERSION` | v23.0 | Meta docs currently show v25.0; any `vNN.N` accepted |
| `NEXT_PUBLIC_WHATSAPP_NUMBER` (frontend build) | | digits, e.g. 919876543210; button hidden when empty |

Routing order: number map > interest code in the text (`ref <code>`, `/i/<code>`, `interested in <code>`; samples and pages go to the owner,
homes to their agent; the click is recorded as an interest event) > owner. Once routed away from the owner, a chat stays with that agent.

## Tests
- Backend: `PYTHONPATH=backend backend/.venv/Scripts/python.exe -m pytest backend/tests/modules/whatsapp -q -c backend/pytest.ini`
  -> **33 passed** (webhook verify; signature good/bad/missing/tampered; Meta retries processed once; disabled; routing by number map,
  interest code, sample code, owner; grounded price from listing facts; sample labelled; Hindi, Hinglish, Marathi prompts and notice;
  translator path; one lead with requirement, consent basis and a single notice; dedupe with a website lead; needs-you notification once;
  STOP/START; media/location/reaction; dry run makes no HTTP call; live mode hits `/{version}/{phone_number_id}/messages` with Bearer and
  marks read; 24-hour refusal incl. late retries; token never in logs or stored errors (Graph error and transport error); conversations
  agent scoped and masked; last 20 messages; notifications scoped and mark-read). Graph is `httpx.MockTransport`; no network.
- Frontend jest: `__tests__/site/whatsapp-button.test.tsx`, `__tests__/app/interest-whatsapp.test.tsx` (plus the existing
  `interest-instagram` and `interest-pages` suites still pass): 24 passed. `npx tsc --noEmit` clean. `next build --webpack`: passes (exit 0).

## Known limits / notes
- Without an LLM, vetted knowledge-base answers (e.g. RERA explainer) stay in English inside an otherwise Hindi/Marathi reply; listing/area
  facts are English sentences with localised framing (same as the website chat and comment replies).
- The engine's quick replies become a "Reply with: Buy / Rent / ..." text line (no interactive buttons yet; those would also be free inside
  the window).
- The STOP confirmation is one message right after STOP (inside the window); after that nothing is sent until START.
- The backend's request-logging middleware logs full URLs, so Meta's GET verification (with `hub.verify_token`) appears once in logs. It is
  only the webhook verify token (not the access token); rotate it by re-running the script if that matters.
- The global per-IP rate limiter applies to Meta's webhook IPs too; fine for pilot volumes.
- Coexistence needs Embedded Signup (Tech Provider / partner) on Meta's side; documented in WHATSAPP_SETUP.md section F.

## Meta sources used (fetched 2026-10-01)
- Webhook payload shape (entry/changes/value/metadata.phone_number_id, contacts[].profile.name, messages[] id/from/timestamp/type/text.body,
  statuses[]): https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks/payload-examples
- Verification (hub.mode=subscribe, hub.challenge, hub.verify_token) and `X-Hub-Signature-256: sha256=<HMAC-SHA256(body, app secret)>`:
  https://developers.facebook.com/docs/graph-api/webhooks/getting-started
- Send text (`POST /<PHONE_NUMBER_ID>/messages`, messaging_product, recipient_type, to, type text), mark read (`status: read, message_id`),
  24-hour customer service window, examples on v25.0: https://developers.facebook.com/docs/whatsapp/cloud-api/guides/send-messages
- Getting started (WhatsApp use case, API Setup, test number, system user token permissions business_management /
  whatsapp_business_messaging / whatsapp_business_management): https://developers.facebook.com/docs/whatsapp/cloud-api/get-started
- Coexistence (WhatsApp Business app 2.24.17+, Solution Partner / Tech Provider, 20 mps, disabled features, 24 h history sync,
  smb_message_echoes): https://developers.facebook.com/docs/whatsapp/embedded-signup/custom-flows/onboarding-business-app-users
- Pricing (per-message since 1 July 2025; non-template messages free; utility templates free inside an open window; marketing always
  paid): https://developers.facebook.com/docs/whatsapp/pricing
