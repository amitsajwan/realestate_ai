# A base for a young site: seen without waiting for Google (2026-11-15, TARGET)

Owner, 2026-11-15, after the second site-wide drop: "for our young website we need a boost, it's like we should come to a base
first", "think of some tricks we can do from here", "plan, and we will implement once it is there". Nothing here is built yet.
Each step is marked code (a session builds it), owner (a login or a decision only the owner has), or both.

Background: [seo-system.md](seo-system.md) section 11 (the drops, 2026-10-27 and 2026-11-11), [search-recovery.md](search-recovery.md)
(fewer, steadier, more our own pages; R4 is the trust-from-outside list this plan carries out).

## Where we stand (read 2026-11-15)

- Search Console: 1,300–2,100 impressions a day until 11 Nov; 76 on 12 Nov, 59 on 13 Nov. By the hour it fell from ~120 to
  near zero between about 12:30 and 21:30 IST on 11 Nov and has stayed at 2–7 an hour. Every page type fell together (projects
  1,620 → 58, builders 267 → 12, area lists 114 → 16). Pages still shown keep their positions: Google shows the site for far
  fewer searches rather than ranking it lower. Same shape as 27 Oct, which came back after two days.
- Nothing of ours is broken: no deploy on 11 Nov, every key page 200 to Googlebot with its own canonical and no noindex, URL
  inspection PASS on home, the Kharadi list and Lodha Camelot (crawled 13–14 Nov), Googlebot visits every day, server up 29 days.
- Not read from here: Manual actions (owner, Search Console → Security & Manual actions). Read this first.
- Likely trigger, not proven: each drop followed a fast rise in pages offered (sitemap ~7,000 before 27 Oct; project pages 343 on
  5 Nov → 737 on 12 Nov from the all-of-Pune read). A filter on young sites that suddenly publish many similar pages fits.

So the base to build is the three things Google uses to trust a new site: real people know the name, trusted sites point to it,
and the site stays steady. None of this needs Google to rank us first.

## Rules

- Nothing that imitates demand or authority: no bought links, click bots or "CTR services", no fake or incentivised reviews, no
  expired domain redirected to us, no second domain with the same pages, no hidden text. Each is a listed spam pattern; a
  manual action would bury everything below.
