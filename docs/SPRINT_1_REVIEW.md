# Sprint 1 review

**Goal:** an agent signs up with a phone number, gets a live site, posts a listing from typed or spoken text, and an enquiry shows up as a scored lead in their inbox.

**Result:** the backend journey is proven end to end against a real MongoDB (`backend/scripts/e2e_smoke.py`, 25 steps, all pass). Frontend screens are built and unit-tested but have not yet been clicked through against the live backend.

## Delivered
| Stream | Delivered | Evidence |
|---|---|---|
| Onboarding | phone OTP (hashed codes, expiry, attempts, rate limits), one-call site creation, idempotent | 10 tests + e2e |
| Tracking / leads | public event + inquiry (bot filter, rate limit, DPDP consent), scoring, agent-scoped inbox | 9 tests + e2e |
| S1 Listings | lifecycle, publish validation (422 lists missing fields), owner isolation, public reads, duplicate fingerprint | 59 tests + e2e |
| S2 AI draft | deterministic + optional LLM extraction (Eng/Hindi/Marathi/Hinglish), copy, voice via Whisper, confidence/missing/warnings | 58 tests, 100% on a 38-input golden set (written by the same author; expect real-world accuracy to be lower) |
| S3 Public site | server-rendered `/agent/<slug>` and listing pages, OG/JSON-LD, tracking beacon, consent enquiry form, fixture mode | 32 tests |
| S4 Agent app | `/join` and `/studio` (listings, voice/typed add listing, review-and-confirm, lead inbox), fixture mode | 49 tests |

Totals: 138 backend tests, 81 frontend tests, plus the e2e smoke test.

## Found only by the real-database run
- Placeholder email domain `.local` is rejected by the legacy `User` email validation, so every new signup returned 500. Fixed (`phone-login.propertyai.app`) with a regression test. Lesson: keep the e2e smoke test in the definition of done.

## Not verified yet
- Frontend against the live backend (only fixture mode exercised); mic recorder and photo picker never used in a real browser.
- AI draft with a real Groq key and real Whisper audio (only fakes/mocks).
- `next build` fails on a legacy type error in `components/property/shared/PropertyImageUpload.tsx`; 70+ legacy type errors elsewhere.
- Photo upload uses the legacy `/api/v1/uploads/images` (no HEIC, absolute URLs built from the request host).

## Known gaps / debt
- `POST /listings/ai/draft` ignores image bytes (only `image_count`).
- Mongo indexes not created yet (`listings(agent_id, created_at)`, `listings(agent_id, status, visibility, published_at)`, `listings(fingerprint)`, `events(agent_id, anon_id)`, `contacts(agent_id, phone)`, `otp_codes` TTL).
- The 30-day freshness expiry job is not built. Hindi/Marathi UI strings are mostly missing.
- Legacy code (`services/*`, ~30 endpoint files, old frontend pages) still present; auth still has dev/mock fallbacks.
- Site is at `/agent/<slug>`; subdomain routing designed, not built. Domain name undecided.

## Sprint 2 proposal (in order)
1. **Wire and harden:** Mongo indexes at startup; run frontend against the live backend and fix integration bugs; remove the legacy auth mock/dev paths; delete dead legacy endpoints; clean legacy type errors so `next build` passes.
2. **Per-listing activity + lifecycle:** activity page (views by channel, feed, ranked people), freshness job and WhatsApp "still available?" prompt.
3. **Distribution v1:** tracked share links per channel (works without Meta approval), then Instagram/Facebook Page publishing and WhatsApp click-to-chat once approvals land.
4. **Notifications:** hot-lead alert and daily digest (WhatsApp/SMS provider decision).
5. **Real OTP provider** (MSG91/Twilio/WhatsApp) replacing the console provider.

## Decisions needed from the product owner
Domain name · pilot city (assumed Pune) · WhatsApp Business / Meta developer account owner (start applications now, weeks of lead time) · OTP/SMS provider · pricing for the free tier.
