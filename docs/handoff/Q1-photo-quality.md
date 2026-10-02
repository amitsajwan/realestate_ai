# Q1 handoff: photo quality and visual review

Rebased onto `c094ca8`. The rebase applied without conflicts.

## What it does

- `backend/app/modules/photoquality/`
  - `analysis.py`: `analyze(img)` returns `{score 0-100, issues, tips, metrics}`. Issues: `dark`, `bright`, `blurry`, `small`, `tilted`, `noisy`, `mostly_sky_or_floor`. It uses OpenCV and numpy only and measures a 640 px copy, which takes about 0.1 s.
  - `enhance.py`: `enhance(img)` changes only tone and geometry:
    - a capped grey-world white balance that keeps warm lamplight
    - exposure gamma, applied only when the photo is too dark or too bright
    - CLAHE on luminance, blended at 55%
    - straightening for tilts of 0.7 to 4 degrees, cropped so no blank corners show
    - a thresholded unsharp mask
    - a fast denoise (bilateral filter plus chroma blur), applied only when the photo is grainy

    It never adds, removes or alters objects, sky or views, and it does not boost saturation. A full photo takes about 0.2 to 0.4 s on an idle CPU. `smart_crop(img, aspect)` keeps the window with the most detail.
  - `store.py`: `process_file(path)` keeps the original file. It writes `<name>-enh.jpg` beside it and caches the result in a `<name>.quality.json` sidecar, so it is idempotent. `use_enhanced` is true when the score improves by at least 5. `display_url()` and `public_media()` choose which copy to show.
  - `vision_review.py`: `review(paths, context)` returns `{score, verdict good|fix|redo, notes, source ai|rules, ai_available, model}`. It caches results per file hash, context and model, in memory and under `<UPLOAD_DIRECTORY>/quality_reviews/`. When no model answers, it falls back to rules (photo analysis plus the creative critic) and adds the note "AI review unavailable". Failed AI calls are not cached.
  - `targets.py`: works out which images and text to review for a calendar item, a news item or a listing's marketing cards. It also provides `warm()`, a fire-and-forget pre-review that runs only when an AI provider is configured.
  - `router.py`: `POST /review {kind: calendar|news|listing, id, refresh?}`.
  - `contact_sheet.py`: a dev tool that builds the before/after sheet.
- Hooks into existing code (small):
  - `api/v1/endpoints/uploads.py`: the upload response now includes `quality`, `enhanced_url` (absolute) and `use_enhanced`. It is best effort, with an 8 s cap, and `PHOTO_QUALITY=off` disables it.
  - `listings/schemas.py`: `Media` gains the optional fields `quality`, `enhanced_url` and `use_enhanced`. `enhanced_url` must be one of our own `/uploads/images/*-enh.jpg` files. `PublicListing.media` returns only the chosen URL.
  - `marketing/images.py`: `first_photo_url` uses the chosen copy.
  - `marketing/service.py` and `newsroom/adapters.card_stage`: call `warm()` after cards render.
  - `creative/pipeline.py`: `make(..., reviewer="default")` attaches `report["vision"]`. When the AI review (not the rules) says `redo`, the pack is regenerated once with the review notes as feedback. The redo must pass every critic guard and is kept only if its review score is not lower.
- Frontend:
  - `lib/app/quality.ts`: badges, an in-browser check that uses the same thresholds, the review client and fixtures.
  - `components/app/quality/*`: `QualityBadge`, `QualityTip`, `EnhanceToggle` (before/after peek), `ListingPhotos` and `ReviewChip`.
  - Wired into:
    - the photo step (`PhotoPicker`)
    - the listing detail photos (Use enhanced, saved through PATCH media)
    - the brand logo and banner pickers. The logo is judged only on size and blur; the banner also gets the enhanced toggle.
    - review chips next to Approve in Studio Content, the Newsroom queue and the concierge Post to Avasetu sheet. The chips never block approval and are hidden if the review fails.

## Integrator wiring (required)

The quality router is **not mounted yet**. Without it, the chips stay hidden: a 404 counts as a failed review. Add this to `backend/app/api/v1/router.py`:

```python
from app.modules.photoquality.router import router as quality_router
api_router.include_router(quality_router, prefix="/quality", tags=["quality"])
```

Nothing else needs mounting. The upload hook, schemas, marketing, newsroom and pipeline changes are already in place.

## Environment

