# Contract: interest links, posts on the site, grounded replies, project and area knowledge

Owner feedback (1 Oct 2026): (1) a tap-to-show-interest link is better than asking people to type INTERESTED; (2) every post should carry the website link, and the website should show and link the posts; (3) replies must be intelligent and answer enquiry details, not 'we will forward to the team'; (4) when a post or listing is created we must also capture project and area information so the AI can answer from it.
Hard rules stay: no phone numbers or personal names in public posts, sample homes labelled as samples, no invented facts, nothing published without the existing approval gates. Brand voice 'PUNE Property team'.

## Shared vocabulary

### InterestLink (module `interest`, collection `interest_links`)
`code` (6 to 8 url-safe chars, unique), `kind` ('listing' | 'post' | 'page'), `ref` (listing id, calendar item id or slug), `agent_id` (owner agent or the listing's agent), `channel` ('facebook' | 'instagram' | 'website' | 'whatsapp'), `created_at`.
Public URL: `<SITE>/i/<code>`. A visit records a `click` event; the one-tap button records an `interest` and creates or updates a lead in the existing tracking/leads flow (source = channel, with the post or listing as context). Contact details are optional and only stored with an explicit consent checkbox (existing consent wording style). Rate limited, honeypot, no PII in URLs.
Instagram captions cannot hold clickable links: they say 'link in our bio' and the bio link is a hub page `<SITE>/go` that lists the latest posts and homes, each with a 'I am interested' button to its own `/i/<code>`.

### About (listing and project knowledge; stored on the listing as `about`, all fields optional)
```
about: {
  project_name: str, builder_known_as: str,            # only if the agent supplies it
  highlights: [str],                                    # up to 6 short lines
  amenities: [str],
  nearby: [{type: 'school'|'hospital'|'transit'|'office'|'market'|'park'|'other', name: str, minutes: int?}],
  connectivity: [str],                                  # roads, metro status worded 'approved is not running'
  water: str, power_backup: str, maintenance: str, society: str, parking: str,
  possession_note: str, rera_note: str,
  faq: [{q: str, a: str}]                               # up to 8 agent-written answers
}
```
### AreaKnowledge (module `knowledge`)
`area_facts(locality: str) -> AreaFacts` for kharadi, upper_kharadi, wagholi: curated, stable, sourced statements (no prices, no predictions, no invented distances). Source of truth is a Python data file `knowledge/areas.py` (derived from frontend/lib/marketing/localities.ts and insights.ts, kept in sync by a test).
`facts_for(ref) -> Grounding` returns `{subject, facts: [str], faq: [{q,a}], links: {interest, page}}` for a listing id, a calendar item (its own verified body and review note), a showcase sample home (its dataset record) or an area. This is the ONLY thing replies are allowed to use.

### Grounded reply (module `knowledge.reply`)
`async answer(question: str, grounding: Grounding, channel: str, llm) -> Reply{text, confident: bool, missing: str|None}`: answers ONLY from `grounding`; guards: no phone numbers, no hype, no prices not in the grounding, no predictions, no URL on Instagram ('link in our bio'), short and warm. If part of the question is not covered the reply states what it can say, says plainly that the detail is not available and offers the interest link so the agent can share it (never the bare 'we will forward your query'); `missing` names the gap so the owner sees what to add.
Deterministic fallback when the LLM fails: match the question to `faq` and facts with simple keyword rules.

## Ownership (disjoint)
| Stream | Owns |
|---|---|
| X1 interest links and hub | `backend/app/modules/interest/`, `frontend/app/i/`, `frontend/app/go/`, their tests |
| X2 posts on the website and contact footer | `backend/app/modules/calendar/public.py` + router addition for `GET /public/posts`, `frontend/app/posts/` (or a section on the landing), `frontend/components/site/*` social strip, footer contact block |
| X3 knowledge and grounded replies | `backend/app/modules/knowledge/`, edits to `backend/app/modules/engage/brain.py`, `engage/service.py`, `chat/engine.py`, `chat/kb.py` |
| X4 listing creation: project and area info | `backend/app/modules/listings/` schema/service for `about`, `backend/app/modules/ai_listing/` (area suggestion), `frontend/components/app/NewListingFlow.tsx`, `ReviewForm.tsx`, `AboutStep.tsx` (new), `frontend/lib/app/*` types |
The integrator wires routers, loops and calendar caption changes (adding the interest link to captions) after the streams report.
