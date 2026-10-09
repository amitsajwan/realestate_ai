# Buyer-intent radar

Status: **v1 LIVE** (YouTube + pasted posts, ran in production 2026-10-09). **v2-v4 BUILT, OFF until deployed** (2026-10-10): every
stage below is in `backend/app/modules/radar/`; sources need their keys (`YOUTUBE_API_KEY`; Reddit works keyless or with
`REDDIT_CLIENT_ID`/`_SECRET`; Instagram uses the Page token; RSS feeds are added as watches). Turn on with `RADAR_ENABLED=true`.
Follows `docs/ARCHITECTURE.md`; the discovery agent is the one exception to §8 there, recorded in §8.

**Where the build differs from the design below** (the design text is kept where it still holds):
- `own_comments` is not a source: `engage` already reads, answers and records our own Page/Instagram comments as leads.
- L2 is a k-nearest-neighbour vote (softmax over cosine, k=9) against the example bank, not a fixed similarity threshold:
  e5 similarities sit in a narrow 0.7-0.95 band. It only drops a comment when the vote for "home need" is below 0.18.
- The embedder is `multilingual-e5-small` (ONNX, quantized) run with onnxruntime + tokenizers in the **worker only**; pasted
  posts in the web process skip L2. A character n-gram hash embedder takes over if the model cannot load.
- Near-duplicates merge only within one person (`person_key`); different people asking the same short question are separate leads.
- Themes use average-linkage agglomerative clustering in numpy (no HDBSCAN dependency).
- The follow-up flow is a five-state machine checkpointed on the signal in Mongo, not LangGraph; nothing is sent by it.
  WhatsApp sends stay out until WhatsApp is turned on.
- The scorer refit is a MAP logistic regression pulled towards the live weights, so it starts at 60 labels, not 200.
- Every reply link is a per-lead short link `/r/<code>` (frontend `app/r/[code]`), so clicks are credited to the lead,
  its watch (bandit) and its source.
- Discovery and the weekly jobs run inside the `radar` worker loop (times kept in `radar_runs`), not a second worker.

## 1. What it does

It finds people who are publicly asking about homes in Pune ("2BHK price?", "Wagholi mein flat under 60L"), works out what they
want, matches them to our listings, drafts a helpful reply, and routes them to the right agent's review queue. **A person sends
every reply.** The radar never posts, DMs or likes anything.

Why: we have no followers and no ad budget, so we go to the people who are already asking. Each find is also proof for agents:
"these people asked about your area this week".

## 2. What we take from the market

| Tool | What it does well | What we take | Where we go further |
|---|---|---|---|
| Octolens, Syften | AI relevance filter instead of plain keyword alerts | A cascade: cheap filter first, then a model | Hindi, Marathi and Hinglish; real-estate entities |
| GummySearch | "Audience" research: finds the communities, then the themes people ask about | A discovery agent that finds where buyers talk; demand themes | Per area and per project, fed back into content |
| ReplyGuy, Redreach | Drafts a reply for each post | Drafts with a human in the loop | Grounded in verified listing facts, with a guard and a critic |
| Brand24, Brandwatch | Volume trends, sentiment, an influence score | Demand trends per area | Turned into agent reports and reel topics |
| Portals (99acres, MagicBricks) | Sell buyer intent to agents | Leads routed to the agent for that area | Found outside the portals, before the buyer goes to one |
| Sell.Do, LeadSquared | Lead lifecycle and follow-up | Statuses through to conversion | Feedback from outcomes trains the scorer |

**What makes us better:** we cover the places they don't (YouTube comments on Pune project videos, Instagram hashtags),
understand Indian languages and real-estate terms, match each person to a real listing, and learn from which leads convert.

## 3. Shape

One module, `backend/app/modules/radar/`, in the **buyers** domain. One worker loop with the same lease, heartbeat and pause
switch as `engage`. No new service, queue or database.

