# Reach and captions: audience-aware tags, cleaner asks, WhatsApp-ready (plan, 2026-10-11)

Owner's questions (2026-10-11): are hashtags chosen for the audience we target, and does every post record that so we can learn?
What in the captions can improve? How does Facebook decide who sees a post? Make WhatsApp easy to switch on when the number arrives.

## What exists (read before changing)

| Part | Where | State |
|---|---|---|
| 5 tags on Instagram, 3 on Facebook, most specific first (locality, corridor, project, type, `#<Locality>RealEstate`, `#MahaRERA`) | `calendar/reach.py` | LIVE |
| Tags on every calendar row (audience buyers/agents, format, hook, cta, area, language) copied into each insights snapshot | `calendar/tags.py`, `insights/collector.py` | LIVE |
| Location tag per area (`IG_LOCATION_*`) | `reach.location_id` | BUILT, OFF (no place ids on the VM) |
| Buyer WhatsApp line in captions with the post's interest code (FB tap link, IG "send: interested in CODE") | `calendar/adapters.whatsapp_lines`, `propertyfacts/identity.posts_whatsapp_number` | BUILT, OFF (`WHATSAPP_PUBLIC_NUMBER` unset) |
| Footer ask on every post: "Comment INFO… Share… Follow…" | `calendar/footer.ask_for` | LIVE |

## Gaps and decisions

1. **Audience is only buyers/agents.** A ₹17 L plot, a ₹2.5 Cr row house and a rental get the same tags and the same label in the
   results. Add a derived **segment** (`renter`, `plot`, `first_home`, `family_home`, `premium`, `unknown`) plus `price_band`, `bhk`,
   `property_type`, `transaction`. Derived by code from fields the row carries (campaign rows get price, BHK and transaction from the
   listing in `schedule.property_of`); never guessed: unknown stays `unknown`. One function, `reach.segment(doc)`, feeds both the
   hashtags and the tags, so what we target and what we measure cannot drift apart.
2. **One audience hashtag.** The segment's own tag takes one slot after locality and project: `#2BHKWagholi` when BHK and an
   apartment are known (what buyers type), `#FlatsForRentPune` for rentals, `#NAPlotsPune` for plots, `#AffordableHomesPune` for a
   first home with no BHK. No growth/investment words in tags (same rule as captions).
   *Rejected:* Devanagari hashtags. Python's `\w` stops at vowel signs (`#पुणे` reads as `#पुण`), which would corrupt our tag
   parsing and the footer's tag trimming; the gain is small.
3. **Record what was actually used.** At publish the runner writes the final hashtag line and whether a location tag went out into
   the row's tags (`hashtags`, `location`). Re-deriving tags keeps them. The collector already copies tags into every snapshot.
4. **Footer asks less.** Three asks on every post read as engagement bait, which Meta demotes, and dilute the one action that
   matters. New rule: **one ask per post**. A post that already carries an action (interest link, WhatsApp line, its own comment
   keyword) gets only a *send* ask ("Send this to someone looking in Wagholi"): sends are the strongest reach signal we can ask for.
   About 1 post in 4 (stable by slug) asks "Comment INFO", so the comment assistant keeps getting work and we can compare.
   Recruitment posts are unchanged (their keyword is the funnel).
5. **A search line in the visible preview.** Instagram and Facebook show about the first 125 characters before "more", and
   Instagram search reads caption words. For a listing post, code adds one line right after the headline, in the post's language:
   `📍 2 BHK flat for sale in Wagholi, Pune · ₹85 lakh` (a starting price stays "from ₹X onwards"; rent says "for rent … a month").
   Skipped when the first line already names both the place and the price. Facts come from the listing record only.
6. **WhatsApp in one command.** `whatsapp_connect.ps1 -PublicNumber` today writes only the website's build value. It will also write
   `WHATSAPP_PUBLIC_NUMBER` (captions) and `NEXT_PUBLIC_CONTACT_WHATSAPP`, then rebuild the frontend. A read-only
   `scripts/whatsapp_status.py` prints which WhatsApp features are on and what is missing. Checklist in `docs/WHATSAPP_SETUP.md` §H.
