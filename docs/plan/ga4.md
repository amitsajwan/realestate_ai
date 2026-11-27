# Google Analytics 4 for SEO (phases 1-2 BUILT 2026-11-27, not deployed; phase 3 TARGET)

Proposed and built 2026-11-27. The SEO page ([seo-system.md](seo-system.md)) lists it as 8a step 6. Property "Avasetu", web
stream `https://avasetu.in`, Measurement ID `G-3MYR5F1C05`; Search Console linked (owner, 2026-11-27).

## As built (2026-11-27)

- `frontend/lib/site/ga.ts`: the ID (`DEFAULT_GA_ID`, overridden by `NEXT_PUBLIC_GA_ID`, empty turns it off; only production
  builds send, so dev and jest never count), the gtag queue set up in code before the first event with
  `send_page_view: false`, our event names to GA4's, the page dimensions, the Web Vitals event. No Dockerfile or build-arg
  change: the ID is a public default in code, like the Facebook domain verification in `app/layout.tsx`.
- `components/site/TrackingBeacon.tsx`: loads gtag.js (`next/script`, afterInteractive) and reports Core Web Vitals
  (`useReportWebVitals`). Only public pages render it, so Studio and the old dashboard never load the tag.
- `lib/site/tracking.ts`: `trackEvent` sends each event on to GA4 (page views too, so a 404 is not a view, as before);
  `submitInquiry` sends `generate_lead` with `form: enquiry | callback` on success, which covers the enquiry form, Call me
  back, the floor-plans lock and the home-plan form. A browser signed in to Studio sends nothing (`isStaff`).
- `/privacy`: a "Google Analytics" section; legal pages dated 27 November 2026.
- Tests: `__tests__/site/ga4.test.ts`.
- Owner step this design needs (page views are sent by our code): Admin → Data streams → Avasetu site → Enhanced
  measurement gear → Page views → Show advanced settings → untick "Page changes based on browser history events" → Save.
  Otherwise a page change inside the site may be counted twice.

## Why, and what it is not

GA4 is **not a ranking signal**. Google says it does not use Analytics data to rank pages, so adding the tag will not move a
position. What it adds is measurement we lack or cannot easily prove:

| Question | What we have today | What GA4 adds |
|---|---|---|
| Which pages Google sends people to, and for what searches | Search Console read daily (`areastats/searchconsole.py`), Rankings, page audit | The same Search Console numbers next to what the visitor did afterwards, in one Google report (Search Console link) |
| Do visitors from Google stay, read and enquire | Our own events (`TrackingBeacon`, `trackEvent`, the visit trail, leads by origin) | A second, outside count to check ours against: Google filters known bots, and our logs have been fooled before (fake Googlebots, scripts guessing addresses) |
| How fast pages feel to real phones (Core Web Vitals: LCP, INP, CLS) | Nothing from the field. Lighthouse by hand; CrUX has too little traffic for most of our pages | Each real visit's LCP, INP and CLS by page type and area, so a slow template shows before Search Console's report does |
| Visits from AI answers | `seo/aivisits` + `origin.AI_REFERRERS` | An "AI assistants" channel group in GA4, as a check on ours |
| Numbers outsiders trust | Studio only | Standard GA4 figures for partners, agents and investors (House Deal, the agent network) |
| Ads later | None | GA4 audiences and key events, ready if we ever run Google Ads |

Our own tracking stays the source of truth for leads, the visit trail and the weekly note. GA4 is a second witness, the
field speed numbers, and the Search Console join. Rankings does not move to GA4.

## What we build

### Phase 1: the tag and key events (frontend only)

- **Where**: the public site only (`frontend/`), through the buyer layout, including agents' branded pages (each carries its
  agent as a dimension). Not Studio, not `/join`, `/login`, `/dashboard`, `/properties`, `/data-deletion` (rule 10: Studio
  does not get it through `shared/`).
- **How**: `next/script` with `strategy="afterInteractive"`, gtag.js from `googletagmanager.com`. No Google Tag Manager (a
  second console and more script for nothing we need). Off when `NEXT_PUBLIC_GA_ID` is empty, so dev, tests and preview
  builds send nothing.
- **Setting**: the ID is a public default in code; `NEXT_PUBLIC_GA_ID` at build time overrides it (empty turns GA4 off).
- **Page views**: sent by `TrackingBeacon` through `trackEvent`, one per page path, not on a 404, not for a Studio user;
  GA4's own automatic page views are off (`send_page_view: false` and the history option unticked).
