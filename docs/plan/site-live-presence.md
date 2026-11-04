# Who is on the site, and a quiet offer of help (plan, 2026-10-26)

Owner asked (2026-10-26): can we see who is on the site right now and what they read, and offer help ("finding the perfect home
for you?") while they browse. Owner's condition: **no visitor is annoyed, or they run away.** Owner handed the calls to us; the
decisions below are taken, not open.

## LIVE today (what we build on)

- Every browser gets an anonymous id (`site_anon_id`, frontend/lib/site/tracking.ts) and the tab keeps its landing page,
  referrer and `src`/utm.
- `TrackingBeacon` sends `page_view` / `listing_view` to `/api/v1/t/event` on every buyer page: the agent pages (SiteShell) and,
  since P1, every page in the Avasetu shell (MarketingShell: home, projects, areas, guides, news, builders, /check). Each view
  carries a `view_id`, and the open page pings `/api/v1/t/ping` with its visible seconds (D1).
- Call / WhatsApp / share taps are events; enquiries carry the same id, so a lead's earlier visits join up (lead origin, 16a7f6f1).
- The website chat (ChatWidget, LLM-led, knows the project page) opens only when the visitor taps it or a page's "Ask" button.
- `seo/aivisits` already names visits sent by ChatGPT, Perplexity and Gemini.

## The rule above all others

The visitor came to read. We never take the page away from them. In practice:

1. **Nothing opens by itself.** No auto-opening chat, no popup, no overlay, no exit-intent box, no sound, no vibration, no
   browser-notification permission prompt. (Mobile overlays also cost Google ranking: the SEO lead matters more than any nudge.)
2. **One hint per visit, at most.** A hint is one short line that appears *inside the page*, next to what they are reading, or
   as a small label beside the existing chat bubble. It never covers content and never moves the layout.
3. **Never in the first 30 seconds or on the first page of a visit.** They must have shown interest first.
4. **Closed once = gone for 7 days** on that browser. Ignored (scrolled past) = not shown again that visit.
5. **Only true lines.** "Price sheet updated on Tuesday" only if it was; never "5 people viewing this", never a countdown.
   (India's 2023 dark-pattern guidelines ban false urgency; it would also break the honest-data brand.)
6. **Fixed copy, not model output.** Hint lines are written by us in strings.ts, one per trigger, in the page's language. The
   model only talks once the visitor taps and the normal chat starts (rule 7: rules first, deterministic).
7. **A switch.** `site_hints` in platform controls turns every hint off at once, with no deploy.
8. **Guarded by a holdout.** 1 in 5 visitors never sees a hint. If hinted visitors read fewer pages or leave sooner than the
   holdout, hints go off and we rethink. This is how we know we are not chasing people away.

## Decisions

### D1. Measure every buyer page first

Without views on guides, news and area pages we would be watching a fraction of the visitors. The beacon sits in both buyer
shells (SiteShell, MarketingShell) and sends one `page_view` per page path, plus a **"still reading" ping every 30 s while the
tab is visible**, once more when the tab is hidden or the page is left, and at most 40 per page. From the pings we get real
reading time, not guesses. Bots (known user agents) are dropped as for every event.

Built differently from the first draft: no separate `presence` collection. A ping updates its own view in `events` (tracking is
still the only writer): `read_s` only goes up, capped at 30 minutes, and `last_seen` moves to now. "Here now" is a view seen in
the last 5 minutes. A ping only reaches a view the same browser recorded in the last 2 hours and never creates one.

### D2. "Live" panel in Studio (owner and agents see their own visitors)

- **Now:** visitors in the last 5 minutes. For each: "Visitor 14 · Ivara price table · 3 pages · from an Instagram reel ·
  4 min". Studio refreshes every 15 s (no websockets).
- **Today:** visitors, pages read, reading time per page, visits that read only one page, the most read pages and the pages
  people most often leave from. Where they came from stays in the "Where they came from" table below it (7 days).
- **Journey:** tap a visitor to see their pages in order, with the time on each. A browser that already belongs to a lead
  shows the lead's name and an "Open lead" link; the lead page already lists their visits.
- Anonymous throughout: no IP, no device model, no city guess shown. Same rule as activity.py ("Visitor N").

### D3. Hints: three triggers to start, in this order

| # | The visitor has... | Hint (where it shows) | Tap does |
|---|---|---|---|
| H1 | stayed on a project's price table 40 s+ | "Want the all-in cost with stamp duty and GST? Ask here" (under the table) | opens chat with that question asked |
| H2 | read 2+ projects in the same area this visit | "Comparing in Kharadi? Tell us your budget, we'll shortlist" (label beside the bubble) | opens chat, area known |
| H3 | come back on a new day to a project they read before | "Welcome back. Ivara's price sheet changed on 21 Oct" (top of that page, only if it changed) | scrolls to the price table |

Not doing: exit-intent boxes, "need help?" on a timer, hints on the home page or on the first page, hints during form typing,
hints on /check (people there are checking a project, not shopping). More triggers only after H1 passes the holdout test.

### D4. Hot-visitor alert to the owner

A visitor who reads 4+ project pages, or 10+ minutes in one visit, and has not chatted, raises one Studio alert ("Someone on their
4th Upper Kharadi page, came from the 85%-booked reel"). The owner can watch the journey. **The owner cannot message an anonymous
visitor**: we have no channel to them, and an unasked message would be exactly the annoyance we are avoiding. If the visitor opens
the chat, the owner can reply from the Inbox as "Avasetu team" (check the web-chat reply path works end to end before promising
this). WhatsApp alerts to the owner wait for the paid alert template (same blocker as lead_waiting).

### D5. Privacy

The privacy page gets one plain paragraph: we count pages read and time spent to improve the site and to answer questions; it is
anonymous until you give us your number. No cookie banner (no third-party trackers, no ads). Pings carry no personal data. If we
ever add a third-party analytics script, this decision is revisited first.

### D6. Who the visitor is, without keeping who they are (2026-10-27)

Owner asked for IP and area after counting 8 visitors when they had used only a laptop and a phone (they were 2 of the 8; 3 came
from ChatGPT). Decided: **the IP address is used at the moment of the visit and dropped**, never stored or shown. It cannot name
a person anyway (Jio/Airtel share one address among thousands of phones and change it often), and keeping it would break the
privacy page's promise. What each event keeps instead:

- **device**: "Android phone · Chrome", "iPhone · Instagram app" (tracking/device.py, from the user agent; the user agent is
  not stored). Headless browsers and speed-test robots are not recorded at all.
- **area** and **network**: "Pune, Maharashtra", "Jio", from DB-IP's free files on our own disk (platform/geoip.py; no address
  is sent anywhere). Shown as "Pune approx.": phones are often routed through Mumbai. Credit "IP Geolocation by DB-IP" sits
  under the list, as the CC BY licence asks. The `geoip` loop refreshes the files monthly (GEOIP_REFRESH, on in production).
- **robot**: a visit from a cloud network (Google, Amazon, Microsoft, Hetzner...) is a robot and left out of the Live panel.
- **robot, on a home network** (2026-11-04): a Linux desktop outside India whose referrer is Google. From 2026-11-02 these were
  72 of 249 visitors (Virginia, Maryland, Turkey; one view, no action, no lead) and the 12 days before had 2, on networks
  `is_data_centre` cannot name. Robots are also left out of the sources table (`origins`) and the weekly report.
  Cloudflare/Akamai/Fastly are not on the list: iCloud Private Relay and WARP carry people through them.
- **staff**: a browser signed in to Studio sends `staff: true`; that visitor is "You" for the whole day, listed last and never
  counted. Older visits from your devices stay counted until they visit again signed in.
- **chat_open**: the chat widget records that a visitor opened the chat (once per page; scores 0), so a story can say so.

Studio > Results gains **Today's visitors**: every visit today, newest first, in India time: who, where from, first page,
device · area · network, pages and reading time, and what they did (opened the chat, tapped WhatsApp/Call, shared, enquired).
Tap one for the pages in order with the time on each.

## Phases (each one is shippable alone)

1. **P1 Measure.** D1 beacon on every buyer page + reading-time pings + bot filter. Done when Studio's existing numbers include
   guide/news/area pages and reading time per page. Watch Core Web Vitals: the beacon must not slow pages (sendBeacon, idle
   callback, no new library).
2. **P2 Live panel.** D2 in Studio. Done when the owner can see right-now visitors and today's sources.
3. **P3 First hint.** H1 only, with the switch and the 1-in-5 holdout. Run 2 weeks or 300 hinted visits, whichever is later.
4. **P4 More hints + alert.** H2, H3, D4, only if P3 passes.

## How we judge it

- **Goal:** chats started and numbers given per 100 visits (today's baseline taken in P1, before any hint).
- **Guardrail (must not get worse vs holdout):** pages per visit, reading time, share of visits that leave after one page.
- **Honesty check:** hint taps per hint shown. Under 2% means the line is noise; rewrite or drop it.
- Expect small numbers: traffic is still low (indexing is the bottleneck, rank-loop baseline 61 impressions). With few visitors
  the live panel is most useful as a way to *watch* real people read; the holdout verdict needs patience, not early calls.

## Progress log

- 2026-10-26: plan written.
- 2026-10-26: P1 + P2 built (work/live-presence). Beacon in MarketingShell; view_id + `/t/ping` (tracking/service.py ping);
  `GET /inbox/live` (tracking/live.py); Studio > Results opens with "Right now" and "Today on the site" (components/app/LiveNow.tsx);
  privacy page names reading time. Reading time starts at zero: views before this deploy have none. Watch after deploy: events
  per day (the weekly report reads the newest 20,000 events, so more page views shorten its window) and Core Web Vitals.
- 2026-10-27: D6 built (work/visitor-story): device, area/network (DB-IP, IP dropped), robots, "You", chat_open, Today's visitors.