7. **Results by audience.** `scripts/content_report.py` groups the latest snapshot per post by any tag (segment, hook_type, format,
   area, hashtag, location) and prints views, reach, saves, shares, average watch time and enquiries per 1,000 views. Small numbers
   are flagged (fewer than 3 posts in a group: "too few to call").

## How Facebook and Instagram decide who sees a post (for the team)
No targeting for organic posts. The system reads what the post is about (caption words, on-screen text, voice, hashtags, location,
the image), shows it to a small test group of followers and non-followers interested in similar things, and widens it when watch
time, sends, saves and comments beat similar posts. Our levers: clear place/BHK/price words in caption, card and voice; the location
tag; the first 2 seconds; a reason to send it to someone; collab posts; paid boosts (the only real targeting).

## Not in this change
Spec-block caption variant (needs the copy pipeline and guards; next), Trial reels and collab posts (done in the app by hand),
Instagram place-id lookup (Meta's place search needs extra permissions; ids are looked up by hand, see MARKETING.md).

## Work items
| # | Change | Files |
|---|---|---|
| R1 | `segment`, `price_band`, segment hashtag | `calendar/reach.py` |
| R2 | Tags schema 2 with segment fields; keep `hashtags`/`location` on re-derive | `calendar/tags.py` |
| R3 | Record hashtags + location at publish | `calendar/store.py`, `calendar/runner.py` |
| R4 | Campaign rows carry price, BHK, transaction | `propertyfacts/schedule.py` |
| R5 | One ask per post | `calendar/footer.py`, `calendar/adapters.py` |
| R6 | Search line after the headline | `calendar/adapters.py` |
| R7 | Report by tag | `backend/scripts/content_report.py` |
| R8 | WhatsApp one-command switch-on + status | `deploy/gcp/whatsapp_connect.ps1`, `backend/scripts/whatsapp_status.py`, `docs/WHATSAPP_SETUP.md` |

## By hand, alongside the code (owner)

**Collab posts with Pune city pages** (the 494K-view ₹17.5 L post came from a city page, not an agent). Ask 3 pages a week; pay
only after seeing their Pune share of followers (ask for an Insights screenshot). Post as an Instagram Collab (both accounts as
authors), our sourced card or reel, their caption style allowed but our facts unchanged.

> EN: Hi! We run Avasetu, Pune property listings checked against MahaRERA. Would you do a collab post with us (you as co-author)
> on a home in {area}? We make the reel and the facts; you check it before it goes up. What do you charge per collab post, and
> what share of your followers is in Pune?
>
> MR: नमस्कार! आम्ही Avasetu चालवतो: MahaRERA वरून तपासलेल्या पुण्यातील प्रॉपर्टी. {area} मधील एका घरावर आमच्यासोबत collab पोस्ट
> कराल का? रील आणि माहिती आम्ही बनवू, पोस्ट होण्याआधी तुम्ही पाहू शकता. एका collab पोस्टचा तुमचा दर किती, आणि तुमचे किती फॉलोअर्स पुण्यात आहेत?

**Brokers who post listings publicly** (captions with "call or WhatsApp", "brokerage", "co-broking"): they are the agent list.
Make one campaign for their listing first, then send:

> Namaste {name} ji, aapki {area} wali {bhk} post dekhi. Maine us property ke liye free mein ek page, posts aur reel bana diya hai,
> MahaRERA details ke saath: {link}. Pasand aaye to aapke naam se live kar dete hain, buyers ke enquiries seedhe aapko aayenge.
> First month free.

**Trial reels** (Instagram app > new reel > Advanced settings > Trial): shown to non-followers only, so two hooks on the same
facts can be compared before one goes to followers. Tag the calendar row's `variant` the same way so `content_report.py --by
variant` lines them up.

**Weekly review (Monday, 15 minutes):** `content_report.py --by segment`, `--by hook_type`, `--by hashtag --min 2`. Keep what
gets saves, sends and enquiries per 1,000 views, not total views; change one thing at a time.
