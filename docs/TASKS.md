# Task list: presence first, then buyers, then agents

Strategy (Oct 2026): build an audience for Kharadi, Upper Kharadi and Wagholi first, collect buyer requirements, then bring
agents in with buyers in hand. The website is the home of all content and listings; every social post links to a page on it,
and every page links back to the social accounts.

Each task has an ID, what to build, why, and "done when". Work top to bottom inside a phase; phases can overlap.
Owner and dates are filled in by the team.

Legend: **[B]** backend, **[F]** frontend, **[O]** ops / non-code.

---

## Phase 0: Domain and brand (week 1)

### T0.1 Register the domain [O]
- Check and buy `avasetu.in` and `avasetu.com` (both if available), plus the matching Instagram, Facebook and YouTube handles.
- Do a quick trademark search for "Avasetu" in class 36 (real estate) before printing anything.
- **Done when:** domain bought, DNS points at the server, HTTPS works on `https://avasetu.<tld>`.

### T0.2 Decide the brand name used on posts [O, decision]
- Today every post, reel and caption is signed "PUNE Property" / "PUNE Property team".
- Decide: (a) site = Avasetu, social = "Avasetu | Kharadi · Wagholi", or (b) keep "PUNE Property" on social and use Avasetu for the site.
  Recommendation: one name everywhere (a), so a viewer who sees a reel and then the site knows it is the same brand.
