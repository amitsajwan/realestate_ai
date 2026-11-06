# The chat speaks first, and keeps what it learned (2026-11-06, LIVE)

Owner, 2026-11-06: "when a person is doing analysis, like home plan, comparing projects, checking multiple for a few minutes, what if our
bot starts communicating? Bot can ask to try home plan. Why we say can we talk in Hindi, why not Marathi also. Why bot cannot suggest good
projects, specially hot ones, if he is in that area." And: "chat means WhatsApp also, and context should be kept."

Why: in the 21 days to 2026-11-06, 610 visits, 14 chats, 1 chat lead, every chat in English. 28 visitors read two or more projects for
over 90 seconds and nobody spoke to them. The first visitor to finish a plan and read it for two minutes left no way to reach them.

Labels: **LIVE** = running, **NEXT** = not built.

## 1. What runs

| What | Website chat | WhatsApp |
|---|---|---|
| Speaks first | LIVE: a note beside the button | Not possible for free: Meta allows us to write first only with a paid template, so the bot answers when they write |
| Offers the home plan | LIVE: a link in the chat, once | LIVE: a link in the message, once |
| Names an area's hot projects | LIVE: as soon as the area is known | LIVE, same cards as text lines |
| Hindi and Marathi | LIVE: buttons in the chat's header | LIVE: they say "Marathi", and the follow-up messages invite it (new templates, see 5) |
| Keeps what it learned | LIVE: their plan and readings stay on the session | LIVE: the website's context comes across (see 4) |

## 2. The note beside the chat button (`chat/nudge.py`, `frontend/lib/site/chatNudge.ts`)

The browser counts the seconds the site is in view (30, 90, 120, 180, then each minute up to 20 minutes) and asks `POST /chat/nudge`. The server picks the words from what
this browser read, from our own page views, so the browser names nothing. It never opens by itself: on a phone an opening chat covers the
page, and Google marks pages down for that.

| They have | After | The note | Its buttons |
|---|---|---|---|
| A finished East Pune plan | 20 s | "Your home plan: 2 BHK, Under ₹75 L. Want today's prices..." | Today's prices for my plan |
| Read 2+ projects (the page they are on counts) | 90 s | "Comparing Lodha Camelot and Godrej Ivara?..." | Compare them, Try the home plan |
| An area of ours | 120 s | "Looking around Kharadi?..." | Hot projects in Kharadi, Try the home plan |
| Anything else, East Pune or no area | 180 s | "Not sure which one fits your family?..." | Try the home plan |

Limits: one note a day; none for 7 days after × (browser) or after a chat; never to someone who gave a number; never on forms, sign-in, the
plan's own questions, agents' pages or agents' sites. A note nobody answered is no chat in Studio: it waits on the session (`data.nudge`)
and joins the conversation only when they answer. `data.nudge_key` stays, so we can count which notes led to a chat.

## 3. Hot projects (`chat/projects.py`)

The first time the area is known (said, or from the page they are on) its projects go up, without waiting for size and budget. Asking for
"good", "popular" or "suggest" does the same, also on a project page. Otherwise a project's page keeps to its project.

Order: priced fits for their size and budget, the owner's banner picks (only for a buyer who has said nothing: a banner note is no fit),
then `hot_score`. Left out: MHADA projects (the bot stays silent on MHADA since 2026-10-20, and the hottest project in Kharadi on
2026-11-06 was one), fewer than `OPEN_MIN` homes open, a published price over budget by more than 10%, a sheet with only other sizes.

A card marked Hot means buyers look at it most: search, bookings, launches, news. It says nothing about quality, so the model may not call
it good; the owner's "good projects" is answered with these plus a sourced fact on each card.

## 4. Context from the website to WhatsApp (`chat/carry.py`)

A WhatsApp chat used to start empty. Now, once per chat:
- **"Continue on WhatsApp"** fills in `(chat <ref>)`, which names the website session (`chat_sessions.wa_ref`);
- **anyone else who writes**: the lead with that number gives its requirement, and the pages its own browsers read (`anon_ids`), a home
  plan among them.

It fills only what the chat does not know: what they say on WhatsApp wins. The model is told what they read and asked, and to ask nothing
again. The language of the website chat comes too. Nothing goes the other way yet.

A plan's answers come from its address, so they are read from page views (`tracking.visits.plan_this_visit`), never asked again, and stay
with the session after the visit ends. The lead shows the plan with the pages read.

## 5. Marathi in the follow-up messages

A template's words are Meta's to approve, so "Hindi ya Marathi mein baat karna ho to bataiye" is a new template: `enquiry_followup_v2`
and `project_enquiry_v2`. `inbox/service.py` tries v2, then v1, so no lead waits while Meta reviews.

## 6. What we measure

After two weeks (`chat_sessions`): notes shown per `data.nudge_key`, how many became a chat, how many gave a number, against the 14 chats
and 1 lead above. If notes bring no chats in four weeks, or visitors dismiss most of them, they go.

## 7. Next

1. Studio count of notes shown, chats and leads by kind.
2. Compare two projects inside the chat, from their facts, instead of handing off.
3. The plan's own picks in the chat and on WhatsApp (they are worked out in `frontend/lib/site/homeplan.ts`, so the bot cannot name them yet).
