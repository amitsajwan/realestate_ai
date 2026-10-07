# N2a Publishers: handoff

Code: `backend/app/modules/newsroom/sources/publishers.py` (`PUBLISHER_FEEDS`, `PublishersSource`, `is_relevant`, `clean_summary`), registered as `publishers` in `sources/__init__.py`.
Tests: `backend/tests/modules/newsroom/test_sources_publishers.py` (17 tests; whole newsroom suite 158 passing, no network).
Fixtures: `fixtures/sources/publisher_*.xml` are REAL captures (plain HTTP GET, 2026-09-30) of the live feeds, trimmed to the first 4-6 items with `content:encoded` bodies removed. Nothing else was edited.

## Why
Google News gives a headline and a long `news.google.com` redirect. These feeds give the real article URL (correct link preview, short readable link) and, for most, a one-sentence summary the extract stage can quote.

## Feeds that work (verified 2026-09-30, no login, UA `Mozilla/5.0 (compatible; ...)`)
| Display name | URL | Summary | Date |
|---|---|---|---|
| Hindustan Times | `hindustantimes.com/feeds/rss/cities/pune-news/rssfeed.xml` | yes, 1 sentence | RFC 822 |
| Times of India | `timesofindia.indiatimes.com/rssfeeds/-2128821991.cms` (Pune city) | only ~3 of 20 items; else title only | ISO 8601 +05:30 |
| The Indian Express | `indianexpress.com/section/cities/pune/feed/` | none (empty description); 200 items, title + real URL only | RFC 822 |
| Punekar News | `punekarnews.in/feed/` and `.../category/real-estate/feed/` | yes (dateline + opening, ends "... The post X appeared first on ..." which we strip) | RFC 822 |
| PMRDA (official) | `pmrda.gov.in/feed/` | notices and tenders, mostly Marathi/PDF; rarely passes the pre-check | RFC 822 |
| Hindustan Times real estate | `.../feeds/rss/real-estate/rssfeed.xml` | yes | RFC 822 |
| ET Realty | `realty.economictimes.indiatimes.com/rss/recentstories` | yes, 2-3 sentences | RFC 822 |
| The Hindu real estate | `thehindu.com/real-estate/feeder/default.rss` | yes | RFC 822 |
| News18 Pune | `news18.com/commonfeeds/v1/eng/rss/pune.xml` | yes, but it is an all-India mix | RFC 822 |
| News18 real estate | `news18.com/commonfeeds/v1/eng/rss/real-estate.xml` | yes | RFC 822 |

The last five (HT real estate, ET Realty, The Hindu, both News18) are "national": an item must also name Pune or one of our areas/corridors (`NATIONAL_FEEDS`). Yield in a live run: HT Pune 2, TOI 5, IE 10, Punekar real-estate 9, ET Realty 1, News18 Pune 7, News18 real estate 6; the main Punekar feed, PMRDA, HT real estate and The Hindu gave 0 that day (feed fine, nothing relevant).

## Feeds that do not work
- Pune Mirror (`punemirror.com/feed/`, `/rss`, category feeds): HTTP 403. Lokmat (`/rss/pune/`): 403. DNA: 403.
- Pune Pulse: connection refused. Free Press Journal: empty 200. Loksatta: HTML page, no items.
- Indian Express real-estate, Mint real-estate, Sakal, The Hindu Pune city, Maharashtra DGIPR, PMC press page, Pune Metro site (HTML only), Moneycontrol: 404/503/410 or not a feed. FE real estate: 410 Gone.
- ET `wealth/real-estate/rssfeeds/48997002.cms`: valid but empty. Use the `realty.economictimes` feed instead.
- TOI `-2128821153.cms` is Ahmedabad, not Pune (easy to mix up); TOI `1898055.cms` is general business.
- Mint industry/companies feeds work but use `30 Sept` month spellings (unparseable dates) and are not Pune/real-estate; left out. PIB Maharashtra RSS: Hindi titles, no summaries, no dates; left out.
- Maharashtra government / PMC / Pune Metro: no working RSS found. Not covered.

## Pre-check (cheap, before the pipeline)
Kept if title+summary contains a whole-word area or corridor phrase from `policy`, or a real-estate word from `REAL_ESTATE_KEYWORDS` (this module; includes metro, ring road, flyover, airport, RERA, stamp duty, homes, flat, builder ...). National feeds additionally need a Pune term (`policy.PUNE_HINT` plus Hinjewadi, Hadapsar, Baner, Wakad, Shivajinagar). Deliberately loose: the real filter stage still decides. `PublishersSource(prefilter=False)` turns it off. A failing feed is skipped; one bad item never breaks a feed.

## Changes outside the new module (small, needed)
- `sources/rss.py`: `parse_feed` now also reads ISO 8601 in `<pubDate>` (Times of India) and `dc:date`. Before, TOI items got `published_at=None`. Other RSS behavior unchanged.
- `sources/google_news.py`: `RawItem.source` is now the publisher name alone (e.g. `Prop News Time`); `Google News` only when the feed has no `<source>`. `draft.py` prints `item.source` to readers, so "Google News / X" would have leaked. Test and N1a note updated.

## Google News URL resolution: not done
Live Google article ids are now opaque (`CBMi...` wrapping an `AU_yq...` token, verified by base64-decoding today's feed), not the old embedded URL. Resolving needs an extra HTTP call per item to a non-public endpoint that changes; no reliable offline way exists, so URLs are left as-is. Prefer `publishers` for anything that will be posted with a link; keep `google_news` for discovery.

## Recommended default
`NEWSROOM_SOURCES=publishers,google_news,maharera`
Order matters for de-dupe by story: publishers first so their real URLs win over Google's redirect for the same story. (The contract default `google_news,maharera` should become this; `config.py` is not in this stream's paths.) Keep the 3-hour cadence; the publishers source makes 11 GETs per run and Google about 25.

## Notes for the integrator
- Indian Express and most TOI items have no summary, so `text` equals the title; the extract stage has little to quote from them. HT, Punekar, ET Realty, The Hindu and News18 summaries are usable.
- Punekar News items include press-release style posts ("By <name>, Founder & CEO ...") that are promotional; the filter/check stage should treat them with care.
- Feeds can change or block without notice; log when a feed returns 0 items repeatedly.
