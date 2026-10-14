# SEO code: review and how we organise it

Reviewed 2026-10-14 over the rank-loop work (R0-R9, docs/plan/rank-loop.md §9, built the same day, not deployed).
Two things here: **what is wrong** (section 1, fix before deploy) and **why it is hard to hold in your head** (2-4, the layout).

**S0 is done (2026-10-14): D1-D7 are fixed in the working tree.** What changed, beyond the lines named in the table:

| | As built |
|---|---|
| D1 | `pages.can_host(d)` is the one test a record must pass to be anybody's primary (a page we serve *and* indexable). `clusters._primary_for` ranks on it, `assign_clusters` leaves a group whose primary cannot host completely alone (no `cluster_id` either, so no towers table and no shared lastmod), `primary_of` re-checks it before following a 301, and the four consumers that asked "is my primary served?" now ask the one question the field answers: `not cluster_primary`. The cluster report prints `→ STAYS ALONE` on such a group, so the pre-deploy read matches what the code will do. |
| D7 | `areastats/text.py` owns the name rules (`ascii_text`, `words`, `promoter_key`, `builder_slug`, `base_name`); `pages.py`, `clusters.py`, `hubs.py`, `sellers.py` all import it, and `pages.py`'s own copies and its `unicodedata` import are gone. |
| D2 D3 D6 | `seo/actions.py` holds the log and the undo rules both steps used to disagree about: `FIELD` (was the doctor's `UNDOABLE`), `numbers` (the doctor's `_numbers` and the target's `_page_numbers`, identical), `gain` (the doctor's, which `report.py` reached into), `log_fix` (was in `targets`), plus `stamp`, `undo` and `blocked`. `undo` restores the value, restarts that field's own hold, opens the page's fix window and keeps the rejected value in `search_name_no` / `seo_description_no`, so neither `targets` nor the doctor can write the same undone value again. The window field is `page_fix_at` / `page_fix` (was `doctor_at` / `doctor_fix`), written by whoever treats the page; `REST_DAYS` moved to `actions`. `measure` skips an action already reverted. Report + RankingsTab show "Last fix". |
| D5 | The Search Console read is the seo loop's first step (`runner.round_once`), not only the enrichment loop's. Its own daily mark means one read whichever loop gets there first. |
| D4 | `pages.view` ships `topic` with each question. Checked the two vocabularies against each other: `questions.TOPICS` (price, oc, possession, rera, booked, builder, size, location) covers every `ownFaq` topic except our own `near`, so a real question now does replace ours on the same topic. |

D8-D10 stay as S3-S4: the `_aware` sweep touches 24 files across modules that have nothing to do with ranking, and the renames are behaviour-neutral. They do not belong in the same unreviewed pile as a deploy.

## 1. Defects

Each one read at the source, not inferred.

