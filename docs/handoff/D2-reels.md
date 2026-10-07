# D2 - Reels (short vertical video)

Answer to "no reels, why?": it was on hold. It is built now: reels are made automatically from our own images and text, cost nothing
(no paid service, no stock video, no music) and publish to Instagram Reels and Facebook Page Reels.

## What was built (all under `backend/app/modules/reels/`, nothing existing edited)

| File | Purpose |
|---|---|
| `ffmpeg.py` | ffmpeg from the `imageio-ffmpeg` wheel (static binary). `run()` and `run_with_frames()` with timeout and sanitised errors (no paths, no tokens). `probe()` is an ffprobe substitute (the bundled build has no ffprobe). |
| `compose.py` | `make_reel(scenes, out_path, seconds_per_scene=3.0, music=None, transition="fade"|"slide")`, `Scene`, `TextLine`, `plan()` timing maths, `contact_sheet()`. Frames are drawn with Pillow and piped to ffmpeg. |
| `templates.py` | `tip_reel(lines)`, `listing_tour(photos, facts, sample=)`, `agent_pitch()`; sample texts and sample facts. |
| `publish.py` | `ReelPublisher` (subclass of `social.graph.GraphPublisher`), `publish_reel()` entry point (honours `SOCIAL_DRY_RUN`), `stage()`, `public_url()`. |
| `backend/scripts/reels_admin.py` | `preview --template tip|tour|pitch --out DIR` and `post --file ... --channel instagram|facebook --caption ...`. |
| `backend/tests/modules/reels/` | 32 tests (timing, safe zones, real encode + file checks, Instagram and Facebook flows with `httpx.MockTransport`, dry run, no tokens). No network. |

Imports only `marketing.images` primitives (`STORY`, `load_font`, `brand_background`, `_logo`, `latin`, `GOLD`) and `social.config/graph/publisher`.

### Dependency changes to apply (listed, not wired)
* `backend/requirements.txt`: appended `imageio-ffmpeg==0.6.0` (done). The wheel bundles a static ffmpeg 7.x for Windows, Linux x86_64 and aarch64
  (manylinux wheel verified to contain `ffmpeg-linux-x86_64-v7.0.2`; it is fully static, so **no apt package is needed** on `python:3.11-slim`).
  Image grows by about 80 MB (the binary). I could not run the Linux container here (no Docker on this machine); the Windows binary runs and encodes
  (libx264, aac) here, and the Linux one is the same upstream static build.
* No Dockerfile change. No application wiring. Nothing else.

## Reel spec (verified by `probe()` in tests and on the samples)
H.264 High profile, yuv420p, 1080x1920, 30 fps, AAC-LC 48 kHz stereo audio track (silent unless a music file is given), `+faststart`,
12-17 s (hard cap 29 s), about 2-6 MB (hard cap 20 MB), crf 21 with 8 Mbit/s maxrate. Matches both platforms' requirements
(Facebook: 3-90 s, 9:16, min 540x960, 24-60 fps, H.264 + AAC-LC 48 kHz; Instagram: 9:16, up to 15 min, H.264/AAC).

Design: slow Ken Burns drift on photos (landscape photos pan across), eased fade-and-rise text with staggered lines, cross-fade or slide
transitions, gold `*emphasis*` markup, thin progress bar, brand tag top-left, brand end card (logo, "PUNE Property", "Find. Compare. Decide.",
"Follow for more" button; no phone numbers anywhere: the renderer rejects any 9+ digit number in reel text). Text and chips stay inside the
Instagram safe zone (nothing in the top 10 % or bottom 20 %; enforced by a test over every template scene). Samples are labelled "SAMPLE LISTING" on every scene.
Listing tour shows no price unless `price_text` is passed.

Music: none by default. `make_reel(..., music="path.mp3")` mixes a file you supply (looped, faded in/out, -3 dB). Nothing is downloaded or bundled;
only use audio you hold the rights to.

