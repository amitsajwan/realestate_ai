# Lead follow-up and DM delivery (2026-10-23)

Two misses on 2026-10-22/23, found by the owner:

- **Akshay Manjarekar** tapped the "🔍 Check my project's MahaRERA status" ice breaker on Facebook and Instagram (23 Oct, 7:05 IST).
  Meta never called our webhook (no POST to /messenger/webhook, last dm_messages row 18 Oct). The app still receives DMs only from
  app-role users: Messenger App Review submitted 18 Oct, Instagram not submitted. Owner to reply by hand.
- **Rahul Thombare** (Hot 50) asked for the floor plans of Puraniks Abitante Fiore Phase 2A from the project page form (22 Oct, 22:15 IST,
  from Google): 2 BHK, Rs 50-80 L, 3-6 months, home loan. Nothing went to him until the follow-up template was sent by hand on 23 Oct.

## LIVE

- Form leads are stored in `contacts` with requirement (bhk, budget, timeline, financing) and first_touch.
- Studio lead button sends the approved `enquiry_followup_v1` template (inbox/service.py start); the bot then answers his replies.

## TARGET (code, later)

1. **Auto follow-up on form leads.** When a form lead has a WhatsApp-able number, send `enquiry_followup_v1` within minutes, same rules
   as the Studio button (once per 24 h, STOP respected). Today it waits for a person to press the button.
2. **Floor-plan form sends the floor plans.** The enquiry came from the floor-plan form: once the 24-hour window is open (he replies),
   the bot sends the project's floor-plan pictures, or says plainly that we do not have them yet and that the team will get them.
   Needs a project-aware template ("You asked for the floor plans of {{project}}") so the first message names what he asked for,
   not a generic "2 BHK home in Pune".
3. **Unanswered-lead alert.** A lead with no outgoing message after 2 hours goes to Studio Home ("Call today") and to the owner's
   WhatsApp/email, so a Hot lead is never silent overnight.
4. **DM delivery check.** Admin health shows the time of the last webhook POST per platform and whether App Review is approved, so
   "the bot did not reply" is visible as "Meta is not sending us messages" without reading logs.

## Studio gaps found 2026-10-23 (owner: "not clear how to track leads, what messages are going")

LIVE today: Leads = form/chat leads with stage, temperature, notes, site-visit timeline (events only). Inbox = conversations
(WhatsApp, DMs, comments, web chat). The two are separate, so a lead page does not show what was said to the person.

