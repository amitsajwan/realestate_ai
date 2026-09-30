# PUNE Property: product plan

*Find. Compare. Decide.* Working plan by the product owner / architect. Updated 30 September 2026. Companion to `docs/PILOT_RUNBOOK.md`.

## 1. What we are building (and what we are not)

**A Pune-first property discovery and lead engine.** For agents, one property becomes a complete marketing campaign (website page, social posts, WhatsApp text)
and the resulting enquiries are captured, qualified and followed up. For buyers, clear, sourced information about Pune localities and homes.

**Not** another listing portal, not an "AI" brand, not a website builder. AI is the engine (extract, write, classify, answer); trust is the product.

**The bet to prove first (pilot, 3 to 10 agents):**
> Does an agent add a second property after the first one, and do enquiries arrive that the agent would not otherwise have got?

Everything in Phases 0 and 1 exists to answer that. Discovery, SEO and the advisor come after the answer is yes.

## 2. Where we are today (verified, live)

| Area | State |
|---|---|
| Agent onboarding | Phone + invite code, site in minutes, optional photo/logo/Instagram/Facebook |
| Listing creation | Typed text to structured listing (rules + free LLM chain), price sanity guard, photos. Voice built but hidden (Premium) |
| Marketing pack | Branded cards (navy/gold), Instagram/Facebook/WhatsApp copy, no phone numbers, "Comment INTERESTED" CTA, LLM polish behind a fact guard |
| Distribution | Facebook Page posting live with consent + approval; Instagram blocked only on linking the account |
| Agent site | Branded, sample listings (labelled), guides, enquiry form with qualification, no phone exposed |
| CRM | Tracking, lead scoring, matching, follow-up drafts, deal outcomes, freshness rules |
| Content | 3 sourced guides, 3 locality pages, sitemap/robots, 15+ Page posts (tips, guides, labelled samples, agent recruitment in EN/HI/MR) |
| Buyer engagement | Comment assistant on the Page (live, verified end to end), website chat with consent-first lead capture, Interest tab |
| Agent proof | Weekly summary card with WhatsApp share; per-listing activity; performance |
| Pilot kit | `docs/AGENT_INVITE_KIT.md` (invite messages EN/HI/MR, quick start, check-in script, tracking sheet) |
| Ops | One GCP VM (shared project), Caddy HTTPS on sslip.io, daily disk snapshot, redeploy script |

## 3. Gaps against the vision

1. ~~Comments and messages go nowhere~~ Done: comment assistant and website chat are live. Messenger (needs Meta App Review for the public) and WhatsApp remain.
2. **No proof loop.** We cannot yet show an agent "this post brought N views and M enquiries" (Sprint 2).
3. **No supply yet.** Only sample listings exist. First real agents are the real milestone.
4. **Content is hand-made.** No research, approval queue or scheduling (Sprint 3).
5. **No discovery.** No search, no locality hubs, no sitemap/SEO structure (Phase 2).
6. **Operational fragility.** Single VM, shared project, no staging, no domain, SMS OTP absent, in-process background work (Sprint 0/4).

## 4. Roadmap

### Phase 0: Pilot-ready (now to about 2 weeks)
Goal: 3 real agents can be onboarded without me in the room.
- Comment assistant (Facebook) in record-only mode, then live after review. **[in progress]**
- Instagram linked and publishing (blocked on Instagram account switching to Professional).
- Agent "My profile" screen (edit name, photo, logo, links, price of listings).
- First real listing with real photos on the Page and site.
- Runbook for inviting an agent + a one-page agent guide (Hindi/English).
- Custom domain (replace sslip.io), SMS or WhatsApp OTP decision, remove personal phone from Page contact.
- **Exit:** 3 agents invited, each posts a real listing with photos.

### Phase 1: Prove the wedge (weeks 3 to 8)
Goal: agents keep using it and get enquiries.
- Enquiry inbox unified: website form + Facebook/Instagram comments + WhatsApp clicks in one list, with hot/warm/cold and suggested reply.
- Weekly report to each agent (WhatsApp message): views, enquiries, top listing, what to do next.
- Content ops: research notes with sources, draft, human approval queue, schedule, publish to site + Page. Three content types: locality guide, market/infrastructure explainer, buyer tip.
- Locality pages for Kharadi, Upper Kharadi, Wagholi (real data only: connectivity, official infra status, checklists).
- Photo quality assist: nudge, reorder, watermark-free cover crop.
- **Exit metrics (per pilot agent, over 6 weeks):** at least 8 listings, 1 or more second-listing added within 7 days of first, 5 or more enquiries, response time under 2 hours, 2 or more site visits.

### Phase 2: Discovery (months 3 to 5)
- Public homepage, search and filters, saved search + alerts, listing SEO (sitemap, structured data, canonical pages).
- 10 locality hubs and comparison pages ("Kharadi vs Viman Nagar"), each fact-checked, dated and sourced.
- Marketplace pool: agents opt in to share listings network-wide with clear rules (dedupe, freshness, ownership).
- **Exit:** at least 30% of enquiries from search/social not sent by agents.

