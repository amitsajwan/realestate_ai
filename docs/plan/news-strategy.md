# News strategy

Decided 2026-10-20 (owner: "fix all news, remove what's not required, plan a proper strategy"). Labels: LIVE = running on avasetu.in,
TARGET = decided, not built.

## What we found (2026-10-20)

- 6 stories were live on /news. 4 were one-line summaries of one report (69-80 words): Kharadi DP roads, Nagar Road metro traffic,
  Purandar airport land, HCMTR survey halt.
- The Lohegaon hospital story went out at 02:46 on 20 Oct saying the hospital was "ready to serve residents". A Punekar News report
  of 19 Oct, already collected by us, says the opening is stalled: no inauguration permission since 11 Sept. The research matched
  other reports by headline words, and "Lohgaon hospital ... delays opening" shares one word with "Lohegaon's hospital set to start OPD".
- Search, last 28 days: all /news pages together had about 66 impressions and 2 clicks, out of 7,112 impressions for the site
  (under 1%). A one-day news item does not rank, and nobody searches for it a week later.
- The pipeline read 1,250 reports and kept 6. Since the rebuild on 17 Oct, one story was published.

## The decision

News is not a traffic channel. Its job is to keep what we tell a buyer **true and current** about the things that change a decision
in our areas: roads, metro, hospitals, airport, approvals, rules, loan rates. Search value comes from **durable pages about those
things** (people search "pune ring road status", not "ring road news 7 Oct"), which news keeps up to date.

1. **Trackers (TARGET):** one page per thing that keeps changing (Pune Ring Road east, HCMTR, metro towards Wagholi/Kharadi,
   Lohegaon hospital, Purandar airport, Kharadi DP roads). Each page has the current status in one line, a dated timeline of the
   reports, what it means for the areas and projects near it, and its sources. Lives under /guides (topic pages, docs/plan/topic-pages.md).
2. **A news report updates a tracker (TARGET):** a new report about a tracked thing goes onto that tracker's timeline and, when the
   status changes (approved -> land acquisition -> work started -> open, or delayed), the status line changes. No new page for each report.
3. **Project and area pages show nearby trackers (TARGET):** "Ring Road (east): approved, land acquisition under way, 3.2 km",
   measured from the project pin (docs: project_google_pins), linked to the tracker. This is what helps a buyer, and it links the
   tracker from many pages, which helps it rank.
4. **/news is the dated change log (LIVE, narrowed):** only full reports (2+ sources, or 1 with 5+ facts) about our areas or about
   city-wide rules and rates (RBI repo, stamp duty, MahaRERA rules, property tax). A one-line summary is never published.
5. **Social posts only on a change (TARGET):** a tracker status change or a rule/rate change is one post. Nothing else from the
   newsroom is posted.

Never news: single MahaRERA listings (they go to the project register), crime, weather, restaurants, airport operations,
Pune-wide items that do not touch our areas, general money advice.

## Done 2026-10-20 (LIVE)

- 4 one-line stories withdrawn (their pages now 404 and drop out of Google; each had under 10 impressions).
- Lohegaon hospital story rewritten from all four reports: "Lohegaon's 100-bed hospital is built, but its opening is stuck waiting for
  approval"; the old address redirects. Facebook caption corrected. The Instagram caption cannot be edited through the API: edit it by hand.
- Ring Road story: its Facebook post was on the old Page and no longer loads, so the "Also on Facebook" link is hidden.
- Research: area spellings count as one word (Lohgaon = Lohegaon), and a **later report** that names the same area and shares a subject
  word with the story (hospital, metro, HCMTR) is read with it and comes first (stages/research.py `follow_up`).
- The fact reader and the writer see each report's date; the newest status leads the article and says what changed.
- A later report about a story we already published is written as the update; once it is out, the old story is withdrawn and its address
  redirects to the update (pipeline `update_of`).
- An approved story that waited more than 48 hours for its posting slot is researched again before it goes out.

## Next (TARGET, in order)

- N1: tracker records + pages for the six things above, seeded from the reports we already hold (kept and withdrawn).
- N2: the pipeline attaches each kept report to a tracker (follow_up match, then a model check "same thing? status changed?"); a status
  change updates the page and makes one post.
- N3: nearby trackers on project and area pages, by distance from the project pin.
- Measure weekly: impressions and clicks on tracker pages, clicks from project pages to trackers, and corrections (target: none).
