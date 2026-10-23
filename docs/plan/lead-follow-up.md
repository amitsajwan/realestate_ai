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
3. **Unanswered-lead alert.** A lead with no outgoing message after 2 hours goes to Studio Home "Needs you now" and to the owner's
   WhatsApp/email, so a Hot lead is never silent overnight.
4. **DM delivery check.** Admin health shows the time of the last webhook POST per platform and whether App Review is approved, so
   "the bot did not reply" is visible as "Meta is not sending us messages" without reading logs.

## Studio gaps found 2026-10-23 (owner: "not clear how to track leads, what messages are going")

LIVE today: Leads = form/chat leads with stage, temperature, notes, site-visit timeline (events only). Inbox = conversations
(WhatsApp, DMs, comments, web chat). The two are separate, so a lead page does not show what was said to the person.

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

## Ice breakers OFF (2026-10-23)

The three DM starter buttons (scripts/set_dm_menu.py) were removed from Messenger and Instagram on 23 Oct: a tap sent a message
nobody could answer while Meta does not deliver public DMs. /check stays reachable as a link (Instagram profile Links). After
App Review is approved and a non-role test DM reaches the webhook, put them back with `python -m scripts.set_dm_menu --apply`.

## Owner (not code)

- Meta App Review: check Messenger status (App Review > Requests); submit Instagram (instagram_manage_messages, instagram_basic).
  After approval, test from an account with no app role.
