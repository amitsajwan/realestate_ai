# N2b: Relevance tightening

Triggered by a live dry run against Google News. All changes are in `newsroom/stages/*` plus tests and fixtures.

## Filter (`stages/filter.py`, new `stages/topics.py`)
- Area must be the subject: named in the title or the first sentence of the text. A mention deeper in the body gives "off-topic: area only mentioned in passing".
- Landmarks (EON IT Park, WTC, Magarpatta) count as an area only when no other locality (list in `topics.OTHER_LOCALITIES`) is in the title or first sentence.
- No more fallback to `locality_life`: no pillar keyword evidence means drop ("no buyer relevance").
- Denylist `topics.DENY_TOPICS`: vehicle prices, hotels/restaurants, PG/rental ads, festivals, sports, entertainment, weather, unrelated government talk (crime already existed). Checked on title and first sentence.
- Short-lived rule `topics.short_lived`: diversions/advisories with one-day wording (today, tomorrow, weekday, time window, immersion) and no durable wording (girder, flyover, months, project...) are "stale by nature".
- Buyer-relevance score: pillar evidence (title 2, body 1) + 2 if area/corridor in title, else 1 if area in first sentence. Below `topics.MIN_SCORE` (3) is dropped. Reason shows the score.
- `topics.EXTRA_PILLAR_KEYWORDS` adds evidence words (land acquisition, drainage, tender, widening, property tax...).

## Draft (`stages/draft.py`)
- `headline_only(item)`: text empty, equals title, title plus a few words, or under 25 words.
- In that case: a separate short prompt (no "why"), output is always a post: fact, "What to check", source, question. No "Our view" line, never an article. A reply without `why` is accepted here; for full-text sources `why` is still required.
- `template_draft` no longer writes a generic "may be worth knowing about" line (no "Our view" at all).

## Check (`stages/check.py`)
- Filler phrases (`FILLER`, about a dozen generic hedges such as "may affect the surrounding area's amenities", "could have implications", "worth keeping an eye on", "stay informed") fail the draft. "worth knowing about" is deliberately NOT listed because an existing test uses it as a fine hedge.
- Sentence-initial gerunds (`Having`, `Knowing`) and a larger set of ordinary adjectives/connectives (`Local`, `Nearby`, `Recent`...) are no longer reported as names. Unknown capitalised words (Sunrise, Hinjewadi) are still caught.
- `12.37L` is parsed as 12.37 lakh; lakh/L and crore/Cr compare equal. A real mismatch (lakh vs crore) is still flagged.

## Tests
`tests/modules/newsroom/test_n2b_relevance.py` (new) and 11 new fixtures `fixtures/articles/live_*.json` (10 drops, 1 keep). Wagholi Ganesh-immersion diversions are dropped as a festival item (and, absent festival words, by the short-lived rule).

## Proposals (policy.py / types.py, not edited)
1. Move `MIN_SCORE`, `DENY_TOPICS`, `SHORT_LIVED`, `OTHER_LOCALITIES`, `LANDMARKS` into policy.py once the owner agrees; `topics.py` then re-exports.
2. Split `AREA_KEYWORDS` into locality names and `AREA_LANDMARKS` so the filter need not keep its own `LANDMARKS` set.
3. Add `education` to `PILLAR_KEYWORDS` (school, college, university, cbse, icse, admission, campus) so the filter can return the `education` pillar; today school items map to `locality_life` (an existing fixture expects that, so the fixture must change with it). `topics.EDUCATION_KEYWORDS` is ready.
4. Remove "school"/"hospital"-style overlap between pillars after that change.
5. Add the filler phrase list and a `MAX_AGE`-style exemption for evergreen education items to policy.
6. Optional: `RawItem.summary_is_headline` flag from the source adapters, so `headline_only` need not infer it.
