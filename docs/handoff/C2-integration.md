# C2: one content engine (calendar + creative + showcase + reels)

The calendar now plans, makes and (after the owner approves) publishes everything: designed posts and carousels, labelled sample homes and reels. Nothing publishes before approval.
`creative`, `showcase` and `reels` are untouched and do not import the calendar; `calendar/adapters.py` is the only file that imports them.

## What was built (all under `backend/app/modules/calendar/` unless noted)
| File | Purpose |
|---|---|
| `adapters.py` | `entry_to_brief(entry)` (library entry to creative `Brief`: facts only from the entry's points, body sentences and the claim in its `review` note; myth/truth, poll options, steps and stat cut from the entry's own text; hand-written hooks), `make_pack(entry, channel, llm, recent_layouts)` (Instagram 1080x1350, Facebook 1080x1080), agent-attraction briefs, `showcase_item` / `publish_showcase`, `reel_scenes` / `render_reel` / `publish_reel` |
| `plan.py` | Pure weekly rhythm (below) |
| `builder.py` | Plan -> creative made per item in due order (layout memory per channel) -> rows with status `planned`; `--llm` falls back per item and logs the path (`llm`, `rules`, `rules (llm failed)`, `rules (llm output rejected by guards)`) |
| `preview.py` | One contact sheet per week (every image, slot, layout, hook, path) plus `week-N-captions.txt` |
| `store.py` | Statuses `planned -> approved -> scheduled -> published / failed / skipped`; fields `kind`, `images` (list), `video`, `creative` notes, `week`; `due()` returns only `approved`/`scheduled`; `approve()`, `reels_to_render()` |
| `runner.py` | Approval gate, kinds, carousels, reels, pre-render step (see below) |
| `router.py` | `GET /calendar/upcoming` (now with `kind`, `image_urls`, `video_url`, `caption`, `status`, `week`, whitelisted `creative` notes), `POST /calendar/items/{id}/approve`, `/skip` (all owner-only as before) |
| `backend/scripts/calendar_admin.py` | `plan`, `preview-plan`, `approve`, `skip`, `list`, `status`, `--dry-check`, `preview-offline` (no database; design review) |
| `frontend/app/studio/content/page.tsx`, `components/app/content/ContentCard.tsx`, `lib/app/content.ts`, tab in `AppShell.tsx` | Studio Content screen: cards with scrolling image carousel, caption, channel badge, due time (IST), Approve and Skip |

`schedule.py` is kept (its `slot_times` is reused; its old `build_schedule` and tests remain but the admin no longer uses it). `render.py` (old plain navy cards) is now used only for the pre-rendered Hindi/Marathi cards (Devanagari).

## The weekly plan (default 4 weeks, times 10:00 or 19:00 IST on varied days, at least 12 h apart per channel)
- Instagram, 5 a week: showcase carousel (5 slides), checklist carousel, myth / poll / big number (rotating), agent product card (phone mock), the week's reel.
- Facebook, 5 a week: two educational posts, one showcase card, an agent post and a poll in alternate weeks, the same reel (on another day).
- Reels alternate tip, tour, pitch (tip: text beats over bundled photos from a checklist entry; tour: a sample home's photos and facts, labelled; pitch: product claims only).
- No library slug repeats within 60 days on either channel (existing rows count). Showcase homes rotate Kharadi, Upper Kharadi, Wagholi (Facebook is offset by one area). Agent attraction is about 1 post in 4 (22% incl. pitch reels). Hindi/Marathi agent posts need `--include-local-languages`.
- No layout twice in a row on a channel (creative's anti-repeat, checked by a test over 4 weeks).

## Runner behaviour
- Only `approved` (or legacy `scheduled`) rows that are due. `planned` rows are never touched, also in dry run.
- At most 1 per channel per pass; retry limits (3 attempts, 10 min apart), stale skip (48 h) and `SOCIAL_DRY_RUN` (fake id, no network, no call to the reel/showcase publishers) are unchanged.
- post: Instagram gets all images (carousel via `GraphPublisher`, max 10), Facebook gets the first image. Missing image file = recorded failure. showcase: `showcase.publish.publish_instagram/facebook` (it re-validates the caption). reel: `reels.publish.stage` + `publish_reel` to Instagram Reels / Facebook Page Reels.
- Reels: `prerender_reels` runs as a background task in the loop for approved reel rows due within 2 hours (both channels share one mp4 at `uploads/calendar/reels/<key>.mp4`); if it was missed, the video is rendered at publish time.

## How the owner reviews and approves
```
docker compose exec -T -e PYTHONPATH=. backend python scripts/calendar_admin.py plan --start 2026-10-12 --weeks 4 [--llm]
docker compose exec -T -e PYTHONPATH=. backend python scripts/calendar_admin.py preview-plan --out /tmp/review     # week-N.jpg + week-N-captions.txt
docker compose exec -T -e PYTHONPATH=. backend python scripts/calendar_admin.py approve --week 1                    # or --all, or an id
docker compose exec -T -e PYTHONPATH=. backend python scripts/calendar_admin.py skip <id>
```
Or open Studio, Content tab: read each card, Approve or Skip. Start with `SOCIAL_DRY_RUN=true CALENDAR_ENABLED=true` (rows become `published` with fake ids), then switch the dry run off. `plan` is idempotent (a second run adds nothing). Use a Monday as `--start`; the default is the next Monday.

## Verification
- Backend whole suite: 1235 passed, 2 skipped (calendar module: 123 tests, no network; the build test blocks `socket.connect`). Frontend: `npx tsc --noEmit` clean; jest `__tests__/app` 28 suites, 313 tests passed (10 new in `content.test.tsx`).
- Guards: every one of the 39 entries, on both channels, produces a brief whose deterministic copy passes creative's `problems_in` (no invented number, price, prediction, phone, URL, hype or filler), and every number in a brief occurs in the entry's own text. A stub LLM that invents "7 flats", "40 lakh", a phone number and "guaranteed returns" produces a caption without any of them. The verification notes (`review`) in `library.py` are untouched.
- Real reel renders checked (tip 65 s, tour 84 s, pitch 81 s on this laptop, 1.7 to 5.3 MB). Not tested against the live Meta APIs.
- Samples: `docs/brand/plan-samples/week-1..4.jpg` (+ captions), `reel-tip-frames.jpg`.

## Honest assessment of the 4-week plan
Good: 40 items with real variety (checklist carousels, myth/fact, polls, big number, product cards, labelled sample homes, 3 reels), no layout repeats, all text on the pixels checked by creative's critic, facts only from verified entries, the owner sees everything first.
Weak spots, for the next round:
- Rule-path headlines are plainer than LLM ones; run `plan --llm` and compare. Some hooks are still generic ("Questions to ask your property agent").
- Only 5 bundled stock photos, so photo_led cards and the tip reel reuse the same two dark buildings. Sample homes use illustrative stock (labelled), not Pune photos. Real agent listings will be the real fix.
- "Save this" closing slide of every carousel is the same card; the agent pool has only 8 posts, so agent items would repeat within 60 days after about 8 weeks (the plan then simply skips that slot).
- creative defects seen in review (not mine to edit): photo_led text can be low contrast over busy photos and the gold emphasis word can be hard to read (for example "project's" in week 4); in the quote_tip card the emphasis chip can overlap the next word ("Visit the flat once when it rains", week 4).
- Facebook gets one image for carousels' topics, so its educational cards are single-idea cards (quote_tip / photo_led / stat), not lists.
- Hindi/Marathi: still captions/cards from the library only (opt-in flag, needs a native reader).
- Showcase slide "Why this area" has small text over a blurred photo (showcase module).