### Phase 3: Intelligence (months 5 to 9)
- AI advisor for buyers: budget + commute + lifestyle in, ranked localities/properties out, with reasons and sources. Human-reviewed prompts, refuses when data is thin.
- Pune property graph from official/open sources (RERA, IGR ready reckoner, Maha-Metro, OSM). No scraped portal data.
- Video: static-to-Reel templates only after the static loop proves itself.

### Phase 4: Builders and monetisation (month 9+)
Builder project pages and demand reports; agent subscription or per-qualified-lead pricing once the entity and legal advice are in place.

## 5. Next three sprints (2 weeks each)

**Sprint 1: "Close the loop on comments and Instagram"**
1. Comment assistant: poll, classify (rules + LLM), safe reply, human queue, record-only default. Kill switch, hourly and per-person caps.
2. Instagram: link account, publish carousel, comment handling reuse.
3. Agent "My profile" and listing photo tools polished.
4. Staging environment (second compose stack) so deploys are tested before live.

**Sprint 2: "Show the proof"**
1. Unified enquiry inbox (site, comments, WhatsApp clicks) with channel and listing attribution.
2. Per-listing performance screen and weekly WhatsApp report.
3. First real agents onboarded (3), with a feedback call each.

**Sprint 3: "Content that earns traffic"**
1. Content workflow: source notes, draft, approve, schedule; publishes to `/insights` and the Page.
2. Three locality pages; sitemap; page speed and SEO basics.
3. Second batch of Kharadi/Wagholi content driven by real search questions from comments and enquiries.

## 6. Architecture decisions

- **Modular monolith stays.** FastAPI + MongoDB + Next.js; modules with frozen contracts (`docs/contracts`). Splitting services is premature.
- **Background work needs a proper home.** Today the comment watcher would run inside the API process. Move scheduled jobs (comments, freshness, reports, publishing queue) to a small worker container with a Mongo-backed job collection and idempotent handlers.
- **Provider abstraction for AI.** One interface for text, extraction and speech with a provider chain and per-provider quotas (already true for text via failover). Add cost + quality logging per call.
- **Every AI output passes a validator.** Facts protected, phone/hype/number checks, source-required for market claims. Human approval for anything published as "information".
- **Data:** official and licensed sources only; no scraping of portals.
- **Environments:** local, staging (same compose), production; separate GCP project for production; domain + HTTPS; secrets in Secret Manager instead of `.env` on disk; backups tested by restore.
- **Observability:** structured logs, error alerts to WhatsApp/email, a simple dashboard (posts, comments, leads, LLM failures, quota use).
- **Security/privacy:** DPDP Act consent and deletion already designed in; keep PII (phone numbers) out of every public surface; rate limits and honeypots stay.

## 7. Trust, compliance and content quality (non-negotiable)

- **Sample vs real:** samples are labelled everywhere and cannot be posted (enforced in the server).
- **Market and infrastructure claims:** cite official sources, show the date, say "approved is not running", never predict prices or say "invest now".
- **Advertising:** RERA number shown when provided; agents warned about MahaRERA registration for their own practice; no guarantees or superlatives.
- **Meta and WhatsApp rules:** comment replies are 1:1 and rate-limited; no mass DMs; WhatsApp only with opt-in.
- **Entity and legal:** pilot is fine as a technology test with permission; before charging, taking commissions or selling leads, incorporate and take CA/legal advice.

## 8. Metrics (weekly review)

Activation (agent posts first listing within 24 h), listings per agent per week, **second-listing rate**, enquiries per listing, time to first response, qualified-lead share, site visits booked,
content views to enquiry rate, post reach by channel, AI failure rate and quota use, cost per agent per month.

## 9. Risks

| Risk | Mitigation |
|---|---|
| Agents do not add a second property | Interview after listing one; make weekly report show value; remove friction (photos, price checks) |
| Free AI tiers throttle or change | Provider chain, deterministic fallbacks, small paid backstop (a few hundred rupees a month) |
| Wrong market information damages trust | Source + date + human approval, no predictions, easy correction path |
| Meta policy or permission changes | Own website first; Meta features degrade gracefully; keep tokens rotated |
| Single VM outage | Snapshots now; separate project + staging in Sprint 1; managed DB when paid customers exist |
| Scope creep toward "portal" too early | Phase gates with exit metrics; nothing from Phase 2 before Phase 1 exit |

## 10. Decisions I need from the owner

1. Pilot agents: who are the first 3 to invite, and what should we promise them?
2. Domain name (buy this week) and whether to keep `sslip.io` only for testing.
3. OTP: WhatsApp Business (needs Meta business verification) vs SMS provider vs keep invite codes for the pilot.
4. Paid AI backstop: approve a small monthly cap (about ₹500) for reliability.
5. Content owner: who approves market/infrastructure articles before they go live (you, or a local expert)?
