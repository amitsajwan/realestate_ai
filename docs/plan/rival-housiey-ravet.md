# Housiey in Ravet: what it taught us about the system (2026-11-06)

**Owner, 2026-11-06:** "It's not about Ravet, but learnings. First priority remains the same." East Pune stays first. Ravet was
the test: a place we have not worked yet shows what the system does on its own in any area, today's or the next one. The
lessons are in the next section; the Ravet read they come from follows it.

## What the system learns (for every area)

| # | Lesson | Change | State |
|---|---|---|---|
| L1 | The rival above us is not always MagicBricks: in Ravet it was Housiey, and the weekly board never named it. | The scoreboard counts **every site above us** in the searches we already run, overall and per area (`seo/scoreboard.leaders`, `area_leaders`); Rankings shows "Above us most often" with each area's top three; the weekly note names the top three. No new searches, no cost. | BUILT 2026-11-06 |
| L2 | One project spread over several registrations stays several pages when MahaRERA files no promoter, or when the tower label is one `base_name` cannot read ("Wing C1 & C2"). None of the pages carries the name buyers search. | `clusters.split_candidates` lists registrations with the same name before the tower label, in the same pincode, at most one promoter; Rankings shows them ("Possibly one project, on separate pages"), our areas first. Nothing merges by itself: the owner confirms a group (`agentprojects.groups`), as a wrong merge 301s a page away. | BUILT 2026-11-06 |
| L2b | Owner, 2026-11-06: "any good algo that can do it perfect? Take LLM help if required." Confirming groups by hand does not scale to every area. | `areastats/samegroup`: among the split candidates, two registrations are one project when a page Google returned for one's MahaRERA number also prints the other's (a project's or builder's own page lists its phases; a page with more than 8 numbers is a list and proves nothing; MahaRERA's own pages never count), unless both pins are measured and more than 1.5 km apart. Links join into groups, merged at the next cluster pass (`web:` cluster ids, joined with any name cluster they touch; a confirmed group is never changed). The merged page's name is the title head at least two sites print on pages showing a member's number, holding every word the towers share, without the place or a portal's tail ("Sonigara The Unicorn"); else the shared name. Reads the stored searches for the numbers only (no new search, no cost). No model: a merge 301s a page, so it needs a proof a rule can check; a model would add a guess, not a proof. What stays unproved stays on the Rankings list for the owner. Numbers never searched get searched: up to 4 a day in the daily Google round (`websearch.split_checks`, our areas first, most homes first, once in 30 days). | BUILT 2026-11-06 |
| L3 | `base_name` keeps "wing c1 c2" ("The Unicorn Building C Wing C1 & C2" → "the unicorn wing c1 c2"), so even with a promoter such towers never merge. | Read letter+number tower ids ("C1", "T-3") in `text.TOWER_LABEL`. It moves pages: towers with one promoter merge at the next cluster pass and their pages 301 to the primary. Owner, 2026-11-06: "we can start, indexing happens when it happens". | BUILT 2026-11-06 |
| L4 | Buyers search the marketed name with the builder's brand ("Sonigara The Unicorn"); MahaRERA's name lacks it. | `pages.branded_name`: the brand in front of the name ("Godrej Ivara", "Kolte Patil Life Republic") when the record joins a known brand by its promoter (`brands.of`) and the name lacks every word of it. Leads the title, H1, cards and links after a searched name (`search_name`), before the marketed name. A record with no promoter (The Unicorn) still needs `marketed_name_override` or a confirmed group (L2). | BUILT 2026-11-06 |
| L5 | Buyers compare price by flat size; a rival shows one price per size and carpet area on every card, we show "from" or nothing. | Cards on the area lists and the place page's rows show each size's starting price ("2 BHK ₹68 L · 3 BHK ₹95 L", up to 3 sizes) when there are two or more (`seo/facets.size_prices`, `sizePriceLine`); a size list keeps its own size's price. Starting prices only, the ones we already publish; no carpet area on the card. | BUILT 2026-11-06 |
| L6 | A rival's thin area page ranks because its project pages rank. Our area page ranks alone where its project pages are noindex. | Nothing new to build: the order the writer fills pages already follows the owner's areas (`enrich.priority`), and a page enters search by `ready_for_search`. Watch the share of an area's Top-list projects in search when we open a new area. | rule |
| L7 | The rival's project page wins on documents and court cases; it does not show homes booked or how the filed date moved. | Already planned: search-recovery R3 (our history first) and R5 (MahaRERA's documents and litigation). | TARGET (R3, R5) |


