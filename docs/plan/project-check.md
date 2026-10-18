# Project check: "Check your project on MahaRERA" (2026-10-18)

Owner: "people search their project, bought or planning to buy, and see the current status", reachable from Facebook and Instagram.
One lookup, three doors: the web page `/check` (installable as an app), the Messenger / Instagram DM button, WhatsApp.

## Who it is for

- **Bought, waiting for possession** (largest, most anxious group): "is my builder late?". Comes back, shares in the society WhatsApp group.
- **Planning to buy**: "is this builder reliable, is this project selling?". Becomes a lead.

## What we can say (and what we cannot)

From our MahaRERA register: possession date now, the date at registration (so how many months it moved), homes booked of total,
towers / registrations, the builder's other projects and how many moved their date, the MahaRERA link, the date we last read it.
We do **not** hold construction progress, OC status or complaints, so the card never claims "on time" or "safe": it says what the
date did. Words: "Possession date unchanged", "moved later by N months", "date has passed: ask for the OC".

## States (one rule, backend `areastats/check.py`, mirrored in `frontend/lib/site/check.ts`)

| state | when | colour |
|---|---|---|
| passed | possession date is before today | rose |
| moved | moved later than at registration (months_later > 0) | amber |
| unchanged | same as at registration | emerald |
| dated | a date, but no registration-time date to compare | slate |
| no_date | MahaRERA shows no date | slate |

## Web: `/check` and `/check/<slug>`

- `/check`: one job. H1 "Check your project on MahaRERA", one line under it, a big search box (name, builder or P5… number),
  results as you type with the state pill on each row. Under it: what we show, where it comes from, "Add to home screen".
- `/check/<slug>`: the status card, made to be read on a phone and shared:
  1. project name, builder, place;
  2. the verdict block (state colour, one sentence, the dates);
  3. homes booked, MahaRERA number, registered on, towers with their own dates when there are several;
  4. the builder's record ("5 of 12 projects moved their date later, by 9 months on average");
  5. source line: "From MahaRERA public records, read <date>" + "Open on MahaRERA";
  6. **"Which are you?"** two buttons. *I've bought here*: what to do now (keep the agreement's date; RERA section 18: possession later
     than the agreement's date gives the buyer interest for each month or a refund; how to complain on MahaRERA), share with co-buyers.
     *Planning to buy*: what to check before booking + talk to an agent (the enquiry form, a lead tagged with the project);
  7. Share on WhatsApp (prefilled text with the verdict and the link), full project page, check another project.
- Canonical is the project page (`/projects/<slug>`) and the card is noindex: it is a tool, not a second copy of the page.
- The share preview (Open Graph title) carries the verdict: "Gera World of Joy: possession moved later by 14 months".

## App

The site's manifest becomes `display: standalone` with `start_url: /check`: "Add to Home Screen" gives an app icon that opens the
checker. `/check` shows an install button where the browser offers one (Android Chrome) and the Share > Add to Home Screen hint on
iPhone. Play Store (Trusted Web Activity) later, same code.

## DMs (Messenger, Instagram, WhatsApp): `whatsapp/check_flow.py`, inside the shared ChatBrain

- Start: the ice breaker / menu button "🔍 Check my project's MahaRERA status", or a message like "check status", "RERA status",
  or a MahaRERA number (P5…). Reply: "Send the project name or its MahaRERA number."
- Search: 1 clear match: the card as text; several: a numbered list of up to 3 ("reply 1, 2 or 3"); none: say so, ask for the
  MahaRERA number, and that we cover Pune district.
- Card text: name, verdict sentence, dates, booked, the /check/<slug> link; then one ask: "Reply 1 if you have bought here, 2 if you
  are planning to buy".
- 1 (bought): what to do now in two lines; stored on the chat (`check.stage = bought`). 2 (planning): the chat carries the project as
  its context and goes on as the buyer conversation (lead, agent).
- Any other message leaves the check flow; the normal brain answers. In the chat's language (en, hi, mr, hinglish, mr_latn).
- Ice breakers and persistent menu set once with `scripts/set_dm_menu.py` (Messenger and Instagram).

## Later (not in this step)

- Alerts when the date or bookings change: WhatsApp utility template (Messenger cannot message after 24 h).
- "Comment STATUS" on reels -> private reply with the link.
- Play Store listing.
