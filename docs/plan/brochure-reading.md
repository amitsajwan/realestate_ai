# Reading a brochure, once (2026-11-07, PROPOSED)

Owner, 2026-11-07: "we need brochure reading and getting floor plans etc, but a brochure understanding is one time activity."
Nothing here is built. It reuses what exists and changes when and how often the reading happens.

## Where we are (read from code and production, 2026-11-07)

- **Studio stores the PDF and reads nothing.** New listing and the run's file question both post to `/uploads/brochures`, which
  only opens the file and counts its pages. Owner, 2026-10-14: reading PDFs inside a marketing run was slow for little gain.
- **The reader exists and nothing feeds it (BUILT, unused).** `propertyfacts/brochure.py` (`POST /listings/{id}/brochure`) makes
  a kit of facts and images to confirm, and `profile.brochure_pictures` already puts a verified kit's plans on the project page.
  Production has no `brochures` collection: it has never run on a live PDF.
- **It can't read what agents actually bring.** KP Supernova's brochure is 25 pages with no text layer (17 characters in all).
  The rules read text, so they find nothing there; only the vision labelling (`brochure_triage.py`) can name its pages. UBC's is
  one page with 3,218 characters of text.
- **It is tied to one listing.** The same PDF from a second agent would be read again.
- **It reads inside the upload request**, with a 30-second budget, on the VM. Too small a budget for a 25-page picture brochure,
  and the wrong place for the work on an e2-medium.
- **Why this matters for search:** a project page needs written text and a fact of its own (`pages.ready_for_search`). A plan
  from a brochure counts as that fact (`pages.own_facts`, source is neither "web" nor "ai"). KP Supernova has neither today.

## Pilot on Kausar's two PDFs (2026-11-07, done by script, nothing stored)

Model `gemini-3-flash-preview`, temperature 0, `thinkingLevel: low`. Every result below was compared with the page by eye.

| Check | Result |
|---|---|
| KP Supernova, 25 picture pages | all labelled and every useful page read in 60 s, ₹2.63 |
| Page sorting | right: cover, map, master plan, plans, specs, legal; lifestyle pages out, page 24 marked as other projects |
| Room sizes | right on the 2 BHK plan; two reads agreed on every plan page |
| Area table (page 18) | every row right, and sq m × 10.764 matches the sq ft, so code can check it |
| Carpet range (page 16) | right: 2 BHK 800-835, 3 BHK 1,100-1,130 sq ft. The listing's 810 is one of these |
| Location, master plan, specs pages | read, amenities and travel claims listed |
| MahaRERA number, whole page | **wrong**: printed PM1260002501030, read P51260002501030 and P5210002501030 |
| MahaRERA number, cropped at 3000 px | right 3 times of 3 |
| UBC, 1 page with a text layer | number right; 4 s at low thinking |

Default thinking took 74 s a page and ₹12.74 on UBC's one page, with no better reading. Low thinking is the setting. Expect about
₹3-4 for a 25-page brochure, measured on this one PDF only; re-check on the first ten.

Fixes the pilot showed:
1. Gemini wraps JSON in a list. `brochure_triage.clean` dropped all 25 labels and `platform.gemini.read` refused the reply. FIXED.
2. A slow page must count as a failed try, not crash the read (a 120 s timeout killed the first run).
3. Page sorting moves to Gemini (it uses the general vision chain today).
4. The number is read in two steps: find it, then read a 3000 px crop twice; the reads must agree. From a text layer, code reads
   it and no model does. It must be exactly this listing's number or one MahaRERA returns for the project. Otherwise the read
   is held. One wrong character can put another project's plans on a page, so this is never "close enough".
5. Check by number, never by name. UBC's page says "VNT INFRA", the register says UBC.
6. Use the plan as a picture. `plans3d.check` is for 3D drawing and refuses a page holding two plans; a buyer only needs the page.
7. Add an area-table read, and a heading read for each plan's title, carpet area and flat label.
8. A plan with no printed carpet area and a joined label ("4 BHK, F-08+09") is shown only as a picture, and is never added as
   a home type the project sells unless the agent confirms it.
