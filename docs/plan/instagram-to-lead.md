# Instagram to lead (2026-10-20)

How an Instagram viewer becomes a lead we can call. Decided 2026-10-20 after the funnel check: in 14 days Instagram gave 0 taps on /go,
0 DMs and 0 WhatsApp chats; only comments came in (8, no phone numbers).

## Why WhatsApp is the way on

- Instagram captions and comments cannot hold a tappable link.
- Our Instagram DMs (and private replies to comments) need Meta's App Review: until then only app admins and testers reach the bot.
- The Instagram profile has no website set, so "link in our bio" led nowhere. /go also showed no reels.
- WhatsApp works for everyone now, and a chat gives us the buyer's number.

So every Instagram post and every buyer comment reply names our WhatsApp number and a word to send. For a listing it is the project's own
word (owner 2026-10-20: "why not LODHA"): `send IVARA to +91 98342 56406` (`app/core/keywords.py`: the distinctive word of the project
name, builder brands and generic words left out; the full name when two live listings share the word). The bot also takes the full name
and a builder name only one live project carries ("LODHA"); a word two projects share gets "which project do you mean". Other posts
(guides, news) keep their interest code. Codes always keep working (old posts, the website's WhatsApp button).

## LIVE (efb90f5d, then this change)

| Piece | What it does | Code |
|---|---|---|
| Caption | Instagram: `💬 Price list and floor plans on WhatsApp: send IVARA to +91 98342 56406.` (the code for a post without a listing) (`Questions? WhatsApp … and send <code>.` on a post without prices). Facebook keeps its tap links. | `calendar/adapters.py` `with_interest`, `whatsapp_lines`, `IG_WA_LINE` |
| Comment reply | Instagram buyer comments: INFO / details / price list / interested get "WhatsApp <number> and send <code>"; answers to questions get the same line under them. MHADA stays silent (quiet topic). | `engage/brain.py` `CTA_ONLY`, `whatsapp_reply`; `engage/service.py` |
| WhatsApp / DM bot | A message that is the project's word or the code (alone, with "interested/info/price list", or the website button's prefilled text) gets the post's price lines, payment plan, possession, MahaRERA, the project page, and "floor plans: our team will send them". The team is told (needs you). A reel's code gets its listing post's full price table (loan / EMI lines are not prices). A guide or news code gets a two-line summary and its page. | `whatsapp/brain.py` `_post_card`, `card_facts`; `whatsapp/adapters.py` `grounding_for`, `listing_posts_groundings` |
| Facts | A post's own asks ("Comment INFO and we will send…", "Swipe", "WhatsApp: …") are not facts: the bot once answered "price list please" with "comment INFO". | `knowledge/grounding.py` `CALL_TO_ACTION` |
| /go (bio page) | Homes only (owner 2026-10-21: news and guides stay on the feed): one card per live listing (its newest post), reels included (their cover), a "See all Pune projects" link under them, Instagram code, Instagram copy wins over Facebook. Recruitment posts get no card. A card goes when its post is no longer published, its news is withdrawn or its listing is no longer live. WhatsApp is the main button. | `calendar/adapters.py` `register_hub`; `interest/store.py` `hub_items`; `frontend/app/go/page.tsx` |
| Agent posts | The library's own agent posts (pillar "agent", e.g. `agent-buyer-summary`) count as recruitment posts, not buyer posts. | `calendar/reach.py` `audience` |

`scripts/rebuild_go_hub.py` rebuilds /go from the last 30 days of posts with this rule.

## Owner steps (Instagram app, cannot be done by API)

1. Edit profile, Website: `https://avasetu.in/go`.
2. Edit profile, Contact options / Action buttons: WhatsApp, +91 98342 56406.
3. Bio for buyers, e.g. `Pune homes: checked MahaRERA facts and prices. WhatsApp a post's code for its price list. Agents: list free.`

## TARGET

- Meta App Review for `instagram_manage_messages` and `pages_messaging`, then `ENGAGE_PRIVATE_REPLY=true`: INFO gets the price list as a DM.
- Floor plans on project pages (the project profile has none for Godrej Ivara), so the bot can link them instead of a person sending them.
