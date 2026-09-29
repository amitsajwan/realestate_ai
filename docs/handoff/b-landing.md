# Handoff: B-landing (public front door, legal pages, invite requests)

Branch `v2/b-landing`, built on `0e9ad8b`. Implements `docs/contracts/landing.md` (unchanged).

## What shipped

### Backend: `backend/app/modules/waitlist/`
- `POST /request-invite` (public). Body per contract; phone normalised with the onboarding `normalize_indian_mobile`.
  Always `200 {"received": true}` for success, duplicate and honeypot (identical bytes). `422` invalid/consent not true, `429` `{"detail": "Too many requests"}`.
- Honeypot `website` non-empty: dropped silently, nothing stored, not counted against limits.
- Rate limits (rolling hour): 3 per phone, 20 per client ip. Blocked requests change nothing.
- Client ip: first hop of `X-Forwarded-For`, else socket peer. Stored only as `sha256("<JWT_SECRET_KEY>:<ip>")`; raw ip never stored anywhere. If no ip can be determined, only the ip limit is skipped.
- Repeat request from the same phone within 24h updates name/city/message/`updated_at` on the existing row (status and consent record are kept).
- Collection `invite_requests`: `{name, phone, city, message, consent:{given_at,text}, ip_hash, status:"new", created_at, updated_at}`.
- Extra collection `invite_request_attempts` `{phone, ip_hash, at}`: rolling-window log for the rate limits (repeat requests update a row, so the main collection alone cannot count them).
- Admin script: `python scripts/invite_requests.py list` (new requests, oldest first: phone, name, city, date, message) and `mark-invited <phone>` (run from `backend/` with `PYTHONPATH=.`).
- Tests: `backend/tests/modules/test_waitlist.py`, `test_waitlist_router.py` (31 tests). Used the existing `fakes.py` unchanged.

### Frontend
- `/` landing (server component, replaces the legacy home), `/request-invite`, `/privacy`, `/terms`, `/data-deletion`.
- `components/marketing/*` (shell, header, footer, contact lines, phone frame, legal layout, invite form), `lib/marketing/*` (config, strings, seo, invite API helper), `__tests__/marketing/*` (28 tests).
- All pages render inside `data-surface="v2"` so the legacy `mobile.css` `!important` rules do not apply. Light theme, single blue accent.
- SEO: title, description, canonical, Open Graph and Twitter tags (image: a real screenshot), JSON-LD `Organization` with name, url, description, area served (Pune) and, only if `NEXT_PUBLIC_CONTACT_EMAIL` is set, a contact point. No logo, address, phone or rating is emitted.
- Real screenshots from `public/landing/*.jpg` with descriptive alt, width/height 780x1688, lazy loading (hero image eager), captioned "Screens show sample data".
- `Navigation.tsx`: returns null for `/`, `/request-invite`, `/privacy`, `/terms`, `/data-deletion`.

## Integrator actions

1. Mount the router (do this next to the existing join router in `backend/app/api/v1/router.py`):
   ```python
   from app.modules.waitlist.router import router as waitlist_router
   api_router.include_router(waitlist_router, prefix="/join", tags=["join"])
   ```
   Endpoint becomes `POST /api/v1/join/request-invite`; it does not collide with `/join/otp/*` or `/join/site`.
2. Optional indexes in `app/core/indexes.py` (not touched by this branch):
   ```python
   ("invite_requests", [("phone", ASC), ("created_at", DESC)], {}),
   ("invite_requests", [("status", ASC), ("created_at", ASC)], {}),
   ("invite_request_attempts", [("phone", ASC), ("at", DESC)], {}),
   ("invite_request_attempts", [("ip_hash", ASC), ("at", DESC)], {}),
   ("invite_request_attempts", [("at", ASC)], {"expireAfterSeconds": 86400}),  # attempts clean themselves up
   ```
3. Proxy: the backend must sit behind a proxy that sets `X-Forwarded-For` (Caddy does). If it is ever exposed directly, a client can spoof the header and dodge the per-ip limit (the per-phone limit still holds).

## Environment variables (frontend, build time: NEXT_PUBLIC_* is inlined at build)
| Var | Default | Effect |
|---|---|---|
| `NEXT_PUBLIC_BUSINESS_NAME` | `PUNE Property` | name in header, footer, legal text |
| `NEXT_PUBLIC_CONTACT_EMAIL` | unset | when unset no email is shown anywhere; pages say "Contact details are shared when you request an invite." |
| `NEXT_PUBLIC_CONTACT_WHATSAPP` | unset | digits, e.g. `919876543210` (a bare 10-digit number gets `91` added); when unset no WhatsApp contact is shown |
| `NEXT_PUBLIC_SITE_URL` | `http://localhost:3000` | canonical and Open Graph URLs (set this in production!) |

Backend: the salt for ip hashes is the existing `JWT_SECRET_KEY`. Rotating it only resets ip rate-limit history.

## Deviation to know about
The legacy home page (`app/page.tsx`) was the dashboard UI, and `app/dashboard/page.tsx` imported it (`import Dashboard from '../page'`). Replacing `/` would have broken `/dashboard` (and the build). I moved the untouched legacy file to `frontend/app/dashboard/DashboardHome.tsx` and changed that one import. No behaviour change for `/dashboard`.

## Open questions for the owner
- Legal text is plain-language and NOT legal advice. **A lawyer must review privacy, terms and data deletion before public launch** (DPDP Act 2023 wording, grievance officer requirements, retention, liability, governing law). Nothing in it names a company, registration number, address or grievance officer; add those once they exist.
- Without `NEXT_PUBLIC_CONTACT_EMAIL`/`WHATSAPP` there is no way for anyone to reach you about deletion except the request-invite form (the data-deletion page tells them to write "Delete my data" in the note). Set at least one contact before Meta app review, which needs a working deletion channel. Requests arrive in `invite_requests` (`scripts/invite_requests.py list` shows the message).
- Meta's "Data deletion instructions URL" is `<site>/data-deletion` (section "Data deletion instructions").
- "Free during the pilot. If that ever changes, we will tell you first." and "we delete within 30 days" are commitments in the copy; confirm you are happy to make them.
- Deletion page says agent deletion also removes the buyer enquiries in that account; confirm this matches how you will actually handle it.
- Privacy page states that third-party AI services process text/voice agents provide (true for the listing drafting module today); update if providers change.
- Landing OG image is a portrait phone screenshot; a dedicated 1200x630 image would look better in link previews.
- Screenshots contain sample data (Rahul Sharma, Priya Sharma...); the page says so.

## Verification
- Backend: `pytest` whole `backend/tests`: 489 passed, 2 skipped (458 existing + 31 new).
- Frontend: `npx tsc --noEmit` 0 errors; marketing jest 28/28; whole `__tests__` jest run: all pass except `lib/utils/__tests__/slug.test.ts` (4 failures, pre-existing: expects `http://localhost:3000`, gets `http://localhost`; unrelated). `next build` compiles all pages (the trailing standalone symlink EPERM comes from the node_modules junction in this worktree).
