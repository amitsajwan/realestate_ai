# S1: sales kit on the website (handoff)

## What is built
- `/for-agents` (`frontend/app/for-agents/`): the agent brochure. Problem, Create/Attract/Qualify/Close, what you get, cost (free during the pilot, we tell you before that changes), what is coming, trust, See it live (demo page, Instagram, /go, /news with printed URLs), invite CTA with a QR code. Hindi and Marathi one-liners (Hind), wordmark in Baloo 2. Copy in `content.ts`.
  - QR: `frontend/lib/qr.ts`, a small pure-TS encoder (no dependency), rendered server-side as inline SVG by `InviteQr.tsx`. It encodes `siteUrl() + '/request-invite'`; `siteUrl()` in `lib/brand.ts` reads `NEXT_PUBLIC_SITE_URL` (default the production sslip.io host), so a domain change is one setting. Verified by decoding the screenshot with OpenCV.
  - Print: A4, two pages, header/footer/chat hidden. The app's global print sheet (`styles/components.css`) makes every background transparent and all text black; the page re-applies its brand colours in print (maps `PRINT_BG/PRINT_TEXT/PRINT_BORDER` in `page.tsx`; keep them in step with the classes).
- Links (`frontend/components/marketing/siteLinks.ts`): header (wide: For agents, See a demo page, News, Area guides, Sign in, Request an invite; phones: a no-JS Menu with everything plus Instagram and Facebook), footer columns For agents / Explore / Legal, contact block unchanged and phone-free. Sign in goes to `/studio` (it sends a signed-out visitor to `/join`); the hero's "Already invited? Sign in" stays `/join`. Landing hero has a secondary CTA "See a demo agent page". Instagram/Facebook come from `lib/marketing/social.ts` (`socialLinks()`), so the new @avasetu_ default on main applies after merge.
- Demo slug: `NEXT_PUBLIC_DEMO_AGENT_SLUG` (default `demo`), `demoAgentPath()` in `lib/brand.ts`.
- DEMO ribbon (`frontend/app/agent/[slug]/DemoRibbon.tsx`) on agent home and listing pages when `branding_data.demo === true`: a note under the header ("This is a demo page showing what an agent's Avasetu page looks like.", link to /for-agents) and a fixed corner ribbon that ignores taps. Fixture agent `demo` in `lib/site/fixtures.ts` (no phone, no RERA, sample-labelled listings).
- Backend: `branding_data.demo` is an owner-only key (`bd.OWNER_ONLY_KEYS`, documented in `docs/handoff/A1-brand.md`). Not a `SiteCreate`/`SiteUpdate` field, so agents cannot set it; agent PATCH keeps it; the public profile passes it through.
- `backend/scripts/create_demo_agent.py`: idempotent. Inactive user with placeholder phone `+910000000000` (not a valid Indian mobile, cannot sign in or receive anything), profile slug `demo` (a reserved slug no agent can get) with no phone/e-mail/RERA, emerald preset, AD monogram logo and banner drawn with Pillow into `uploads/images/`, and the 9 showcase homes as live listings labelled like `seed_samples.py` ("Sample:" title, "SAMPLE LISTING ... not available for sale"). Refuses to touch a `demo` slug owned by another user. Re-run monthly (live listings hide after 45 days unconfirmed; a re-run restarts the clock).

## Server command (integrator)
```
cd backend && PYTHONPATH=. python scripts/create_demo_agent.py --dry-run   # optional preview
cd backend && PYTHONPATH=. python scripts/create_demo_agent.py
```
Run it where the backend runs (same `MONGODB_URL`/`DATABASE_NAME`, cwd `backend/` so images land in the served `uploads/images`). In Docker: `docker compose exec backend python scripts/create_demo_agent.py` (from the container's app dir).

## Edits outside the owned paths (small, needed)
- `frontend/components/Navigation.tsx`: `/for-agents` added to the list of pages without the legacy app bar.
- `frontend/app/sitemap.ts`: `/for-agents` added.
- `frontend/lib/site/types.ts` (`demo?: boolean`), `frontend/lib/site/fixtures.ts` (demo fixture).
- Tests updated for Sign in -> `/studio`: `__tests__/marketing/landing.test.tsx`, `legal-pages.test.tsx`.

## Visuals
`docs/brand/avasetu/sales-kit/` (for-agents 390/1280 viewport and full page, demo agent 390/1280, landing top/menu/footer) and `docs/brand/avasetu/avasetu-for-agents.pdf` (A4, 2 pages). Screenshots use fixtures, so the Instagram link shows the old default until main's change merges; regenerate the PDF after merge/deploy.

## Crawl
Local `next dev --webpack` with fixtures; all internal hrefs from /, /for-agents, /go, /news, /posts, /localities, /insights, /agent/demo, /request-invite: 33 URLs, all 200.

## Follow-ups
- SECURITY (pre-existing, not changed here): `POST /api/v1/agent/public/{slug}/update-branding` in `backend/app/api/v1/endpoints/agent_public.py` has no auth and replaces `branding_data` wholesale. Anyone can deface any agent page or set `demo`. Remove it or put it behind the owner check.
- Agent hero eyebrow still says "PUNE PROPERTY · <areas>" (`components/site/Hero.tsx`, not in this stream).
- Page 1 of the PDF has some white space at the bottom; fine to leave or add a short line.
- Tests: jest in this worktree needs a regex `testMatch` because the path contains `.claude` (globs skip dot folders); in the normal checkout `npx jest` works as is.
