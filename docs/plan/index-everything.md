# Index everything, then beat MagicBricks on our searches

> **Current state of all SEO work: [seo-system.md](seo-system.md).** This file is design history; where they differ, seo-system.md is right.

Owner, 2026-10-18: "we want all pages to be indexed", sitemaps by area, fix the 8 error pages, target: beat MagicBricks.
Follows [rank-loop.md](rank-loop.md) (LIVE): the page doctor needs impressions, and pages that are not indexed get none.

## 1. Where we are (measured 2026-10-18)

| | |
|---|---|
| URLs in the sitemap | 8,611 (7,728 `/projects`, 783 `/builders`, 53 posts, 20 localities, rest fixed pages) |
| Inspected by our coverage loop | 976 (200 a day; 1,800 a day from 2026-10-21) |
| Indexed | 301 of 976 (84 of 223 on 2026-10-14) |
| Discovered, not indexed | 470: Google knows the URL and has not spent a crawl on it |
| Unknown to Google | 159 |
| Server error (5xx) | 8, all crawled 2026-10-14 19:51 to 2026-10-15 01:03 UTC |
| Google's last crawl | 2026-10-17 22:25 UTC (crawling continues) |

**The 8 errors are not a page bug.** All 8 return 200 today in under 3 s. `/projects/[slug]` deliberately returns a temporary
error when neither the catalog nor the register API answers (better than a 404, which drops the page). They were hit during
the 14 Oct evening deploys, the same day the catalog list took about 12 s (fixed in ef73267e). The pages:
pandharinath-complex-warje, indeco-atrium-baner, the-lords-part-3-bavdhan, vasundhara-kothrud, prithvi-paradise-nxt-hinjawadi,
godrej-evergreen-square-hinjawadi, ellora-enclave-pimpri, shiv-sonai-residency-rajgurunagar-khed.

**Why most pages wait.** Google decides how much to crawl a site from links pointing to it and from how many of the
pages it has already read were worth indexing. A new domain that lists 8,600 URLs gets crawled a little at a time, and every
thin page it reads lowers the rate. `<priority>` in the sitemap is ignored by Google, so a "priority sitemap" changes nothing.
The real levers are below.

## 2. Goal and how we keep score

"Beat MagicBricks" means: **for the searches our pages target, we rank above magicbricks.com**. MagicBricks wins broad searches
("flats in Pune") on domain strength; we cannot win those this year. We can win the long tail, where we hold facts they don't
show (MahaRERA register, homes booked, possession filed vs promised, tower merge, nearby measured from the pin):

- project name searches: "godrej evergreen square hinjawadi", "<project> possession date", "<project> maharera"
- area lists: "new launch projects in lohegaon", "ready to move flats wagholi"
- builder searches: "<builder> projects pune"
- guides: "mhada pune lottery 2026"

Scoreboard (new, step I6): for each page's target phrase (`seo_target`, LIVE), our position and MagicBricks' position from
the SERP we already fetch (Serper). Weekly numbers on the Insights screen:

| Metric | 2026-10-18 | Target 2026-11-15 | Target 2026-12-31 |
|---|---|---|---|
| Sitemap pages indexed | ~31% of inspected | 50% | 75% |
| Target phrases where we are above MagicBricks | not measured yet | baseline | 2x baseline |
| Project pages on page one (GSC) | 17 (2026-10-14) | 50 | 150 |

## 3. The build

### I1. Sitemap split: one index, sitemaps by area | NEW
`/sitemap.xml` becomes a sitemap index (Next 16 `generateSitemaps`, plus a route that writes the index), listing:
- `core`: home, localities, area list pages (facets), guides, insights, posts, news, agent pages, fixed pages
- `area-<place>` for each of our 8 areas (Kharadi, Wagholi, Viman Nagar, Lohegaon, Keshav Nagar, Hinjawadi, Baner, Wakad):
  every project page and place page in that area