- **Events**: one place, `lib/site/tracking.ts` `trackEvent`, also calls `gtag` (new `lib/site/ga.ts`, which does nothing
  when the tag is off). Names:

  | Our event | GA4 event | Key event |
  |---|---|---|
  | enquiry form sent (`EnquiryForm`) | `generate_lead` (GA4's recommended name) | yes |
  | `whatsapp_click` | `whatsapp_click` | yes |
  | `call_click` | `call_click` | yes |
  | `chat_open` | `chat_open` | no |
  | `share` | `share` (recommended) | no |
  | `satellite_open`, `streetview_open` | same names | no |

- **Dimensions** (event-scoped, registered in GA4 once): `page_type` (project, area list, guide, news, tracker, builder,
  home, other: the same kinds `seo/aivisits.page_kind` uses), `area` (the page's place slug), `agent` (`house` or the agent's
  slug), `in_search` (the page's indexable state as the page itself decides it). Set once per page through `gtag('config')`.
- **No personal data**: no name, phone, email, message text or lead id in any event or URL parameter sent to GA4. Our
  `anon_id` is not sent as a user ID.

### Phase 2: field speed (Core Web Vitals)

A small client component using Next's `useReportWebVitals` sends LCP, INP, CLS, FCP and TTFB to GA4 as events (value,
rating, page_type). A GA4 exploration "Web vitals by page type" shows the 75th percentile per template. Phones on Indian
networks are our buyers, so this is the number that matters for page experience.

### Phase 3 (later, only if phases 1-2 prove useful): read GA4 into the page audit

`seo/ga4.py`, a step in `seo/runner.py`: once a day the GA4 Data API (free) gives each landing page's organic sessions,
engagement rate and key events for 28 days; the page audit (`seo/pageaudit.py`) gains "earning leads" beside clicks. Same
service account as Search Console, added in GA4 as a Viewer. Its own setting `GA4_PROPERTY_ID` in `seo/config.py`, off until
set, and a row on Admin → Health when the read fails. Writes only the seo module's own collection (rule 4).

## What the owner does by hand (once, about 30 minutes)

1. analytics.google.com → create property "Avasetu", time zone India, currency INR; a web data stream for
   `https://avasetu.in` with enhanced measurement on (page changes on history: on; form interactions: off, we send our own).
   Send the Measurement ID (`G-…`) to the team; it is public.
2. Admin → Data collection: **Google signals off**, ads personalisation off. Data retention: 14 months.
3. Admin → Product links → **Search Console links** → `sc-domain:avasetu.in` (the owner is its owner, so this works).
   Then Reports → Library → publish the Search Console collection.
4. Admin → Data filters → internal traffic: the owner's and the team's IPs, so our own checks are not counted.
5. Admin → Key events: mark `generate_lead`, `whatsapp_click`, `call_click` once they first arrive.
6. Admin → Custom definitions: the four dimensions above.
7. Admin → Channel groups: copy the default group and add "AI assistants" above Referral, source matching
   `chatgpt|openai|perplexity|copilot|gemini|claude|you\.com|phind|meta\.ai|grok|deepseek` (the same list as
   `origin.AI_REFERRERS`; change both together).
8. Phase 3 only: Admin → Property access → add the Search Console service account's email as Viewer.

## Privacy

- `/privacy` names Google Analytics, the `_ga` cookies, what is collected (pages, clicks, device, rough location), that no
  contact details go to it, and Google's opt-out add-on. Same commit as the tag.
- India's DPDP Act and its 2025 Rules: most duties take effect about 18 months after the Rules were notified (around mid
  2027). Analytics with no contact details and Google signals off is the low-risk setup; read the Rules again before then
  and decide on a consent notice. We do not target EU visitors, so no Consent Mode banner now.

## Guards

- **Speed**: Lighthouse (mobile) on a project page, an area list and the home page, before and after. If INP or LCP worsens
  by more than 10%, switch to `strategy="lazyOnload"` and accept missing a few very short visits.
- **Crawlers**: the tag changes no HTML a crawler needs; the Monday site audit must stay green.
- **Tests** (jest, `frontend/__tests__/site/`): no script when `NEXT_PUBLIC_GA_ID` is empty; the script on a buyer page when
  set; `trackEvent` maps our names to the GA4 names above and sends no contact fields. `npm run build`.

## How we know it worked (2 weeks after release)

- GA4 organic sessions to project pages within ±25% of our own page views from Google for the same pages and days. A wider
  gap means bots in our numbers or the tag missing on some template: find which.
- The Search Console report in GA4 shows landing pages with engagement.
- Web vitals: a 75th percentile LCP, INP and CLS per page type; any template in "poor" goes on the SEO to-do list.
- Enquiries: GA4 `generate_lead` count close to the leads Studio shows from the public site.

## Cost

₹0. GA4 standard and the Data API are free at our volume.

## Files (when built)

`frontend/lib/site/ga.ts` (new), `frontend/components/site/GoogleAnalytics.tsx` (new), `frontend/components/site/WebVitals.tsx`
(new, phase 2), `frontend/lib/site/tracking.ts`, the buyer layout (`frontend/app/layout.tsx` or `SiteShell.tsx`),
`frontend/components/site/EnquiryForm.tsx`, `frontend/app/privacy/page.tsx`, `frontend/Dockerfile`, the image build args (CI
workflow, `deploy/gcp/deploy.ps1`), `docs/plan/seo-system.md` (8a row, section 2 "Where to look", section 11).
Phase 3: `backend/app/modules/seo/ga4.py`, `seo/config.py`, `seo/runner.py`, `seo/pageaudit.py`, `admin/health.py`.
