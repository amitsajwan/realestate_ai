# A1: branded agent pages (handoff)

## Stored shape: profile `branding_data` (all keys optional, additive)

```json
{
  "tagline": "Aundh and Baner homes, explained properly",
  "colors": {"primary": "#0b5d46", "secondary": "#083f31", "accent": "#f4c95d"},
  "logo": "/uploads/images/logo1.png",
  "social": {"instagram": "kulkarnihomes.pune", "facebook": "https://www.facebook.com/..."},

  "business_name": "Kulkarni Homes",
  "about": "plain text, max 600",
  "banner": "/uploads/images/banner1.jpg",
  "preset": "navy-gold | emerald | terracotta | royal-purple | slate-teal | cream-ink",
  "custom_primary": "#1a2b5c",
  "rera_agent_no": "A52100012345",
  "areas": ["Aundh", "Baner"],
  "languages": ["English", "Marathi"],
  "years_experience": 12
}
```

- Owner-only key `demo` (bool, `bd.OWNER_ONLY_KEYS`): `true` only on the fictional demo agent made by `backend/scripts/create_demo_agent.py`. The public profile passes it through and the agent page shows a DEMO ribbon and note. Agents cannot set it (not a `SiteCreate`/`SiteUpdate` field, so it is ignored) and their PATCH keeps it.
- `colors` (and `site_config.theme`) are derived from `preset` / `custom_primary` for legacy consumers; the frontend ignores them.
- Public response: `GET /api/v1/agent/public/{slug}` already passes `branding_data` through, so all fields are public. No phone numbers are ever stored in it.
- `tagline` also sets `site_config.hero.subheadline`; `about` also sets the profile `bio`; `business_name` sets `site_config.hero.headline`.

## API

- `GET /api/v1/join/site` (auth): `{slug, agent_name, photo, logo, social, branding_data}`.
- `PATCH /api/v1/join/site` (auth): any of `photo, logo, banner, instagram, facebook_url, business_name, tagline, about, preset, custom_primary, rera_agent_no, areas, languages, years_experience`. Empty string / null / `[]` clears; omitted fields stay. Returns the same shape as GET.
- `POST /api/v1/join/site` also accepts the brand fields (the join step sends `business_name` and `preset`).
- Validation (`backend/app/modules/onboarding/branding.py`): text fields reject phone numbers (7+ digits), links, e-mail, markup; lengths business_name 60, tagline 90, about 600; `custom_primary` is #rrggbb and must give >= 4.5:1 with white; `rera_agent_no` is `A` + 6 to 18 digits (spaces and dashes stripped, uppercased, max 20); `areas` up to 6, Pune localities (known list, or text containing Pune/Pimpri/Chinchwad/PCMC); `languages` up to 6; `years_experience` 0 to 60; `logo`/`banner` only `/uploads/images/...` (upload through the existing route).

## Frontend

- Presets and theme: `frontend/lib/site/presets.ts`, `theme.ts` (`resolveTheme`, `themeVars`, `displayName`, `safeImage`, `safeRera`), `contrast.ts`. Colours mirror the backend; a jest test pins them.
- Site: `components/site/{SiteShell,Hero,AboutAgent,Skyline}.tsx`. Agent header shows logo or monogram + business name; hero uses the banner under a dark overlay (0.62 to 0.86) or the preset gradient, texture and skyline. RERA is shown as "RERA agent registration: <no>", stated by the agent, not verified, with a MahaRERA link. Footer: "Powered by PUNE Property". "Verified" is never claimed. Agents with no branding get navy-gold and their own name in the header.
- Editor: `components/app/BrandEditor.tsx` props `{agentId?, loadBranding(agentId?), saveBranding(patch, agentId?), uploadImage(file, agentId?), onSaved?}`; types `BrandingDoc`, `BrandingPatch` and the real/fixture client `brandingApi` are in `lib/app/branding.ts`. Studio screen: `/studio/profile` ("My brand", linked from the Studio home). Join step: business name and preset picker.
- Cards: `Facts.agent_business` / `agent_rera_no`; cover and story cards show "Listed by <business> · RERA <no>" (cta card adds a small line); without them the old "Listed by PUNE Property team" stays. Design unchanged, no phone numbers.

## For A2

Import `BrandEditor` and pass `loadBranding/saveBranding/uploadImage` bound to an agent id. The existing PATCH is for the signed-in agent only; an owner endpoint that edits another agent's `branding_data` must reuse `SiteUpdate` and `OnboardingService.update_site` logic (it works on a user, so pass the target user).

## Tests and visuals

- Backend: `backend/tests/modules/test_agent_branding.py`, `test_agent_branding_cards.py`.
- Frontend: `__tests__/site/presets-contrast.test.ts` (WCAG AA for all six presets, banner overlay worst case, custom colour), `__tests__/site/agent-branding.test.tsx`, `__tests__/app/brand-editor.test.tsx`.
- Screenshots: `docs/brand/agent-brand-samples/` (five fictional agents at 390 and 1280 wide, the About section, the BrandEditor). Script: `frontend/e2e/agent-brand-shots.js`. Fixture agents live in `frontend/lib/site/fixtures.ts` (`FIXTURE_BRAND_AGENTS`). Photos are the Unsplash samples listed in `docs/brand/photo-credits.md`.
- Known: `frontend/e2e/site-brand-check.js` still asserts the old navy header and PP logo for every agent; it is out of date by design.
