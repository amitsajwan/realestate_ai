# Studio: how it is laid out and why

Studio (`/studio`) is the phone app for agents and the owner. This page records its shape after the 2026-10-27 pass, so later
changes keep to it. Studio is its own Next.js app since 2026-11-03 (`studio/`, ARCHITECTURE §9). Code: `studio/app/studio/`,
`studio/components/app/`, rules in `studio/lib/app/`; its copy is in `shared/strings.ts`.

## Principles

- **One thing, one place.** Each person or task appears once on a screen. Home used to name the same buyer in "Needs you now",
  in an "AI recommends" card and under "Hot buyers".
- **Act from the row.** Call and WhatsApp sit on the row of a person to call; a listing's publish, marketing, share and
  sold/pause buttons sit on its first screen.
- **Open on what needs you.** Lists open on their "Needs you" tab while anything waits there (Inbox, Leads, Listings, Content).
- **Navy and gold.** Primary buttons, selected chips, tab bars and the spinner use navy `#0f2340`; counts that need you are gold
  `#f0b440`. WhatsApp actions stay green. Links stay blue.
- **A failing source is left out, never an error on the screen**, except the server's day summary on Home, which shows a retry.
- **Tab rows are one line** that scrolls sideways (`TabBar`); a wrapped second row read as another set of tabs (2026-11-19).
- **Save stays in reach.** A long form keeps its Save in a sticky bar right on the tab bar (`ABOVE_TAB_BAR` in `ui.tsx`), with
  its answer (saved, or the error) in the same bar: listing Edit, My brand.
- **Full width on a phone.** An old modal rule in `styles/mobile.css` padded every `fixed inset-0` element by 16 px, the whole
  Studio frame and its bottom sheets included, until 2026-11-19; Studio's frame (`data-surface="v2"`) is left out of it now.

## Tab bar

| Who | Bar | More |
|---|---|---|
| Agent | Home, Inbox, Leads, Listings | Results, Content, Buyer radar, My brand and website |
| Owner | Home, Inbox, Content, Newsroom | SEO, Leads, Listings, Results, Buyer radar, Agents, Site, Admin, Press, My brand and website |

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

## Admin and Site (owner, 2026-11-19)