```
            ┌──────────────── DISCOVERY AGENT (read-only, daily) ─────────────────┐
            │ finds new videos / hashtags / threads / subreddits per area+project │
            │ proposes watches ──▶ budgeted by a multi-armed bandit               │
            └───────────────────────────────┬─────────────────────────────────────┘
                                            ▼
 SOURCES (adapters)        DETERMINISTIC PIPELINE (status machine in Mongo)
 youtube ─┐   ┌────────┐ ┌──────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌──────────┐ ┌─────────┐
 ig_tag  ─┼──▶│collect │▶│ dedupe + │▶│ L1 rules  │▶│ L2 embed  │▶│ L3 LLM    │▶│ resolve +│▶│ match + │
 reddit  ─┤   └────────┘ │ identity │ │ (free)    │ │ similarity│ │ extract   │ │ enrich   │ │ score   │
 own     ─┤              └──────────┘ └───────────┘ └───────────┘ └───────────┘ └──────────┘ └────┬────┘
 manual  ─┘                                                                                       ▼
                ┌────────────┐   ┌───────────────┐   ┌──────────────┐   ┌───────────────────────────────┐
  learn ◀───────│ outcomes   │◀──│ human sends   │◀──│ review queue │◀──│ draft → guard → critic (LLM)  │
 (scorer,       │ click/WA/  │   │ (copy, open)  │   │ per agent,   │   └───────────────────────────────┘
  bandit,       │ skip label │   └───────────────┘   │ best first   │
  few-shots)    └────────────┘                       └──────────────┘
                                    │
                                    └──▶ DEMAND INSIGHTS: themes per area/week → agent report, reel topics
```

## 4. Sources: the extension point

Each source is one file implementing one protocol. **A new channel is one adapter plus one config entry.**

```python
class Source(Protocol):
    name: str
    async def fetch(self, watch: Watch, since: datetime) -> list[RawSignal]: ...
    async def discover(self, query: str, area: str) -> list[WatchProposal]: ...   # used by the discovery agent's tools
    def reply_url(self, sig: RawSignal) -> str: ...

@dataclass
class RawSignal:
    source: str; external_id: str; url: str
    author_id: str | None; author: str | None; text: str; posted_at: datetime
    context: str          # video title / caption / thread title, so a bare "price?" is understood
    thread: list[str]     # parent and sibling replies (was it already answered? did someone else reply?)
    watch_id: str
```

| Adapter | Access | Phase |
|---|---|---|
| `youtube` | Data API v3, free key (`commentThreads`, `search`) | 1 |
| `manual` | Operator pastes a link and text (Facebook groups, WhatsApp forwards) | 1 |
| `ig_hashtag` | Graph `ig_hashtag_search` with our business account (30 hashtags a week) | 2 |
| `own_comments` | Reads what `engage` stores | 2 |
| `reddit` | Public API | 3 |
| `google_alerts`, forums | RSS | 3 |

**Never:** scraping Facebook or Instagram profiles or groups, logged-in bots, auto-DMs. Meta bans the page, and it is what makes
the competitors' accounts get shut down.

## 5. The pipeline: a classification cascade

Each layer is cheaper than the next and removes most of what reaches it, so the LLM sees only about 2-5% of comments. That
matters because we run on free-tier models.

1. **collect**: per active watch, from its cursor.
2. **dedupe + identity**: unique `(source, external_id)`; near-duplicates (the same person pasting the same question on 5 videos)
   are caught with MinHash/SimHash on normalised text. A `person_key` (source + author_id, later linked across sources by handle)
   lets a repeat asker raise the score instead of making a new lead.
3. **L1 rules (free)**: script-aware normalisation (Devanagari ↔ Latin transliteration, "2 bhk"/"2bhk"/"two bedroom" made the
   same); home words in EN/HI/MR; reject brokers (phone number + "deal", "contact for", many posts a day), spam and our own replies.
4. **L2 embeddings (cheap, local)**: a multilingual sentence-embedding model run in process (`multilingual-e5-small` class, CPU,
   no API) compares each comment with a bank of labelled intent examples ("kitna hai 2bhk", "possession kab", "loan possible?").
   Comments below the similarity threshold stop here. The bank grows from operator labels (§7). This is what keeps quality up
   while LLM cost stays near zero.
