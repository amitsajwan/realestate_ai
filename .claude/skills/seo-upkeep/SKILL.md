---
name: seo-upkeep
description: Keep Avasetu's Google and AI-search lead (ChatGPT, Perplexity, Gemini, AI Overviews), check that the SEO loops are alive and the pages fresh, find out why rankings or AI citations dropped, and change SEO code or plans without losing what runs. Use for any SEO, ranking, indexing, sitemap, llms.txt or "AI answers cite us" question or change.
---

# SEO upkeep

`docs/plan/seo-system.md` is the one SEO page: what runs (section 6), what the owner does by hand (section 7, with the weekly
and monthly upkeep table), what is planned (sections 8 and 8a) and the rules (section 9). Read it before anything else. When
it and an older plan in `docs/plan/` disagree, it is right.

Why we rank: each page opens with a short, dated answer from the register, prices and plans, and the loops keep it true.
AI answers cite pages that already rank and hold such an answer. So the work is keeping the loops alive and the facts right.
More pages or more words are not the goal.

## 1. Is it healthy? (read only)

| Check | How | Healthy |
|---|---|---|
| Keys and senders | Studio → Admin → Health | no BAD row for IndexNow or Search Console |
| Loops | `gcloud compute ssh pune-property --zone asia-south1-a --command "sudo docker exec gcp-newsroom-1 python -m app.worker --check --role newsroom"` | `seo` and `project_enrich` fresh, exit 0 |
| Loop log | same ssh, `sudo docker logs --since 24h gcp-newsroom-1 2>&1 \| grep pipeline=seo` | one line per step per round, no repeated errors |
| Numbers | Studio → Newsroom → Insights → Rankings | clicks, page one count and AI search counts not falling week on week |
| Index | Rankings → "Indexed by area" | share rising, our 8 areas first |
| Live pages | GitHub → Actions → "SEO audit (live site)" (Mondays) | green, including the 4 AI fetcher reads |
| Demand | same ssh, `sudo docker exec gcp-backend-1 sh -c "PYTHONPATH=. python scripts/demand_report.py --area kharadi"` | our pages on the searches people make |

Check the container names with `sudo docker ps` if one is not found.

## 2. Rankings or AI citations dropped

Work down this list. Stop at the first thing that explains it.
1. **A loop stopped or a key lapsed** (section 1 above): Search Console key, Serper credits, Gemini budget, IndexNow. Fix the
   key with `deploy/gcp/keys.ps1` (operator guide, section 6). The loops catch up by themselves.
2. **Pages went stale**: open three project pages in Kharadi, Upper Kharadi and Wagholi. If "As of" and "Updated" are weeks old,
   enrichment is being refused. Read `pipeline=enrich` in the log (MahaRERA down, model refusing, builder site changed).
3. **A deploy broke a page for crawlers**: look at the latest audit run and `curl -A "OAI-SearchBot" https://avasetu.in/projects/area/kharadi`
   (it should return 200 with an `<h1>`). Check `robots.ts`, canonical and noindex in the diff since the last good week.
4. **The doctor's fix lost**: Rankings → fixes. A title or description that lost 5+ places is undone automatically; check
   that the undo happened.
5. **A rival moved**: Rankings → MagicBricks scoreboard and "win next". The answer is facts they don't show (homes booked,
   possession filed vs promised), never copying them.
6. **Google or the assistants changed**: if many sites moved at once, wait two weeks before changing pages.

Write what you found and did as a line in `seo-system.md` section 11.

## 3. Changing SEO code or plans

- Update `docs/plan/seo-system.md` **in the same commit**: the row in sections 4–8a that changed, a line in section 11, and the
  "Last updated" line. Add and mark as BUILT, TARGET or DROPPED. Never delete a row to tidy up: history is kept with
  strikethrough (`~~...~~ BUILT <date>`).
- The rules in section 9 are fixed: facts only with their source, no AI-written pages, no thin indexable pages, one fix per
  page per 28 days, no bought links, no copied portal text.
- A new SEO job is a step in `seo/runner.py` (`add-background-loop` for a new loop). It needs its own on/off setting, off
  until its key is set, and a row on Admin → Health when it can fail quietly.
- A paid call (Serper, Gemini grounding, Perplexity) states its calls per day and cost in section 8a. Check the price on the
  provider's own page before switching it on. The build machine cannot open those pages, so search limited to their domains.
- Never throw a reading away. The history (homes booked, filed dates, prices) is what a competitor cannot copy
  (`seo-system.md` section 8b). A new reading is appended, dated, beside the current value; never overwrite it or cut it short.
- AI referrers live in two lists today (`seo/aivisits.REFERRERS` and `tracking/origin.REFERRER_SOURCES`). Change both until
  8a step 3 makes them one.
- Run the backend suite and `lint-imports` (CLAUDE.md). If `frontend/` changed, run jest and `npm run build` too.

## 4. Owner's routine

The weekly and monthly table is in `seo-system.md` section 7, "Weekly and monthly upkeep". When the owner asks "what should
I do this week", read it out from there, together with Rankings → "Ask Google to index".
