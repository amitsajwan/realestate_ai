# Marketing pipeline: architecture review

Review date 11 Oct 2026, against the code on `cursor/analyze-and-fix-styling-issues-cacb` (PR #62 merged). It covers one
journey: **the agent gives us photos and a brochure, and we hand back finished reels and posts.** It is written from two
seats: a **solution architect** (shape, data, flow, operations) and a **GenAI architect** (models, grounding, evaluation,
cost, safety). It sits under `docs/ARCHITECTURE.md`. Where it disagrees with that file, this review proposes a change; it does
not make one. How the pipeline works today is in `docs/MARKETING.md`, and the work items are in `docs/CONTENT_PLATFORM.md`.

## 1. Verdict

The back half of the pipeline is sound and should be kept: the creative pipeline, the guards, the approval calendar, the
single way out (`distribution.send` and `publish_ledger`), the reel compositor and the measurement tags. "Code calculates,
models write" is the right rule for a regulated, number-heavy domain. Keeping agents and LangGraph out was also the right
call.

The front half is the weak part. **The journey starts with photos and a brochure, but the system reads neither.**
- **Brochures are not read at all.** No module accepts a PDF, and `requirements.txt` has no PDF library. The word "brochure"
  appears only in hooks that warn buyers about brochures.
- **Photos are stored, scored and enhanced, but never understood.** `photoquality/analysis.py` measures exposure, blur, tilt
  and noise, and that score is advice only. Nothing knows whether a photo shows a kitchen, a façade, a floor plan or a
  builder's render. Reels take photos in the agent's upload order (`reels/listing_reel.py:78`, first 5).

So a campaign is only as rich as what the agent typed, plus MahaRERA and OpenStreetMap. That is the "a plot yields 3 basic
posts" pain in `CONTENT_PLATFORM.md`. The brochure the agent already holds would add configurations, specs, amenities, floor
plans and renders, and today we ignore it.

**Main recommendation:** add one **intake stage** in front of the existing pipeline. It turns photos and a brochure into a
**listing kit**: a catalogue of labelled media plus candidate facts, each with a source. The kit feeds the fact sheet and the
creative pipeline that already exist. Nothing downstream of the Brief has to change shape.

## 2. The journey, today and target

```
TODAY
 agent photos ─► uploads/images ─► quality score (advice) ─┐
 agent text / voice ─► ai_listing extractor ─► listing ────┼─► propertyfacts (listing + MahaRERA + OSM + calc)
 brochure ─► (dropped; the agent may retype parts)          │        │
                                                            │   Brief per angle ─► creative pipeline ─► cards
                                                            └─► photos in upload order ─► reels ─► calendar ─► approve ─► send

TARGET
 agent photos ─┐                ┌─► media catalogue: kind, room, hero rank, quality, flags, source, rights
 brochure PDF ─┼─► INTAKE ──────┤
 text / voice ─┘   (worker job) └─► fact candidates: value, page, bbox, level = builder_claim
                                          │
                     cross-check with MahaRERA / listing (existing levels; conflicts become an Issue)
                                          │
                     fact sheet (property_facts) + media catalogue  =  LISTING KIT  ──►  agent confirms in Studio (one screen)
                                          │
              angle planner picks angles AND the media each angle needs (needs: kitchen photo, floor plan, exterior)
                                          │
                     creative pipeline / reel director (as today) ─► guards ─► vision review ─► calendar ─► approve ─► send
                                                                                                      │
                                                                           insights ─► "what worked" ─► angle and hook choice
```

## 3. Solution architect findings

Severity: **High** blocks the journey or carries legal or brand risk. **Medium** costs quality or money. **Low** is hygiene.

| # | Finding | Evidence | Severity | Recommendation |
|---|---|---|---|---|
| S1 | The brochure is not an input | no PDF handling; `grep -ri brochure app` finds only hook text | High | Intake stage (§5). Store the original PDF and treat it as a source document with page references. |
| S2 | Photos are not understood | `photoquality` measures pixels only; reels use upload order | High | A media catalogue with a kind and room per photo, a hero rank, duplicate groups and flags (§5.2). Angle and reel planners then ask for media by role. |
| S3 | No MahaRERA QR code or registration line on project ads | no QR code anywhere in `app/`; the reel's closing card shows the agent's RERA number only | High (confirm) | MahaRERA's advertisement orders require the project registration number, and the QR code since 2023, on project ads. Confirm the current order, then add a QR and registration badge layer to cards and the reel end card whenever the fact sheet holds a project RERA number. |
| S4 | Builder renders could pass as real photos | nothing marks a brochure render or a 3D image | High once S1 ships | Each media item carries `source: agent_photo | brochure_render | brochure_plan | brochure_photo`. Renders always carry "Artist's impression" on screen. A walkthrough reel uses agent photos only, unless a reel is marked "project preview". |
| S5 | Two ways to post a listing | pack posting (`social/service.py`) and campaigns through the calendar; `MARKETING.md` §8 | Medium | Already an open decision. Recommend retiring direct pack posting: keep the pack as a WhatsApp kit and send every post through the calendar. It is one gate and one dedupe point, and measurement then covers every post. |
| S6 | The owner is the only approver | `CALENDAR_OWNER_IDS`; agents cannot see approval state | Medium (High at 10+ agents) | Two-step approval: the agent approves their own listing's content (they own the facts), and the owner approves brand and channel fit. Show the state to agents. The owner can delegate per agent once trust is earned. |
| S7 | Facts live in three places | `reels/trend.py FACTS`, `knowledge/areas.py`, `property_facts` | Medium | X-6 (`verified_facts`). Brochure facts go into the same fact record (PF-1 shape) with a new level, not into a fourth store. |
| S8 | Media lives on one VM disk | `uploads/` under `settings.upload_directory`; Meta fetches from `PUBLIC_MEDIA_BASE_URL` | Medium | Move uploads, renders and brochures to object storage (GCS) behind `platform/media`, with the same URL contract and lifecycle rules for render variants. Back up originals. This also lets a second render worker run later. |
| S9 | Rendering is serial and CPU bound | one reel job at a time per process; `marketing_runs` runs facts, posts, slides and walkthrough in one job | Medium | Keep the Mongo status machines (no Temporal), but split the run into steps that record their own progress (`facts → kit → plan → assets → reels`). A failed reel then never re-runs the LLM steps, and reels can render on a separate worker. |
| S10 | Content is not marked stale when the listing changes | LC-9 still open | Medium | When a listing edit or a new upload changes the kit's hash, mark its planned rows stale. Approved rows stay as approved, with a "listing changed since approval" chip. |
| S11 | No consent or privacy check on photos | nothing checks faces, people, number plates, or visible documents and phone numbers | Medium | Flags in the media catalogue (§5.2). Blur or exclude by default. Our DPDP Act 2023 duties apply to a seller's home interiors and the people in them. |
| S12 | Hindi and Marathi stop at the voice | no Devanagari font in reels; walkthrough caption built in English | Low to Medium | Already in `MARKETING.md` §9. Use Noto Sans Devanagari with HarfBuzz shaping (Pillow's `raqm` layout). |

## 4. GenAI architect findings

| # | Finding | Evidence | Severity | Recommendation |
|---|---|---|---|---|
| G1 | No call log, so no tracing and no cost view | `llm_calls` appears in `ARCHITECTURE.md` §8 but nowhere in `app/` | High | Build it before adding vision and brochure calls: task, prompt version (`prompts.VERSIONS` exists), model, provider, latency, tokens, outcome, and which guard rejected the output. A TTL index keeps it small. It is the base for every point below. |
| G2 | Every failure becomes `None` | `LLM.json` "or None on any failure" (`platform/llm.py`) | Medium | Return an outcome type (`ok | quota | timeout | invalid | refused`). Fallbacks stay the same, but Studio can say "AI was busy, rules draft used" and the log can tell quota from bad prompts. |
| G3 | Free-tier models and failover make quality vary | default `openai/gpt-oss-120b` on Groq, a comma-separated failover list; `ModelHealth` rests models | Medium | Route models per task (already the target in `ARCHITECTURE.md` §8). A small, cheap model classifies and filters. Copy, the brochure reader and the vision tagger get a pinned, paid, stable model per task, with the free model as failover only. Pin model ids in the prompt-version tags so a model change shows up as a version change. |
| G4 | No document understanding | no PDF or vision extraction | High (the gap itself) | Brochure reader (§5.1): a text layer first; a vision model per page for tables, plans and image-only pages; schema-checked output where **every value cites a page and a box**; deterministic validators after it. |
| G5 | Vision is used only to review finished cards | `photoquality/vision_review.py`, advice only, at most 3 images, Groq | Medium | Use the same provider chain to tag input photos (§5.2), batched and cached by content hash, as the review already is. The review stays advice; tagging feeds planning. |
| G6 | Brochure claims need their own trust level | the levels are official, measured, corroborated, single, conflict | High | Add `builder_claim`. It is usable only for **non-numeric, attributable** facts (amenity names, specification items, configuration labels), always worded "as per the builder's brochure". Never usable for possession date, unit counts, carpet area or price when MahaRERA or the listing has a value; a disagreement there becomes a conflict `Issue`. Carpet area from the brochure is checked against the MahaRERA unit table where we have it. |
| G7 | Evaluation covers copy, not perception | golden tests exist for prompts and guards (`tests/modules/creative`), none for extraction from images | Medium | Build a small labelled set: 20 brochures and about 300 photos from pilot agents, with consent. Measure field-level precision and recall for the brochure reader, and accuracy for room and kind tags. Run it in CI against recorded responses and nightly against the live model. Gate a model or prompt change on it. |
| G8 | Approvals and edits are not used as feedback | approve, skip, caption edits and redo notes are stored, not learned from | Medium (cheap) | Log every human decision with the prompt version: approved unchanged, approved after edit (keep the diff), skipped with a reason, redo with a note. That gives the first quality metric before Meta insights mature ("share approved unchanged" per prompt version and angle). It also gives few-shot examples for the copywriter. No fine-tuning yet. |
| G9 | The voice-over sounds machine-made | per-line TTS (`reels/voice.py`), noted in `MARKETING.md` §9 | Medium | One TTS take per script, cut by SSML marks or timepoints, and music ducking. Keep Chirp 3 HD (free tier covers the volume). No voice cloning without a consenting speaker. Set Meta's AI-content label for synthetic voice. |
| G10 | No per-listing LLM budget | PM-10 / LC-5 still open | Medium | Count calls and tokens per `marketing_run` from the call log (G1). When the budget is spent, the rest of the run uses the deterministic path. Vision tagging is cached per photo hash, so a re-run is nearly free. |
| G11 | Prompt injection through the brochure | not yet exposed; it will be once PDF text reaches a prompt | Low now, Medium after S1 | Brochure text is data. Put it in a delimited block, never in the system prompt. The reader's output is schema-only, and nothing it returns can change instructions, links or channels. The guards already refuse URLs and phone numbers not in the facts. |

**Kept as is (the GenAI seat agrees with `ARCHITECTURE.md` §8):** no agents or LangGraph in content flows; no model as the
final judge (the rule-based critic blocks, the AI review advises); no retrieval search (RAG) for claims; no AI publishing. The
intake stage is a fixed pipeline too: read, validate, cross-check, ask a person. It is not an agent.

## 5. Proposed design: the intake stage

A new content-layer module, `modules/intake/`, added to `.importlinter` below `propertyfacts`. The worker runs it as a step
of the `marketing_runs` job, and it can also be triggered on upload. It owns the `listing_media` and `brochures`
collections and writes fact candidates through `propertyfacts` (one writer per collection).

### 5.1 Brochure reader
1. Upload a PDF, up to 40 pages and 30 MB, on the listing's marketing screen. Store the original under `uploads/brochures/`
   (object storage later, S8). Keep its hash, so the same brochure is read once.
2. **Text layer first** (`pypdfium2` or `pymupdf`; licence check needed: PyMuPDF is AGPL, pypdfium2 is Apache/BSD). Pages with
   too little text are rasterised at 150 dpi for the vision model.
3. **Extraction**, one schema per page type. A cheap call classifies each page: `cover | amenities | specifications |
   floor_plan | master_plan | location_map | pricing | legal | render`. Then that type's schema is filled. Every field holds
   `value`, `page`, `bbox` and `quote` (the exact words seen).
4. **Validators in code:** the quote must appear in the page text or the OCR; numbers parse with `platform/text`
   (lakh/crore, sq ft, BHK); the RERA number matches the MahaRERA format and resolves through `registration.lookup`.
5. **Cross-check** against the listing and MahaRERA with the existing levels, plus `builder_claim` (G6).
6. **Image harvest:** floor plans, master plan and renders are cut from pages into the media catalogue, with the source
   marked (S4).
7. **Studio "Confirm the kit"** screen: the agent sees each fact with its page thumbnail and ticks it, fixes it or drops it.
   One screen, one tap per fact. This is where "a person confirms" (`CONTENT_PLATFORM.md` rule 2) stays cheap.

### 5.2 Media catalogue (photos and harvested images)
One document per media item:
`{listing_id, url, hash, source, kind: exterior|interior|view|amenity|floor_plan|master_plan|map|render|document,
room: living|kitchen|bedroom|bath|balcony|lobby|..., quality: {score, issues}, hero_rank, dup_group,
flags: [face, person, number_plate, phone_or_text, watermark, portal_logo], usable: bool, tagged_by: model@version}`

- Pixel checks stay in OpenCV (`photoquality.analysis`). A vision model, batched by 3 as Groq allows, gives `kind`, `room`
  and `flags`. Results are cached by hash.
- Duplicate groups come from a perceptual hash, in code.
- `hero_rank` is computed in code from kind, quality and a fixed preference order (exterior or living room first, a portal
  watermark never).
- `usable=false` for portal watermarks (the existing rule: portal photos are never reused), unblurred faces and visible
  phone numbers.

### 5.3 What changes downstream
- **Angles declare media needs** next to fact needs (CA-1 already declares facts): "amenities" needs amenity photos or the
  amenities page, "size made real" needs a floor plan, "walkthrough" needs 4 or more interior rooms. An angle without its
  media is skipped, not faked.
- **The reel director** orders scenes by room flow (exterior, living, kitchen, bedrooms, balcony or view), not by upload order.
  A beat's line is matched to the photo of the room it talks about.
- **The Brief** carries media refs by role. `listing_media_refs` already exists on the listing brief (`creative/listing_brief.py`).

## 6. Work items

The same format as `CONTENT_PLATFORM.md`. Sizes: S = under a day, M = 1 to 3 days, L = more.

| ID | Item | Done when | Size | Needs |
|---|---|---|---|---|
| AR-1 | `llm_calls` log in the gateway, with outcomes (G1, G2) | Every creative, reel and vision call writes a row; Studio Admin shows calls, failures and tokens per day | M | |
| AR-2 | Per-task model routing (G3) | `AI_MODEL_<TASK>` settings; the vision tagger and brochure reader have pinned models | S | AR-1 |
| AR-3 | MahaRERA QR and registration badge (S3) | Current MahaRERA advertisement order confirmed and cited in `docs/`; cards and reel end cards carry the QR whenever a project RERA number is known. BUILT 11 Oct 2026: Order 46C/2025, `MARKETING.md` §4 "MahaRERA on our ads" | M | |
| AR-4 | Media catalogue with pixel checks, perceptual hash and hero rank, no AI yet (S2) | `listing_media` filled on upload; reels choose photos by hero rank, then upload order | M | |
| AR-5 | Vision tagging: kind, room, flags (G5, S11) | Tags on every new photo; 85% or better room accuracy on the labelled set (AR-9) | M | AR-1, AR-4 |
| AR-6 | Brochure upload and text-layer reader (S1, G4) | A text PDF gives amenities, specs and configurations with page and quote; validators pass | L | AR-1 |
| AR-7 | Vision pages, floor plans and image harvest (G4, S4) | Image-only pages read; floor plans and renders appear in the catalogue with their source, and renders get "Artist's impression" | L | AR-5, AR-6 |
| AR-8 | `builder_claim` level and the Confirm-the-kit screen (G6) | Brochure facts appear in Studio with page thumbnails; confirmed ones reach Briefs with attribution | M | AR-6 |
| AR-9 | Labelled evaluation set and CI gate (G7) | 20 brochures and 300 photos labelled, with consent; a score per model and prompt version in CI | M | AR-5, AR-6 |
| AR-10 | Angles declare media needs; room-flow reel order (§5.3) | Gulmohar City-style runs skip angles without media; walkthrough scenes follow the room order | M | AR-5 |
| AR-11 | Approval and edit feedback log (G8) | "Approved unchanged" rate per prompt version and angle in Studio | S | AR-1 |
| AR-12 | Retire direct pack posting (S5) | One posting path; the pack remains a WhatsApp kit | S | owner decision |
| AR-13 | Two-step approval: agent, then owner (S6) | Agents see and approve their own rows; the owner sees agent-approved rows first | M | owner decision |
| AR-14 | Object storage for media (S8) | Uploads and renders on GCS with the same public URL contract; originals backed up | M | |

**Order (owner, 11 Oct 2026): best output first.** The call log (AR-1) and model routing (AR-2) wait until after the pilot.
First the items that change what a buyer sees: AR-4 (best photos, no duplicates, no blurry ones), then the reel and voice fixes
in `MARKETING.md` §9, then AR-6 and AR-8 (the brochure, which is the main source for new projects; see below), then AR-5,
AR-7 and AR-10. AR-3 follows the registration rule below. AR-12 and AR-13 wait on the owner, and AR-14 waits until a second
worker is needed.

**New projects without a MahaRERA record.** Many new projects have no record we can read yet, so the brochure and the agent
are the only sources. The pipeline must work without MahaRERA:
- Facts come from the listing (`official` for the agent's own offer) and the brochure (`builder_claim`, attributed). Nothing
  is shown as "MahaRERA checked", and the angles that need MahaRERA (MahaRERA check, possession moved) are skipped.
- The QR code and registration line (AR-3) appear only when the fact sheet holds a registration number.
- A project the brochure shows a RERA number for, but that MahaRERA does not return, is held for the agent to confirm. It is
  not posted as registered.
- Under section 3 of the RERA Act, a project that needs registration (more than 500 sq m of land or more than 8 units) may not
  be advertised before it is registered, and an agent may not market it. Small projects and resale homes are outside this
  rule. So "no record" should ask the agent one question, "Is this project registered, or exempt?", and keep the answer on
  the listing.

## 7. Decisions for the owner

1. **Brochure facts in posts.** Allow attributed `builder_claim` facts (amenities and specs, worded "as per the brochure"), or
   keep brochures as a media and layout source only? This review recommends allowing them, attributed and non-numeric.
2. **Renders in reels.** Allow builder renders only in a separate "project preview" reel with "Artist's impression" on screen,
   or never use them?
3. **Paid models for perception.** Brochure reading and photo tagging need a stable vision model. Free tiers rotate and
   rate-limit. Expected volume is low (one brochure and about 20 photos per listing, cached), so the cost is small, but it is
   a new bill.
4. **Who approves.** Two-step approval (AR-13) or owner-only for the pilot?
5. **Pack posting.** Retire it (AR-12)?

## 8. Not recommended

- An "AI marketing agent" that reads the brochure and posts. The pipeline stays fixed, and a person approves.
- Generative image editing of property photos: sky replacement, virtual staging, removing objects. `photoquality/enhance.py`
  deliberately changes tone and geometry only. Keep it that way unless staging is clearly labelled and the owner decides
  otherwise.
- A vector database for brochures. Facts are extracted into records with citations, not retrieved at answer time.
- Fine-tuning. Prompt versions, few-shot examples from approved posts (G8) and the evaluation set come first.
