# Handoff: S2 AI listing draft

Branch `v2/s2-ai-listing`. Module `backend/app/modules/ai_listing/`, tests `backend/tests/modules/test_ai_listing*.py`.

## What shipped
`POST /listings/ai/draft` (multipart: `text?`, `audio?`, `image_count?` int, `city_hint?`, plus optional `language?` hint for Whisper). Bearer auth via `current_active_user`. Returns the frozen `AIDraft` (`draft`, `confidence`, `missing`, `transcript`, `warnings`). Nothing is persisted.

Pipeline: audio -> Groq Whisper (`Transcriber`) -> combined with typed text -> deterministic extractor (regex + gazetteer, Devanagari numerals/words normalised) -> optional Groq LLM (JSON mode, 8 s timeout) -> merge (deterministic wins at confidence >= 0.75, LLM fills gaps at 0.6, LLM amenities accepted only if they map to the known vocabulary) -> copy (English title <= 120 chars and a short description built only from extracted facts; hi/mr via LLM when available) -> `missing[]` and `warnings[]`.

Files: `router.py` (route, upload limits), `service.py` (orchestration), `extractor.py` + `extract_numbers.py` + `extract_text.py` + `text_norm.py` (deterministic), `geo.py` + `gazetteer.py` (cities/localities with Rs/sqft bands; extend the dicts), `merge.py`, `plausibility.py` (warnings), `copywriter.py`, `llm.py` (Groq clients, injectable), `schemas.py`.

## Integrator mount line
In `backend/app/api/v1/router.py`:
```python
from app.modules.ai_listing.router import router as ai_listing_router
api_router.include_router(ai_listing_router, prefix="/listings", tags=["listings-ai"])
```
Route is POST-only at `/ai/draft`, so it does not clash with S1's `GET /listings/{id}`; mount it before the S1 router anyway in case S1 adds a `POST /listings/{id}` catch-all.

## Env vars
- `GROQ_API_KEY` (env or existing `settings.GROQ_API_KEY` / `groq_api_key`). Without it: deterministic-only drafts, and audio uploads return 503 "Voice input is not configured" (text still accepted).
- Optional: `AI_LISTING_LLM_MODEL` (default `openai/gpt-oss-120b`; the old llama-3.1-8b-instant was retired by Groq on 2026-08-16). Any OpenAI-compatible provider: `AI_LLM_BASE_URL`, `AI_LLM_API_KEY`, `AI_LISTING_STT_MODEL` (default `whisper-large-v3`).

## Limits and errors
Audio <= 10 MB (413), types webm/ogg/mp3/m4a/wav/mp4 (415; octet-stream accepted by extension), empty audio 400, transcription failure 502, no key 503, text > 6000 chars 413. `image_count` clamped 0..50; `media` is listed in `missing` when it is 0. Empty/garbage input returns an empty draft with `missing` populated (never 500).

## Accuracy
Golden set (`test_ai_listing_golden.py`): 38 inputs (English, Hinglish, Devanagari Hindi/Marathi, sale/rent, plots, commercial, RK/studio), 211 asserted fields (price, BHK, area, locality, transaction, type, floors, furnishing, possession, RERA, project, city): 211/211 = 100% on the deterministic path (gate is >= 90%). The set was authored alongside the extractor, so expect lower on real traffic; add real agent messages to `GOLDEN` as they arrive.

## Known gaps / notes
- Plot area has no contract field: plot/land area is stored in `carpet_sqft` (sq yd, gaj, guntha, acre, sq m converted to sq ft).
- An unqualified area is treated as carpet (confidence 0.6, with a warning).
- Sale vs rent is inferred from price size when not stated (confidence 0.6, with a warning).
- Gazetteer is ~90 localities in 6 metros plus ~20 city names; unknown localities are only caught via "in/at Capitalised Name" (conf 0.5) or by the LLM. Project names need capitalised text with a suffix (Heights, Towers, ...) or a "project/society:" cue.
- Devanagari number words are covered for Hindi 1-100 and common Marathi; Roman-script Hindi numbers only for BHK ("do bhk") and "hazaar".
- Price-per-sqft bands are rough 2025 figures, used only for soft warnings.
- The LLM path is tested with fakes and `httpx.MockTransport` only; it has not been run against the live Groq API.
- Translation (hi/mr) adds a second LLM call (up to 8 s) after extraction.
