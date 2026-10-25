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

## Newsroom makeover, 2026-10-25 (BUILT, deploys with the commit)

Owner: "news room, news content, news editor: lets get proper newsroom setup, a makeover". What we found: in 25 days the pipeline read
1,478 reports and dropped 1,450; 2 stories were live. Most drops were "no target area" (1,028), yet many were exactly what a tracker
needs: 39 Purandar airport reports, 14 Ring Road, 8 HCMTR, 9 Metro Line 3, 8 Lohegaon hospital, 27 on the October repo rate rise.

Decided and built (N1, most of N2 and N3):

- **Eight trackers** (`backend/app/modules/newsroom/tracker_data/<slug>.json`): Purandar airport, Pune Ring Road, HCMTR, Metro Line 3
  (Hinjawadi to Shivajinagar: Hinjawadi, Wakad, Baner), Lohegaon hospital, water in merged villages (Wagholi), home loan rates (RBI repo),
  ready reckoner and stamp duty. Each file holds the name, stages, the areas it touches, the matching rules, what it means for a buyer and
  the dated status history we wrote from the reports. Metro to Wagholi/Kharadi and Kharadi DP roads are left out: under two reports each.
- **Reports attach by rules, not by a model** (`trackers.attach_new`, every newsroom cycle): every collected headline is matched to the
  trackers' `all`/`any`/`not` patterns, whatever the news filter decided; MahaRERA records never. A dry run over all 1,478 stored headlines
  matched 114, none wrong (the Bengaluru and Delhi "ring road" stories and "Mumbai Metro Line 4" are excluded by `not`).
- **The status line is ours and only the owner changes it** (Studio, Newsroom, **Trackers** tab): the new reports since the last check,
  "Update the status" (stage, sentence, date, sources), "Read them: the status still holds", and "Not about this: hide it" for a wrong
  match. The older lines stay as "How the status changed". No model writes a status: a page must never say "open" because a headline did.
- **Pages:** `/news/track/<slug>` (where it stands, stage bar, what it means, reports newest first with the same story from several
  publishers as one line, status history), `/news` leads with the trackers and keeps "Our full reports" below, area pages show
  "What is changing near <area>" when a tracker names the area (the city-wide rate trackers come along, never alone).
- Mangled text from feeds read as Windows-1252 (the Ring Road headline showed "â‚¹10,502") is put back in `presentation.one_line`.

## Next (TARGET, in order)

- N2b: a model *suggests* a new status line when new reports arrive (shown in the Trackers tab with the headlines it read; the owner
  accepts or edits). Rules first, the copy guards on the suggestion, and no suggestion when the model fails.
- N2c: a status change makes one social post (through `social.distribution.send`, dry run outside production).
- N3b: nearby trackers on project pages by distance from the project pin (needs a checked line or point per tracker; area-based today).
- New trackers when a thing gets two reports in a month (Metro to Wagholi/Kharadi, Kharadi DP roads, PMRDA inner ring road).
- Measure weekly: impressions and clicks on tracker pages, clicks from area pages to trackers, and corrections (target: none).
