# Agent network: briefs for the project owner, the architect and the developers

Each brief stands alone and points at the same plan, `docs/plan/agent-network.md` (the flow, the points table, what already runs,
the build order). The screens are on the design canvas https://claude.ai/artifact/Q2PS2sEcNNtFa71S92n9wg. 27 November 2026.

---

## 1. Project owner

**What we're doing:** Avasetu becomes a network of MahaRERA-verified property agents across all of Pune. Buyers ask on our
project pages. Every verified agent sees each buyer on one lead board, with no name or number, and can ask for them free within
30 minutes. The best fit by fixed points gets the buyer and must call within 2 hours. Nobody can pay to win.

**Targets to 31 December 2026**

| | Target | How it's counted |
|---|---|---|
| Agents contacted | 30 | prospect list in Studio |
| Agents signed up | 15 | Studio accounts with a page |
| MahaRERA verified | 10 | checked against the register |
| Active (listing or ask in the last 14 days) | 5 | Studio activity |
| Buyers given to an agent through the board | first 5 | passes by "board" |

Inactive accounts don't count, and no number is rounded up.

**Your weekly part (about 2 hours)**
- Post the founder's LinkedIn post; the Studio session hands you the text and image ready to paste.
- Send the one-to-one messages it drafts, and take the calls.
- Check new agents' MahaRERA numbers until the code does it.
- Approve each "give" on the owner screen until picking is automatic.

**Decisions only you can make (needed before step 4 of the build)**
1. **Sealed offers on the lead board** (agents bidding a fee or a brokerage share). They clash with "nobody can pay", and a fee per
   lead probably needs Avasetu's own MahaRERA agent registration. Recommendation: switch offers off now and ask a RERA lawyer
   before any money is taken for a lead.
2. **House Deal's six areas.** House Deal gets the first 15 minutes on those leads, those leads stay theirs and off the board, or
   they're treated like everyone else.
3. **/for-agents page:** replace the "1 month free / trial" wording with "open and free to join".

**Risks:** agents don't come from posts alone (the October reels brought none), so direct messages carry the target. Buyers
may not answer the rating message. The WhatsApp alert template needs Meta approval, which takes days.

**Money:** joining and asking stay free through the pilot. Subscriptions (₹999 / ₹1,499) are tested only after agents use it.
Running cost today is above ₹5,000/month (VM about ₹5,600, plus AI), so the ₹5,000 budget covers new spend only.

---

## 2. Architect

**Shape:** no new module. The work extends `inbox` (conversations domain) and `onboarding` (identity domain), and adds one
worker loop. The layer and owner rules in CLAUDE.md and ARCHITECTURE §4 apply as they are.

**Ownership decisions**

| Concern | Owner | Notes |
|---|---|---|
| Agent verification status (`pending` / `verified` / `rejected`, who, when, register reference) | identity: `onboarding`, on `agent_public_profiles` | inbox reads it through onboarding's public query functions, never writes it |
| Reading the MahaRERA agent register | outside identity | identity is the lowest domain. If the MahaRERA client lives in a domain (areastats), `wiring.py` passes a `check_agent(rera_no)` callback into onboarding. A shared HTTP client belongs in `platform/` |
| Asks, ask window, scores | conversations: `inbox` (`lead_asks`, already its collection) | add window open/close times and the scored result to the ask or card. No new writer |
| Points | `InboxService.agent_shortlist`, grown, not a second scorer | deterministic, with a rule version, logged to `agent_recommendation_events` |
| Buyer ratings after a call | `inbox`, new collection e.g. `lead_feedback` | add it to the ARCHITECTURE §4 table in the same commit |
| WhatsApp alert and "Ask" reply | `whatsapp` sends, `inbox` decides who | a button reply comes back through the existing inbound path and calls `board.ask` |
| Closing windows, the 2-hour reassign, the next-day rating | one new loop in the `conversations` worker role | use the `add-background-loop` skill (lease, heartbeat, health) |

**Invariants to hold**
- A buyer's name, number or own words never reach an agent before `give`. That's already true of board cards; keep it so for
  the alert and the "How you'd score" view.
- No model picks an agent. AI may write copy only through `platform.text` guards with a fallback.
- Offers never feed the points. If the owner keeps offers at all, they stay sealed and separate.
- `give` stays an ordinary `pass_lead`, so routing rules, the handover card and the audit trail don't fork.
- Publishing the recruiting posts goes through `social.distribution.send`, and only the owner posts on LinkedIn.

**Review points:** no new `ignore_imports`. No function-level imports to dodge a cycle. No `os.environ` reads (window lengths
and points go in the inbox module's config). The import baseline only shrinks.

---

## 3. Developers

Read `docs/plan/agent-network.md` and CLAUDE.md first. Ship each step as its own commit, in this order, deployed when green.

**Step 1: Verification** (onboarding + Studio + site)
- Add a verification status to the agent profile, plus `POST` for the owner to set it, with a note and the register URL.
- Show a "MahaRERA verified" badge on `/agent/[slug]` (frontend) and in the Studio header.
- Only verified agents see the board and can ask; the others get "your MahaRERA number is being checked".
- Done when: an unverified agent gets 403 on `POST /lead-board/{ref}/ask`, and the badge shows only when verified.

**Step 2: All-Pune board** (inbox `board.py` + `studio/app/studio/lead-board/page.tsx`)
- Every verified agent sees every open card. Add "Fits you" and "All Pune" filters, plus area and BHK.
- Fit uses the same signals as `agent_shortlist`: declared areas and fresh listings.
- Hide the offer fields in `AskBox`, and stop sending `offer_kind` from Studio (keep the API accepting `none`).
- Done when: two verified agents in different areas both see a Kharadi card, and only the Kharadi agent sees it under "Fits you".

**Step 3: Ask window and "How you'd score"**
- A 30-minute window from the card's first appearance, with a countdown and "N agents asked".
- On opening a card, show the agent their own breakdown from the points table.

**Step 4: Pick by points**
- On close, score every ask. The owner sees them ranked with the breakdown, and `give` stays one tap.
- Automatic give goes behind a switch, off by default.
- Every give is logged in `agent_recommendation_events` with the rule version.

**Step 5: WhatsApp alert** to agents covering the project or area, with an "Ask for this buyer" reply that calls `board.ask`.
Draft the template and get it to the owner to submit on day 1 of the work.

**Step 6: The 2-hour rule.** An "I called" button on the handover card. The loop passes the lead to the next ask if nobody called,
and tells both agents.

**Step 7: Buyer side.** A consent line on the enquiry form, the "who will call you" message, and the next-day rating into
`lead_feedback`.

**Each step:** follow CLAUDE.md's definition of done (`lint-imports`, the backend suite or the module's tests, jest + build in
whichever app changed). A new behaviour gets a test named for it. Commit by path, because the checkout is shared. Update
`docs/plan/agent-network.md` (mark the step LIVE with the commit) and ARCHITECTURE §4 if a collection is added.

**Also yours:** the recruiting posts in the plan's "Recruiting posts" section. Make the FB/IG versions through
`social.distribution.send`, and hand the owner the LinkedIn text and image.
