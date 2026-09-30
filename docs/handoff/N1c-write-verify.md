# N1c: write and verify (draft + check)

Files: `backend/app/modules/newsroom/stages/check.py`, `stages/draft.py`, tests `backend/tests/modules/newsroom/test_check.py`, `test_draft.py`. 56 tests pass, no network.

## check(draft, facts, item, now=None) -> CheckResult
Pure code. `now` is an optional extra argument (tests pin the clock); the contract signature still works. Rules, each giving a plain problem line:
- Figures: every number must appear in the source (title + text, plus the as-of and publish date parts). Facts texts are NOT trusted as a source. Number+unit pairs (crore, lakh, %, km, ...) and day+month dates are matched too, so a changed unit or date fails even if the digits exist elsewhere.
- Proper nouns: capitalised words must be in the source, the source names, or a small allowlist (Pune, PUNE Property, Facebook, our areas, months). Sentence-start words pass only if ordinary English (`COMMON`). `policy.DISCLAIMER` is exempt.
- `policy.BANNED`, `polish.HYPE`, `polish.PHONE`; 16-word runs copied from the source; repeated headline.
- Source name present; link in `draft.link` or text; post length and a `?`; `as of` line.
- Sentence rules: price + forward verb (will, set to, expected to...) is a prediction; builder word + opinion word is endorsement/criticism; transport word + open/operational/running/inaugurated/launched/completed needs the same word in a source sentence that also has a transport word, unless the sentence is negated ("not open yet").
- Stale: older than `MAX_AGE_DAYS` from publish date (or `facts.as_of`); no date at all is a problem.

Known limits: hedged price talk ("may", "could") is allowed; number words ("two lakh") are not checked; proper-noun check is word-level, not phrase-level; it errs on rejecting.

## draft(item, facts, relevance, fmt, llm)
LLM sees only fact texts, area, pillar and as-of date, and returns JSON parts (`title, what, why, check, question`). Code assembles the text so the source line, link, as-of, hashtags and disclaimer are always present. Post: what, "Our view:", "What to check:", "Source: X, as of D. link", question, hashtags. Too long: the check line is dropped. A question without `?` is replaced. URLs in LLM output are stripped. LLM None, raising, or unusable reply gives None. `llm=None` (unavailable) uses `template_draft`, exposed for callers, which also passes `check`.

## Proposed contract changes (not made)
1. `check(..., now: Optional[datetime] = None)` in the contract, so the clock is injectable.
2. Add `evergreen: bool` (or pillar) to `Draft`/`Facts` so education items skip the stale and as-of rules; today they would be rejected for having no date.
3. `RawItem.source` should be a display name ("Pune Mirror"); draft humanises the id (`pune_mirror` -> "Pune Mirror") as a fallback.
4. Add a shared `display_name(area)` and area hashtag map to `policy.py` (draft.py holds its own copy now).
5. Consider a `builders` allowlist/denylist in policy and a `Fact.kind` (figure, date, status) so check can verify specific statuses rather than by wording.