| | What happens | Where | Fix |
|---|---|---|---|
| **D1** · bug | A project can vanish from the sitemap. The primary is chosen on "has a served page, then oldest date" with no indexability term; `listing` then drops the cluster members *and* the non-indexable primary. A tower with no completion date, merged under a served-but-unindexable registration, leaves neither page in the sitemap, and its 301 lands on a noindexed page. | `areastats/clusters.py:179-189` (`_primary_for`), `areastats/pages.py:453-461` (`listing`) | Put `indexable` in the primary's sort key, and in `listing` keep a member standalone when its primary is not indexable. |
| **D2** · bug | A title the doctor reverted comes back. Revert restores `search_name` and marks the action, but never touches `search_name_at`; 28 days later the cooldown in `targets` expires and the same phrase is re-applied and re-logged. It oscillates forever, and the doctor's own measurement is what should have stopped it. | `seo/doctor.py:94-100`, `:271-282` (revert), `seo/targets.py:124-128` | On revert set `search_name_at = now` and remember the phrase on the record; `pick`/`readable` in targets skip a phrase already reverted. |
| **D3** · bug | A page the owner reverted by hand still gets measured. `measure` fills `after14`/`after28` from the page's current numbers whatever the state, so a reverted fix is scored as if it were still live and `gain()`/the results table credit the wrong thing. | `seo/doctor.py:78-88` vs `:94` | Skip the fill when `reverted`; keep the reading the page had before the undo. |
| **D4** · bug | R4's "a real question replaces our own question on the same topic" never fires. The API ships only `q`, `a`, `source`, so `topic` is `undefined` on the frontend and the set it builds is `{undefined}`. Both phrasings of the same question ship on the page. | `areastats/pages.py:312`, `frontend/lib/site/register.ts:124-125` | Add `topic` to the tuple in `view`. |
| **D5** · risk | The rank loop can run on no ranking data at all. `searchconsole.refresh` (which fills `search_demand` and every `gsc_*`) sits in the **project_enrich** loop behind `PROJECT_ENRICH_ENABLED`, while `targets`/`doctor`/`gaps` sit in the **seo** loop behind only the keys. With enrichment off, the doctor still treats 15 pages a day against yesterday's numbers and measures against nothing. | `areastats/enrich.py:468`, `seo/runner.py:20-21`, `seo/doctor.py:245` | Either run the GSC read from the seo loop too, or no-op `doctor`/`targets` when the newest `gsc_read_at` is older than 48h. One rule, stated in the runner's docstring. |
| **D6** · mess | "One fix per page per 28 days" is not true. The skip window reads `doctor_at`, which only `doctor` sets; a title change from `targets` logs into the same `seo_actions` log but leaves `doctor_at` alone. Two different fixes then land on one page inside one window and both are scored against whole-page position — which is the number the doctor exists to attribute. | `seo/doctor.py:147-149`, `seo/targets.py:127-128` | One window field for both writers (`page_fix_at`), set by whoever treats the page. |
| **D7** · mess | `promoter_key` and `_ascii` exist twice, on purpose. `clusters.py` re-implements what `pages.py` owns "to avoid a circular import" — the two will drift, and they decide which towers merge. | `clusters.py:57-64` vs `pages.py:27,202` | The name/normalisation code moves out of both into one place (section 3). |
| **D8** · mess | `_aware` (coerce a Mongo value to a datetime) is hand-copied in **24 files**, seven of them in the two SEO modules. | `grep -rln "def _aware" app` | One `app/platform/time.py`. |
| **D9** · dead | `report.week_lines` has no caller (the weekly e-mail was dropped, plan §9 R9). `KEEP_UPPER` is unreachable: `GENERIC` deletes "rera"/"bhk" from the phrase first. `parse_sitemap` is written twice with different return types. | `seo/report.py:100-111`, `seo/targets.py:41-45,50`, `seo/audit.py:176` vs `seo/indexnow.py:60` | Delete `week_lines` or wire the digest; fold the `GENERIC` overlap; one sitemap parser. |
| **D10** · naming | The step names no longer say the job: `doctor` reads + diagnoses + treats + measures + reverts; `coverage` is URL indexability inspection; `gaps` (seo) collides with `knowledge/gaps` (the answer loop). Three words describe page visibility — `seo_index`, `gsc_coverage`, `gaps` — and the thresholds disagree: `targets.MIN_IMPRESSIONS=5` vs `searchconsole.NEAR_MIN_IMPRESSIONS=20`. | `seo/*.py`, `areastats/searchconsole.py:36` | Section 3's vocabulary, and one config. |

Untested and worth knowing before deploy (no new tests written, per your rule): every backend step of R1-R4, R6-R9 — no test imports `targets`, `doctor`, `questions`, `gaps`, `report`, `hubs`; and no frontend test covers a member slug's 301, `/builders/<slug>`, or `RankingsTab`. D1-D3 are exactly the paths with no test.

## 2. Why it scattered

- **Two modules, one job, split by history.** `areastats` (16 files, 3,400 lines) holds the MahaRERA register, the page, *and* the GSC client; `seo` (10 files, 1,250 lines) holds everything that decides what to do with a page. The split is not a layer boundary, it is where the files happened to land.
- **The GSC client is on one side of the line and all its readers on the other.** `areastats/searchconsole.py` owns the API; `seo/coverage.py:17`, `targets.py:21`, `gaps.py:17`, `doctor.py:27`, `report.py:18`, `runner.py:9` all import across for it.
- **Three files decide what a page should say.** `areastats/pages.py` renders it, `areastats/enrich.py` writes its text, `seo/doctor.py` picks and applies a fix — with the doctor calling back into enrich (`doctor.py:14,27`) to do the writing.
- **One document, eleven writers.** The `projects` record is written by refresh, pages, clusters, enrich, hot, searchconsole, websearch, watch, targets and doctor. `set_project` is field-atomic (`newsroom/store.py:175-177`) so nothing loses a write, but nothing says who owns which field either — which is how D2 and D6 happened.
- **Backwards reads.** `areastats/websearch.py:46` reads the doctor's `seo_actions` log; `areastats/hubs.py:5,58` reads `seo_link_slot_until`; `pages.py:309-314` serves `seo_faq`. The data flows seo→areastats→seo with no rule about it.
- **Two lazy imports guarding a cycle.** `clusters.py:182` imports `pages.in_register` at call time, `pages.py:78` imports `clusters.assign_clusters` at call time, both with comments. The pair is one module wearing two files.
- **No rule covered either module.** `.importlinter:34-46` lists every domain and its allowed direction; `areastats` and `seo` are absent from it. Nothing could have stopped any of the above.

