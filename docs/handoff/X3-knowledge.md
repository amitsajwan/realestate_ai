# X3: knowledge and grounded replies

Replies to buyers now answer the enquiry from what we know about THAT home, post or area. Only a detail we truly do not have is handed to a person, and the reply says so plainly
("I do not have the maintenance figure for this home, but the agent can tell you: <link>"). Never "we will forward your query".

## What was built (`backend/app/modules/knowledge/`, loosely coupled)
- `areas.py`: curated `AreaFacts` for kharadi, upper_kharadi, wagholi. Every statement restates our own pages (localities.ts, insights.ts), which cite PIB and MahaRERA. No prices, no predictions, no
  distances, no school or hospital names (unsourced, so left out on purpose). Metro is "approved is not the same as running". `tests/modules/knowledge/test_areas.py` parses the two TS files and fails
  if a number, a name, a metro line or the wording is not on those pages.
- `grounding.py`: `await facts_for(Ref, db) -> Grounding` for `Ref.listing(id)`, `Ref.sample(slug)`, `Ref.calendar(item_id)` (evergreen post: library body + review note; showcase item: its home),
  `Ref.area(name)`, `Ref.text(post message)`. A Grounding has `subject`, `facts`, `faq`, `links` (`{"interest": "{interest_url}", "page": ""}`, the caller fills them), plus `area_facts`, `area_faq`,
  `general` (site visit, loan, RERA how-to), `advice` ("Check: ...", never stated as fact), `kind`, `sample`, `sources`. Listing `about` is read with `.get` and may be absent or null. Agent text with a phone,
  a link or a hype word is dropped. A sample (or a stored listing whose title starts with "Sample") is always labelled and never "available".
- `reply.py`: `await answer(question, grounding, channel, llm) -> Reply{text, confident, missing, basis, language, via}`.
  Topics: price, carpet/size, possession, floor, facing, parking, amenities, power backup, school, hospital, market, metro, nearby, commute, maintenance, water, RERA, site visit, availability, booking,
  negotiation, loan, furnishing, builder, location, address. English, Hindi, Marathi, Hinglish and romanized Marathi questions are routed; the reply is in the same language.
  - Everything found: English questions get the LLM's phrasing from the grounding alone (prompt = grounding + question); other languages get the grounded English sentence translated by the LLM. Without an LLM,
    or when the draft fails the checks, the grounded sentences are used as they are (framing words in the buyer's language).
  - Checks on every LLM text: length; no phone, link, `{}`, hype, prediction or brush-off; every number must be in the grounding (a number only the commenter typed never counts); every proper noun must be in
    the grounding; for free English answers every content word must be in the grounding too (catches "away from the road noise"); a sample answer must say it is a sample.
  - Part not covered: what we can say, then one honest sentence naming the gap with the link. `confident=False`, `missing` names the gap ("the maintenance figure", "the exact distance or travel time").
  - Sample home: "is it available / can I visit / negotiable / can I book" say it is an illustration and invite budget and area; price gives only "The sample price figure is ₹98 Lakh, a labelled sample figure".
  - Channels: `facebook` text ends with the placeholder `{interest_url}` (caller fills it); `instagram` never has a URL ("link in our bio"); `chat` has no link ("I will ask our team to confirm it for you").

## Wiring
- `engage/brain.py`: `decide(..., grounding=None)`. A comment that asks about the post (topic found and a question, or a short comment naming one thing) gets `grounded_decision`; the LLM can still say spam,
  complaint, praise or greeting first. `Decision` has `missing` and `basis`. Without `grounding` behaviour is unchanged. Interested/greeting/spam/own-account/DM paths are unchanged.
- `engage/service.py`: the context builds a grounding per post: listing (via `publications`) -> calendar item (via `content_calendar.external_id`, evergreen post or showcase sample) -> the post's own text.
  A confident answer is posted and NOT queued; an unconfident one is posted AND queued (`needs_human`, `missing` recorded). Rows gain `answer_basis` (list of fact strings) and `missing`.
  All caps, dedupe, spam, own-account, dry-run and `only_ids` rules are untouched. `EngageService(..., interest_url=None)`: optional `interest_url(ctx, channel)` (sync or async) returns the interest URL;
  `ctx` has `listing_id`, `calendar_id`, `agent_id`, `link`.
- `chat/engine.py`: `turn(d, text, llm, grounding=None)`. Topic questions are answered from the grounding; gaps are said plainly, `needs_human` is set and the existing consent-first phone step follows. `d["missing"]` is kept.
- `chat/service.py` (small edit outside the listed paths): `message(..., context=None)` builds the grounding (`grounding_for`): public listing (status live/under_offer) > published calendar post > locality. All ids are
  re-checked server side; unknown or hostile context is ignored. `conversations()` also returns `missing`.
- `chat/router.py`: `POST /chat/message` accepts `context: {listing_id?, post_id?, locality?}` (patterns and length limits).
- Frontend: `frontend/lib/site/chatContext.ts` (`chatContextFromPath`) + `ChatWidget.tsx` sends `context` from the page path (`/agent/<slug>/listings/<id>` or `/agent/<slug>/<id>`, `/localities/<slug>`).
  Test `frontend/__tests__/unit/lib/chatContext.test.ts` was written but not run (no node_modules in this worktree).

## What other streams / the integrator must provide
- Interest URL: pass `interest_url=` to `EngageService` in `engage/runner.py` (X1's function: `(ctx, channel) -> str`). Until then the listing page or landing page link is used (as before). Instagram never uses it ("link in our bio").
- Listing `about` (X4): read defensively; shape per contract. `about.nearby[].minutes`, `about.maintenance`, `about.parking`, `about.faq` etc. are what make answers specific. Agent FAQ answers win over facts when the FAQ question is about the same topic.
- Calendar: published rows must keep `external_id` (the Facebook post id or Instagram media id) so a comment can be tied to the item. Showcase rows use the home slug in `slug`.
- Chat widget: pass `post_id` from a post page if X2 builds `/posts/<id>`; `chatContextFromPath` only handles listing and locality today.

## Tests (no network)
`PYTHONPATH=backend backend/.venv/Scripts/python.exe -m pytest backend/tests/modules/knowledge backend/tests/modules/test_engage.py backend/tests/modules/test_engage_instagram.py backend/tests/modules/test_chat.py -q -c backend/pytest.ini`
- `knowledge/test_areas.py` (sync with the site pages), `test_grounding.py`, `test_reply.py` (53-question table across sample, listing with `about` and area, on Facebook and Instagram; fake-LLM tests for acceptance,
  rejection of unsafe drafts, fallback, language, sample labelling, prompt injection).
- Updated: `test_engage.py` (the old "Our team will reply here soon" expectation is now the honest "I do not have ..." wording) plus new grounded cases; `test_engage_instagram.py`; `test_chat.py` (context, honest gaps, consent-first).

## Eval with the real LLM
`docker compose exec -T -e PYTHONPATH=. backend python scripts/knowledge_eval.py [--channel instagram] [--only L] [--no-llm]` prints each question and the answer (rules and LLM side by side).

## Known limits
- Hindi and Marathi replies on the no-LLM path keep the fact sentence in English with Hindi/Marathi framing; with the LLM it is translated and checked.
- Questions with no known topic (e.g. "is it a good investment?") are answered only by the LLM (English) from the grounding or by a close fact match; otherwise honestly marked missing.
- The area has no schools, hospitals or distances until someone supplies sourced data; a listing gets them from the agent's `about.nearby`.