Render time: about 50-70 s for a 16 s reel on this laptop (pure Python frame drawing), so run it as a background job, not inside a request.

## How to publish
1. Render: `python scripts/reels_admin.py preview --template tip --out out/` (or call `templates.*` + `compose.make_reel` from code).
2. Stage + post: `python scripts/reels_admin.py post --file out/tip.mp4 --channel instagram --caption "..." [--live]`.
   `stage()` copies the file to `<UPLOAD_DIRECTORY>/reels/reel-<id>.mp4`; it must then be reachable at
   `PUBLIC_MEDIA_BASE_URL/uploads/reels/<name>.mp4` (https, public; same mechanism as the image cards).
   Without `--live`, `SOCIAL_DRY_RUN` decides (default: dry run with fake `dryrun_...` ids and no network).
3. Facebook can skip the public URL: `--upload-bytes` sends the file bytes straight to rupload.facebook.com.
4. From code: `await publish.publish_reel("instagram" | "facebook_page", video_url, caption, cfg=..., file_path=...)`.

## API findings (developers.facebook.com, checked 2026-10-01)
**Instagram Reels** (`POST /{ig-id}/media`): `media_type=REELS`, `video_url` (public, fetched by Meta), `caption`, `share_to_feed=true`; poll
`GET /{container}?fields=status_code` (`IN_PROGRESS`, `FINISHED`, `ERROR`, `EXPIRED`, `PUBLISHED`); then `POST /{ig-id}/media_publish`
with `creation_id`. Limit: 100 API-published posts per 24 h per account. Polling default: every 5 s for up to 300 s (configurable, injectable clock).
Also exists: resumable upload to rupload.facebook.com for files not hosted publicly (not implemented; the public URL route is enough for us) and trial reels (`trial_params`).

**Facebook Page Reels** (three phases, all implemented):
1. `POST /{page-id}/video_reels` `upload_phase=start` -> `{video_id, upload_url}`.
2. `POST https://rupload.facebook.com/video-upload/{version}/{video_id}` with header `Authorization: OAuth <page token>` and either
   `file_url: <public https url>` (hosted) or `offset: 0` + `file_size: N` with the binary body. Response `{"success": true}`.
   We only ever send the token to the `rupload.facebook.com` host (an `upload_url` on any other host is ignored).
3. Poll `GET /{video_id}?fields=status` until `video_status` is `upload_complete`/`processing`/`ready` (errors: `upload_failed`, `error`, `expired`),
   then `POST /{page-id}/video_reels` with `video_id`, `upload_phase=finish`, `video_state=PUBLISHED`, `description`. Response `{"success": true}`
   (no post id, so we return the video id and `https://www.facebook.com/reel/<video_id>`).
Needs `pages_show_list`, `pages_read_engagement`, `pages_manage_posts` and a user with CREATE_CONTENT on the Page; limit 30 API reels per Page per 24 h.
Video: 3-90 s, 9:16, >= 540x960.

## Limits and open points
* Not tested against the live APIs (no network in tests, and publishing was out of scope); the request shapes follow the current docs. First live run should be one
  dry-run post, then one real post to each channel, checked by hand. Check that the app's Meta permissions include `pages_manage_posts` and (for IG) `instagram_content_publish`.
* Serving: `/uploads/reels/` must be publicly reachable over https. Instagram rejects URLs that need redirects or auth.
* No scheduler or database wiring: hooking reels into the content calendar is a follow-up (the calendar owner decides cadence; 2-3 reels a week is plenty).
* Text is Latin only (same as image cards; Devanagari needs the pre-rendered route).
* Sample photos (Unsplash, see `docs/brand/photo-credits.md`) are not in the repo; the tour/tip-photo samples were rendered from them. Real listings must use the agent's own photos.
* Instagram may still show a small "suggested" crop in the grid (reels appear in the grid at 3:4); the important text sits in the middle, so it survives.
