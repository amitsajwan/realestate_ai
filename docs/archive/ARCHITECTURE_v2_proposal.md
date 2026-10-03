# Architecture (v2 direction)

Status: proposal. Supersedes the scattered root-level *_PLAN / *_SUMMARY docs.

## Product
An India-focused real estate platform where:
1. Agents post listings (in our app, or by publishing to social from our app).
2. **Every agent-posted listing is captured into our marketplace** (the platform-owned pool).
3. We track the buyer journey (views, clicks, comments, DMs, visits) and score leads.
4. Agents with a buyer but no property can search the pool and reach the owning agent.

## Governance model (decided)
- Agent owns their listing content and can edit/withdraw it. The platform holds the canonical marketplace record and a license to display/share it in the pool.
- Default visibility on posting: `network` (all verified agents). Agent may narrow to `agency` or `private` per listing; `public` = buyer-facing pages.
- Lead attribution: buyer contact on a listing routes through the platform (masked phone / WhatsApp deep link with tracking) so attribution and referral terms are enforceable.
- Duplicate control: the same physical property is often posted by many agents. Listings are clustered by fingerprint (locality + building + area + BHK + price band + image hash); the cluster shows all listing agents, none can claim exclusivity without an explicit `exclusive` flag and proof.
- Verification: RERA registration number (state-wise), agent KYC, listing freshness (auto-expire / re-confirm every N days).

## India-specific requirements
- WhatsApp Business Cloud API is the primary channel (templates, opt-in, click-to-chat links with tracking id). Facebook/Instagram second.
- INR with lakh/crore formatting; areas in sq ft with carpet / built-up / super built-up distinguished.
- Location hierarchy: state > city > micro-market > locality > project/building.
- Consent and retention per DPDP Act 2023: record buyer consent, purpose, and support erasure.
- Languages: English + Hindi + Marathi first (existing multi-language content support).

## Modules (modular monolith: FastAPI + MongoDB + Redis + Celery)
```
backend/app/modules/
  identity/    users, agencies, roles (agent, agency_admin, buyer, platform_admin), agent KYC
  listings/    core listing facts, media, RERA, freshness, fingerprint/dedupe
  marketplace/ pool capture, visibility, listing clusters, intro requests, referral terms
  crm/         contacts, requirements, pipeline stage, tasks, site visits
  tracking/    append-only events, anonymous->known identity merge, lead scoring
  social/      connectors: publish + ingest comments/DMs/leads (WhatsApp, FB, IG)
  matching/    requirement <-> listing (rules first, AI ranking later)
  messaging/   agent<->agent threads, notifications
  ai/          single content service + single scoring service
backend/app/platform/  config, db, outbox/events, jobs, rate limits, audit log
```
Rules: modules talk via service interfaces and events, never each other's collections. Every query is tenant/owner scoped.

## Core data model (sketch)
- Agent{agency_id, rera_no, kyc_status, languages, service_areas}
- Listing{owner_agent_id, cluster_id, visibility, status, freshness_at, rera_no, facts..., media[]}
- ListingCluster{fingerprint, listing_ids[], canonical_listing_id}
- Contact{owner_agent_id, phones[], emails[], consent{}, anonymous_ids[]}
- Requirement{contact_id, budget_min/max, localities[], bhk[], type, timeline}
- Event{contact|anon_id, listing_id, agent_id, type, source, utm, ts, meta}  (append-only)
- Visit{contact_id, listing_id, scheduled_at, status, outcome}
- IntroRequest{from_agent, listing_id, requirement_id, status, referral_terms}

## Business model (decided)
- Goal is reach first, revenue second: free or minimal-fee for agents. Our value to agents is distribution + buyer tracking + agent network.
- Monetization later, without gating the core: paid boosts / ad credits, premium lead tools, agency plans. Referral cut is optional and off by default.

