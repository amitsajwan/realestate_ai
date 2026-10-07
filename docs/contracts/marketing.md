# Contract: Marketing Pack, reverse matching, property performance, recommended actions (Sprint 3, frozen)

The PROPERTY is the central object. After an agent confirms a property, the platform creates a "marketing pack" from the
facts already on the listing and shows which existing buyers match it. Nothing here posts to any external network:
Instagram/Facebook/WhatsApp publishing needs Meta approvals we do not have, so packs are copy / download / share ready and
the UI shows a clearly labelled "connect account to publish (coming soon)". Nothing invents facts: every number, amenity,
price, locality and RERA number comes from the listing. No superlatives or claims ("best", "guaranteed", "lowest price").

## 1. Marketing Pack  (collection `marketing_packs`, `_id` = listing_id, owner scoped by agent_id)
```
MarketingPack {
  listing_id, language: "en" | "hi" | "mr", version: int, generated_at: ISO,
  angle:    string      one line buyer angle, e.g. "Ready-to-move 2 BHK in Baner under Rs 1 Cr"
  headline: string      <= 90 chars
  instagram: { caption: string (<= 900 chars, ends with a call to action), hashtags: string[] (<= 12, city/locality/BHK/type),
               images: ImageAsset[] }                       carousel: cover, facts, amenities (only if amenities exist), cta
  facebook:  { post: string }                               longer, informative, paragraphs allowed
  whatsapp:  { message: string, status_text: string, status_image: ImageAsset | null }   short, conversational, includes the listing link
  reel:      { hook: string, beats: [{ seconds: string, text: string, visual: string }], cta: string, duration_s: number }   SCRIPT ONLY
  share_url: string     the public listing link with ?src=whatsapp
}
ImageAsset { kind: "cover" | "facts" | "amenities" | "cta" | "status", url: string, width: number, height: number }
```
Angle rules (deterministic): possession ready -> "Ready-to-move", under construction -> "Under-construction"; budget bucket phrase
("under Rs 50 L", "under Rs 1 Cr", "under Rs 2 Cr"...) chosen as the smallest round ceiling above the price; then BHK, type and locality.
Channel voice: Instagram short/visual with emoji sparingly; Facebook more detail; WhatsApp 2-3 short lines; reel beats
hook -> property -> location -> price -> call to action (total ~15 s).
An optional injectable LLM may only re-word text and is discarded if any protected fact (price text, BHK, locality, area,
RERA number) is missing from its output. Hindi/Marathi: simple templates or fall back to en (`language` reports what was used).

Images: 1080x1080 cards (cover, facts, amenities, cta) and one 1080x1920 status card, rendered server side with Pillow using the
listing's FIRST photo as background when it is one of our own local uploads (`/uploads/images/<file>` served from the
backend uploads directory; NEVER fetch remote URLs: no SSRF), otherwise a clean solid/gradient card. Text: price (lakh/crore),
BHK + type, locality/city, area, possession, agent name and a short call to action; keep text inside safe margins and legible on
any background (dark overlay). Use Pillow only (already installed, no new deps, no bundled binary fonts; `ImageFont.load_default(size)`
scalable font is fine; Devanagari text on images is out of scope: image text stays English/numerals). Files are written to
`<uploads>/marketing/<listing_id>/<kind>.jpg` and served via the existing `/uploads` static mount; `url` is absolute like the
existing uploads endpoint builds them (`<base>/uploads/marketing/<listing_id>/<kind>.jpg`).

API (bearer auth, mounted by the integrator at prefix `/listings`, agent owner only, other agents get 404):
```
POST /api/v1/listings/{id}/marketing   body { language?: "en"|"hi"|"mr" }  -> MarketingPack   (generate or regenerate; version += 1)
GET  /api/v1/listings/{id}/marketing                                          -> MarketingPack | 404
```
Only listings with status live/under_offer (not draft) can be marketed (409 otherwise).

## 2. Reverse matching: "N of your buyers match this property"  (tracking module)
```
GET /api/v1/inbox/matching-leads?listing_id={id}
-> { listing: { id, title, price_inr, locality, share_url },
     buyers: [{ lead_id, name, phone, temperature, score, requirement_line, match_pct, reasons: string[],
                draft: { message: string, whatsapp_url: string } }] }   sorted by match_pct desc then score, only match_pct >= 60, max 10
```
Buyers = the agent's own leads not in stage won/lost. Uses the SAME transparent rule scoring as lead -> listing matching (budget fit,
BHK, locality, transaction/type), applied in reverse. `draft.message` is personalised and factual ("Hi {first}, I have a new
{2 BHK in Baner} at {85L}; it fits your {80L-90L} budget. Details: {share_url}") and only says "fits your budget" when the price is
inside the buyer's stated budget (never claim a fit that is not there). `whatsapp_url` = wa.me/<digits>?text=<encoded>.

## 3. Property performance
```
GET /api/v1/inbox/performance -> { items: [{ listing_id, title, price_inr, status, views, unique_visitors, enquiries, qualified,
                                             site_visits, by_source: { <source>: enquiries } }] }   sorted by enquiries desc, then views
```
views = listing_view events; unique_visitors = distinct anon_id among them; enquiries = leads whose first_listing_id is the listing;
qualified = those enquiries that are warm/hot OR have a stated budget or timeline; site_visits = those enquiries at stage site_visit or
later (site_visit, negotiating, won); by_source counts enquiries by their source (missing -> "direct"). Owner scoped.

## 4. Recommended actions (extends GET /api/v1/inbox/today with `actions`)
```
actions: [{ type: "call" | "follow_up" | "send_property" | "create_marketing",
            title: string, detail: string, priority: 1..3,
            lead_id?: string, listing_id?: string, buyer_count?: number }]      ordered by priority then recency, max 6
```
Rules: hot buyer not yet contacted -> call (priority 1); overdue follow-up -> follow_up (1); a live listing created in the last 3 days with
>= 1 matching buyer (per section 2) -> send_property "Send the {label} to {n} matching buyers" (2); a live listing with no marketing pack ->
create_marketing (3). Existing fields of /today are unchanged.

## Ownership (Sprint 3)
- M  backend/app/modules/marketing/** and tests/modules/test_marketing*.py (pack generation, images, router, `marketing_packs` collection)
- T  backend/app/modules/tracking/** and tests/modules/test_tracking*.py, test_qualification*.py, new test_matching_reverse*.py (sections 2-4;
     section 4's create_marketing rule reads the `marketing_packs` collection read-only)
- F  frontend/components/app/**, frontend/lib/app/**, frontend/app/studio/**, frontend/__tests__/app/** (post-listing marketing screen, buyers-match card,
     home recommended actions, performance on the listings screens)
