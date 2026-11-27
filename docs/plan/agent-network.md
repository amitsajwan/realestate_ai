# Agent network: lead board, asks and picking by points

**Status:** TARGET. Decided by the owner 2026-11-27; nothing below beyond "What already runs" is built.
**Design:** the screens are drawn on the design canvas https://claude.ai/artifact/Q2PS2sEcNNtFa71S92n9wg (the flow, buyer form,
WhatsApp alert, lead board, one buyer opened, owner pick, handover, buyer told who calls, LinkedIn post image). Figures on it are
placeholders.
**Recruiting post:** `docs/content/linkedin/agents-01-founding-network.md` (going out the week of 2026-11-27).

## The goal

Avasetu 2.0: a network of MahaRERA-verified property agents across **all of Pune** (not only east Pune). Target: 30 agents
contacted and 15 signed up by 31 December 2026, 5 of them active. Agents come for the tools (page, listings filled from a RERA
number, posts and videos, project research) and stay for the buyers.

## The flow (owner, 2026-11-27)

1. A buyer asks on a project page. The enquiry form says one MahaRERA-verified local agent will call them.
2. The buyer appears on the **lead board**, which **every verified agent in Pune** sees: no name, no number, no buyer's own words.
   Agents who cover that project or area also get a WhatsApp alert.
3. Any agent asks for the buyer, free, within **30 minutes**. Opening a card shows the agent their own points ("How you'd score").
4. When the window closes, the asks are scored by fixed points (below). At first the owner approves the top one with one tap;
   later it is automatic. Nobody asked: the lead stays with the owner.
5. The chosen agent gets name, number and the handover card, and must call within **2 hours** or the next-highest agent gets it.
   The others are told it went.
6. The buyer is told on WhatsApp who will call (name, verified, their page). Next day: "Did they call, were they helpful?" The
   answer feeds the agent's points.

### Points (deterministic, no model in the choice)

| Signal | Points | Source |
|---|---|---|
| Live listing in this project | 30 | `listings` (fresh, by `freshness_of`) |
| Covers this area | 20 | profile `branding_data.areas` |
| Called past buyers within 2 hours | 20 | handover "I called" + call log |
| Buyer ratings of past calls | 15 | next-day buyer answer (new) |
| Fewer leads lately (spreads them) | 10 | passes in the last 7 days |
| Speaks the buyer's language | 5 | profile `languages` vs lead |

Missing evidence scores 0, never a guess. Version the rule and keep writing `agent_recommendation_events` on every pass.

## What already runs (extend it, don't rebuild)

- **Lead board** `backend/app/modules/inbox/board.py` (module docstring has every owner decision since 2026-10-31), routes in
  `inbox/router.py` under `/lead-board` (`GET`, `POST /{ref}/ask`, `DELETE /{ref}/ask`, `POST /{ref}/give`, `POST /{ref}/remove`),
  Studio screen `studio/app/studio/lead-board/page.tsx`. Asks live in `lead_asks` (written only by board.py). Cards already hide
  name, number and the buyer's words, and show pages read, reading time and "why we think they're real".
- **Give = ordinary pass:** `InboxService.pass_lead` (`inbox/service.py`) with the handover card and `lead_passed_v1` template.
- **Shortlist:** `InboxService.agent_shortlist` already ranks agents by declared area and fresh listings and logs
  `agent_recommendation_events`. Grow it into the points table rather than writing a second scorer.
- **Agent profile:** `onboarding/service.py`, collection `agent_public_profiles` (owned by onboarding). Has `rera_agent_no`,
  `areas`, `languages`, `years_experience`, and `rera_due_at` (7-day grace for the RERA number).
- **Area routing:** `radar/routing.assign` (least-loaded agent in an area) and owner rules in `pass_lead(always=...)`.
- Pilot notes and interview questions: `docs/plan/agent-intelligence-pilot.md` (untracked in the main checkout).

## What to build, in order

1. **Verification.** A status on the profile: `pending` → `verified` / `rejected`, with who checked, when and the register
   page. Owner checks by hand first. Later the MahaRERA agent register is read by code. A "MahaRERA verified" badge goes on
   `/agent/[slug]` and in Studio. Only verified agents see the board and can ask. Onboarding owns the write.
2. **Board for all of Pune.** Every verified agent sees every open card. Add "Fits you" vs "All Pune" filters, plus area and BHK,
   using the same signals as the shortlist.
3. **Ask window.** 30 minutes from the card's first appearance. Show a countdown, "N agents asked", and the agent's own "How you'd
   score" on the card.
4. **Pick by points.** On close, score the asks. The owner sees them ranked with the breakdown and gives with one tap (`give`
   exists). Behind a switch, give automatically later.
5. **WhatsApp alert** to agents covering the project or area, with an "Ask for this buyer" button. **This needs a new template, so
   submit it to Meta early** (approval takes days).
6. **2-hour rule.** An "I called" button on the handover. No call in 2 hours: pass to the next ask, and tell the first agent.
7. **Buyer side.** A consent line on the enquiry form, a "who will call you" message, and the next-day rating. Ratings are
   stored, never invented, and shown only when there are enough of them.

## Decisions still open (ask the owner, don't assume)

- **Offers on the board.** `ask` takes a sealed offer today (`fee` for the lead, or a `share` of brokerage; owner 2026-10-31).
  The 2026-11-27 rules and the recruiting post say **nobody can pay for a higher place**. Also, taking a fee for passing a buyer
  probably makes Avasetu a "real estate agent" under RERA s.2(zm), which needs a MahaRERA registration. **Recommendation:**
  hide the offer fields, never use offers in the points, and keep the stored data until the owner and a RERA lawyer decide.
- **House Deal.** Since 2026-10-30, leads in House Deal's six areas pass to House Deal automatically. Options: House Deal gets
  the first 15 minutes on those leads, those leads stay theirs and off the board, or they're treated like everyone else.
- **Subscriptions** (₹999 / ₹1,499) come after the pilot. Charge nothing to join or to ask until then.

## Rules for whoever builds it

- CLAUDE.md layers and owners: board writes `lead_asks`, onboarding writes profiles, inbox writes passes. Cross-module needs go
  through `wiring.py` callbacks.
- No AI picks the agent. Scoring is plain code with a rule version. AI may write the alert or card text only through the usual
  copy guards.
- A buyer's name, number or own words never reach an agent before the give.
- Never show a rank or rating to buyers until it rests on real ratings. Nothing paid touches the order.
- The `/for-agents` page still says "1 month free, first 20 agents" and "Claim your free trial". The owner wants "open and
  free to join" with no trial wording.
