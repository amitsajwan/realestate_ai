# Roadmap

## Phase 0 - Stabilize (1 wk)
- Commit current working tree on cursor/analyze-and-fix-styling-issues-cacb.
- Fix backend env (venv points to missing Python; install motor etc.) so tests run.
- Archive root-level status/plan docs to docs/archive/.
- Reconcile 40+ endpoint files vs 4 registered routers; delete dead endpoints, mock/demo/test routes.
- Pick one auth approach and one canonical property model.

## Phase 1 - Listings + capture + tracking seed (2-3 wks)
- identity (agencies/roles), listings module, migrate existing properties.
- Marketplace capture: every posted listing enters the pool with visibility + fingerprint.
- Public listing page + tracked share links (source/UTM) -> first Event type.
- Inquiry form -> Contact + lead with source. Minimal agent dashboard.

## Phase 2 - Buyer tracking + CRM (3 wks)
- Event pipeline, anon->known merge, lead score, pipeline, tasks, site visits, requirements.

## Phase 3 - Distribution + WhatsApp/social two-way (3 wks)
- distribution module: syndicate pool listings to IG/FB Page/WhatsApp with tracking ids.
- AI listing creation v1: photos/voice/WhatsApp message -> structured draft -> confirm.
- WhatsApp Business Cloud API (templates, opt-in, inbound webhooks -> leads).
- FB/IG comment + DM ingestion -> leads linked to listing.

## Phase 4 - Marketplace marketplace features (4 wks)
- Pool search, requirement matching, intro requests, agent<->agent messaging.
- Dedupe clusters, RERA verification, referral terms, moderation, freshness expiry.

## Phase 5 - Growth
- Agent onboarding funnel, plans/billing, AI matching, buyer app.

## Open questions
- Pricing: free tier limits, and when to introduce paid boosts.
- RERA verification: manual review vs state portal scraping/API?