The owner said Housiey is always at the top of Google for Ravet. We read their Ravet page
(`housiey.com/in/pune/ravet`), one of their Ravet project pages (`/projects/sonigara-the-unicorn`) and our own pages for the
same projects, on 2026-11-06, as a browser would fetch them. We did not copy their text, prices or pictures and never will
(seo-system.md section 9). This page is about what their pages do, what ours lack, and what we change.

## What Housiey's Ravet page is

| | Housiey `/in/pune/ravet` | Ours `/projects/area/ravet` |
|---|---|---|
| Title | "New Projects in Ravet, Pune with Detailed Pricing, Floor Plans \| Housiey" | "Flats & Residential Projects in Ravet, Pune: all 599 on MahaRERA" |
| H1 | "Top Projects in Ravet" | "Flats and residential projects in Ravet, Pune" |
| Projects in the HTML | 6 cards ("Showing 6 of 70"; the rest load in the browser) | all 599, in 8,754 words |
| Page size | 195 KB | 959 KB |
| Each card | marketed name with the builder ("Sonigara The Unicorn"), builder, carpet range, possession, and a price per flat size and carpet area ("2BHK 716 sqft ₹84.55 Lac", "All inc"), sold-out sizes marked | MahaRERA name, booked homes, filed possession; a starting price on some |
| Dated answer, FAQ | none | "As of 6 Nov 2026, MahaRERA lists 275 housing projects…", FAQPage |
| Structured data | one `Place` | Place, ItemList, FAQPage, BreadcrumbList, WebPage |
| Sub-pages | none (`/in/pune/ravet/2-bhk` is a 404) | new launches, top, 2 BHK, ready to move |

So their area page is thinner than ours. **It does not win on the page.** It wins on what it links to and on the domain.

## What their project page has

`/projects/sonigara-the-unicorn`, 3,244 words, "Last updated: Oct 7, 2026":
- A **price sheet**: every flat by carpet area, all-inclusive price, minimum down payment, sold-out flats listed as sold out.
- Possession two ways ("Target Possession Dec 2029", "RERA Possession"), the MahaRERA number (P52100052724).
- **Litigation**: the court cases against the land, with court, case number and year.
- **Documents**: commencement certificate, legal title report, layout plan.
- Pros and cons, payment plan, maintenance per month, 30-odd FAQ answers, a video ("Reels"), amenities, floor plans.
- `RealEstateListing` with an `AggregateOffer`, the brand as `RealEstateAgent`.
- Sales copy as well ("premium residences", "good investment", "why buy through Housiey").

Their project pages also rank for the area search itself: "Rama Celestial City Phase 2" and "Gawade Geo Aristo" come up for
"new projects in ravet". Every project page ranks the area page up with it.

What they do not have: homes booked, how the filed completion date moved since registration, how many registrations the
project is spread across. That is all on our pages.

## Why we lose in Ravet today

1. **Our Ravet project pages are out of search.** Housiey's six Ravet cards are Sonigara The Unicorn, Yashada Earthsong,
   Jhamtani Ace Of Atmosphere, Shaligram The Mile, Aditya Vivaaz and Nirman Astoria Royals. On 2026-11-06 our page for every one
   of them says `noindex` (`pages.ready_for_search`: no written text or no fact of its own yet). Jhamtani Ace Of Atmosphere is
   not on our Ravet page at all. The area page alone is up against their area page *and* their 70 project pages.
2. **Ravet is not one of our 8 areas.** The page writer and the prices round take Upper Kharadi, Kharadi and Wagholi first, then
   the rest of east Pune, then Baner, Wakad and Hinjawadi; Ravet waits behind all of them (`pricing.ORDER`, `enrich.priority`).
   That follows the owner's call of 2026-10-27 ("for now just concentrate on east Pune").
3. **One project, three pages, none with the name buyers search.** Sonigara The Unicorn is three MahaRERA registrations
   (P52100052724, PR1262022600338, PM1260002601012). MahaRERA gives no promoter on our records, so the cluster rule cannot merge
   them (`clusters.cluster_key`: no promoter, no merge) and the pages are titled "The Unicorn Building C Wing C1 & C2". Nobody
   searches that. Aditya Vivaaz (3 pages) and Celestial City Phase II (2) are the same story.
