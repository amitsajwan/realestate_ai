# W1 Website UX handoff

Audit: `docs/brand/web-audit/AUDIT.md`. Evidence: `docs/brand/web-audit/before/` (live) and `after/` (local dev against the live read-only API, writes blocked). Mobile = `-m` (390x844), desktop = `-d` (1280x800), plus `landing-fold-m`, `invite-errors-m`, `landing-submit-ok-m` (submit path with mocked API).

## Changed
- Landing (`frontend/app/page.tsx`): problem-first hero ("A buyer comments INTERESTED. Do you know who they are?"), HTML/CSS phone mock of comment -> lead card (`components/marketing/LeadCardMock.tsx`, labelled sample data), "Sound familiar?", Create / Attract / Qualify / Close in plain words, WhatsApp-first line, real screens in a lazy horizontal strip, honest pilot/cost/what-is-coming, FAQ (added cost, who sees leads, RERA), short invite form embedded at the bottom (`#invite`).
- Brand: navy/gold/cream, Poppins (`lib/marketing/font.ts`), shared by all marketing pages through `MarketingShell` / `SiteHeader`.
- `RequestInviteForm`: name + mobile + consent only; city and note under "More details"; `idPrefix` prop; clearer placeholder.
- `components/Navigation.tsx`: also hidden on /localities and /insights (removes the duplicate "PropertyAI" bar).
- `AgentStrip` invite on localities and insights pages; locality index cards restyled.
- Agent site `ListingBrowser`: sample-homes explainer when sample listings are present, richer empty state with an enquiry link.
- `/join`: one-line value text, pilot status and "No invite yet? Request one".
- Share preview: `public/brand/og-landing.jpg` (rendered by `e2e/render-og.js`) used for the landing.
- Scripts: `e2e/web-audit-shots.js`, `web-audit-fold.js`, `web-audit-submit.js`.

## Tests
`npx tsc --noEmit` clean; `next build --webpack` passes; marketing + site jest suites pass (88 tests). In a `.claude/` worktree jest needs a local config with `testRegex` (dot-directory defeats `testMatch` globs) and Turbopack rejects the node_modules junction, so use `--webpack`.

## Not done / next
- Hindi/Marathi toggle: no i18n scaffold exists in `lib/marketing/strings.ts`; add a `strings.hi.ts` + cookie toggle for hero, steps, FAQ.
- Agent site: sticky mobile "I'm interested" bar on the home page, per-agent og image, real photos instead of Skyline placeholders for sample homes.
- `/studio` first-run (AppShell) and `/join` OTP/profile steps untouched beyond the first screen.
- Contrast check of slate-600 captions on cream and gold-on-navy with a tool; add visible focus ring tokens site-wide.
- Chat widget overlaps the hero mock on small phones; consider hiding it until scroll.
- Root `app/layout.tsx` metadata still says "PropertyAI" for non-marketing routes.
