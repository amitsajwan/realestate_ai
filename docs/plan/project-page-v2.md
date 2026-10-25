# Project page v2: each fact once, built to sell, built for search (2026-10-25, IN PROGRESS)

Owner, 2026-10-25, on /projects/park-eden-phase-i-kharadi: "why we have duplicate. Also think how it should be presented",
then "think design, ux, how a property can be sold, seo, and enrichment ... implementation, full force".

## What was wrong
- The same facts were said by up to eight blocks: the code-written answer (frontend `registerAnswer`), the model's summary
  (`page_text`), the model's sections, "The record", the side checks panel, "Verified facts", "Check before you book" and the
  FAQ. "27 of 249 homes booked" appeared four times. The model's prompt (areastats.enrich.SYSTEM) asked for the very facts the
  answer above it already gives, and nothing checks for repetition across blocks.
- Errors: five towers (builder's site, whole project) next to two buildings (MahaRERA, this registration) with no scope;
  MahaRERA's 4-month blanket extension written as "moved from" / "an increase" (the builder moved nothing); "All homes BHK
  from ₹1.99 Cr" (`askedPrices` adds " BHK" to the "All homes" row); "249 homes are available" for 249 in total.
- What a buyer comes for first (price and sizes, pictures and plans, possession, location) sat below the checks; sizes were
  not shown at all.

## The page, in order (phone first)
1. Hero: marketed name + phase, area, MahaRERA number; chips (BHK, price from, possession, booked); main action "Get today's
   price sheet & floor plans", second "Book a site visit".
2. One answer paragraph (code, the one AI search quotes), wording fixed. The model's summary is no longer shown.
3. Photos.
4. Prices and sizes: a row per home size (carpet sq ft, price range, ₹ per sq ft, source and date); the area's ₹ per sq ft
   beside it; "Ask for the current offer".
5. Floor plans (some open, the full set for a phone number).
6. Location: map, straight-line distance to the work hubs people commute to, then what is nearby.
7. Highlights (bullets).
8. About the project: the model's sections only, saying what the facts above cannot (layout, the phase in the whole
   project, location in words). No figure the page already shows.
9. Checked by us: one section for the MahaRERA record, the checks, tower by tower, the builder's track record and the
   cautions.
10. Compare: other projects in the area with price from and possession.
11. FAQ, short answers. 12. Enquiry form; sticky bar on phones.

## SEO
- H2s that match what people search: "<name> price", "floor plans", "possession date", "location", "amenities",
  "RERA details".
- Title "<name> <area>: 3 & 4 BHK from ₹1.99 Cr, possession Feb 2031"; description with price, sizes, the RERA check.
- Structured data: ApartmentComplex (+ an Offer per home size with price and floor size), FAQPage, BreadcrumbList, the
  builder as Organization.
- No repeated text. Names: marketed, MahaRERA's and "<name> <area>" each once.

## Contract between the backend view and the page (areastats.pages.project_page)
New or changed fields, all optional on the frontend (absent or null shows nothing):
- `prices.rows[].per_sqft`: int, ₹ per sq ft of the row's lowest price when its `sqft` is known (rounded).
- `area_rate`: `{place: str, per_sqft: int, projects: int}` | null: the median ₹ per sq ft of the published prices with a
  size in the same area (pune_place, else locality), from at least 3 other projects; null otherwise.
- `sales`: `{booked: int, days: int, since: "YYYY-MM-DD"}` | null: homes booked between the two MahaRERA reads in
  `booked_history` closest to 30-90 days apart (the latest read and the oldest one within 90 days); null without two reads
  or when none were booked.
- `commute`: `[{name: str, km: float}]`: straight-line km from the checked map position to our work hubs (app.core), nearest
  first, at most 4; [] without a checked position.
- `web_facts.facts[].scope`: "project" | "registration" | null: "project" when a count (towers, homes) on the builder's
  or property site is larger than this registration's MahaRERA count (it describes the whole marketed project).
- `same_area[].price_from`: int | null; `same_area[].bhk`: str | null ("2, 3 BHK" from the published price rows).
- `extension_only`: bool: the only change to the filed completion date is MahaRERA's 2026 blanket extension.
- `paragraph` stays (code paragraph or old model summary) for the description fallback; the page no longer renders it in
  "About". `sections` are the model's text.

## The page writer (areastats.enrich, TEXT_VERSION 4)
Sections only ("The project", "Location"), no summary. The writer is told what the page already shows (name, builder,
area, number, completion date, bookings, prices, BHK, the highlights) and not to repeat it; a code check refuses a draft that
repeats the booking count, the completion date or a price, says the date moved/increased/was pushed when the only change is
the extension, or gives a whole-project count as this registration's. A one-line search summary stays. Rewrites go through
the model budget (areastats.budget), premium projects first.