## 3. The layout

Three layers, dependencies in one direction only, each answering one question:

```
app/modules/areastats/   what exists      MahaRERA register, area stats, the searches people run
   refresh · discover · watch · service · hot · demand · sellers · webfacts · websearch(fetch)
app/modules/pages/       what we publish  the page record: slug, cluster, view, listing, sitemap entry, hubs
   record · clusters · hubs · questions          (from areastats: pages.py, clusters.py, hubs.py)
app/modules/seo/         how we rank      read the numbers, pick a fix, apply it, measure, show it
   gsc · coverage · targets · doctor · gaps · report · indexnow · runner · config
```

- `seo` may import `pages` and `areastats`; `pages` may import `areastats`; `areastats` imports neither. The three backwards reads above become forwards: the target check asks `seo`, the hub link slot is a `pages` field the doctor writes.
- **One GSC client** (`seo/gsc.py`, from `areastats/searchconsole.py`). Anyone else reads the stored `search_demand` / `gsc_*` fields, never the API.
- **One owner per field**, written down, and it stops the D2/D6 class of bug for good:

| Field | Owner |
|---|---|
| `page_slug` `cluster_id` `cluster_primary` `cluster_skip` | `pages/clusters` |
| `seo_target` `search_name` `search_name_at` | `seo/targets` |
| `seo_faq` | `pages/questions` |
| `seo_description` `seo_link_slot_until` `page_fix_at` | `seo/doctor` |
| `gsc_*` `search_demand` | `seo/gsc` |
| `hot_score` `active` | `areastats/hot` |

- **`pages` fixes D7 and the cycle**: the name normalisation (`promoter_key`, `ascii`, tower-label stripping) is one file both clusters and hubs call.
- **`seo/config.py`** holds every threshold with its reason (the two conflicting impression floors get reconciled once, in the open).
- Vocabulary in one place: *rank* (a position for a search), *indexed* (Google has the page), *gap* (a search with no page of ours in the top 20), *fix* (one change to one page, measured).

## 4. Stages

| Stage | Work | Done when |
|---|---|---|
| **S0** | D1-D6, only in the working tree. Small, local edits: two sort keys, two revert lines, one tuple entry, one gate, one shared window field. | The four bugs stop being possible; nothing else changes; commit the rank-loop work. |
| **S1** | Deploy and check production (rank-loop plan §9). | Cluster report read, no member 301s wrongly, `cluster_skip` set where it must be; baseline copied into plan §5. |
| **S2** | Cut `pages` out of `areastats`. Pure move + imports, no line of behaviour. | `lint-imports` green with the new contract; `pytest tests/ -q` no worse than today; site renders the same pages. |
| **S3** | Shared helpers: `app/platform/time.py` for `_aware` (24 sites), one sitemap parser, `seo/gsc.py` as the only GSC client, `seo/config.py`. | `grep -rln "def _aware" app` returns 1. |
| **S4** | Names for the job (`doctor` → read/choose/apply/measure, `coverage` → `indexed`), rename `gaps` where it collides, one action vocabulary in `seo_actions`, delete D9's dead code. | A reader of `seo/runner.py`'s docstring knows what runs and in what order without opening a file. |
| **S5** | Lock it in: `areastats > pages > seo` as an import-linter contract with a baseline, plus the field-ownership table in docs/ARCHITECTURE.md. | CI fails a new backwards import. |

S2-S4 are the reorganisation; they change no behaviour, and each is one reviewable commit. S0 must come before the deploy: D1 is the one that can take a live page away, and D2/D3 quietly poison the numbers the whole point loop learns from.
