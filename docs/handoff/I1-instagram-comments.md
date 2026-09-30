# I1: Instagram comment assistant

The Facebook comment assistant (`backend/app/modules/engage/`) now also answers comments on the linked Instagram account (@kharadi_prop).
One loop, one service, two channels (`facebook`, `instagram`); same classification, caps, dedupe and owner attribution.

## What changed
- `ig_graph.py` (new): `IgGraph(EngageGraph)`. `GET /{ig_id}?fields=username` (once, cached), `GET /{ig_id}/media?fields=id,caption,timestamp,permalink,comments.limit(50){id,text,username,timestamp,replies{id,username}}`,
  `POST /{comment_id}/replies`. Output is normalised to the Facebook shape; each comment carries `own` (our username) and `replied` (a reply from us exists).
- `brain.py`: `decide(..., channel="facebook", handle="")`. Facebook output is byte-identical. Instagram replies use separate templates ending in "the link in our bio" and never contain a URL
  (drafted answers get "More details: the link in our bio."). A comment that mentions `@<our handle>` or asks "DM me / message me / DM us" is queued for a person with no public reply
  (status `needs_human`, reason "mention or DM request"), unless the rest is plain spam.
- `service.py`: `EngageService(db, graph, llm, cfg, now, ig_graph=None)`; `run_once(only_ids=None)` loops the enabled channels. Hourly cap is shared by both channels; person caps
  key on `ig:<username>`. Stored `_id`: Facebook unchanged (`<id>`), Instagram `instagram:<id>`; rows gain `channel` and `comment_id` (raw id). Older rows without `channel` mean Facebook.
  `only_ids` accepts raw platform ids or stored ids. Own-account and already-replied comments are recorded as `ignored`. A failing channel does not stop the other (`{"error": n}` counted).
  Page-level posts use `ENGAGE_OWNER_AGENT_ID`; Instagram listing posts are matched to `publications` with `channel: "instagram"` (`external_id` = media id).
- `config.py`: `META_IG_BUSINESS_ID` -> `ig_business_id`; `ENGAGE_INSTAGRAM_ENABLED` defaults to true when the id is set, else false (an explicit false turns it off). `ENGAGE_DRY_RUN` covers both channels.
- `runner.py`: builds one cached `IgGraph` when Instagram is enabled.
- `router.py`: `GET /engage/comments` rows have `channel` (default "facebook"). `GET /engage/status` keeps the Facebook fields at top level and adds `instagram: {ok, reconnect, checked_at}` once checked.
  `engage_status` holds one doc per channel (`_id` = `facebook` / `instagram`).
- Frontend: `FacebookInterest.channel?`, `FacebookStatus.instagram?` in `lib/app/types.ts`; `app/studio/interest/page.tsx` shows a small "Instagram" label, "Open on Instagram", and the reconnect banner for either channel.
  Test: `frontend/__tests__/app/interest-instagram.test.tsx`.

## Tests
- Backend: `backend/tests/modules/test_engage_instagram.py` (httpx MockTransport, real `IgGraph`/`EngageGraph`): bio-link reply without URL, own account ignored, already replied ignored, spam ignored,
  question queued, mention/DM queued, dry run, person and hourly caps, Facebook unchanged, id collision across platforms, `only_ids` per channel, disabled channel, per-channel status, config defaults.
- Frontend: `npx tsc --noEmit` clean. In a worktree under `.claude/`, plain `npx jest <file>` finds no tests (path is treated as ignored); run
  `npx jest --testPathIgnorePatterns "<rootDir>/.next/" --testMatch "**/__tests__/app/*.{ts,tsx}"`.

## Live verification (integrator)
Prereqs: Page token with `instagram_manage_comments` (already), `META_IG_BUSINESS_ID` set, at least one live post on @kharadi_prop.
```
docker compose exec -T -e PYTHONPATH=. backend python scripts/verify_engage_live.py --channel instagram
```
It comments on the newest Instagram post through the Graph API, treats our own username as an outsider for the run, runs one real cycle limited to those comment ids
(`only_ids`), checks the replies (contain "link in our bio", no URL or phone number), the spam ignore and the queued question, then deletes every comment, reply and row.
Must end with `ALL PASSED`. Note that the Instagram reply-exists check only verifies the reply can be fetched by id. Without `--channel` the script behaves exactly as before.
To go live: set `ENGAGE_ENABLED=true`, keep `ENGAGE_DRY_RUN=true` for a day and read `/engage/comments` rows with `channel=instagram`, then `ENGAGE_DRY_RUN=false`.
Set `ENGAGE_INSTAGRAM_ENABLED=false` to switch Instagram off while Facebook stays on.

## Known limits
- The bio link must point somewhere useful; the assistant only says "link in our bio".
- Instagram replies to replies: only top-level comments are read in full; nested replies are used only to detect that we already answered.
- Instagram comments from accounts Meta hides have no username: they share the per-post unknown-person cap.
