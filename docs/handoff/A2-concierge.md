# A2: owner concierge (Agents screen, on-behalf listings, attribution)

The owner sets up an agent (login, site, invite code), enters his brand and listings, records his consent, and posts his listings on the PUNE Property Page and Instagram with "Listed by ..." attribution. We do not connect the agent's own Facebook or Instagram.

## Backend (`backend/app/modules/concierge/`)
| File | Purpose |
|---|---|
| `config.py` | `owner_ids()` from `CONCIERGE_OWNER_IDS`; `owner_agent_ids()` adds `INTEREST_OWNER_AGENT_ID` / `ENGAGE_OWNER_AGENT_ID` |
| `service.py` | `ConciergeService`: create/reuse agent (user via `BeanieUserStore`, site via `OnboardingService.create_site`, invite via `InviteService.issue`), list/detail with checklist, consent, listing create/patch/publish through `ListingService` (Pune-only city from the schema, price sanity here), branding, marketing pack, caption preview, post. Audit rows in `concierge_audit` (keys only). Agent rows in `concierge_agents` |
| `attribution.py` | `attribution_line(profile)` ("Listed by <business or name> \| RERA agent reg: <no>", phone-like text stripped), `attribution_text(db, agent_id, listing, channel)`, `register_hub_item` (Instagram: /go hub item with the interest code) |
| `router.py` | owner-only routes (403 closed by default), in-memory rate limits (10 invites/hour, 60 writes/minute, 20 posts/minute) |

Routes (all under `/concierge`): `POST /agents`, `GET /agents`, `GET /agents/{id}`, `POST /agents/{id}/consent`, `POST /agents/{id}/listings`, `PATCH /agents/{id}/listings/{lid}`, `POST .../publish`, `POST .../pack`, `POST .../captions`, `POST .../post`, `GET|POST /agents/{id}/branding`.

Edit in `social/service.py` (minimal): `build_payload(..., attribution="")`, `SocialService._attribution`, new `SocialService.captions()` (exact text, nothing recorded), and after a real Instagram publish `register_hub_item`. With no profile, an owner id or a sample title the attribution is empty and behaviour is identical to before.

Notes
- Invite codes are hashed, so an existing agent only gets a new code when the owner asks (`reissue`), which invalidates the old one.
- Posting requires recorded consent (409 otherwise). The owner's approval is the existing `approve` + consent flags of the social flow; the audit row says who approved for whom.
- Posting an agent's listing needs his marketing pack; the Agents UI creates it on first use when the server says it is missing.

## Wiring snippet (integrator): `backend/app/api/v1/router.py`
```python
from app.modules.concierge.router import router as concierge_router
api_router.include_router(concierge_router, prefix="/concierge", tags=["concierge"])
```
Env: `CONCIERGE_OWNER_IDS=<user ids, comma separated>` (superusers are always allowed). Existing: `PUBLIC_SITE_URL` (join link in the WhatsApp message and site URL), social settings for real posting.

## Frontend
- `lib/app/concierge.ts`: types, `createConciergeApi`, stateful fixtures, `conciergeApi` (fixture mode switch), `CONSENT_TEXT`.
- `app/studio/agents/page.tsx`, `[id]/page.tsx`, `[id]/listings/new/page.tsx`.
- `components/app/agents/`: `AgentsScreen`, `AddAgentSheet`, `AgentDetailScreen` (checklist, brand, listings, consent), `PostSheet` (exact captions then approve), `ProgressRing`, `NewListingForAgent`, `useIsOwner`, `BrandEditorSlot` + `BrandEditorStub`.
- `NewListingFlow` gets an optional `onBehalfOf={{id, name}}`: create/update/publish go through the concierge, a different done screen, back link to the agent. `ReviewForm` needed no change.
- `AppShell`: one extra tab ("Agents") shown only when `useIsOwner()` (the server answers the list call with 403 for non-owners). `StudioGate`: hides the tab bar on `/studio/agents/<id>/listings/new` like the existing new-listing screen.
- Tests: `frontend/__tests__/app/concierge.test.tsx` (13), backend `backend/tests/modules/concierge/` (24). Screenshots: `docs/brand/concierge-samples/` (`frontend/e2e/concierge-shots.js`).

## For A1 (branding)
`BrandEditorSlot.tsx` imports `BrandEditor` from `./BrandEditorStub` (logo and photo only). When A1 merges, change that import to `../BrandEditor` (props `{agentId?, loadBranding, saveBranding, uploadImage}`) and delete the stub. Backend: `ConciergeService.update_branding` calls `onboarding.update_branding(user, data_dict)` if `OnboardingService` has it, else the existing `update_site` (logo, photo, instagram, facebook_url). `GET /agents/{id}/branding` returns `branding_data` plus `agent_name` and `photo`. The checklist reads `branding_data.logo`, `banner`, `rera_agent_no`, `areas` (or profile `specialties`) and profile `photo`; the attribution reads `business_name` and `rera_agent_no`. Please keep those key names.