5. **L3 LLM extract**: `llm.json("radar.classify", schema=Intent)` through the existing gateway (Groq/Gemini failover), with
   few-shot examples drawn **dynamically** from the most similar labelled comments (embedding kNN). Output fields:
   `role` (buyer, renter, investor, broker, seller, noise), `intent` (0-1), `stage` (exploring, comparing, ready, post-visit),
   `area`, `project`, `bhk`, `budget_min/max` (INR, normalised by `platform.text`), `timeline`, `language`, `question`,
   `answered_already`. A schema failure gets one repair retry, then the comment is marked `noise`, never a guess.
6. **resolve + enrich**: `project` and `area` are linked to the MahaRERA register and our area list (fuzzy match plus aliases), and the
   video's own project becomes the context ("price?" under a Kolte Patil Life Republic video is about that project).
7. **match + score**: hybrid retrieval over our listings: hard filters (area, BHK, budget ±15%) plus embedding similarity on the
   request vs the listing text. Score:
   `p(convert) = σ(w · features)`, logistic regression over intent, stage, freshness decay (half-life 48h), match quality,
   source and watch weight, repeat asker, already answered (negative), thread popularity.
   It starts with hand-set weights and is refitted weekly from outcomes once there are ~200 labelled items.
   (Logistic regression, not a black box: the operator sees *why* a lead ranks first.)
8. **draft → guard → critic**: the draft comes from a callback wired in from `conversations/knowledge` (same facts as chat and
   engage). Rule guard: `valid_reply`, no hype, no phone numbers, the listing link present, language matches the asker.
   An LLM critic scores helpfulness and "sounds like a person, not an ad", and a low score gets one rewrite. The rules block;
   the critic only advises (ARCHITECTURE §8). A template is used if both fail.
9. **review**: per agent and area, best first, with the reason shown ("ready buyer, 2BHK ≤60L Wagholi, 3 listings match, 5h old").
   One tap copies the draft and opens `reply_url`.
10. **outcome**: tracked link (`channel=radar_<source>`), WhatsApp start, or operator mark → `converted`. `skipped` with a reason
    (broker, already bought, wrong area) is a training label.

## 6. Agents: where they help and where they don't

| Job | How | Why |
|---|---|---|
| **Discovery**: find where Pune buyers talk now (new project videos, active hashtags, threads, subreddits) | **An agent**: a tool-calling loop with read-only tools: `youtube.search`, `ig.hashtag_search`, `reddit.search`, `register.projects(area)`, `watches.stats()`, `propose_watch()` | Open-ended exploration where the next step depends on the last result. It can only *propose* watches; it cannot post or spend beyond its quota. |
| **Watch budget** | **Thompson-sampling bandit** over watches (Beta prior on hits/conversions per quota unit) | Spends the daily YouTube and Instagram quota where buyers are, and keeps testing new watches. Best-known algorithm for this explore/exploit problem. |
| **Classify, match, score, draft** | **Fixed pipeline** (§5) | It has to be predictable, cheap and testable, and it is the part that reaches buyers. An agent here adds cost and risk and gains nothing. |
| **Demand insights** | Weekly batch: cluster the embeddings of a week's buyer questions (HDBSCAN), LLM names each cluster | "Wagholi: 34 asked about possession delays" → agent report, FAQ entries in `knowledge`, reel topics |
| **Follow-up** (later) | A small LangGraph graph (state: no reply → nudge after 24h → answered → handed to agent → visit), with a human approving each send | It branches more than 3 ways and waits days between steps, which is what LangGraph's checkpointed state is for (ARCHITECTURE §8 threshold). |

**Framework choice:** the discovery agent is a hand-written tool loop on the existing gateway, with about 6 tools, so it needs no new
dependency. LangGraph comes in only for the follow-up flow, when it is built. The rule stays: **no agent publishes.**

## 7. Learning loop (what makes it better every week)

- **Labels for free**: every operator `sent`, `skipped`, reason, edit to the draft, and conversion is stored.
- **Active learning**: each day the queue includes ~5 items the model is *least sure* about (intent near 0.5), marked "help me
  learn". Their labels improve the scorer the most.