- `pune-<n>`: projects outside the 8 areas, in chunks of 2,000
- `builders`

Why: Search Console then reports submitted vs indexed **per sitemap**, so we see "Kharadi 80% indexed, rest of Pune 12%"
and act on the area that lags. Smaller files are also read faster and fully. IndexNow (LIVE) and the coverage loop (LIVE) read
the index and follow it into the children. Submit each child in Search Console once (owner, 5 minutes).

### I2. No 5xx for Google | NEW, small
- The register API gets a short timeout and one retry in the page loader, so a slow backend gives a slow page, not a 500.
- Deploys: the frontend keeps serving the cached page (ISR) during a backend restart; check the 3,600 s cache really serves
  stale pages instead of erroring (one manual test with the backend stopped).
- The coverage loop already re-inspects; any page still 5xx after a recrawl is listed in the Admin health row (LIVE).
- Owner: in Search Console, "Validate fix" on the Server error group.

### I3. Every page reachable in three clicks | LIVE already (measured 2026-10-18), nothing to build
Checked on the live site: home links the area pages and `/projects`; `/projects` links all 97 place pages; a place page links
every one of its projects (Kharadi: 283 of the 287 in its sitemap, no noindex pages); each project page links 6 projects nearby,
its builder page and its place page. So "discovered, not indexed" (797 of 815 on 2026-10-12 in Search Console) is Google's crawl
budget for a new domain, not missing links. Uncached project pages answer in 0.45 to 0.8 s (0.1 s cached); the Baner place page
is 0.9 MB. The levers left are outside links (I5) and fuller pages (I4).

### I4. Thin pages get one real fact before they are listed | change
Pages already noindex while thin (`indexable`, LIVE). Raise the rate of filling: the page writer (LIVE, every 5 min) works
through register pages in sitemap order area by area, our 8 areas first, so each page Google reads has a summary, the
MahaRERA dates and booking numbers, and nearby places. A page enters the sitemap only when it is indexable (rule kept).

### I5. Outside signals | owner and content, alongside
- Every reel and post caption links to its project or area page (FB/IG links are nofollow, but they bring visits, and visits bring crawls).
- Google Business Profile for Avasetu, linking to the site.
- 10 listings in Pune real-estate directories and builder/agent sites that link back; agents' own sites link to their project pages.
- Search Console "Request indexing", 10 a day: the 8 area pages, the MHADA guide, then the hottest projects.

### I6. MagicBricks scoreboard | LIVE (counting) 2026-10-21, doctor fix TARGET
For each target phrase the seo loop already checks, keep both positions (ours, magicbricks.com, also 99acres and housing.com)
from the Serper result in `seo_serp` {phrase, at, ours, mb, acres99, housing}. The page doctor (LIVE) gets one new fix from its
menu when MagicBricks is above us: compare what their result shows (price, BHK, possession in the title/snippet) and add the fact we hold that they don't.
Insights → Pages shows "above MagicBricks: n of m", weekly.

## 4. Order

1. I2 + owner "Validate fix": LIVE 0b602943 (2026-10-18)
2. I1 sitemap index: LIVE 0b602943, 99 sitemaps, 8,659 pages; owner resubmitted /sitemap.xml
3. I3: already in place (see I3)
4. I4 writer order (next)
5. I6 scoreboard: `seo/scoreboard.py`, weekly, on Insights → Rankings (2026-10-21). Baseline: 261 searches, we show in 45, above MagicBricks in 23. The doctor fix is TARGET (seo-system.md 5.3)
6. I5 runs alongside, every day

## 5. Rules
- No page is dropped to make the numbers look better; all real pages stay listed (owner's call).
- No Google Indexing API: Google allows it only for job postings and livestreams.
- Thin pages stay noindex until they hold a real fact; a noindex page is not listed in the sitemap.
- Never copy MagicBricks text or data; we compare positions and what their snippet shows, nothing more.
