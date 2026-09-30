# D1 Creative studio

`backend/app/modules/creative/` replaces "template plus light polish" with four layers, each with its own prompt, rules and tests.
It imports only `marketing.images` (fonts, logo, wrap, save_jpeg), `marketing.polish` (HYPE, PHONE) and a duck-typed LLM (`json`, `text`; `GroqLLM` fits).

## Layers
| Layer | File | In -> out |
|---|---|---|
| Strategist | `strategist.py`, `hooks.py` | Brief + audience + channel -> `Angle` (pain, idea, hook <= 9 words, proof from facts, format, CTA). Six rotating hook patterns: mistake, number, myth, nobody, comparison, question. |
| Copywriter | `copywriter.py`, `guards.py` | Angle -> `Copy` (cover hook, support line, slides <= 14 words, caption first line <= 125 chars, body, question CTA, hashtags, optional Hinglish/Marathi caption variants). |
| Art director | `art_director.py`, `catalog.py` | Copy -> `Design` (layout, palette, photo, emphasis words). Avoids the last two layouts. |
| Critic | `critic.py` | Rules on the copy and on the rendered pixels (contrast, margins, truncation, orphans, density, dead space, repeat layout); optional LLM critique (advice only). |

The LLM proposes, code disposes: every LLM field is validated and replaced by its rule-based draft when it fails (length, hype, phone, price, prediction, personal name, URL, filler, any number not in the facts, proof not in the facts, impossible format).

## How to call
```python
from app.modules.creative import make
from app.modules.creative.models import Brief
brief = Brief(topic="Possession date", short="possession date", facts=["The agreement should state the possession date."],
              tip="Ask for the date in the agreement, in writing.", prefer="single")   # prefer is optional
pack = await make(brief, "buyer", "instagram", llm, seed=7, recent_layouts=["photo_led", "quote_tip"], out_dir=Path("uploads/creative"),
                  languages=(), llm_critic=False)
pack.images   # list of JPEG paths (cover first; a carousel has cover + slides + closing)
pack.caption, pack.hashtags, pack.alt_text, pack.design, pack.angle, pack.report, pack.variants, pack.used_llm, pack.attempts
```
`llm=None` runs the deterministic path (same guards, same layouts). With an LLM: attempt 1, then one regeneration with the critic's feedback, then the rule path; the best attempt is returned and `pack.report["ok"]` says whether it is clean.
Instagram is 1080x1350, Facebook 1080x1080. Brief fields carry structure (stat, myth/truth, options, messy/clean, steps, tip); a format is only chosen if the brief has its material. Hand the integrator's calendar entries over as Briefs (title -> topic/short, points -> steps, body facts -> facts).

## Layouts (8) in `layouts/`
big_number, myth_fact, checklist (cover + slides + closing, progress dots, swipe cue), poll, before_after, photo_led, product_showcase (drawn phone, INTERESTED comment, lead card), quote_tip. Four palettes: navy_gold, navy_teal, navy_coral, cream.
All text is logged (box, size, colour, sampled background) and proven inside the 84 px margins, so nothing is cut by Instagram's 3:4 grid crop (tested on the 1012 px centre).

## Design review
`python -m app.modules.creative.samples <dir>` renders 14 Instagram packs (8 buyer, 6 agent, 3 carousels) and 6 Facebook ones, plus contact sheets. Final sheets: `docs/brand/creative-samples/`.

## Known limits
- Text on cards is English/Latin only (Pillow cannot shape Devanagari); Hinglish/Marathi exist as captions only.
- Rule-path hooks are template-filled and read mechanically when `short` is awkward ("The buyer comments mistake that costs agents leads"); give Briefs good `short` values or `hooks={...}`.
- Stock photos are generic, labelled "Illustrative photo"; only five are bundled.
- The phone mock shows sample data, labelled as an illustration; it is not a screenshot of the real app.
- Facts the brief does not list cannot appear; the critic catches digits only (it cannot detect an invented non-numeric claim).
- Not wired to the calendar, router or storage.

## Next
Feed real product screenshots into the phone mock, more photos (Pune-specific, licensed), a hook A/B log fed by reaction data, Devanagari cards via the Chrome-rendered path, and a per-post palette memory (only layouts are remembered today).