The Groq vision model needs **no new key**. It uses `AI_LLM_API_KEY` or `GROQ_API_KEY`, the same keys as the text LLM, which are read through `ai_listing.llm.groq_api_key()`.

| Variable | Default | Purpose |
|---|---|---|
| `AI_VISION_MODEL` | `qwen/qwen3.8-27b` | Groq vision model. A comma-separated list is tried in order. |
| `AI_VISION_API_KEY` | (falls back to `AI_LLM_API_KEY` / `GROQ_API_KEY`) | Only needed if vision should use a different key. |
| `AI_VISION_BASE_URL` | `AI_LLM_BASE_URL`, then `https://api.groq.com/openai/v1` | Endpoint for the vision model. |
| `AI_VISION_FALLBACK_MODEL` | unset (no fallback) | For example, an OpenRouter `:free` vision model. |
| `AI_VISION_FALLBACK_API_KEY` / `AI_VISION_FALLBACK_BASE_URL` | `AI_LLM_FALLBACK_API_KEY` / `AI_LLM_FALLBACK_BASE_URL` | Key and endpoint for the fallback model. |
| `AI_VISION_REVIEW` | `on` | `off` turns off AI review everywhere (rules only) and turns off the pipeline hook. |
| `PHOTO_QUALITY` | `on` | `off` skips analysis and enhancement on upload. |
| `QUALITY_CACHE_DIR` | `<UPLOAD_DIRECTORY>/quality_reviews` | Where review results are cached. |
| `UPLOAD_DIRECTORY` | `uploads` | Existing setting, used to locate card files. |

**Vision model:** `qwen/qwen3.8-27b`. I checked console.groq.com/docs/vision and the deprecations page in October 2026. It is Groq's only documented vision model: `qwen/qwen3.6-27b` was deprecated on 2026-09-14 and Llama 4 Scout on 2026-07-17.

Limits:
- At most 3 images per request; we send up to 3.
- Each image costs about 2,048 input tokens.
- The request limit is 20 MB; we send 1024 px JPEGs.
- Free-tier daily caps apply. When the cap is reached, the review falls back to the rule score.

The model may wrap its answer in `<think>` tags; the parser strips them. The prompt asks only about legibility, cut-off text, crop, clutter, a professional look and whether the text matches the image, and it forbids inventing facts.

## Dependencies

None new. `opencv-python-headless` and `numpy` were already in `backend/requirements`. The frontend needs nothing new.

## Tests

- **Backend:** `backend/tests/modules/photoquality/`, 37 tests with no network. A fake vision client and an `httpx.MockTransport` stand in for the model. They cover:
  - analysis of good, dark, blurry, tilted (with sign), small, grainy and mostly-floor photos
  - enhance: fixes the measured issue; a structure similarity above 0.9 shows the content is unchanged; no extra saturation; tilt fixed with a correct crop
  - smart crop
  - store: original untouched, idempotent, media choice, schema validation
  - vision review: fallbacks, cache, provider chain, request shape
  - the pipeline redo-once, including that a worse redo is not kept
  - API scoping: the listing agent or the concierge owner; calendar and news are owner-only; anyone else gets 404 or 403
- **Frontend:** `__tests__/app/photo-quality.test.tsx` (13 tests). Related suites also pass: brand-editor, content, newsroom, concierge, marketing and components (293 tests in total). `npx tsc --noEmit` is clean.
- **Running Jest in a worktree:** the repo's `testMatch` globs do not match under `.claude/worktrees`, a dot directory. Use a config that swaps `testMatch` for a `testRegex`. In the main checkout, plain `npx jest` works.

## Visual check

`docs/brand/avasetu/photo-quality-check.jpg` has six bundled photos plus darkened, blurred, dark-and-grainy, and tilted copies, each shown before and after.
- Lifted dark rooms look like evening light, not noon, and warm light stays warm.
- There are no halos and no oversaturation.
- Straightening crops cleanly.
- Blurred photos are flagged but not "fixed": enhancement cannot fix blur, and the tip asks the agent to retake the photo.

## Known limits

- Tilt is measured from near-vertical lines. Converging verticals (a building shot from below) count as perspective, not tilt.
- `mostly_sky_or_floor` is a band heuristic.
- A lifted dark photo looks slightly less saturated, because chroma is never boosted on purpose.
- Calendar items are reviewed on demand. The pipeline's own review uses a different context, so the first chip load runs one AI call.
