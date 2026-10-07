# R2: Make reel for listings

An agent's Marketing screen can now make a real video reel of his listing (not just the script): his own photos, his listing's facts,
a voiceover in English, Hindi or Marathi, our own music bed, 'Listed by <business> · RERA <no>' at the close and the Avasetu end card.
The owner can do the same for a managed agent (concierge), and post the finished reel as an Instagram / Facebook Reel.

## Backend

- `backend/app/modules/reels/listing_reel.py`: the job queue (`reel_jobs`), the script, the renderer, the worker.
  - Job fields: `_id, listing_id, agent_id, lang, status (queued|rendering|done|failed), video_path, script, audio, note, error,
    sample, created_at, started_at, finished_at, posts`.
  - Script: an LLM (`ai_listing.llm.default_llm`) writes beats from the facts of the listing and its `about` only, and
    `director._valid` checks them: no number that is not in the facts, no phone number, no Devanagari on screen, 3 to 5 beats.
    Two tries, then a rules script built from the same facts (all three languages; tested to pass `_valid`).
  - Render: Hindi/Marathi voice with Hinglish/Roman screen text. Without `GOOGLE_TTS_API_KEY` (or if the voice service fails) the
    reel is made with music only and the job says so in `note` (`audio: "music"`).
  - Sample listings (title starts with "Sample") get the `SAMPLE LISTING` badge on every scene and say so in the closing voice line.
  - Output: `<uploads>/reels/listing-<id>-<lang>-<job8>.mp4`, served at `/uploads/reels/...`.
- `backend/app/modules/reels/router.py` (agent): `POST /listings/{id}/reel {lang, again?}` -> 202 `{job, created}`;
  `GET /listings/{id}/reel` -> `{jobs: {lang: job}}` (the latest per language).
- Concierge (owner only, already mounted at /concierge): `POST|GET /concierge/agents/{a}/listings/{l}/reel` and
  `POST /concierge/agents/{a}/listings/{l}/reel/post {lang, channels}`. Posting needs the recorded consent (409 otherwise) and a finished
  reel, reuses `reels.publish.publish_reel` (SOCIAL_DRY_RUN respected: in test mode nothing is sent), and the caption carries the concierge
  attribution (`Listed by <name> on Avasetu`, plus the interest link on Facebook or 'Link in our bio' on Instagram). Audited as `reel.make` / `reel.post`.
- `reels/compose.py`: one-line change. The phone-number guard no longer treats a MahaRERA number such as `A51800012345` as a phone number
  (a digit run that starts inside a word is skipped). Phone numbers are still refused.

## Limits

- 5 reels per agent per rolling 24 hours (queued, rendering and done count; failed ones do not) -> 429.
- One active job per listing + language: a re-request returns it. A finished reel is returned again unless the listing changed since,
  or `again: true` is sent ('Make it again' / 'Try again').
- Needs at least 2 of the listing's own uploaded photos (`/uploads/images/...`; remote URLs are never fetched) -> 422 'Add at least 2 photos'.
- Live or under-offer listings only (409), like the marketing pack.
- One render at a time per process. A job left in 'rendering' for over 15 minutes (a restart) is marked failed when the worker starts.
- Render time: the local check took about 10 minutes on a loaded Windows laptop (no parallax). On the server expect a few minutes.
  The UI says "about 1 to 2 minutes", so measure it on the VM and change the wording if needed.

## Integrator wiring (not done by this stream)

1. Mount the agent routes in `backend/app/api/v1/router.py`, next to the marketing router:

```python
from app.modules.reels.router import router as listing_reels_router
api_router.include_router(listing_reels_router, prefix="/listings", tags=["listing-reels"])
```

2. Worker: nothing is required. The reel routes start it in that process on first use (`listing_reel.ensure_worker()`, idempotent).
   To start it at boot instead, add this to the lifespan in `backend/app/core/application.py` next to the calendar task:

```python
from app.modules.reels.listing_reel import loop as listing_reel_loop
app.state.listing_reel_task = asyncio.create_task(listing_reel_loop())
```

   and add `"listing_reel_task"` to the shutdown tuple `("engage_task", "newsroom_task", "calendar_task")`.
   With more than one uvicorn worker each process runs its own loop. Claims go through `update_one({_id, status: "queued"})`, so a
   job is not rendered twice, but CPU use doubles.
3. Optional index: `reel_jobs` on `(listing_id, agent_id, lang, created_at)` and `(status, created_at)`.

## Frontend

- `frontend/lib/app/reels.ts`: the client (agent and concierge), the fixture fake (queued -> rendering -> done) and the helpers
  (`reelVideoUrl`, `whatsappReelUrl`).
- `MarketingPackView.tsx`: the Reel card keeps the script and Copy button and adds `ReelMaker` (exported). It has a language picker
  (English, हिंदी, मराठी), 'Make my reel', a progress line that polls every 5 s, and when done a video player, Download (a plain link with
  `download`) and Share on WhatsApp (wa.me with the headline and the video URL). A failed job shows its message and 'Try again'.
- `agents/AgentDetailScreen.tsx`: a 'Make reel' button on live listings opens the same ReelMaker for the owner.
- `agents/PostSheet.tsx`: when a finished reel exists, it adds 'Or post the finished reel as an Instagram and Facebook Reel'. That button is blocked until consent is recorded.

## Tests

- `backend/tests/modules/reels/test_listing_reel.py` (20): job creation, idempotency, the daily limit, the photo, status and owner checks,
  reuse and `again`, the worker with a stubbed renderer, the sample badge, failure messages, stale jobs, the LLM script used only when it passes
  the director rules, the rules script in all three languages, the Listed-by line, the compose RERA fix, `render()` with stubbed
  compose/voice/ffmpeg (voiced, no key, voice failure), the agent routes, and concierge posting (consent, finished reel, attribution, dry run).
- `pytest backend/tests/modules -k "reel or marketing or concierge"`: 252 passed, 2 skipped.
- `frontend/__tests__/app/reel-maker.test.tsx` (7): idle, queued/rendering polling, done with player and links, failed, refused, client
  paths, the fixture fake, and posting from the Post sheet. `npx tsc --noEmit` is clean.
  Note: in a worktree under `.claude/`, jest's default testMatch skips the dot directory. Run it with
  `--testMatch "**/__tests__/app/reel-maker.test.tsx" --testPathIgnorePatterns "frontend.\.next" "frontend.node_modules"`.

## Visual check

`docs/brand/avasetu/listing-reel-check.jpg`: 6 frames of a real Hindi reel for a sample 2 BHK in Kharadi made from 2 showcase photos
(rules script, music only, no parallax). The first render showed ' · ' separators starting wrapped lines. Screen text now uses commas, and
the closing is two lines ('Listed by Rahul Homes' / 'RERA A51800012345').

## Not done / follow-ups

- No voiced render was checked locally (no TTS key on this machine). The voiced path is the director's mix and is covered by a stubbed test.
- The WhatsApp share sends a link to the mp4, not the file. Sending the file itself needs the Web Share API with files, which could be added later.
- A posted reel is not added to the /go hub with a cover image (it is registered with an empty image when Instagram really publishes).
