# C3: Chat v2 (website assistant)

The website chat after the live test on a demo listing page. Grounded answers, honest unknowns, Hinglish and consent-first lead
capture were already right; v2 fixes the conversation around them.

## What changed

| # | Problem in the live test | v2 behaviour | Where |
|---|---|---|---|
| 1 | Asked "buy or rent?" again after a budget and after the lead | Intent is inferred: a budget in lakh or crore, or buy words, mean buy; rent, per month, deposit and kiraya mean rent. A known slot is never asked. Each question is asked at most twice, and not again straight away when the buyer answered something else. After the website lead the funnel stops: the bot only answers and shows homes. | `chat/engine.py` `extract`, `next_field`, `after_lead` |
| 2 | Ignored "Rahul" | The name is caught when offered ("I am / my name is / mera naam / maza nav X") or as a short reply to "May I know your name?". A stop-list keeps "I am looking for..." from being read as a name. It is stored on the session and the lead (a name given after the number replaces the "Website visitor" placeholder). It is used at most twice ("Thanks, Rahul." and "Thank you, Rahul!"). | `engine._name_in`, `service.message` |
| 3 | The long number and consent paragraph four times | The number is asked at most twice per conversation, never in back-to-back replies, and only after the bot has given something: an answer, homes, a no-match or a hand-off. The consent sentence appears once, next to the first ask. The second ask is short. "Not now" (also "abhi nahi" and "aata nako") pauses asking for 5 turns. A "no" to "anything else?" pauses it too. A number the buyer volunteers is confirmed with only its last 4 digits shown. | `engine._can_ask_phone`, `_phone_ask` |
| 4 | Never showed homes | Once area, BHK and budget are known or skipped, the bot shows up to 3 cards from the agent's live, public, not-stale listings, using `tracking.matching.top_matches` at the 60% "recommend" level. A card from a platform or demo page comes from that listing's agent. Samples get `sample: true`, no price, and a title without "for sale". When nothing matches, the bot says so and offers the agent's help. Cards come again when the requirement changes or the buyer asks ("show homes", "similar homes"). | `service.finder`, `service.card`, `engine._show_homes` |
| 5 | The agent was not told | `notify(... "new_chat_lead")` fires when a chat lead is stored, with the summary and a `lead_id`. `"chat_needs_you"` fires once per chat when the bot cannot answer or the buyer asks for a person. Summaries never include a number. The Studio badge counts every unread alert kind. | `service._notify`, `notifications/service.KINDS`, `components/app/LeadAlertsBadge.tsx` |
| 6 | Generic greeting | On a listing page: "Asking about the 2 BHK in Kharadi, 780 sq ft? I can tell you about it or find similar homes." For a sample, the greeting says it is an illustration. The home's area and BHK become soft defaults, so the bot asks the budget instead of "which area?". On a locality page: "Looking at homes in Upper Kharadi?" Everywhere else: the old greeting. "Tell me about it" answers from the listing's vetted facts. | `engine._greeting`, `service.page_for` |
| 7 | WhatsApp | "Continue on WhatsApp" appears only when `WHATSAPP_PUBLIC_NUMBER` (or `NEXT_PUBLIC_WHATSAPP_NUMBER`) is set in the **backend** env. It shows with the listing greeting, with cards, after a hand-off and after the lead. The response carries `whatsapp_url` (wa.me, prefilled with the listing's interest code `ref xxxxxxx` when one exists, else its title, else the requirement; never the buyer's number). The widget shows it as a link only when that URL is a wa.me URL. | `service.whatsapp_url`, `lib/site/chatApi.ts` |
| 8 | Language | The website chat keeps the buyer's language (en, hinglish, hi, mr, mr_latn; sticky across short answers) for every fixed sentence: greetings, the questions, the number ask, consent, no-match, cards, thanks and the "Got it:" words. KB answers stay as written. WhatsApp state keeps `localise=False`, so the engine still speaks English there and `whatsapp/lang.py` translates it. The English questions are unchanged word for word, so its table still matches. | `chat/phrases.py` |

The API is backwards compatible. `POST /api/v1/chat/message` now also returns:
`cards: [{id, title, locality, bhk, carpet_sqft, price_text, sample, url, image_url}]`, `follow_up` (the next question, which the widget
shows after the cards) and `whatsapp_url`.

Widget: compact tappable cards (64 px photo or a navy placeholder, title, "Kharadi · 2 BHK · 780 sq ft", then the price or a Sample badge)
linking to the listing page. Quick replies sit in one horizontally scrolling row. A reply with homes scrolls to its first line.
Screenshot (390x844, mocked API on `next dev`): `docs/brand/avasetu/chat-v2.jpg`.

## Safety rules kept
- The consent line is shown before any number is stored. A number typed before that needs a YES.
- The bot never writes a phone number (the confirmation shows only the last 4 digits).
- Samples are labelled in the text and on the card and never show a price. With only samples, the text calls them illustrations, not "homes that fit".
- Homes and prices come only from the agent's own live listings.
- The rate limit (60 per hour per session) and the tracking honeypot and limits are unchanged.

## Deploy note
To offer "Continue on WhatsApp", set `WHATSAPP_PUBLIC_NUMBER=+91XXXXXXXXXX` in the backend env. The backend also reads
`NEXT_PUBLIC_WHATSAPP_NUMBER` if that is shared with it. If neither is set, the option never appears.

## Changes outside chat/
- `whatsapp/test_service.py::test_hindi_buyers_get_hindi_questions_and_notice` now expects the area question (in Hindi). The buyer gave
  "बजट 80 लाख", and intent inference now treats that as buying.
- `tracking`: read-only use of `matching.top_matches`. Nothing changed there.
- `e2e/chat-journey.js` follows the new flow (no-match, then the number ask, then the name).

## Tests
- `backend/tests/modules/test_chat_v2.py`: 45 conversation-level tests, with and without a fake LLM. They cover intent inference (6 phrasings
  plus rent budgets), no repeated questions, the live-test conversation, name capture (14 cases) and use, the number asked at most twice with
  the 5-turn cooldown, cards (agent scoped, sample labelled, none-match, demo agent), notifications, greetings, WhatsApp on and off, and
  Hinglish, Hindi and Marathi consistency.
- `frontend/__tests__/site/chat-widget.test.tsx`: card rendering, Sample badge, follow-up order, quick replies, the WhatsApp link, and the badge.
- Jest in this worktree: the path contains `.claude`, so the default `testMatch` glob finds nothing. Run with a config that sets `testRegex`.

## Known limits / next
- A KB answer (English) followed by a Hinglish closing sentence mixes languages across sentences. Translating KB answers needs the
  knowledge module's checked translator (an LLM call).
- "Kharadi mein school kitna door hai?" without page context still hits the generic Kharadi KB entry (existing behaviour).
