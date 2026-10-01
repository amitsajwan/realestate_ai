# X1 handoff: interest links and link-in-bio hub

## Wiring (backend/app/api/v1/router.py)
```python
from app.modules.interest.router import router as interest_router, public_router as interest_public_router
api_router.include_router(interest_router, prefix="/interest", tags=["interest"])
api_router.include_router(interest_public_router, prefix="/public", tags=["public"])
```
Optional indexes: `interest_links` unique on `code`, and on `(kind, ref, channel)`; `interest_log` on `ts`.

## Function other streams call
```python
from app.modules.interest.service import interest_url
url = await interest_url(db, kind="post"|"listing"|"page", ref=<calendar item id | listing id | slug>,
                         agent_id=<owner or listing agent>, channel="facebook"|"instagram"|"website"|"whatsapp",
                         title="...", locality="...", image_url="...", subtitle="...")   # -> "<PUBLIC_SITE_URL>/i/<code>"
```
Idempotent per (kind, ref, channel). Titles are snapshotted on the link (for a real listing id it reads the title from `listings`; a showcase sample slug is detected and labelled as a sample).

Hub: `await upsert_hub_item(db, kind, ref, title, image_url, subtitle, interest_code, permalink, sample=False)` (service.py). Doc shape in the docstring. Until hub_items has rows, `GET /public/hub` shows the 9 labelled samples.

## Behaviour
- `GET /public/interest/{code}`, `POST .../{code}/click`, `POST .../{code}` (name/phone/note only with `consent: true`, else 400), honeypot field `website`.
- Rate limits: 3 interests per IP and code per hour, 60 clicks per IP per hour (429 with the tracking wording).
- A one-tap with no details creates an anonymous lead (phone "", source = channel, message = context, score 8) in the target agent's contacts; adding a phone later goes through `TrackingService.capture_inquiry` and replaces the placeholder.
- Sample homes and `page` links route to the owner agent (env `INTEREST_OWNER_AGENT_ID`, else `ENGAGE_OWNER_AGENT_ID`, else public profile slug `INTEREST_OWNER_SLUG` default `amit-sajwan`); message starts `PLATFORM INTEREST (...)`.
- Env: `PUBLIC_SITE_URL`, `HUB_FACEBOOK_URL`, `HUB_INSTAGRAM_URL` (hub buttons are hidden when unset).
- `GET /interest/links/{ref}` returns the caller's links with click and interest counts.

## Integrator notes
- `frontend/components/Navigation.tsx` is not owned by X1: add `/i/` and `/go` to its hide-list (line ~66). Until then both layouts hide it with a `body > nav` CSS rule.
- Anonymous leads have `phone: ""`; the inbox UI and followup WhatsApp draft should tolerate that (check `lead.phone`).
- Frontend `/i/[code]/tap` is the no-JS form target; the browser fetches use `/api/v1/public/interest/...`.
- Screenshots: `docs/brand/interest-samples/`.
