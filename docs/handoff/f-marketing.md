# Handoff: stream F (marketing pack, matching buyers, AI recommends, performance)

Branch `v2/f-marketing`, built against `docs/contracts/marketing.md` (frozen). Fixture mode implements everything.

## What was added
- Client (`lib/app/api.ts`, `types.ts`): `createMarketingPack(id, language?)` POST `/listings/{id}/marketing`, `getMarketingPack(id)` GET (404 = none yet),
  `getMatchingLeads(id)` GET `/inbox/matching-leads?listing_id=`, `getPerformance()` GET `/inbox/performance` (returns `items`), `BusinessToday.actions?`.
- Fixtures (`fixtures.ts`, `fixtures-marketing.ts`): storage key bumped to `app_fixture_state_v3` (state gains `packs`). Marathi falls back to English
  (`language: "en"`), Hindi has a small template. Images are 1080x1080 (status 1080x1920) SVG data URIs. Seed listing `l1` is now ready-to-move and 20 h old
  so `send_property` shows up.
- Screens: `MarketingScreen` (language chips, skeleton, retry, pack cards, buyers card), `MarketingPackView` (Instagram carousel, Facebook, WhatsApp, Reel,
  disabled "Publish everywhere"), `MatchingBuyersCard`, route `/studio/listings/[id]/marketing`, "Your property is ready" after Confirm & post
  (generation failure never blocks; the listing is already live), "AI recommends" on home, performance row on listing cards, Marketing and
  Buyers-who-match buttons on listing detail (live / under_offer only).
- Helpers in `lib/app/marketing.ts` (hashtags, copy texts, wa.me builders, share/download, action targets). Strings in `strings.ts`.

## Behaviour notes
- Home actions: Call and Follow up open the lead detail (the action has no phone number, the Call button lives there); Send property and Create marketing open
  `/studio/listings/{id}/marketing`. The card text and the primary button share the target.
- Post flow calls POST straight away (no GET). The route calls GET first and POSTs on 404, so opening it never needs a manual "create" tap.
- Buyer "Send on WhatsApp" uses the server `draft.whatsapp_url` while the message is unedited, and rebuilds `wa.me/<digits>?text=` after an edit.
- Nothing is sent automatically. Connect buttons are disabled and marked "Coming soon".

## API gaps / assumptions
- The performance endpoint response is read as `{ items: [...] }` per contract; a listings-screen failure of it is ignored (cards just omit stats).
- Images are used as returned (absolute URLs). Share/Download fetch the image as a blob; if the browser blocks that (CORS) we open it in a new tab. If the
  backend serves `/uploads` from another origin, it needs CORS for `GET` to allow real file share and one-tap download.
- `#buyers` anchor from listing detail does not scroll after load (the page fetches the listing first); minor polish.
- Old `app_fixture_state_v2` local data is ignored (reseeded).
