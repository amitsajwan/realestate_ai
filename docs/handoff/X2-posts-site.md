# X2 Posts on the website and contact block

## Built
- `backend/app/modules/calendar/public.py`: `router` with `GET /posts?limit=` (1-50, default 12). Only `published` rows that have a permalink; newest first; same slug and kind published within 3 days on two channels is one item with `links` for both (Facebook leads). Fields: id, kind, channel, channels, title, excerpt (max 220, no hashtags, links, footer line or phone-like numbers), image_url (`PUBLIC_MEDIA_BASE_URL/uploads/<first image>`, null if unset or no image), permalink, links[{channel,url}], published_at, sample (kind == showcase). 60 s in-process cache plus `Cache-Control: public, max-age=60`.
- `backend/app/modules/calendar/footer.py`: `FACEBOOK_FOOTER`, `INSTAGRAM_FOOTER`, `with_footer(caption, channel)` (idempotent, FB < 900, IG < 2000, at most 10 hashtags, body trimmed never footer). Not applied anywhere yet.
- Frontend: `lib/posts/data.ts` (fetch, 60 s revalidate, https-only cleaning), `lib/marketing/social.ts` (Facebook/Instagram URLs, env override `NEXT_PUBLIC_FACEBOOK_URL`, `NEXT_PUBLIC_INSTAGRAM_URL`, contact wording), `components/site/{PostCard,PostsGrid,PostsSection,SocialStrip}.tsx`, `components/marketing/ContactBlock.tsx`, `app/posts/{page,loading}.tsx`.
- Landing: `PostsSection` between the screens strip and "How it works"; Organization json-ld now has `sameAs`. Footer of `SiteFooter` (marketing) and `SiteShell` (agent sites) shows the contact block and social strip; the old email/WhatsApp ContactLines is no longer used in the footer (no phone or email public). Footer also links /posts. /posts is in the sitemap; root Navigation hidden on /posts.
- Small edits outside the owned list: `app/page.tsx`, `app/sitemap.ts`, `lib/marketing/seo.ts` (optional `sameAs` arg), `components/Navigation.tsx` (hide on /posts), `__tests__/marketing/landing.test.tsx` (mocks the async PostsSection).
- The Facebook URL is the one given by the owner (profile.php?id=61595137641524); it could not be verified as canonical from here.

## Integrator wiring
```python
from app.modules.calendar.public import router as calendar_public_router
app.include_router(calendar_public_router, prefix="/api/v1/public")   # -> GET /api/v1/public/posts (no auth)
```
The frontend reads `${SITE_API_URL}/api/v1/public/posts`. Apply `with_footer` where calendar captions are built (library / adapters) and before publish.

## Tests
Backend: `test_public.py` (6), `test_footer.py` (6) pass. Frontend: `__tests__/posts/posts-site.test.tsx` plus marketing and site suites (98) pass; `tsc --noEmit` clean.

## Screenshots
`docs/brand/posts-site-samples/`: posts, landing-posts, footer at -m (390x844 viewport) and -d (1280x800), with mocked API data (sample images from docs/brand). Known: wide Facebook sample images are cropped by object-cover in the 4:3 card.
