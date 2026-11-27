# Agent network: lead board, asks and picking by points

**Status:** TARGET. Decided by the owner 2026-11-27. Steps 1 and 2 built on branch `agent-network/verify-and-board` (2026-11-27,
not merged); offers hidden. The rest is not built.
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

### Progress

- 2026-11-27, steps 1 and 2 (branch `agent-network/verify-and-board`): `onboarding/verification.py` keeps `rera_check` on the
  profile (pending until the owner records verified, with the register page, or rejected; a changed number is pending again).
  Owner screen: Studio > Agents > MahaRERA check (`GET/POST /admin/agent-checks`). The badge shows on `/agent/[slug]` and in
  Studio from `branding_data.rera_verified_no`. The board (`inbox/board.py`) shows cards and takes asks only from verified
  agents (others get `locked` with the reason); every card carries `fit` (listing in the project, listing in the area, area
  covered) and Studio filters "Fits you" / "All Pune", area and BHK. Before the deploy, the two agents with a MahaRERA number
  were checked on the register and recorded as verified (House Deal A031262502865, Kausar Patanwala A011262605235, the only
  agent with asks), so nobody who used the board was locked out. The register's agent pages are on
  `maharerait.maharashtra.gov.in/agent/view/<id>` (the search on maharera.maharashtra.gov.in links there): that host is
  accepted as a register page. Search the register by name; it has no search by number.
- Offers: hidden (the recommendation below). Studio no longer asks for or shows one, the API drops any offer it is sent, and
  offers stored before stay in `lead_asks` untouched.