- **Done when:** name, handle and one-line promise agreed (example: "New projects, possession dates and area news for
  Kharadi and Wagholi. Facts from MahaRERA, no hype.").

### T0.3 One setting for the site address [B]
- The site URL is hard-coded as `https://34-180-39-243.sslip.io` in:
  `backend/app/modules/newsroom/policy.py`, `marketing/brand_posts.py`, `marketing/text_posts.py`,
  and as a fallback in `showcase/captions.py` and `calendar/library.py`.
- Replace all with `settings.public_site_url` (env `PUBLIC_SITE_URL`). No URL literals left in `app/`.
- **Done when:** `grep -r sslip.io backend/app` returns nothing; changing `PUBLIC_SITE_URL` changes every generated link; tests pass.

### T0.4 Rename the brand in generated content [B, F] (after T0.2)
- Brand constants: `reels/compose.py` (`BRAND`, end card), `marketing/facts.py` (`PUBLIC_NAME`), newsroom `draft.py` (`BRAND`),
  showcase / calendar captions, site header and footer, page titles, OG tags.
- **Done when:** no "PUNE Property" left in generated posts, reels or site pages (unless kept by decision).

---

## Phase 1: Content engine (weeks 1-2)

### T1.1 Newsroom: stop dropping new projects [B]
Diagnosis (see chat, Oct 2026): 10 of 10 newest MahaRERA projects were dropped by the filter.
- MahaRERA gives the taluka ("Haveli"), not the locality. Match by **pincode** too: Kharadi 411014, Wagholi 412207,
  Lohegaon 411047 (confirmed 2026-10-02: Upper Kharadi shares 411014; Kesnand and Bakori share 412207). Also match the project name.
- For the `new_supply` pillar (and MahaRERA items), look for the area in the whole text, not only the title / first sentence.
- Plural bug: `_phrase(p, plural=True)` adds only "s", so "launches" does not match "launch". Accept "es" as well.
- Read more MahaRERA pages per run (the newest 20 across all of Pune district is too few once we filter by pincode).
- Drafts say "listed or updated on MahaRERA", never "newly registered" (the date we have is "Last Modified").
- Files: `newsroom/policy.py`, `newsroom/stages/filter.py`, `newsroom/sources/maharera.py`, `newsroom/stages/draft.py`.
- **Done when:** tests built from `tests/modules/newsroom/fixtures/sources/maharera_pune_last.html` keep the in-area projects
  and drop the rest; "Developer launches project in Pune" with Kharadi in sentence 2 is kept; "launches" counts.
- **Status:** done 2026-10-02 (`tests/modules/newsroom/test_new_projects.py`).

### T1.2 Project register [B]
- New collection `projects`: one document per MahaRERA registration number. Fields: name, reg no, promoter (organisations
  only), locality (from pincode), pincode, first seen, last modified, source URL, linked news items.
- The newsroom writes to it whenever it sees a MahaRERA item; news items that name a registered project or our locality get linked.
- Facts only, every field with source and date. No ratings, no opinions about builders.
- **Done when:** after a newsroom run, `projects` holds every in-area MahaRERA project once, with no duplicates.
- **Status:** done 2026-10-02 (`newsroom/register.py`, `tests/modules/newsroom/test_project_register.py`). As built:
  projects are recorded when MahaRERA is read, before the news filter (so a project last modified months ago still counts);
  news is linked only by registration number or by the full project name in a story about the same area (no fuzzy matches,
  no "every Kharadi story to every Kharadi project"). MahaRERA's search answers "No Records Found" to about a third of
  requests, so empty pages are asked for again (3 tries); a page still lost is picked up by a later run.

### T1.2b Backfill older projects [B, spike]
- The register only sees the newest ~150 Pune district registrations (about 10 days), so the many older projects in Kharadi
  and Wagholi never appear, and the T2.2 area pages would look thin.
- Find out whether the MahaRERA search can filter by pincode or location (`project_location=` exists in the search URL;
  untested), or whether a one-off read of older pages is needed. Be polite: the site throttles bursts.
- **Done when:** we know the method and its cost; then one run fills the register with every in-area project.

### T1.3 Monthly "New on MahaRERA" post [B]
- From the register: "Projects listed or updated on MahaRERA in Kharadi and Wagholi this month" as an Instagram carousel
  plus a Facebook post, linking to the site page from T2.2.
- Goes through the existing review queue (owner approves).
- **Done when:** one click in the newsroom review UI produces the carousel and the post for the last 30 days.
- **Status:** done 2026-10-03 (`newsroom/roundup.py`, `POST /newsroom/maharera-roundup`, button on Studio > Newsroom).
  Titled "Listed or updated on MahaRERA" (never "new": MahaRERA only gives Last Modified). Carousel: cover, up to 7 projects
  (Instagram's 10-image limit), what to check, closing; the post lists every project. Links to `/localities` until T2.2
  adds project pages. A second click while one waits for review returns that one.

### T1.4 Festival and events calendar [B]
- Add dated moments to `calendar/plan.py`: Navratri, Dussehra, Diwali (buying muhurat), Gudi Padwa, Akshaya Tritiya,
  RBI policy dates, monsoon checks, year end.
- **Done when:** the 4-week plan includes the next moments with matching content.

---

## Phase 2: Site is the home, posts link to it (weeks 2-3)

### T2.1 Every post links to a page, every page links back [B, F]
- Facebook posts: direct link with `src=facebook` (exists for listings; extend to newsroom, calendar and showcase posts).
- Instagram: "link in bio" points to a **link page** on our site (`/links`) listing the latest posts' pages (our own
  "link in bio", no third-party tool). Each entry tagged `src=instagram`.
- Site pages show "Follow us" with Instagram, Facebook, YouTube and WhatsApp Channel links.
- **Done when:** every published item has a page URL, and enquiries from it show the right source.

### T2.2 Area and project pages [F, B]
- `/localities/[slug]` (exists): add the area's projects from T1.2, the latest news, and listings.
- New `/projects/[regno]`: MahaRERA facts with source and date, linked news, nearby listings. No opinions.
- SEO: title "New projects in Kharadi, Pune (October 2026)", structured data, sitemap entries.
- **Done when:** each in-area project has a page, and Google can see it (sitemap submitted in Search Console).

### T2.3 Full property listing on the site [F, B]
- A public `/properties` page across **all** agents: filters for locality, BHK, budget, sale or rent, ready or under
  construction; sort by newest. Uses the existing public listing endpoints (add a combined one if needed).
- Every listing page: photos, facts, RERA number, the agent's card, "I'm interested" form (exists), share buttons.
- **Done when:** a buyer can browse every live listing in our three areas from one page.

### T2.4 "Alert me" buyer sign-up [F, B]
- On area, project and property pages: "Alert me about new projects / homes in Kharadi under ₹1 Cr" capturing name,
  WhatsApp number (with consent text), area, budget, BHK, timeline.
- Stored as a buyer requirement (re-use `tracking/requirement.py`), counted per area on an internal dashboard.
- **Done when:** sign-ups are stored and visible per area; consent is recorded.

### T2.5 Buyer guide page [F]
- `/guide`: Kharadi and Wagholi buyer checklist + this month's new projects. This is what "Comment GUIDE" sends people to.
- **Done when:** page live, linked from the bio link page.

---

## Phase 3: First partner agent: import "House Deal" listings (weeks 2-3)

The agent has said we can take listings from his website. We publish them on his agent page, every lead from our site
goes to him.

### T3.0 Get permission in writing [O]
- One written message from the agent (WhatsApp or email is fine): he owns or is authorised to market these listings,
  we may copy the text and photos from his site, show them on our site and social, and leads go to him.
- Collect his MahaRERA **agent** registration number (needed on his listings), and the website URL.
- **Done when:** permission and agent RERA number saved in his profile.

### T3.1 Ask for a feed before scraping [O]
- Ask his web developer for an export: CSV / Excel, a JSON feed, or the site's sitemap. A feed is more reliable than reading
  pages and keeps working when the site design changes. Only build T3.2 if no feed is available.

### T3.2 Website importer (only for sites whose owner agreed) [B]
- New module `backend/app/modules/importer/`:
  1. **Find listing pages:** from the sitemap, or by following the site's listing index pages. Same domain only.
  2. **Read each page:** prefer structured data (JSON-LD `Product`/`Residence`/`Offer`, OpenGraph tags); otherwise the
     page text goes through the existing `ai_listing` extractor (price, BHK, area, locality, RERA, amenities).
  3. **Photos:** download the listing's images into our uploads (with permission) so our pages do not depend on his site.
  4. **Create draft listings** on his account, with `source_url` and `imported_at`. Never publish automatically.
- Be gentle with his site: one request every few seconds, honour `robots.txt`, identify ourselves in the User-Agent,
  cache pages, and stop if the site errors.
- Admin only: an endpoint / button "Import from website" on the agent's profile, taking the site URL; only domains on an
  allow list (agents who gave permission) can be imported.
- **Done when:** importing his site creates draft listings with correct facts and photos; a re-run does not duplicate.

### T3.3 Review and publish [F]
- The agent (or we, on his behalf) reviews each draft in `studio/listings`, fixes anything wrong, confirms it is available,
  and publishes. The existing freshness rules (`listings/freshness.py`) then ask him to re-confirm periodically.
- **Done when:** his listings are live on `/agent/<slug>` and in `/properties`.

### T3.4 Keep in sync [B]
- Daily re-check of `source_url`: if the page is gone or says sold, mark our listing "needs confirmation" (never delete
  silently); new pages on his site become new drafts.
- **Done when:** a listing removed from his site is flagged on ours within a day.

### T3.5 His leads reach him [B, F]
- Enquiries on his listings go to his lead inbox (exists) and a WhatsApp / email notification to him.
- Weekly summary for him: views, enquiries, qualified buyers per listing (exists in `tracking/performance.py`).
- **Done when:** a test enquiry on one of his listings reaches him within a minute, tagged with the source.

---

## Phase 4: Audience growth features (weeks 3-5)

### T4.1 "Comment GUIDE" auto-reply [B]
- When someone comments GUIDE (or a configured keyword) on a post, reply publicly and send the `/guide` link by direct message
  through Instagram's official messaging API (needs the `instagram_manage_messages` permission and app review).
- Extends `engage`; same safety checks as today's comment replies.
- **Done when:** a GUIDE comment gets a DM with the link within a minute; it is counted as a sign-up source.

### T4.2 Follows per post [B, F]
- Pull Instagram insights per post: reach, plays, follows, shares, saves, profile visits. Store with the post's format and hook.
- Internal page: follows per 1,000 views by format, so we post more of what earns follows.
- **Done when:** the page shows the last 30 days by format.

### T4.3 YouTube Shorts cross-posting [B]
- Publish the same reel to YouTube Shorts via the YouTube Data API.
- **Done when:** a reel published from the calendar also appears on YouTube.

---

## Phase 5: Later (after ~100 buyer requirements)

- Agent onboarding with buyers in hand ("we have N buyers for 2BHK in Kharadi under ₹1 Cr").
- WhatsApp Business inbound messages with AI qualification.
- MahaRERA project detail pages (completion date, revisions) for possession tracker and delay facts.
- Click-to-WhatsApp ads, ad attribution, billing.
- Area-vs-area reel template, AI voiceover.

## Not doing
- Fake or purchased followers, follow/unfollow bots, engagement pods.
- Builder ratings or verdicts; price predictions.
- Importing listings from any site whose owner has not agreed in writing, or from property portals.
- Taking a share of brokerage before checking whether we need MahaRERA agent registration ourselves.
