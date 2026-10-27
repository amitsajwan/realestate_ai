# Studio: how it is laid out and why

Studio (`/studio`) is the phone app for agents and the owner. This page records its shape after the 2026-10-27 pass, so later
changes keep to it. Code: `frontend/app/studio/`, `frontend/components/app/`, rules in `frontend/lib/app/`.

## Principles

- **One thing, one place.** Each person or task appears once on a screen. Home used to name the same buyer in "Needs you now",
  in an "AI recommends" card and under "Hot buyers".
- **Act from the row.** Call and WhatsApp sit on the row of a person to call; a listing's publish, marketing, share and
  sold/pause buttons sit on its first screen.
- **Open on what needs you.** Lists open on their "Needs you" tab while anything waits there (Inbox, Leads, Listings, Content).
- **Navy and gold.** Primary buttons, selected chips, tab bars and the spinner use navy `#0f2340`; counts that need you are gold
  `#f0b440`. WhatsApp actions stay green. Links stay blue.
- **A failing source is left out, never an error on the screen**, except the server's day summary on Home, which shows a retry.

## Tab bar

| Who | Bar | More |
|---|---|---|
| Agent | Home, Inbox, Leads, Listings | Results, Content, Buyer radar, My brand and website |
| Owner | Home, Inbox, Content, Newsroom | Leads, Listings, Results, Buyer radar, Agents, Admin, My brand and website |

Counts: Inbox (conversations waiting for an answer), Leads (not contacted, or their reply unanswered), Content (posts to approve,
owner), Newsroom (drafts to review, owner). More shows the sum of the counts inside it, and each row in the sheet shows its own.
Whether the user is the owner is remembered for the browser session (`useIsOwner`), so the bar does not redraw on load.

## Home (`components/app/home/TodayScreen.tsx`, rules in `lib/app/home.ts`)

Top to bottom:
1. Greeting with first name and date; the photo or logo opens My brand.
2. The MahaRERA reminder while the number is owed and dated (agents).
3. **Add listing** and **Share my website** (WhatsApp).
4. **Call today**: each person once, most urgent first: overdue follow-ups, the server's "call now" picks, leads nobody answered
   (longest waiting first), follow-ups due today, hot buyers. Five shown, the rest behind "Show all". Won and lost leads never show.
5. After Call on a row, **Called X? Answered / No answer** logs the call on the lead (the same log as on the lead screen).
6. **To do**: buyers passed to you, messages waiting, listings to confirm (and how many buyers no longer see), live listings
   without photos, listings without marketing (one row however many), posts to approve, join requests, trials, the SEO week.
7. **Get set up** while any step is open: logo or photo, RERA number (agents; left out while the dated reminder shows), first
   listing, first share of the website (remembered on the phone). Below the lists: a new agent has nobody to call, so it is at the top for them.
8. **All caught up** when both lists are empty; then **This week**.

Home reads everything once, and again when the app comes back to the front (after a call or WhatsApp).

A logged call: answered moves a New lead to Contacted with a follow-up in 2 days, and moves an overdue follow-up 2 days on; no
answer sets the follow-up to tomorrow; a date sent with the call wins (`tracking/service.py`, `tests/modules/test_call_log.py`).

## Listing (`app/studio/listings/[id]/page.tsx`)

Tabs: **Overview** (first), Edit, Photos & files, Checked facts, Ask AI. `?tab=status` from older links opens Overview.
Overview: "still available?" card when due; cover photo (or a nudge to add photos); price and facts; views, enquiries and site
visits; for a draft, a publish box that names what is missing and opens the tab to fix it; Start marketing and share for a live
listing; the status buttons (Under offer, Mark sold or rented, Pause, Make live), each that hides the listing asking first; Delete.
Edit keeps Save in reach above the tab bar.

## Add listing (`components/app/NewListingFlow.tsx`)

Describe, Check, Live along the top. A six-line box with an example; chips tick as the agent types the BHK or type, area, price,
size and possession (`lib/app/listingHints.ts`; hints, never a block). Voice is a one-row Premium teaser.

## Inbox

Opens on Needs you while anyone waits. A WhatsApp reply has quick replies that fill the box (sent by hand). Demo mode
(`app_fixtures`) has three conversations.

## Demo mode

`localStorage.app_fixtures = 1` runs Studio on fake data (as the owner). Add `localStorage.app_fixture_agent = 1` to see it as an
agent sees it (agent tab bar, no posts or join requests).

## Leads

A search box (shown once there are more than five leads) finds by name, phone digits (three or more), area, BHK or words they
wrote; every word must match (`matchesSearch` in `lib/app/leads.ts`).