**Admin** (`components/app/admin/AdminScreen.tsx`): Add agent, **Today** (the day's counts, each tile opening its screen), Agents
in one line ("3 agents · 2 still setting up · 1 asked to join", opening Agents), Site in one line, **Health**, **Controls**. What
waits for the owner is on Home's To do and the Newsroom tab's count, not repeated here. It used to be eight sections, five
screens on a phone.

**Site** (`/studio/site`, `SiteScreen.tsx`): what the owner edits on the public site, a tab each: Hot banner, Map pins, From
above (pictures from above), Photos (the area photos screen; agents still reach it from their own More as Area photos).

## SEO (owner)

Tabs: To do, Rankings, Rivals, Audit, Hot projects, Pages, Found on Google, System. **Rankings** opens on This week; every other
section (project pages in Google, indexed by area, page check, AI search, what works, target searches, latest fixes, searches
with no page) is closed to its title and one number until tapped, and long lists show 10 at a time. **Rivals** holds the
weekly scoreboard: where we stand, the sites above us, MagicBricks head to head (2026-11-19; it used to open Rankings).

## Listing (`app/studio/listings/[id]/page.tsx`)

Tabs: **Overview** (first), Edit, Photos, Facts, Ask AI (short labels from 2026-11-19, so all five fit a 360 px phone). `?tab=status` from older links opens Overview.
Overview: "still available?" card when due; cover photo (or a nudge to add photos); price and facts; views, enquiries and site
visits; for a draft, a publish box that names what is missing and opens the tab to fix it; Start marketing and share for a live
listing; the status buttons (Under offer, Mark sold or rented, Pause, Make live), each that hides the listing asking first; Delete.
Edit keeps Save in reach above the tab bar.

Activity (`/studio/listings/[id]/activity`): totals, the 14-day chart, sources, interested people (each opens the lead), then
recent activity with views by anonymous visitors folded into one line ("7 views by visitors (WhatsApp 2, ...)", Show each view);
what people did (enquiries, taps, shares, a named lead's views) stays in the list (`quietFeed`, 2026-11-19).

## Add listing (`components/app/NewListingFlow.tsx`)

Describe, Check, Live along the top. A six-line box with an example; chips tick as the agent types the BHK or type, area, price,
size and possession (`lib/app/listingHints.ts`; hints, never a block). Voice is a one-row Premium teaser.

## Inbox

Opens on Needs you while anyone waits. A WhatsApp reply has quick replies that fill the box (sent by hand). Demo mode
(`app_fixtures`) has three conversations.

## On your phone (2026-11-03)

Studio installs from the browser, with no app store: its own manifest (`/studio/manifest.webmanifest`, scope `/studio`, opens on
Studio home; long press: Add listing, Leads) and a service worker (`/studio/sw.js`) that shows alerts and a short offline note.
Nothing is cached, so Studio never shows old leads.

- **Studio on your phone** card (`components/app/PhoneApp.tsx`, rules in `lib/app/phone.ts`): on Home after Get set up, while
  installing or lead alerts are still to do, until Not now; always on My brand, where alerts can be turned off. Chrome gets an
  Install button; iPhone gets Share > Add to Home Screen, and alerts only once Studio is on the home screen (iOS 16.4+).
- **Lead alerts** ring for what has a person waiting: a new lead (website form, chat, WhatsApp, messages), a buyer waiting for an
  answer, a WhatsApp reply, a comment to answer, a buyer passed to you, the 2-hour waiting alert, and for the owner trials, invite
  requests and agents asking for a lead (`push.TITLES` in the backend). A tap opens that lead or screen. The SEO week and similar
  wait on the badge.
- A lock screen never shows a buyer's number. Signing out turns that phone's alerts off; opening Studio links them to whoever is
  signed in.

## Demo mode

`localStorage.app_fixtures = 1` runs Studio on fake data (as the owner). Add `localStorage.app_fixture_agent = 1` to see it as an
agent sees it (agent tab bar, no posts or join requests). Since 2026-11-19 every owner screen has demo data too: SEO (all tabs),
project pages, buyer radar, press and the lead board (`lib/app/fixtures-owner.ts`, made-up projects and numbers in the server's
shapes; `__tests__/app/fixtures-owner.test.ts` checks none of them calls the network).

## Owner-only screens (2026-11-19)

Admin, SEO, Newsroom, Press, Site and Agents (`lib/app/owner.ts`) are the owner's: the server refuses their data to anyone else.
An agent who opens one by a link or an old bookmark gets "This screen is for the owner" and Back to Home from the Studio frame
(`AppShell`), not a server error. While Studio does not yet know who is signed in, it shows a spinner, so the owner never sees
the note flash. Buyer radar and the lead board are open to agents (the server scopes them).

## Lead (`components/app/LeadDetailView.tsx`, 2026-11-19)

Top to bottom: name, phone, how they reached us; **Call and WhatsApp in a bar that stays at the top** while scrolling; "Called
them? Answered / No answer"; their message; **Stage**; **Follow-up** (Tomorrow, In 3 days, Next week), Draft follow-up and the
message from Avasetu's WhatsApp; then the AI summary and the buyer brief, chats, what they want, matching listings, site visits,
add a note, notes, timeline. The AI summary names a call or WhatsApp step without a second button (the bar has it); a visit or
follow-up step keeps its button. It used to offer five ways to reach the buyer in five places, with the stage two screens down.

## Leads

A search box (shown once there are more than five leads) finds by name, phone digits (three or more), area, BHK or words they
wrote; every word must match (`matchesSearch` in `lib/app/leads.ts`).