4. **Few prices.** Buyers search for "price" and "2 BHK"; Housiey shows a price for every flat size. Most Ravet rows on our
   page say "MahaRERA only".
5. **Authority.** Housiey has been around for years and has offices, a YouTube channel and reels. Its links come from all of that.
   We will not out-link them this year (section 1 of seo-system.md: we win the long tail with facts they don't show).
6. Our Ravet page is 959 KB with all 599 projects, including 261 finished ones, for a search ("new projects in Ravet") about
   the 59 new launches. seo-system.md 8 item 8 already counts page weight as a target.

## How we beat them (in order; nothing here copies them)

| Step | What | Who | Holds the rules? |
|---|---|---|---|
| 1 | **Decide whether Ravet is ours.** Add Ravet (and Punawale and Kiwale next to it, the same buyers) after the 8 areas in the page writer's and the prices round's order, or as a 9th area. Until then steps 2 to 4 wait. | owner | east Pune stays first |
| 2 | **Group Housiey's six (and the next 20 Ravet projects buyers name) by hand**: a confirmed group in `agentprojects.groups` for Sonigara The Unicorn's 3 registrations, Aditya Vivaaz's and Celestial City Phase II's; `marketed_name_override` "Sonigara The Unicorn" so the title says what people type. One page per project. | owner in Studio; code only if a group can't be confirmed there | yes: no merge by guess |
| 3 | **Fill those pages** (urgent list in `enrich.priority`): written text, prices from the builder's site or two agreeing sites, the builder's photos. They then go into search by the rule they already follow (`ready_for_search`), not by an exception. | loops | yes |
| 4 | **Lead with what Housiey cannot show** on those pages: homes booked and how fast (`booked_history`), each registration's filed date and how it moved (P52100052724: 31 Dec 2026 at registration, 30 Apr 2028 now; Housiey's card says "Dec 2029"), and the litigation and documents MahaRERA itself lists for the registration (search-recovery R5). | code, R3 and R5 | yes: MahaRERA facts with their date |
| 5 | **A price per flat size on the Ravet cards**, from the prices we read, with the carpet area and its kind of area. Never "all inclusive" unless the source says so. | code (already read; cards show only "from") | yes |
| 6 | **Ravet's place page leads with the new launches**: the dated answer first, then the 59 new launches; the 261 finished projects behind one link (the page stays the owner of "projects in Ravet"). Cuts the page weight too (8, item 8). | code | template change: after the hold, 2026-11-17 |
| 7 | **Measure it**: Ravet's 7 phrasings into the daily Google searches (`websearch.area_queries` runs them for our 8 areas only) and Housiey beside MagicBricks on the scoreboard, so we see when we pass them. Ravet takes its turn inside today's ~25 Serper searches a day, no new spend. | code | yes |

Not doing: copying their price sheet, pros and cons or FAQ wording; "best", "luxury" or "good investment" (banned words); pages
for every Ravet project at once (search-recovery R2: fewer, better pages); buying links.

## What to expect

Housiey's lead in Ravet is their project pages plus years of links. Our pages win where they show what Housiey lacks: the
search "Sonigara The Unicorn possession" (their "Dec 2029" against the register's dated figure), "is <project> delayed",
"<project> homes booked", the 2 BHK and price searches once our cards show prices. Those are the searches we take first, then
the head term once a dozen Ravet project pages are in search and linking up to the place page. A realistic first reading: Ravet's
project pages in search four weeks after step 3, and above Housiey on the per-project searches by the end of January.

## Checked on 2026-11-06

- Housiey area page: 200, canonical to itself, 1 H1, no H2, 12 H3 (6 projects, the rest footer), `Place` JSON-LD only,
  `meta keywords` filled with phrasings ("flats in ravet, property in ravet, luxury apartments in ravet…"), no FAQ, 774 words.
- Housiey project page: 15 H2 sections and the FAQ as H3s, `RealEstateListing` + `AggregateOffer`, "Last updated: Oct 7, 2026".
- Our six matching project pages: all `noindex, follow`; three Unicorn registrations under three titles, no promoter on any.
- A web search for "new projects in ravet pune" (not Google India: the search tool runs from the US) showed NoBroker, Housing,
  Houssed, Square Yards, Ghar.tv and Housiey's area page and two of its project pages; not us. Read it with Serper `gl=in`
  before reading too much into the order.