LIVE 3af3d9ce (2026-10-23): items 5, 6 (messages shown on the lead, reply stays in the Inbox thread), 7 (Answered / No answer;
"call back at" = the existing follow-up date) and the lead-page half of 9. Contact status = tracking/contact.py. The follow-up
template no longer starts the 12-hour bot hold (only a person's typed reply does), and moves a New lead to Contacted.

LIVE 52588f4d (2026-10-23): items 1 (auto follow-up, LEAD_AUTO_FOLLOWUP=true on the VM, owner's form leads, 2 min after they
come in, leads of the last 24 h only), 3 (one Studio alert per 2 h+ wait, kind lead_waiting; Home "Call today" lists waiting
leads live; no owner WhatsApp/email yet: that needs a paid alert template) and 11 (timeline points in the score). Loop:
inbox/followups.py, role conversations.

LIVE 2026-10-30: **a project page enquiry is answered as one.** Subhash Girase asked for a site visit on the 96 Arrcade, Kharadi page
(from ChatGPT) and the follow-up asked him which part of Pune he wanted. Now an enquiry on `/projects/<slug>` gets UTILITY template
`project_enquiry_v1` ("Thank you for asking about 96 Arrcade, Kharadi ... You asked for a site visit. Our team will call you
shortly"; submitted 2026-10-30, id 1363081072448084). Until Meta approves it, `enquiry_followup_v1` goes instead, with the area in
place of "your enquiry on our website" when there is no budget. The lead record also gets the page's area (project page or
`/projects/area/<area>/...`) when the buyer names none (tracking `_page_area`, the project lookup passed in by `wiring.py`).

TARGET, in this order:
5. **Contact status on every lead**, worked out by code, shown on the list row and the lead page:
   "Not contacted · 14 h" (red after 2 h) / "Follow-up sent 7:45, no reply" / "Replied 9:08 · waiting for you" / "Bot is talking".
   Leads list gets a "Not contacted" tab first. Stage moves New -> Contacted by itself when we message or log a call.
6. **Conversation on the lead page**: the WhatsApp/DM/web chat messages (ours, the bot's, theirs, held ones) inline, with the
   24-hour window ("free replies until 9:08 tomorrow") and a reply box; the timeline mixes page visits and messages.
7. **Log a call** button: Answered / No answer / Call back at..., saved as a timeline entry, so calls made outside the app count.
8. **One WhatsApp button**: the list row button opens the person's own phone (wa.me) and is not tracked; the lead page has two.
   Keep "WhatsApp from Avasetu" (tracked) as the main one, "from my phone" as a small secondary link that asks to log it.
9. **Bot hold visible**: a thread where the bot is holding back says so ("Bot paused for you until 19:45") in the Inbox and on the lead.
10. **Messages log** (Studio > Inbox > Sent): every outgoing message across channels with status sent / failed / held / refused,
    plus "last message received from Meta" per channel (item 4), so silence from Meta is visible.
11. **Score check**: a form lead with timeline "now" scored 25 (Veebha) while "3-6 months" scored 50 (Rahul, floor-plan form);
    timeline should count more than which form was used.

## Passing leads to agents (2026-10-26)

Owner: Saket's Mansha Phase-II lead (2 BHK, Google) reached House Deal as a name and a phone, and went to the retired House Deal
account (both read "House Deal" in the picker). The old message was built from the chat's state, empty in a chat our follow-up started.

LIVE (this change):
- **Handover card** (`inbox/handover.py`): every fact on the lead: name, phone, project + MahaRERA number, what they asked for
  (price sheet / visit / floor plans), BHK, budget, when, home loan, areas, their own words, page, source, time (IST), pages seen,
  what we already sent, owner notes, and "not known yet, please ask: ...". The agent's lead page shows it ("Passed to you").
- **Pass from the lead page or a chat**: the owner sees the card first; the lead and all its chats move together.
- **WhatsApp to the agent from our number**: UTILITY template `lead_passed_v1` (submitted 2026-10-26, id 1459495656106326; until
  Meta approves it the send fails, the pass still happens and the owner gets the wa.me button with the full card).
- **Rules** (`lead_routes`): "pass every Wagholi lead / every <project> lead to House Deal by itself", picked in the pass box or added in
  Leads > Passed. The follow-ups loop passes a matching lead 4 minutes after it comes in (after the auto follow-up), once per lead,
  and alerts the owner (`lead_auto_passed`).
- **Retired accounts** (slug `*-retired-*`, profile or user switched off) are left out of the picker and refused.
- **Leads > Passed** (owner): the last 14 days' passes, card, WhatsApp status, resend from my phone, the rules.

LIVE 2026-10-30: **an enquiry on an agent's own site is theirs.** The form there says "Enquire with <their business>" and the buyer
agrees to be contacted by them. Every 5 minutes the follow-ups loop sends each new one to the agent's office WhatsApp
(`branding_data.office_phone`, else the profile phone) from our number as UTILITY template `agent_site_enquiry_v1` ("New buyer enquiry
on your <business> website", no Studio line, since the office phone may have no login; submitted 2026-10-30, id 1096997010008481).
Until Meta approves it, `lead_passed_v1` goes instead. The owner gets an `agent_site_enquiry` alert and sees it in Leads > Passed
("enquired on their site", read only).

TARGET: tell the buyer who will call them (needs a buyer template naming the agent); the agent's outcome back to the owner.

## Lead board (2026-10-31, LIVE 3f025910)

Owner: agents have signed in but listed nothing, while our own leads wait. `/studio/lead-board` (backend `/lead-board`,
inbox/board.py) shows signed-in agents every open owner lead from the last 30 days that left an Indian mobile: project or area,
BHK, budget, when, how they pay, wants, where they came from, how old, and why it is genuine (wrote back, picked up our call, gave
their own budget, read 5+ pages). Never the name, the number or their own words. An agent asks, with an optional sealed offer
(a fee in rupees, or a share of brokerage on closing) and a note; the owner gets a `lead_asked` alert, sees every ask on the same
page and taps "Give to ...", which is the normal pass (`by: board`): lead, chats and card move, the others get `lead_ask_closed`.
The owner shares the link from the board's green box (WhatsApp text counts buyers and areas). Sign-in returns to the link (?next=).
Tests stay off: a lead whose number is a Studio sign-in or an agent page's number, or "test" in the name; the owner removes any
other with "Remove from board" (`lead_board_off`). The page is live: it reads the board every 30 s while open (and on return to
the tab), shows "Live · <time>", and marks leads that came in since the viewer last opened it as New.
Passed leads are on the board too (owner, 2026-10-31): a lead passed by hand or by a rule shows "already shared with one agent"
to agents (the owner sees who has it), its holder does not see it, and giving it moves it from the holder (passed_by stays the
owner). A lead given from the board does not come back.

All leads (owner, 2026-10-31: "show all leads even if passed to House Deal before, we will manage leads from there"): no 30-day
limit; every passed lead (by hand, rule or board) shows and is never dropped as a test; lost leads show marked "Marked lost"; a
lead with no number shows when it gave a BHK, budget, area or date (a bare comment stays in the Inbox, like Studio Leads); won
deals are off. Each card has its stage. On 2026-10-31 that is 18: 7 the owner's, 11 with House Deal.

From scratch (owner, 2026-10-31: "start from scratch, as if nothing shared"; "think how it can be sold, not information that is not
required"; "show numbers against areas"): no card says a lead was shared, who has it, or its stage; any agent (the holder too)
can ask, and giving it to the holder just keeps it with them. Only "Spoke with us on the phone" (an answered call) or "Replied on WhatsApp" (they wrote back to our message) is highlighted;
the first version said "spoke with us" for a WhatsApp reply, and none of the five had been called. The area chips carry
lead counts, busiest first. Any lead whose number is ours or an agent's is off, passed or not: every Studio sign-in, every agent
page's number and office number (House Deal's team WhatsApp), our WhatsApp line +91 98342 56406 and the owner's 9767971656. An
ask alerts the owner, also for a lead an agent holds.

What they looked at (owner, 2026-10-31: "more details, what the visitor was checking, what pages"): each card has the pages in
order with minutes read (project pages by their shown name, area lists, guides, news), visits and days, phone or computer, the
city of the visit (an NRI in Bahrain shows "Manama"), and taps on WhatsApp/call; signals add "came back on N days", "sent N
enquiries", "compared N projects". Events are read by the lead and by its browsers (anon_ids), so visits before or after the
enquiry count. A browser that opened our agent pages (/agents, /for-agents, /trial, /join, /studio) gets a caution "may be an
agent, not a buyer"; one signed in to Studio (staff events) is a test and stays off. Leads from before visit tracking reached
them have no pages (most of the 4+ day old ones on 2026-10-31).

Automatic pass OFF (owner, 2026-10-31: "we will not pass it automatically to House Deal for now"): the six area rules (Upper
Kharadi, Kharadi, Wagholi, Mundhwa, Hadapsar, Keshav Nagar -> House Deal 6abf5cacd2c1e770709ab741) were deleted from `lead_routes`;
backup on the VM at /tmp/lead_routes_backup_20261031.json. The code is unchanged: adding a rule (Leads > Passed, or "Next time" in
the pass box) turns it back on. Enquiries on House Deal's own site still go to them (step 4 of followups).

TARGET: agent asks via WhatsApp (a template with the board link when new leads arrive); auto-give to the best offer after N hours.

## Ice breakers OFF (2026-10-23)

The three DM starter buttons (scripts/set_dm_menu.py) were removed from Messenger and Instagram on 23 Oct: a tap sent a message
nobody could answer while Meta does not deliver public DMs. /check stays reachable as a link (Instagram profile Links). After
App Review is approved and a non-role test DM reaches the webhook, put them back with `python -m scripts.set_dm_menu --apply`.

## Owner (not code)

- Meta App Review: check Messenger status (App Review > Requests); submit Instagram (instagram_manage_messages, instagram_basic).
  After approval, test from an account with no app role.