## Distribution (our marketplace -> social reach)
New module `distribution/` (replaces the old publish-only services). The pool is the source of truth; channels are outputs.
- Instagram: Graph API publishing (feed, reels, stories) from a connected business account.
- Facebook: Page posts via Graph API; Meta "Home Listings" catalog feeds for dynamic ads (eligibility to be verified).
- WhatsApp: Business API broadcasts (opt-in only), Channels, click-to-chat links with tracking id.
- Own SEO pages + shareable links per listing/agent (`/l/<slug>?src=..`) - the tracked landing surface for every channel.
- IMPORTANT: Facebook Marketplace has no open API for individual real-estate listings (partner-only). Do not build on it; treat as manual/assisted or a partner-program application later.
- Every outbound post carries a tracking id so views/comments/DMs come back as Events and attribute to listing + agent + channel.

## AI-driven listing creation (new model)
Listing creation starts from the lowest-effort input agents already have, not a form:
- Inputs: photos/video, a voice note, a WhatsApp message/forward, a pasted portal link.
- AI extracts structured facts (BHK, area, locality, price, amenities), proposes missing fields for one-tap confirm, generates multilingual copy (En/Hi/Mr) and channel-specific creatives, flags duplicates (fingerprint) and RERA/price anomalies.
- Human confirms before publish; the confirmed record enters the pool.
- Prompting/vision lives in `ai/` behind one interface (Groq now; swappable).

## Agent website in a few clicks (core feature)
Every agent gets a site automatically at onboarding; posting a listing updates it with no extra step.

Existing code to build on (audited):
- Backend `endpoints/agent_public.py` + `services/agent_public_service.py`: slug lookup, profile CRUD, agent's properties (filters/paging), posts, contact inquiry, view/contact counters. Collection `agent_public_profiles`.
- Frontend `app/agent/[agentName]/{page,properties/[id],posts/[id],contact}` and `PublicWebsiteManagement.tsx`. Brand theme from `lib/theme.ts` (3 colors), AI branding suggestions from `endpoints/branding.py` and `agent_onboarding.py`.
Gaps to close:
- Site is a client-rendered page (`'use client'`, fetch in useEffect): no SSR/SEO, no OG tags, weak link previews on WhatsApp/Facebook. Move to server components with `generateMetadata`, sitemap, JSON-LD.
- Slug path only (`/agent/<slug>`): add subdomain `<slug>.<ourdomain>` and optional custom domain later (wildcard DNS + host-based routing in Next middleware).
- Branding is a temp-fix endpoint that saves an untyped dict; theme is stored in localStorage on the viewer's browser. Store a typed `SiteConfig{theme, logo, hero, sections[], languages}` on the agent and serve it to visitors.
- Site shows the agent's own listings and posts only. Add "network picks" from the pool (agent can feature pool listings on their site, with attribution), which is the marketplace value for site owners.
- No tracking: only counters. Site views/clicks/inquiries must emit `Event`s (tracking module) with source/UTM, and the contact form must create a Contact/lead.
- Two-step onboarding is scattered across 3 endpoints (onboard, onboarding, agent_preferences). Collapse to one flow.

Target "few clicks" flow: sign in with phone OTP/WhatsApp -> name, photo, city (prefill from Facebook/Instagram/WhatsApp profile) -> AI picks theme, tagline, bio (En/Hi/Mr) -> site is live at `<slug>.<domain>` -> first listing via AI creation (voice/photos/WhatsApp) -> posted to site, pool, and chosen social channels in one confirm.

## Known code-state issues found during audit
- Two API routers are both mounted: `api/v1/router.py` (about 25 routers, mounted by `core/routes.py`) and `api/v1/api.py` (4 routers, mounted again in `main.py`). `/properties` and `/publishing` are registered twice. Pick one.
- ~15 endpoint files are dead or duplicates (`facebook_mock`, `demo`, `unified_ai_unified`, two enhanced-post prefixes for one router, etc.).
