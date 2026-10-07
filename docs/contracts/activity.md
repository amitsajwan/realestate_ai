# Contract: per-listing activity, listing freshness, inquiry abuse protection (Sprint 6, frozen)

## 1. Listing activity  (GET /api/v1/inbox/listings/{listing_id}/activity?limit=50, agent auth, owner scoped; other agents 404)
```
{ listing: { id, title, status, price_inr },
  totals:  { views, unique_visitors, enquiries, qualified, site_visits, deals, whatsapp_clicks, call_clicks, shares },
  by_source: { "<source|direct>": { views, enquiries } },
  daily:   [{ date: "YYYY-MM-DD", views, enquiries }]            last 14 days, INDIA dates (IST), oldest first, zero-filled
  feed:    [{ ts, type: "view"|"whatsapp_click"|"call_click"|"share"|"enquiry",
              who: { kind: "visitor"|"lead", label: string, lead_id?: string },
              source: string | null, text: string }]              newest first, max `limit` (<= 100)
  people:  [{ lead_id, name, temperature, score, requirement_line, last_activity_at }]   leads who enquired on this listing or
                                                                   interacted with it, hottest first, max 10 }
```
- Same counting rules as GET /inbox/performance (views = listing_view events; unique_visitors = distinct anon_id; enquiries = leads whose
  first_listing_id is this listing; qualified/site_visits/deals as there).
- PRIVACY: anonymous visitors are labelled "Visitor 1", "Visitor 2"... (stable per anon_id within the response); never expose anon ids, IPs or
  user agents. A visitor who later became a lead is shown as the lead's name.
- `text` is plain English, e.g. "Visitor 2 viewed this from Instagram", "Priya Sharma tapped WhatsApp", "Amit Kulkarni sent an enquiry".

## 2. Freshness ("still available?")
Listing responses on the AGENT side (GET /listings, GET /listings/{id}, PATCH, publish, status) gain:
```
freshness: "fresh" | "confirm" | "hidden"      only meaningful for status live/under_offer; other statuses -> "fresh"
days_since_confirmed: integer | null
```
Rules (based on freshness_confirmed_at, falling back to published_at, then created_at): < 21 days -> fresh; 21..44 days -> confirm (the app asks "Is this still
available?"); >= 45 days -> hidden (NOT shown on public reads until confirmed; the agent sees "Hidden from buyers until you confirm").
- `POST /api/v1/listings/{id}/confirm-available` (owner only, live/under_offer only, else 409) sets freshness_confirmed_at = now and returns the Listing.
- Public reads (GET /public/agents/{slug}/listings, GET /public/listings/{id}) exclude listings whose freshness is "hidden" (404 for a single hidden one).
- Reactivation from paused/expired already re-stamps freshness (unchanged).

## 3. Inquiry abuse protection  (POST /api/v1/t/inquiry)
- Honeypot: the body may carry an optional `website` field (a hidden input real visitors never fill). When non-empty the request returns the normal
  success response `{received: true, new_lead: false}` but NOTHING is stored.
- Per (agent, phone) limit: at most 3 inquiries per rolling hour; the 4th returns HTTP 429 with a friendly message ("Too many messages. Please try again later").
- Per anonymous visitor (anon_id) limit: at most 5 inquiries per rolling hour (429 likewise).

## Ownership (Sprint 6)
- C1 backend/app/modules/tracking/** and backend/app/modules/listings/** (+ their tests, new tests test_activity*.py, test_freshness*.py, test_inquiry_limits*.py)
- C2 frontend/components/app/**, frontend/lib/app/**, frontend/app/studio/**, frontend/__tests__/app/** (activity page, freshness prompts)
