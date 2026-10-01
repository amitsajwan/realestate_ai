# X4 handoff: project and area information at listing creation

## Stored shape (`listings.about`, optional, nothing migrated)

```
about: {
  project_name: str|null, builder_known_as: str|null,
  highlights: [str]            # max 6
  amenities: [str]             # max 20
  nearby: [{type: 'school'|'hospital'|'transit'|'office'|'market'|'park'|'other', name: str, minutes: int 0-240 | null}]   # max 12
  connectivity: [str]          # max 8; metro lines worded 'approved, not running'
  water, power_backup, maintenance, society, parking, possession_note, rera_note: str|null
  faq: [{q: str, a: str}]      # max 8 (the UI offers 4)
}
```
Every string is at most 300 characters, control characters and angle brackets stripped, whitespace collapsed. A phone number (10+ digits) or a web link anywhere in the object is rejected with 422 ("must not contain a phone number" / "must not contain a web link"). `maintenance` holds only the amount text (for example `₹3,000 per month`); the key is the label. A PATCH with `about` replaces the whole object; `about: null` clears it. Listings without it read `about: null`.

For the knowledge stream: read `listing["about"]` from the `listings` collection (a dict, or missing). `faq` answers are agent-written and are the best grounding for buyer questions. `faq` is NOT in the public listing response; all other fields are.

## Backend
- `listings/about.py` (models and sanitising), wired into `_Fields` (create, update, agent read) and `PublicListing` (`PublicAbout`, no faq).
- `ai_listing/area_seed.py`: curated lines for Kharadi, Upper Kharadi, Wagholi (connectivity wording and Kharadi offices EON Free Zone and World Trade Center Pune; sources are PIB cabinet releases and wtca.org). No prices, distances, times or predictions. Metro text is always "approved, not running yet". Corridor 2B length and station count were left out on purpose: sources disagree (11.6 km / 11 stations vs 12.75 km / 13 stations).
- `ai_listing/about.py`: `extract_about(text)` deterministic keyword rules (English, Hinglish, Devanagari keywords); optional LLM proposals through `llm.json(...)`, kept only if every longer word is traceable to the agent's text (amenities only from the known vocabulary); `suggest_about(...)` adds `source: 'agent' | 'area_guide'`.
- `POST /listings/ai/about-suggest` (router mounted at `/listings`, so the full path is `/api/v1/listings/ai/about-suggest`; the brief said `/ai/listings/about-suggest`, the integrator can add an alias). Body `{locality?, project_name?, bhk?, description}`. Response `{highlights:[{text,source}], amenities:[{text,source}], nearby:[{type,name,minutes?,source}], connectivity:[{text,source}], fields:{water|power_backup|maintenance|parking|society: {text,source}}, project_name, area_known, area_name}`. Persists nothing.
- AIDraft: `draft.about` is filled from the agent's words with the same rules (key absent when nothing found; not counted in `missing`).
- Marketing: `Facts.highlights` (first 2 of `about.highlights`, in `marketing/facts.py`) used by the Instagram caption (optional line, dropped if it would not fit) and the Facebook post. No other channel changed.

## Frontend
- `components/app/AboutStep.tsx`: step between drafting and review in `NewListingFlow`; skippable; chips, inputs, up to 4 buyer questions, suggestion list with keep and remove and source tags, client-side phone and link check. Strings in `lib/app/strings.ts` (English, Hindi and Marathi for the main labels).
- `ReviewForm` shows a summary with Edit (or Add when skipped). `lib/app/about.ts` holds helpers.
- Public page: `components/site/ListingAbout.tsx` (renders nothing without `about`).
- Fixture mode: `suggestAbout` in `lib/app/fixtures.ts`; the Kharadi site fixture has an `about`.
- Screenshots (390x844): `docs/brand/about-step-samples/`; script `frontend/e2e/about-step-shots.js` (needs `next dev --webpack` in a worktree because Turbopack rejects the node_modules junction).