- **Example bank**: labelled items feed L2 (embedding thresholds) and L3 (dynamic few-shots) at once, with no fine-tuning.
- **Draft learning**: operator edits are diffed, and recurring edits ("drop the first line", "always mention RERA no.") become prompt rules.
- **Weekly refit**: logistic-regression weights and bandit priors. An offline eval set (`backend/tests/modules/radar/fixtures`)
  must not get worse before new weights ship.
- **Metrics** in the studio: found → shown → sent → clicked → WhatsApp → visit, per source, watch and area; precision@10 of the
  queue; LLM calls per lead.

## 8. Data (owned by `radar`; only it writes)

| Collection | Holds |
|---|---|
| `radar_watches` | `{source, kind, value, area, project_id?, origin: manual\|agent, active, cursor, alpha, beta, quota_used}` |
| `radar_signals` | Raw fields, `person_key`, `simhash`, `embedding` (384 floats), `Intent`, matches, `features`, `score`, `why`, draft, critic, status, `agent_id`, label |
| `radar_examples` | Labelled example bank: text, embedding, label, language |
| `radar_models` | Versioned scorer weights and thresholds, with eval results |
| `radar_themes` | Weekly demand clusters per area |

Single Mongo with no vector search (ARCHITECTURE §1): similarity is computed in process with numpy over the example bank (a few
thousand vectors take under a few milliseconds). The same in-process approach that §8 plans for vector search.

## 9. Boundaries, wiring, config

- `radar` (buyers) imports `inventory` and `platform/*` only. The draft writer and critic come in as callbacks from
  `conversations/knowledge` in `app/wiring.py`.
- New platform pieces: `platform/youtube.py` (client) and `platform/embed.py` (multilingual embedder, loaded once per process).
- Public API: `loop`, `router`, `configure`, `top_signals(db, agent_id, area?)`, `area_demand(db, area)` (for agent reports).
- Routes: `GET /radar/signals`, `POST /radar/signals/{id}/label`, `GET|POST /radar/watches`, `POST /radar/manual`, `GET /radar/metrics`.
- Worker: `radar` (every 2h; discovery daily, refit / draft rules / themes weekly). Pause switch `radar_paused`.
- Config `RADAR_*`: `ENABLED`, `INTERVAL_SECONDS`, `MIN_SCORE`, `DAILY_LLM_CAP`, `DAILY_SEARCH_CAP`, `VIDEOS_PER_CYCLE`, `SOURCES`,
  `L2`, `CRITIC`, `ROUTE_BY_AREA`, `DISCOVERY_ENABLED`, `OWNER_AGENT_ID`; `EMBED_MODEL_DIR`, `EMBED_BACKEND=hash` (no model).
- Routes (built): `GET /radar/signals` (owner: all; agent: theirs), `POST /radar/signals/{id}/label`, `GET /radar/followups`,
  `POST /radar/followups/{id}`, `GET|POST /radar/watches`, `PATCH /radar/watches/{id}`, `POST /radar/manual`, `GET /radar/themes`,
  `GET /radar/runs`, `GET /radar/metrics`, public `GET /radar/r/{code}`. Studio: Queue, Follow-ups, Demand, Watches, Health tabs.
- **Beyond ARCHITECTURE §8:** one read-only tool-calling agent (discovery). This needs the owner's OK and a line in §8 once built.

## 10. Build order

1. **v1 (first leads)**: module, `youtube` + `manual`, L1 + L3 (skip embeddings), match, hand-weighted score, draft + guard,
   review tab with copy/open/label. Watches seeded by hand: the top ~50 Pune project videos per area.
2. **v2 (smart)**: `platform/embed.py`, L2 + dynamic few-shots, identity and near-duplicates, critic, `ig_hashtag` + `own_comments`,
   outcome tracking, metrics.
3. **v3 (self-improving)**: discovery agent + bandit, weekly refit, active learning, demand themes into agent reports, routing by agent.
4. **v4**: `reddit` and RSS, LangGraph follow-up flow with human-approved sends over WhatsApp.
