# Buyer mind: one thinking agent behind every lead and every chat (2026-11-18)

## Why
Every AI part we run today is a fixed pipeline: our code picks the steps and the model fills one blank each time (chat/agent.py,
brochure reading, reel narration, the newsroom). That is right for publishing, but it is why a lead still needs a person to work
out who the buyer is and what to say. Rahul Thombare asked for Fiore Phase 2A's floor plans at 22:15 and got nothing for a day
(lead-follow-up.md); had someone looked, they would also have seen that the project's possession date is after the date he wants
to move in. The owner (2026-11-18): an agent that understands the buyer, thinks as a person would, gets what they asked for, and
does it the same way on the website chat, WhatsApp and DMs.

## What it is
One **buyer mind** in the conversations domain, used by every channel. It keeps one **buyer profile** per person and works in two
speeds:

| | Fast mind (in the chat) | Deep mind (in the background) |
|---|---|---|
| When | every buyer message | just after the chat reply goes out, and on every new form lead |
| Time | 2-4 s (the buyer is waiting) | as long as it needs, within a step and token budget |
| Does | reads the profile, answers from what we already know, asks the one question that matters for this buyer | updates the profile, looks things up, checks facts, notices problems, prepares the next move |
| Who sees it | the buyer | the agent, as the Lead Brief in Studio |

The deep mind is a tool loop: the model reads the lead, plans what it needs, calls read-only tools, reads what came back,
reflects ("does this answer them? is anything wrong or missing?") and either looks again or writes its result. Reasoning models
we already reach (gpt-oss-120b on Groq, Gemini) do this through the OpenAI-compatible `tools` field; no new provider is needed.

