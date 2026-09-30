# D3: Listing showcase (labelled sample homes)

Module: `backend/app/modules/showcase/` (imports only `marketing.images/facts/polish` and `social.config/graph/publisher`).

- `samples.py`: 9 sample homes (3 Kharadi, 3 Upper Kharadi, 3 Wagholi; 2 and 3 BHK; 6 ready, 3 under construction), 27 Unsplash photos (credits in `docs/brand/photo-credits.md`, 4.5 MB in `assets/photos/`). Prices are labelled sample figures via `money()`.
- `render.py`: Instagram carousel (5 x 1080x1350: cover, inside, at a glance, why this area, CTA), Facebook card 1200x630, story scenes 5 x 1080x1920 (`write_home` saves them under `<slug>/scenes/`, for the video composer). `icons.py`: amenity icons drawn with shapes.
- `captions.py`: deterministic hook-first captions; optional `polish()` via any client with `text(system, user)` with guards (protected facts, no new numbers, phones, URLs, hashtags, hype).
- `publish.py`: `publish_instagram / publish_facebook / publish_showcase`. Renders on demand into `<UPLOADS_DIR or uploads>/showcase/<slug>/`, media URL = `PUBLIC_MEDIA_BASE_URL/uploads/showcase/<slug>/<n>.jpg` (Facebook: `facebook.jpg`). Honours `SOCIAL_DRY_RUN` (default on). Bypasses `social.service` on purpose; the caption is validated (label, disclaimer, no phone, IG: no URL, `link in our bio`, 3 to 8 hashtags) before any send.
- `plan.py`: 2-week plan (1 home / 2 days, alternating channel and area).
- CLI: `backend/scripts/showcase_admin.py` with `list`, `preview --out DIR [--slug]`, `post --slug S --channel instagram|facebook|both [--polish]`, `schedule-plan [--start D] [--days N]`.
- Contact sheets: `docs/brand/showcase-samples/`.

## Wiring the integrator needs (optional)
- `/uploads` must be served publicly (already mounted in `core/routes.py`); the first post renders the images into `uploads/showcase/<slug>/`. To pre-render on deploy run `showcase_admin.py preview --out uploads/showcase`.
- No publication records are written (no DB use). If the calendar/scheduler should post showcases, call `publish.publish_showcase(slug, channel)` from its runner and store the returned permalink itself.
- Real posts need `SOCIAL_DRY_RUN=false`, `META_PAGE_ACCESS_TOKEN`, `META_PAGE_ID`, `META_IG_BUSINESS_ID` and an https `PUBLIC_MEDIA_BASE_URL`.
- Real agent listings must use the agent's own photos: nothing here is reusable for them except the renderer primitives.

## Known limits
- Stock photos are not of the named localities (one visible shop sign on `kharadi-2bhk-ready`); all are labelled illustrative.
- The Wagholi under-construction cover photo is dark and moody; a brighter exterior would help.
