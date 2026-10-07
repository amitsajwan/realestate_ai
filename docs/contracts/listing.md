# Contract: Listing (frozen for Sprint 1)

Changes need a contract PR reviewed by the integrator (WS-0). India-first.

## Listing
```
id                     string (uuid hex)
agent_id               string            owner (== user id)
status                 draft | live | under_offer | sold | rented | paused | expired
visibility             private | network | public     default: network
transaction            sale | rent
property_type          apartment | villa | house | plot | commercial | office | shop
title                  string (<=120)
description            { en: string, hi?: string, mr?: string }
price_inr              integer (rupees; rent = per month)
city                   string
locality               string
project_name           string?           society / building / project
bhk                    number?           1, 2, 2.5, 3 ... (null for plot/commercial)
carpet_sqft            integer?
super_built_up_sqft    integer?
floor                  integer?
total_floors           integer?
furnishing             unfurnished | semi | furnished  ?
possession             ready | under_construction | string date  ?
rera_no                string?
amenities              string[]
media                  [{ url: string, kind: image | video, order: int }]   optional, max 10
created_at, updated_at, published_at?, freshness_confirmed_at?   ISO datetimes (UTC)
```
Money is always integer rupees; the UI formats lakh/crore (85,00,000 -> "85 L", 1,25,00,000 -> "1.25 Cr").

## Lifecycle
`draft -> live -> under_offer -> sold|rented`; `paused` and `expired` reachable from live/under_offer.
Only `live` (and `under_offer`, flagged) listings are shown publicly. `publish` requires: title, transaction,
property_type, price_inr, city, locality, description.en. Photos are OPTIONAL (agents upload their own; max 10 per listing, resized in the browser before upload to keep hosting cost low).
Freshness: `freshness_confirmed_at` older than 30 days -> listing auto `expired` (job comes later; field exists now).

## API (all under /api/v1, JSON, bearer auth unless marked public)
```
POST   /listings                      create draft                      -> Listing
GET    /listings?status=&limit=       my listings                       -> { items: Listing[] }
GET    /listings/{id}                 mine                              -> Listing
PATCH  /listings/{id}                 partial update (owner only)       -> Listing
POST   /listings/{id}/publish         validate + status=live            -> Listing (422 lists missing fields)
POST   /listings/{id}/status          { status } allowed transitions    -> Listing
POST   /listings/ai/draft             multipart: text?, audio?, images[] -> AIDraft   (owned by ai_listing module)
GET    /public/agents/{slug}/listings [public] live listings of an agent, paged      -> { items: PublicListing[], total }
GET    /public/listings/{id}          [public] live listing                          -> PublicListing
```
PublicListing = Listing minus agent-private fields (visibility, freshness_confirmed_at, rera_no is included) plus
`agent: { slug, agent_name, phone, photo }`.

## AIDraft (returned by /listings/ai/draft, never persisted until the agent confirms via POST /listings)
```
draft        Listing fields (partial; same names/types as above, description.hi/mr filled when possible)
confidence   { field_name: 0..1 }        per extracted field
missing      string[]                    fields required to publish that are still empty
transcript   string?                     when audio was supplied
warnings     string[]                    e.g. "price looks low for Baner 2BHK"
```

## Tracking (already built: backend/app/modules/tracking)
Public site posts `POST /t/event` (page_view, listing_view, share, call_click, whatsapp_click) and `POST /t/inquiry`
(consent required) with `agent_slug`, a random `anon_id` kept in localStorage, `listing_id`, `source`, `utm{}`.
Agent inbox: `GET /inbox/leads`, `GET/PATCH /inbox/leads/{id}`.

## Onboarding (already built: backend/app/modules/onboarding)
`POST /join/otp/request`, `POST /join/otp/verify` -> `{access_token, is_new_user, has_site, site_url}`,
`POST /join/site` (auth) -> `{slug, site_url, agent_name, tagline, created}`. In development the OTP request returns `dev_code`.
