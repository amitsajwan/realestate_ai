# Lead follow-up and DM delivery (2026-10-23)

Two misses on 2026-10-22/23, found by the owner:

- **Akshay Manjarekar** tapped the "🔍 Check my project's MahaRERA status" ice breaker on Facebook and Instagram (23 Oct, 7:05 IST).
  Meta never called our webhook (no POST to /messenger/webhook, last dm_messages row 18 Oct). The app still receives DMs only from
  app-role users: Messenger App Review submitted 18 Oct, Instagram not submitted. Owner replied by hand.
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

## Owner (not code)

- Meta App Review: check Messenger status (App Review > Requests); submit Instagram (instagram_manage_messages, instagram_basic).
  After approval, test from an account with no app role.