9. Pages with no project content stay out: lifestyle pages (the child and family stock photos) never reach a page or post.
10. Run questions said "The brochure shows 810 sq ft" when nothing had read it. Now "We found". FIXED.

## The rule

**One PDF file is understood once, ever.** The file's sha256 is the key. Whoever uploads it, on whichever listing, the answer is
the stored one and no model is called.

| Event | What happens |
|---|---|
| New file | queued, read once in the background, stored for good |
| Same file again, any agent | stored answer at once, no cost |
| Newer brochure of the same project | it is a new file: read once, and it replaces the older one on the page |
| A read fails | 3 tries at most (a rate limit or empty credit is not a try), then "could not read", and nothing retries by itself |
| We improve the reader | nothing re-reads by itself; a re-read is the owner's decision, by hand |
| Marketing run, chat, page writer | never read the PDF; they use the stored answer (the 2026-10-14 decision stands) |

## How a read works (TARGET)

1. **Upload stays instant.** Both Studio paths save the file and queue it. The agent is never kept waiting.
2. **Runs in the renderer, not on the VM.** A fourth queue in `reels.render_job.drain`, which already starts on demand, reaches
   the uploads and stops when idle.
3. **Page images and text** with pdfium, as today, without the 30-second budget. Limits stay at 40 pages and 30 MB.
4. **Name every page** with Gemini from contact sheets (`brochure_triage`): plans, location, amenities, RERA, or the builder's
   other projects and stock photos, which are left out.
5. **Read only the useful pages**, Gemini only: free vision models made up sizes (2026-11-01). Each page gives BHK, carpet area,
   tower, amenities, location claims, MahaRERA number, possession. Every value is checked against the page; room sizes need
   two reads that agree, as in `plans3d`.
6. **Check the project.** The brochure's number must be one MahaRERA returns, and it must be this listing's project or its
   group's. A mismatch holds the whole read back from the public page and asks the agent.
7. **Store it** in `brochure_reads` (key sha256), owned by propertyfacts, with the reader version, cost and date, beside the
   page images. The listing's kit points to it. A read is never overwritten: the history is kept (seo-system 8b).

## What the result feeds

- **Project page:** floor plans behind the existing form, master plan, location. Goes to the project, so every agent's listing
  of it gains, and it asks for a round at once (`enrich_now`).
- **Search:** with a plan on record the page writer can take the project, and a page with text can go into search by the
  existing rule. No rule changes, no noindex changes, and the search hold still applies.
- **Marketing:** kit images the agent kept, and confirmed facts labelled "as per the builder's brochure".
- **Listing:** a one-screen check for the agent ("We read your brochure"): keep or drop each plan, confirm each fact.
- **MahaRERA always wins.** A brochure saying December 2027 never replaces a filed April 2030. The gap goes to the agent as a
  question, not onto the page.

## Order

1. ~~**Pilot by hand**~~ DONE 2026-11-07 (above). Plans read well, so the build goes on. UBC is offices and shops, so it stays out
   of search whatever the brochure says.
2. **One-time store and queue:** `brochure_reads`, the renderer queue, both upload paths, a failed-read state, tests.
3. **Agent's check screen:** reuse `useBrochure` and the kit UI, and change the Studio text that says brochures are never read.
4. **Project page:** the kit's plans through `profile.brochure_pictures`, then Rankings shows pages that gained a plan.

## Owner's calls

1. **Do verified floor plans show without the agent's tick?** Recommended yes: the page already does this for a verified kit,
   an agent can drop any page, and agents rarely come back to confirm. Facts always need the tick.
2. **Cost limit:** recommended ₹10 a brochure. The pilot's ₹3-4 fits it; a run past it stops and is marked failed. The day's cap
   stays shared with `ENRICH_GEMINI_INR_PER_DAY`, which production sets to ₹5,000 (notes said ₹300): the owner confirms the figure.
   Gemini credit has run out before (402, 2026-10-14 and 2026-11-01).

## Not in this plan

Drawing 3D plans (`plans3d`), asking builders for brochures, reading PDFs from other sites, and reading videos.
