# Website audit (W1) - before state

Evidence: `docs/brand/web-audit/before/*.jpg` (live site, 390x844 `-m` and 1280x800 `-d`, full page). Script: `frontend/e2e/web-audit-shots.js`.

## The 10-second test for an agent (landing)

| Area | Finding | Severity |
| --- | --- | --- |
| Value proposition | "Get more buyer enquiries. Know who to call first." is fine but generic; it never names the agent's actual pain (comments and DMs that vanish in the scroll) and never says "WhatsApp". | High |
| Product visibility | Hero shows a real screenshot ("Your business today") that does not explain itself. The strongest story ("a comment becomes a lead card") is only visible 4 scrolls down. | High |
| Brand | Blue/slate generic SaaS look. Social creative is navy/gold/cream with bold Poppins hooks; the site that posts link to looks like a different company. | High |
| CTA | "Request an invite" exists but the form is a separate page with 4 fields and a long hint text; no sticky CTA on mobile; header CTA is the only one above the fold on 390px. | High |
| Trust | Honest status ("free pilot", "invite only") is present but buried in small chips. No RERA answer, no "who sees my leads" answer in FAQ. | Medium |
| Story | Four steps exist but are labelled Create / Market / Attract / Qualify and close, not the brand's Create, Attract, Qualify, Close; copy is feature-first. | Medium |
| Language | English only; Hindi/Marathi appear only in the product description. No i18n scaffold exists, so a toggle would be a new system: deferred. | Medium |
| Speed | Landing loads 6 phone PNG-sized JPGs (780x1688) in a vertical stack: about 7,900 px tall on mobile with large empty phone frames. | Medium |

## Cross-page problems

- `/localities` and `/insights` render the generic "PropertyAI" app bar above the real "PUNE Property" header: two headers, wrong brand name, wasted 64px of a phone screen (Navigation.tsx only hides itself on some paths).
- Locality, insight and agent pages never offer agents a path to the product, and landing never offers buyers anything: two audiences, one funnel.
- `/localities` cards have no imagery or hook, text-only; gold used as plain amber.
- `/join` first screen is a bare form: no explanation of what the OTP is for, no "no invite yet?" path, no reassurance, default blue buttons.
- `/studio` signed out only redirects to `/join` (AppShell and tabs belong to another stream; untouched).

## Agent site `/agent/amit-sajwan`

- Good: navy hero, gold CTA, "Sample listing" badges, contact buttons.
- Weak: the sample homes read like real inventory with no explanation of why they are samples; a visitor cannot tell what the page is. Placeholder tiles (Skyline) next to real photos look broken.
- Enquiry form sits at the bottom of a 6,800 px page; the hero CTA scrolls there, no sticky bar on mobile (StickyBar exists, check usage).

## SEO / share

- Every page falls back to a single generic `og.jpg`; the landing uses a raw product screenshot as its preview (phone UI, no headline), which looks poor in a WhatsApp card.
- Global `<title>` is "PropertyAI - AI-Powered Real Estate Platform" (wrong brand) wherever a page forgets its own.

## Accessibility

- Small grey captions (slate-600 on white is fine) but gold on white would fail; keep gold only on navy.
- Tap targets mostly 44px+: good. Footer links ok.
- Form errors use role=alert: good. Honeypot is hidden: good.
- Missing: visible focus ring on many marketing links, `prefers-reduced-motion` irrelevant (no animation).

## Plan (highest impact first)

1. Navy/gold Poppins landing: problem hook, HTML/CSS phone mock of the INTERESTED -> lead card story, Create/Attract/Qualify/Close in plain words, WhatsApp-first copy, honest pilot status, FAQ (cost, data, RERA, who sees leads), short inline invite form, sticky mobile CTA.
2. Remove the double header; apply the brand to localities/insights/legal via the shared shell.
3. New landing og image (1200x630) in brand style.
4. Buyer paths: localities/insights get an enquiry CTA and an agent invite strip.
5. Agent site: explain sample homes; join: reassurance and a no-invite path.
