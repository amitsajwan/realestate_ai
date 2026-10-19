# Adding a listing: short by default (2026-10-19)

Owner, after listing Godrej Ivara: "Adding a listing is so complex. Work on it. Get UX, sales and all involved."
Three reviews (UX, sales/agent operations, data/compliance) read the flow and the Ivara run; this is the merged decision.

## What went wrong on Ivara

- About 8 screens and 40 fields before anything reached Instagram; the same facts asked three times (review form, "About the
  project and area", the marketing run's questions).
- We held the full MahaRERA record for PR1260002502426, but the draft took only number, place and name from it: the agent
  re-checked possession, floors, project or flat.
- The parser misread the text: 13 acres became a 5,66,280 sq ft carpet area, "2, 3 and 4 BHK" became 4, possession became the
  bookings date (Oct 2026), no project name. Fixed in eade18ec.
- The place came from the PIN (our guess, "Kharadi") but carried a MahaRERA badge.
- "About the project and area" asked for Keep/Remove on ~10 lines (from the wrong area's guide) before the facts were settled.
- Ask AI and Post & market sat on other pages after posting; the owner thought Ask AI was lost.

## Decisions

| # | Decision | State |
|---|---|---|
| 1 | A MahaRERA number fills everything the register holds: name, promoter, builder's possession date (MahaRERA's later date is mostly its Aug 2026 +4 months, Order 66/2026), towers, floors, homes booked, whole project when no flat's carpet or floor is given, sale, Pune. These are never flagged "please check". | LIVE |
| 2 | The new-listing check is short (`ReviewForm compact`): one read-only "From MahaRERA" card, then only the agent's fields (price, BHK, carpet for a flat, place when not sure), photos; everything else under "More details", which opens by itself when a field there is required or needs a look. The listing's Details tab keeps the full form. | LIVE |
| 3 | A place from the PIN alone is labelled "Our map: please check" (source `map`), not MahaRERA. Hand-checked places stay in `pune_places.VERIFIED` (Ivara added: Upper Kharadi). | LIVE |
| 4 | "About the project and area" no longer opens after drafting; it is one link on the check screen. | LIVE |
| 5 | Photos, brochure and video are asked once (capture screen); the check screen shows the photo picker only when none were added. The false "At least 1 photo is needed to publish" is gone (photos are optional). | LIVE |
| 6 | A whole project's title is "<Project>, <Place>: 2 BHK and up from ₹1.29 Cr", and the per-sq-ft price warning is skipped for it (a "from" price is not one flat's). | LIVE |
| 7 | After posting, one main button: Start marketing. Ask AI (ChatGPT / Gemini prompts) is the second button. Marketing stays a deliberate tap, never automatic (owner, 2026-10-14). | LIVE |
| 8 | Two doors at the start: "Builder project (MahaRERA number)" and "My resale / rent flat", each asking only its minimum. | TARGET |
| 9 | Several configurations and "from" pricing as data (2/3/4 BHK, price per type) plus one offer line (pay plan, booking amount). | TARGET |
| 10 | A number not in our register: say so, read MahaRERA live, keep the listing a draft until the number is confirmed. A new project with no number is not published (RERA Act). | TARGET |
| 11 | Lead feedback on WhatsApp after each post ("your post went live, 3 people asked"), leads per listing on Home. | TARGET |

## Not taken

- Sales asked for Post = market in one tap with auto-scheduling. Kept as one deliberate tap: the owner decided on 2026-10-14
  that posting must not start marketing by itself.

## Homes and prices, two posts (2026-10-19 evening, owner feedback on the Ivara campaign)

LIVE after this deploy:
- Listing: `configurations` (BHK, carpet, price per home type, smallest first) and `payment_plan` ("20:20:30:30"). Form:
  "Homes and prices" rows or a pasted builder price list; the smallest row sets the listing's BHK, carpet and "from" price.
- Posts: ONE carousel drawn by code from the listing (`propertyfacts/listing_posts.py`; owner: "why a post with just the price? include it in the single"): cover with name,
  place, home types, from-price, payment plan; three pictures combined on one slide from 5 pictures; smart crop on edge energy;
  phone photos lifted; maps, QR codes, clipart, screenshots and small pictures left out) and a details card (price table,
  payment plan, possession, MahaRERA QR) whose caption lists everything.
- Reels: the creative room's ideas only (no "why Avasetu" piece), else two formats the facts support; silent story scenes
  2.6-3 s each (~17 s reel). Calendar: gallery, a reel, details, the other reels, then the walkthrough.
- Walkthrough voice: "Possession Aug 2032" (was "2032-08"), "1 crore 29 lakh rupees" (was "1.29 crore").
- Our own posts carry the WhatsApp line (wa.me link on Facebook, wa.me + number on Instagram, with the post's code).
- MahaRERA badge reads PR + 13-digit numbers too.

TARGET: the AI draft reads a price sheet image into `configurations`; Marathi/Hindi cards (captions are translated now).
