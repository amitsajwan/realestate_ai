# Contract: public front door, legal pages, invite requests (Sprint 6, frozen)

## Public pages (Next.js, server-rendered, no login, mobile-first; not inside the agent app or agent sites)
- `/`           agent-facing landing page (replaces the legacy home page; the legacy pages login/register/dashboard stay untouched)
- `/request-invite`  form: name, mobile (Indian), city (default Pune), optional message, consent checkbox, honeypot field named `website`
- `/privacy`  `/terms`  `/data-deletion`   plain-language legal pages (see below)
All show the business name and contact details from environment variables (NEXT_PUBLIC_*), never hard-coded personal data:
```
NEXT_PUBLIC_BUSINESS_NAME   default "PUNE Property"
NEXT_PUBLIC_CONTACT_EMAIL   optional; when unset the email line is simply not shown (do NOT invent an address)
NEXT_PUBLIC_CONTACT_WHATSAPP optional (digits, e.g. 919876543210); when unset no WhatsApp contact is shown
NEXT_PUBLIC_SITE_URL        existing; used for canonical/OG
```

## Landing page content (honest: describe only what works today)
Headline about getting buyer enquiries and knowing who to call first (not "a website builder"). Sections: what it does in 4 steps (Create, Market, Attract,
Qualify/Close), how it works for an agent (invite-only pilot in Pune), what it costs (free during the pilot), a short honest "what's coming"
(posting to Instagram/Facebook/WhatsApp needs approvals; automatic follow-ups later), FAQ (data, consent, who sees my listings), a clear CTA to /request-invite and
a link to sign in (/join). Use real screenshots only if supplied as static files under frontend/public/landing/ (a few are provided by the integrator in
frontend/public/landing/*.jpg); never invent testimonials, numbers, customer logos or ratings.

## Legal pages (plain language, India-oriented, NOT legal advice; the integrator tells the owner to have a lawyer review)
- /privacy: who we are; what we collect (agent: name, phone, city, listings, photos; buyers: name, phone, message, enquiry preferences, pages viewed on an agent's
  site via a random id in the browser, source link); why (to connect buyers and agents, show agents their enquiries, improve the service); the buyer's consent is asked
  on the enquiry form; who sees it (the agent the buyer contacted, and us as service provider; not sold); when a listing is posted to our Facebook/Instagram page the
  agent's name (never their phone number) appears in it with the agent's consent; retention (kept while the account is active, deleted on request within 30 days); rights (access,
  correction, erasure, withdraw consent) under India's Digital Personal Data Protection Act 2023; children; security in general terms; changes; contact + grievance contact
  from the env values (or a note that contact details are on the request-invite page).
- /terms: pilot service terms in plain language: who may use it (real estate agents invited by us), agent responsibilities (accurate listings, real photos, RERA
  compliance where applicable, consent for posting), buyer data use limits, no misleading content, we may remove listings/accounts, service provided as-is during the
  pilot, liability in general terms, governing law India (city Pune), contact.
- /data-deletion: how anyone (agent or buyer) asks for their data to be deleted: contact channel(s) from env, what we need (the phone number used), what is deleted,
  timeline (30 days), what may be retained if required by law. Also the exact wording Meta accepts for "data deletion instructions".
Each page: last-updated date, clear headings, links to each other, footer links on the landing page and the enquiry form area (footer of agent sites may link /privacy).

## Invite request API (public, no auth)  POST /api/v1/join/request-invite
```
body:  { name: string (2-100), phone: Indian mobile (normalised +91XXXXXXXXXX), city: string (2-60, default "Pune"), message?: string (<= 500),
         consent: boolean (must be true: "OK to contact me about the pilot"), website?: string (honeypot) }
200:   { received: true }                 always the same body (also for duplicates and honeypot hits: no information leak)
422:   consent not true or invalid fields
429:   more than 3 requests per rolling hour from the same phone, or more than 20 per hour overall from the same client ip ("Too many requests")
```
Stored in collection `invite_requests`: { _id, name, phone, city, message, consent: {given_at, text}, ip_hash (sha256 with a server secret, never the raw ip), status: "new",
created_at, updated_at }. A repeat request from the same phone within 24 hours updates the existing record (message/name) instead of adding a row. Honeypot hits
are dropped silently. Admin script `backend/scripts/invite_requests.py list|mark-invited <phone>` (like scripts/invite.py) prints new requests and sets status.

## Ownership (Sprint 6)
- B  backend/app/modules/waitlist/** + backend/scripts/invite_requests.py + backend/tests/modules/test_waitlist*.py (integrator mounts the router at /join alongside the existing one)
     frontend/app/page.tsx, frontend/app/request-invite/**, frontend/app/privacy/**, frontend/app/terms/**, frontend/app/data-deletion/**,
     frontend/components/marketing/**, frontend/lib/marketing/**, frontend/__tests__/marketing/**, frontend/public/landing/** (read only)