- Every post, video and answer carries a fact and its source (MahaRERA, the builder's sheet, our dated readings), in our own
  words; nothing a model wrote without a checked fact behind it (seo-system.md section 9).
- Publishing still goes through `social.distribution.send` (idempotency, pause switches, dry run outside production). A new
  channel (YouTube) is a new target there, not a new sender.
- No personal names in anything public; "Avasetu team" (owner, 2026-10-23, 2026-11-06).

## The plan, in order

### 0. Stay steady while Google decides (owner decision, then code)

- ~~Hold the budget lists due 19 Nov~~ BUILT 2026-11-15 (owner: "continue autonomously"): `seo/grow.BUDGET_LISTS_FROM`, the
  weekly round keeps every budget list a candidate (`gate.waits_until`) until 2026-12-01, after the 11-29 judgement. Nothing is lost;
  move the date in code to hold longer.
- Pause new pages from outside our 8 areas for two weeks (`enrich` wider read off), keep east Pune's enrichment and the hot lane
  running. This reverses part of the owner's 2026-11-12 "no cap" call, so it is the owner's to make.
- No mass rewrites or title changes in the same two weeks (the page doctor's hold already runs to 11-17; extend it to 12-01).
- Judge on 2026-11-29: impressions by day in Search Console. A return without our doing anything, as on 29 Oct, tells us the
  filter is about churn, and the pacing rule below becomes permanent.

### 1. Ride platforms Google already trusts

| What | Why it works | Who | Status |
|---|---|---|---|
| **YouTube channel, every reel uploaded** with the project name in the title ("Godrej Ivara Upper Kharadi: price, possession, homes booked, Nov 2026"), the project page link first in the description, chapters where a reel has parts | Google ranks YouTube videos in days where a new site waits months; "<project> review" searches show the video on page one. Views come back as visits (`tracking/origin` already counts `youtube` as a source) | owner creates the channel (text ready in `docs/content/youtube/channel-text.md`) and runs the setup below; code BUILT 2026-11-15: `platform/youtube_upload.py` (resumable upload, OAuth refresh token), `social.distribution.youtube_short` (ledger key `youtube:<reel slug>`, the owner's posting pause, at most `YOUTUBE_UPLOADS_PER_DAY`, default 5, for the 10,000-unit quota), called by the calendar after each reel is out (`calendar/adapters.to_youtube`; title names the project and place, description opens with the page). Off until `YOUTUBE_UPLOAD=on` | code BUILT 2026-11-15, waits for the channel |
| **Google Business Profile** (House Deal's, website avasetu.in) with a weekly post from our data ("5 Kharadi projects moved their possession date this month") and a "Call" button | The local map pack sits above organic results and is not touched by this filter; "property agent kharadi" shows it today | owner: profile and link; code BUILT 2026-11-15: the Monday note's last part is the week's post to paste (`seo/note.business_post`: one area's possession dates moved, areas in turn, the tracker link); the Business Profile API when the profile is verified | post text BUILT 2026-11-15 |
| **Google News / Publisher Center** for `/news` | News and Discover are separate indexes and want exactly what the newsroom writes: dated, sourced, with a large picture | owner: publishercenter.google.com → add avasetu.in/news; code: check `/news` articles carry `NewsArticle` data, a 1200 px picture and `article:published_time` | BUILT 2026-11-15 (96c33190: a 1200x675 card per story, `max-image-preview:large`, `/news-sitemap.xml`; owner submitted the news sitemap 2026-11-15, Publisher Center to confirm). The newsroom had published nothing since 20 Oct, so the news sitemap was empty: filter, editor and check fixed the same day (`news-strategy.md`, "Nothing published for 26 days") |
| **Reddit and Quora answers** with our numbers and the page that holds them, disclosed as Avasetu | Google puts both at the top of "is <project> good" and "<area> vs <area>" questions | owner posts (as today, [project_reddit_posts]); code: a weekly "answers to post" list in Studio → SEO from `search_demand` questions, each with a drafted answer from the page's facts and its link | TARGET |

### 2. Be seen where the filter does not reach

| What | Why | Who | Status |
|---|---|---|---|
| **Bing Webmaster Tools** | Bing is the index behind ChatGPT search, Copilot and DuckDuckGo, and lenient with new sites; AI answers already send visits | owner, 10 minutes: bing.com/webmasters → add avasetu.in → import from Search Console → submit `/sitemap.xml` (seo-system.md section 7 has the steps). Code (section 8a step 4): the Bing API into `search_demand` once the key exists | owner step open since 2026-10-26 |
| **A small Google Ads budget** (about ₹3,000–5,000 a month) on "new projects kharadi / wagholi / upper kharadi", "2 bhk kharadi" and the brand name | Not SEO, but the honest "buy a boost": page one today, real buyers, and real brand searches follow. Ads are not a ranking signal | owner decision and account; code: `utm_source=google&utm_medium=cpc` on the landing links so leads say they came from Ads (origin tracking reads utm already) | owner decision |

### 3. Earn links with tools and data, not asks

| What | Why | Who | Status |
|---|---|---|---|
| **"Checked on MahaRERA" badge** agents and willing builders embed on their sites and bios, linking to the project's page (`/projects/<slug>`) with its last-checked date | Badges are how many sites earned their first links; ours stands on data we hold. Agents on Avasetu have sites and bios already | code BUILT 2026-11-15: `/badge/<regno>.svg` (frontend `app/badge/[file]/route.ts`: the project's name, MahaRERA number and the month we read it; 404 for a number we do not hold), the embed in `shared/site/badge.ts`, and "Badge for your website" with the code and a copy button on a Studio listing's overview when its number is in our register (`studio/components/app/BadgeBox.tsx`); owner asks the first agents | code BUILT 2026-11-15, asking TARGET |
| **One data report a month, pitched to press** ("X East Pune projects moved their possession date in 2026", from `completion_history`; "homes booked in Kharadi, Nov 2026" from the readings), English and Marathi | One link from a news domain (Pune Mirror, HT Pune, Sakal, Lokmat) outweighs hundreds of our own pages; journalists link to whoever has the numbers | code: BUILT 2026-11-15 as a section of `/pune-maharera-tracker` ("Possession dates that moved": per area, being built, moved 3+ months by the builder, usual move, extension only, the biggest moves; `areastats.pages.date_moves`), under the page's existing "Use these figures" citation; owner (House Deal) sends it to two journalists a month. Marathi version and CSV TARGET | page BUILT 2026-11-15, pitching TARGET |
| **`/check` pushed as a free tool** ("paste any MahaRERA number, see its real status") in Pune housing groups, Reddit, WhatsApp | Tools get shared and linked by themselves | owner shares; code: an "Embed this check" snippet and a share card on `/check` | LIVE tool, sharing TARGET |

### 4. Turn our reach into brand searches

| What | Why | Who | Status |
|---|---|---|---|
| **"Search 'Avasetu <area>' on Google"** as the last line of every reel caption, post and voice-over, and in free-form WhatsApp replies (not in approved templates: Meta fixes their words) | Real brand searches are the strongest trust signal a new site can get, and we already have the audience | code: BUILT 2026-11-15, `calendar/footer.brand_search_line` just above the footer of every buyer post and reel caption (en, mr, hi; the brand in Latin letters), never twice; voice-overs and free-form WhatsApp replies still TARGET | caption BUILT 2026-11-15 |
| **Agents' bios link their Avasetu page** | Links and visits from accounts Google already knows | owner asks each agent; code: the link ready to copy on the agent's Studio home | TARGET |
| **QR codes** at House Deal's office and on site-visit sheets, to the project's page | Visits from people on site are the most real traffic there is | code: `/projects/<slug>/qr.png`; owner prints | TARGET |

## What a session builds first (code, about three days)

1. YouTube target in `social.distribution` + upload of each posted reel, title from the project page's search title, description
   with the page link (needs the owner's channel and one OAuth token; dry run until then).
2. The brand-search caption line in `calendar/adapters`, per language, with tests.
3. The possession-move report page under `/news/track/`, from `completion_history`, with the method paragraph and a CSV.
4. Then: the badge SVG and Studio box; the weekly Business Profile post text in the Monday note; the Reddit/Quora answer list.

## YouTube set up (owner, about 30 minutes, once)

1. Create the channel from `docs/content/youtube/channel-text.md`, signed in as the account that will own it.
2. In the Google Cloud project the site already uses (Search Console key): APIs & Services → enable "YouTube Data API v3"; OAuth
   consent screen (External, app name Avasetu, your email); Credentials → Create OAuth client ID → Desktop app. Keep the client
   ID and secret.
3. On this PC: `cd backend && python scripts/youtube_token.py --client-id <id> --client-secret <secret>`; approve in the browser
   with the channel's account. It prints five lines.
4. Add them to `deploy/gcp/.env` on the VM (`keys.ps1` or by hand) and redeploy. Uploads start with the next reel.
5. Google keeps uploads from an unaudited API project private. Leave `YOUTUBE_PRIVACY=private` and send the audit form
   (support.google.com/youtube/contact/yt_api_form: what we upload, our own channel only, about 5 videos a day). When it
   passes, set `YOUTUBE_PRIVACY=public`. Videos uploaded while private can be made public in YouTube Studio in one go.

## What the owner does (about two hours in all)

1. Search Console → Security & Manual actions. Tell the session what it says.
2. Decide step 0 (hold the budget lists, pause the wider read).
3. Create the YouTube channel from `docs/content/youtube/channel-text.md`; give the session access to set up the upload.
4. Bing Webmaster Tools (10 minutes).
5. House Deal's Google Business Profile: website avasetu.in, Call button, first post.
6. Publisher Center: add avasetu.in/news (news sitemap submitted in Search Console 2026-11-15; confirm the publication shows Published).
7. Decide on the Ads budget.
8. Pick two journalists for the first report.

## How we judge it (2026-12-15, four weeks after the first build)

- Search Console: impressions by day back above 1,000; brand queries ("avasetu", "avasetu kharadi") listed with a count.
- Bing Webmaster: pages indexed and impressions reported.
- YouTube: videos published, views, and `youtube` visits in Studio → Leads → origins.
- Links: Search Console → Links shows at least one news domain and the agents' sites.
- Leads: enquiries from Google Ads (utm) and from Business Profile calls, counted beside the organic ones.
- Steadiness: no site-wide drop in the four weeks.

## Not doing

- Fake clicks or any "CTR" service; bought or exchanged links; incentivised reviews; an expired domain redirected to us; a mirror
  domain; hidden text or keyword blocks. Also no mass "Request indexing" (it does not lift a filter) and no page rewrites during
  the hold.