### The Lead Brief (what the agent sees)
- who the buyer is, in one line (said and implied: "2 BHK, Rs 50-80 L, 3-6 months, home loan; read Fiore Phase 2A twice at night")
- what they asked for and whether we can answer it (floor plans: have / found, waiting for approval / not found)
- problems the buyer did not ask about (possession after their move-in date, budget at the top of the project's range)
- 2-3 alternatives that fit
- a price range with its sources and date, marked indicative, or none
- the next step and when ("call tomorrow morning, hot")
- a drafted reply, and a short "why I suggest this"; how sure it is

The agent edits and sends with one tap. Their edit is kept next to the draft, so we can see where the mind is wrong.

### The tools (all read-only)
| Tool | Reads through |
|---|---|
| lead history | tracking (contacts, events), the Inbox thread, chat sessions, pages read |
| project facts | areastats / propertyfacts, whole-project figures from `areastats.pages.project_scope` (CLAUDE.md rule 11) |
| MahaRERA status | the project register |
| matching homes | the finder the chat already uses (chat/engine) |
| floor plans | brochure facts we hold (brochure-reading.md), then the floor-plan library below |
| area answer | knowledge/vectors.py (grounded passages) |
| web search (step 5) | areastats/websearch.py (Serper, already paid for) |

## Rules it keeps
- **No AI sends on its own** (CLAUDE.md rule 6). The agent taps Send for anything the deep mind prepared. The chat bot keeps
  replying as it does today, under the same rules.
- **Code decides the sensitive things**: asking for the number, consent, abuse, handover, the short-chat limit (chat/agent.py).
- **Every output is checked** (rule 7): a number, price, project or builder name in a draft or a chat reply must appear in a tool
  result; otherwise it is refused. A model failure falls back to today's behaviour (lead card without a brief, the rules chat).
- **Prices are ranges with sources and a date**, marked indicative; never one confident figure.
- **Floor plans come from the builder's own site or brochure and from the plans filed on MahaRERA**, never from portals
  (their terms forbid it and they are often wrong). A found plan is kept with its source and date, and the owner approves it once
  in Studio; after that every buyer of the project can get it. Only approved plans go to a buyer, in the chat too.
- **We change the cover, never the plan**: our cover page, the asked-for BHK highlighted, the MahaRERA number, the source and
  "as per the builder's plan dated ...". A plan that differs from the approved one is misleading advertising under MahaRERA.
- **It says when it is not sure** rather than guessing.

## Steps
1. **Tool loop in the platform.** `platform/toolloop.py`: `run_tools(llm, system, user, tools, ...)` with a step cap, a time
   budget, the tool calls of one step run together, a tool's failure told to the model rather than raised, a forced final answer
   when the steps run out, and one `trace` line per step. `GroqLLM.step` / `FallbackLLM.step` send one OpenAI-style turn with
   `tools`. No business knowledge; any module may use it.
2. **Buyer profile.** One record per person across web chat, WhatsApp and DMs (`buyer_profiles`, one writer: the new
   `buyermind` module in conversations): what they said, what it implies, what we still do not know. The chat stops asking what
   the profile already has.
3. **Deep mind and the Lead Brief.** `buyermind.brief`: the tools above, the prompt, the checks, the fallback; run from the
   lead_followups loop on new leads and buyer replies behind `BUYER_MIND=true`. Stored in `lead_briefs`.
4. **Fast mind in the chat.** chat/agent.py reads the profile and the latest brief. Behind a switch, website chat first, then
   WhatsApp and DMs.
5. **Floor plans and price ranges.** Web search on the builder's site and MahaRERA, the floor-plan library with owner approval,
   the branded floor-plan PDF, the price range from listings, price sheets and pages we read.
6. **Studio.** The brief on the lead page, one-tap send, the agent's edits kept.

Steps 1-3 change nothing a buyer sees. Step 4 is the first live change and starts behind a switch on the website chat.

## Progress
- 2026-11-18: plan written (owner's direction). Step 1 started.
- 2026-11-18: step 1 built: `platform/toolloop.py` (`run_tools`) and `GroqLLM.step` / `FallbackLLM.step`, tests in
  `tests/platform_layer/test_toolloop.py`.
- 2026-11-18: steps 2-3 core built, not yet run anywhere: `modules/buyermind` (in the conversations layer of `.importlinter`).
  `BuyerMind.think(agent_id, lead_id)` reads the lead's handover card (InboxService.handover_for; the phone is never put in a
  prompt), thinks with two lookups (`project_facts`: the project page, whole-project figures when it stands for several
  registrations, prices labelled as the buyer reads them; `area_question`: the knowledge search), holds the answer to the facts
  (`brief.checked`: a draft with a figure, price or builder no lookup gave, or hype, is dropped with the reason; so is a flag or
  price idea with such a figure, and an alternative never looked up) and keeps the brief in `lead_briefs` and the profile in
  `buyer_profiles`. No model or no usable answer: the brief from the card alone (`brief.fallback`). Settings: `BUYER_MIND`
  (off), `BUYER_MIND_EFFORT`, `BUYER_MIND_ROUNDS`. Next: run it from the lead_followups loop on new leads and replies, and a
  Studio endpoint to read the brief; then matching homes and floor plans as tools.
- 2026-11-18: step 3 runs and step 6 started. In the background: `inbox.followups` step 5 (`fresh_briefs`) gives each open lead
  that came in or heard from its buyer since its last brief a new one, newest first, at most 6 a cycle and none started after
  2 minutes of it, through `app.wiring._brief_lead`, connected only with `BUYER_MIND=true`. By hand: `GET /buyer-mind/leads/{id}`
  and `POST /buyer-mind/leads/{id}/think` (works with the switch off, once per 2 minutes a lead). Studio: the "Buyer brief"
  panel on the lead page (`studio/components/app/BuyerBrief.tsx`): who they are, "Tell them" flags, the price idea, what to
  ask, projects to also show, the next step, and the draft in a box the agent edits and sends from their own WhatsApp.
  Still to do: try it on real leads with the switch off (the button), keep the agent's edits, then the chat's fast mind (step 4).
- 2026-11-18: step 4 begun on WhatsApp and DMs (owner: "handle as much as we can with our agents"). When a conversation belongs to
  a lead, the reply reads `buyermind.chat_facts` (through `whatsapp.adapters.configure`, app.wiring): the brief's "tell them"
  flags, its published price range and the names of the projects it looked up, dates written as a buyer reads them. They go
  into the chat agent's KNOWLEDGE as "Checked for this buyer", so its reply checks accept those figures and refuse any other;
  the price rule now allows a price from there, said as indicative with when it was published and the source named without a
  web address. Never sent: what the mind read into the buyer, the agent's draft, an alternative's unchecked reason, or a brief
  from the rules, marked low confidence or older than 7 days. Briefs exist only with `BUYER_MIND=true` or after "Think about
  this lead". The website chat does not read them yet (it has no lead until the number is given).

- 2026-11-27: the switch is on in production (`BUYER_MIND=true`, backend and conversations), but only 1 of the 5 leads since
  2026-11-21 had a brief. Each was a WhatsApp or ChatGPT lead the bot had answered, so its contact status read "in touch" and
  `fresh_briefs` skipped it (it took only not_contacted / waiting_you). Now a lead whose last word is the bot's is briefed too,
  from the buyer's last message (`tracking.contact.last_heard`), so each new buyer message gets one fresh brief. Of the 5 briefs
  before the fix: 2 done, 2 stopped at the round cap ("forced"), 1 failed. Watch those outcomes on the next leads.
