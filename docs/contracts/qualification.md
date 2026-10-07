# Contract: buyer qualification, matching, follow-up, "Your business today" (Sprint 2, frozen)

Extends `backend/app/modules/tracking` (events, contacts, scoring, inbox). Everything is optional-first: a buyer may
send only name + phone + consent as today. All money is integer rupees. Nothing here sends a message on its own:
follow-ups are DRAFTED and the agent taps to send (wa.me link), so no WhatsApp Business API is needed.

## 1. Buyer requirement (captured with the enquiry, or inferred from the message)
```
Requirement {
  bhk:             number | null            1, 2, 2.5, 3 ...
  budget_min_inr:  integer | null
  budget_max_inr:  integer | null
  timeline:        "now" | "1_3_months" | "3_6_months" | "exploring" | null
  financing:       "home_loan" | "own_funds" | "undecided" | null
  localities:      string[]                 e.g. ["Baner"] (defaults to the enquired listing's locality)
  source:          "stated" | "inferred" | "mixed"     stated = buyer filled the fields; inferred = parsed from message text
}
```
Budget choices offered on the public form (each maps to min/max): under 50L (0-5,000,000) | 50-80L | 80L-1.2Cr | 1.2-2Cr | 2Cr+ (open max).
Timeline labels: Now / 1-3 months / 3-6 months / Just looking. Payment labels: Home loan / Own funds / Not sure.

## 2. Public enquiry (extends POST /api/v1/t/inquiry — old bodies keep working)
Adds optional fields: `bhk`, `budget_min_inr`, `budget_max_inr`, `timeline`, `financing`. The service also parses `message`
(e.g. "2bhk under 90 lakh, need it next month, home loan") to fill anything the buyer left empty (`inferred`). If the buyer
enquired on a listing, `localities` defaults to that listing's locality and `bhk` to its bhk when not stated.
Response unchanged plus nothing sensitive: `{received: true, new_lead: boolean}`.

## 3. Lead detail (extends GET /api/v1/inbox/leads/{id}); lead list items gain `requirement_line`
```
requirement:  Requirement | null
ai_summary:   string      plain sentence, e.g. "Wants a 2 BHK around 80L-90L in Baner within 1-3 months, on a home loan.
                          Viewed the Baner flat 3 times and tapped WhatsApp. Likely ready for a site visit."
next_action:  { type: "call" | "whatsapp" | "schedule_visit" | "follow_up", reason: string }
matches:      [{ listing_id, title, price_inr, locality, match_pct: 0..100, reasons: string[] }]   top 3 of the agent's live listings
follow_up:    { due_at: ISO | null, overdue: boolean }
```
`requirement_line` (list items) = short text like "2 BHK · 80L-90L · Baner · 1-3 months" or null.
`ai_summary` and `next_action` are RULE-BASED and deterministic (no LLM required); an optional injectable LLM may polish
wording but must never change facts. `match_pct` is a transparent rule score (never a fake "AI %"): transaction/type fit,
BHK fit, budget fit (price inside the buyer's range = full, within +10% = partial), locality fit; `reasons` lists what matched.
`next_action` rules (first match wins): stage is site_visit -> follow_up "confirm the visit"; temperature hot -> schedule_visit;
inquiry with phone and never contacted for >24h -> call "respond within a day"; timeline now/1_3_months -> whatsapp;
otherwise follow_up.

## 4. Follow-up drafts (agent taps to send; nothing is sent by the platform)
```
POST /api/v1/inbox/leads/{id}/followup-draft   body: { language?: "en" | "hi" | "mr" }  (default en)
-> { message: string, whatsapp_url: string, language: string, based_on: string[] }
```
`message` is a short, polite, specific WhatsApp text using the lead's real facts (name, listing enquired, budget, a matching
listing if any). `whatsapp_url` = `https://wa.me/<digits>?text=<urlencoded message>`. `based_on` explains why in plain words
("No reply for 2 days", "Budget 80L-90L", "New listing in Baner within budget"). Templates for en; hi/mr templates optional
(fall back to en). Optional injectable LLM polish; deterministic fallback always available.
Follow-up scheduling: when an agent moves a lead to `contacted`, `follow_up_due_at` = now + 2 days unless `follow_up_at`
(ISO) is supplied on `PATCH /inbox/leads/{id}` (`{stage?, note?, follow_up_at?}`); a lead is overdue when due_at < now and
stage not in (won, lost).

## 5. Your business today (GET /api/v1/inbox/today, agent auth)
```
{ counts: { new_enquiries_24h, hot, site_visits, follow_ups_due, uncontacted },
  hot_buyers:    [{ id, name, phone, score, temperature, requirement_line, top_match: {title, match_pct} | null }],   max 5
  follow_ups:    [{ id, name, phone, due_at, overdue, reason }],                                                       max 10
  headline:      string }   e.g. "3 buyers haven't been contacted today." or "You're all caught up."
```
`hot` = temperature hot and stage not won/lost; `site_visits` = stage site_visit; `uncontacted` = stage new with no agent activity;
`follow_ups_due` = due_at <= end of today or overdue. Owner scoped like every inbox read.

## Ownership (Sprint 2)
- B  backend/app/modules/tracking/** and tests/modules/test_tracking*.py, test_qualification*.py
- F1 frontend/components/site/**, frontend/lib/site/**, frontend/__tests__/site/** (public enquiry form)
- F2 frontend/components/app/**, frontend/lib/app/**, frontend/app/studio/**, frontend/__tests__/app/** (dashboard, lead detail, drafts)
