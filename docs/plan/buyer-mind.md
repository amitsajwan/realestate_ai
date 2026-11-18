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