- 2026-11-27, `/for-agents` (where the recruiting posts link): "Open and free to join" in the title, description, badge, cost box
  and call to action; no trial, offer or "first 20 agents". It names the lead board, the MahaRERA check and "nobody can pay
  for a higher place". The guide (`/for-agents/guide`) lost its offer lines and says the board opens once the number is
  checked. The same day the rest of the sign-up path followed: `/trial`, `/agents`, the header, footer and sticky buttons
  ("Join free"), terms and privacy, and the replies agents read (WhatsApp sign-up and code messages, comment and DM replies,
  the chat's agent answers). The word agents send is still TRIAL, because old posts and QR codes say it.
- 2026-11-27, before the LinkedIn push: the last trial wording went. Studio's sign-in page (`/join`, `JoinFlow.tsx`) said "1
  month free, first 20 agents"; the guide's step 1 said "Claim the trial"; the privacy page said "about their free trial"; the
  brand post, text post, calendar and reel templates (Hindi and Marathi "pilot, invite only" too) said "Claim your free trial".
  All now say open and free to join. `tests/modules/test_join_free_wording.py` fails if a post or reel offers a trial again.
- 2026-11-27: steps 1–2 and the wording are LIVE (d130fd04, 16e97490). The call-back form's consent text ("about joining
  Avasetu", b4a80292) is on main but NOT live: the owner paused deploys the same day (`AUTO_DEPLOY=false`) to release
  several pieces together.

### Next: what the board screen still lacks (steps 3, 4, 6 in screen terms)

What runs today (`studio/app/studio/lead-board/page.tsx`): agents see every open card (no name or number), why it fits them,
what the buyer read, how many agents asked, and ask free with a note; the owner sees the asks (name, time, note) and gives
with one tap. What is missing, most important first:

1. **The owner chooses blind.** An ask shows only the agent's name and note. Show each ask's points with the breakdown
   (listing in the project 30, covers the area 20, called fast 20, buyer ratings 15, fewer recent leads 10, language 5;
   missing evidence scores 0) and rank the asks by it. Grow `agent_shortlist` into this scorer if its owner commits it
   (uncommitted in the main checkout, owner unknown); otherwise score in `inbox/board.py`. One scorer, no model.
2. **No deadline.** The 30-minute ask window from a card's first appearance: a countdown on the card ("closes in 18 min"),
   and a **Ready to decide** tab at the top of the owner's board with the closed windows that have asks.
3. **Agents are not told the outcome.** A **My asks** list for agents (waiting, given to you, went to another agent), and a
   plain note when a buyer goes to someone else. No name of the other agent.
4. **The agent's own score.** "How you'd score" on each card for the signed-in agent, from the same table, so they know
   why they would or would not get it.
5. **Nothing after the give.** "I called" on the handover; no call in 2 hours passes the buyer to the next ask and tells
   the first agent (step 6).
6. **Agents hear of new buyers only from the owner's WhatsApp link.** Step 5's alert template ("A buyer in {area} wants a
   {bhk}. Ask for this buyer") goes to Meta first: approval takes days.

Build 1–4 together (one screen, one release); then 5; then 6 once the template is approved. Step 7 (buyer side) after that.

### Before the next deploy

- Open the Studio screens signed in, as the owner and as a verified agent: Agents > MahaRERA check, the lead board
  (Fits you / All Pune, ask, take back), and the locked screen for an unverified agent. Not yet looked at in a browser.
- Turn deploys back on only when the owner says (`gh variable set AUTO_DEPLOY --body true`), then check the release
  (deploy skill).

## AI in the network (proposed 2026-11-27, not decided)

What already runs, and where it shows up:

| AI part | What it does | Role in the network | State |
|---|---|---|---|
| Project intelligence (MahaRERA reads, enrichment, page writer, fact checks) | Keeps every Pune project page researched and current | The research agents send their buyers; why buyers trust our pages | Live |
| Listing copilot (`ai_listing`, listing from a RERA number) | The agent types a RERA number and the listing fills itself | The main reason agents join | Live |
| Posts and reels (creative room, reel drawing, voice-over) | Draws posts and videos for each listing | "Made for you, you approve" | Live |
| Website chat as salesperson (chat + knowledge search) | Answers buyers and collects BHK, budget and timing | Where the lead card's details come from | Live |
| Buyer mind (deep mind, Lead Brief; `docs/plan/buyer-mind.md`) | Reads a lead: who the buyer is, what they need, problems (possession after their move-in date), 2–3 other projects | The best thing to hand an agent after the pick | Live (aa5011c7: it no longer skips leads the WhatsApp bot answered; first 5 model-written briefs 2026-11-27 04:36 UTC). Next: read those briefs before handing them to agents |

Where it plugs into the flow, in order:

1. **Handover, after the pick (recommended first, about 2 days, mostly wiring).** The full Lead Brief plus a suggested first
   WhatsApp message the agent can edit, and anything to know before calling. "You don't just get a number, you get the buyer
   understood": the reason to pay for a subscription later.
2. **Board card, before the pick.** A one-line summary by the buyer mind ("2 BHK, own home, moving in 6 months, compared 3
   Kharadi projects"), written without name, number or the buyer's own words and checked by the same copy guards. After the
   brief has been tried on real leads.
3. **Studio copilot for agents.** Point the existing "Ask AI" at the project research, so an agent can ask "What's the real
   possession date of Ivara, and has it moved?" and get an answer with its source.
4. **Later, not now:** voice listing ("2 BHK in Ivara, 850 sq ft, 1.35 crore" spoken into the phone), and reading the MahaRERA
   agent register by code for step 1's check.

What AI will not do (already rules here and in CLAUDE.md): pick the agent (fixed points do that); make up ratings, deals or
availability; post anything without the agent's or the owner's approval.

## Recruiting posts: the Studio session owns them too (owner, 2026-11-27)

The same session that builds the board also makes and puts out the posts that bring agents in. The owner should not have to
draft or post anything except the founder's own LinkedIn post.

| When | Post | Where | How |
|---|---|---|---|
| Week of 27 Nov | "Looking for property agents across Pune": text in `docs/content/linkedin/agents-01-founding-network.md`, image = canvas artboard "LinkedIn post image" | LinkedIn (founder profile, then shared by the company page) | **By the owner.** There is no LinkedIn API in the code. Give the owner the final text and the PNG, ready to paste |
| Same week | Same message, cut for buyers' channels: one image plus a short caption that says "for agents" in its first line | Avasetu Facebook page and Instagram | Through `social.distribution.send` only (CLAUDE.md rule 6), key `recruit:agents-01:<platform>`. Dry run first, then live. Send the owner the links of what went out |
| Week 2 | "How it works" carousel: the canvas screens (lead board, one buyer opened, owner pick, handover) as 4–5 slides | LinkedIn (owner), FB/IG (send) | As above. Say on the first slide that it's being built with the first agents |
| Week 4 | First agents on the network (name, area, page link), **only with each agent's written OK** | LinkedIn, FB/IG | As above |
| Every week | One-to-one messages to the prospect list (short version in the post file) | WhatsApp / LinkedIn DM from the owner | Draft them; the owner sends. Business-initiated WhatsApp needs an approved template |

Rules for the posts:
- Name the audience first (agents, not buyers), as every piece of content does.
- Claim only what is live that day. The board, the ask window and picking by points are "being built with our first agents"
  until they ship.
- No lead numbers and no promise of buyers. Never say anyone can pay to rank. No made-up agents or quotes.
- Company channels sign as the Avasetu team. Only the founder's LinkedIn post is in the founder's voice.
- The agent recruitment reels of Oct 2026 brought no agents. Posts back up the direct messages; they don't replace them. Count
  replies per channel in the prospect list.
- Images are drawn in code where the reel and post renderers can do it. Otherwise export them from the canvas. Keep the brand
  look: navy `#102340`, gold `#F0B13B`, Inter.

## Decisions still open (ask the owner, don't assume)

- **Offers on the board.** (Hidden 2026-11-27 as recommended; stored offers kept. The decision itself is still open.) `ask` took a sealed offer (`fee` for the lead, or a `share` of brokerage; owner 2026-10-31).
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
- Joining is "open and free" with no trial wording anywhere an agent reads (done 2026-11-27); keep it that way.
