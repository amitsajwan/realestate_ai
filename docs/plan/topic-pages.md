# Topic pages

Owner 2026-10-18: the MHADA Marathi reels got most of our views, so the subject gets a page of its own. **Information only**: no
sign-up, no selling ("this is information to public, they will never buy our flats"). Lottery results go on it after the draw.

## LIVE (v1)

- `/guides/<slug>`: one page per topic, in the topic's language (Marathi for MHADA) with the whole page in English folded
  underneath (Google reads both). Status line, key dates (with "not confirmed" tags), sections, results box, FAQ (FAQPage
  data), official links, a scam warning, sources, and the reels we posted about it.
- Content lives in `backend/app/modules/calendar/topics/<slug>.json`, every text as `{"mr": ..., "en": ...}`. A date change is
  one edit there; `checked_on` says when it was last true. `GET /api/v1/public/topics[/{slug}]` (calendar/topics.py).
- A reel is listed on a topic when its calendar row's slug starts with one of the topic's `row_prefixes`, or its guide JSON says
  `"topic": "<slug>"` (copied onto the row's creative).
- Sitemap lists every topic.
- First topic: `mhada-pune-lottery`.
- Second (2026-10-18): `upper-kharadi`, an English area research page for ₹1.5-4 crore buyers: MahaRERA booking table (read
  18 Oct, static in the file), prices with their source, metro status, a checklist. Sections may carry `text` (lead paragraph)
  and `table` ({columns, rows: [{cells, href}], note}); a row's `href` links to our project page. Four English reels
  (`guides/upper-kharadi-*-en.json`, 19/20/22/24 Oct 19:30) use screenshots of the page, every line locked.
- Own screenshot frames: put the picture BELOW y=370 of the 1080x1920 canvas. The renderer draws its progress bar and logo row
  across the top, which looked like a strike-through on a page title.
- Our register has no village field: "Wagholi" on a project page is from the PIN (412207). Say "Wagholi PIN", not "Wagholi village".

## Next (TARGET)

1. **One fact file per topic.** Guide reels take their `reply_facts`/`reply_faq` from the topic file, so the page, the comment
   bot, the DM bot and chat say the same thing. Today each guide JSON still carries its own copy.
2. **Results.** When MHADA publishes the draw: link the official winners and waiting lists in `results.links`, a "how to check
   your result" section, and a results reel. We do not republish winners' names (personal data); we link MHADA's lists.
3. **A watcher** on MHADA's lottery pages for a new notice (extension, draw date, results) that tells the owner and drafts the
   change to the topic file.
4. **Topics from the radar.** When the topic radar picks a subject, its reels carry the topic; a page goes live once the topic
   has 2+ reels or one passes ~2k views, so a flop never becomes a thin page. After the event the page stays (next year's
   lottery uses the same address).
5. Where the reels point: Instagram bio link while a topic is hot, the link in Facebook captions, the DM bot sends it when asked.

Candidate topics: PMAY 2.0, ready reckoner / stamp duty (April), PMC property-tax rebate (May-June), home-loan rate changes,
MHADA boards outside Pune.
