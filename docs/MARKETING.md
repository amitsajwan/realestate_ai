# Marketing: how it works

How content is made, approved, posted to Facebook and Instagram, and followed up. Code as of 7 Oct 2026; production settings
read from the VM the same day. Plans and work items live in `docs/CONTENT_PLATFORM.md`; the architecture review of the photos and brochure to reels and posts journey is `docs/MARKETING_ARCHITECTURE_REVIEW.md`; the rules every module follows are in
`docs/ARCHITECTURE.md` §6 and §7. Update this file when a part changes status. Reels and campaign reels updated 11 Oct 2026.

Every part below carries one status:

| Status | Meaning |
|---|---|
| **LIVE** | Built, switched on in production, used. |
| **BUILT, OFF** | Built and tested; its switch is off in production. |
| **TARGET** | Not built. Planned in `docs/CONTENT_PLATFORM.md`. |

## 1. Status at a glance

| Part | Status | Notes |
|---|---|---|
| Approval calendar and its runner | LIVE | Real posting on. Testing pace: approved posts go out 10 minutes apart (`CALENDAR_PACE_MINUTES=10`). Set it to 0 for planned times. |
| Listing campaign from Studio ("Start marketing") | LIVE | Facts, posts, slides reels, edit and redo, send to calendar. |
| Agent marketing pack (cards, captions, WhatsApp) | LIVE | One per listing. |
| Posting a pack straight to the Avasetu Page and Instagram | LIVE | Bypasses the calendar; see §8. |
| Listing walkthrough reel | LIVE | Voice-over on (Google TTS key set). Two styles: tour and stack (§4). |
| Agent-recruitment reels | LIVE | 10 reels, 4 to 13 Oct, through the calendar. |
| Brand calendar plan (evergreen library, by script) | LIVE | Run by the owner when needed. |
| Trend reels, House Deal launch (by script) | LIVE | Run by the owner when needed. |
| Newsroom (news and MahaRERA, owner approves) | LIVE | |
| Comment replies and DMs | LIVE | Facebook and Instagram, real replies. |
| Interest links, `/go` hub, `?src=` tracking | LIVE | |
| Public feed of our posts (`/posts`) | LIVE | |
| Project page enrichment from MahaRERA | LIVE | |
| MahaRERA QR badge on project ads (AR-3) | BUILT | Pack cards, campaign cards, reel closing scene; only for a trusted project number (§4). |
| Daily reels (area insight + project, 2 a day) | BUILT, OFF | `CALENDAR_DAILY_REELS` unset. |
| Instagram location tags | BUILT, OFF | Needs `IG_LOCATION_*` place ids. |
| Reading reach, plays and watch time back from Meta | BUILT | `insights/collector.py` (PR #60) reads them into `content_metrics`, grouped by the calendar tags. Production state not checked here. |
| Shared store of verified facts | TARGET | Facts live in three places today. |
| Builder record, portal prices, road distances | TARGET | Campaign facts come from MahaRERA, OpenStreetMap and calculators only. |
| Per-listing LLM budget | TARGET | |
| Campaign drafts sent to the calendar automatically | TARGET | Today the agent taps "Send to calendar". |

## 2. The shape

```
 MADE BY                                       GATE                              OUT                          AFTER
 Brand calendar, scripts (owner)      ─┐
 Listing campaign (agent, Studio)     ─┼─► content_calendar rows   ─► calendar runner ─┐   interest links, /go hub
 Daily reels (off)                    ─┘   "planned" until the        (worker loop)    │   comment replies + DMs
                                           owner approves in                           ├─► distribution.send ─► Meta Graph
                                           Studio > Content                            │   (publish_ledger:      (FB Page,
 Newsroom (worker loop)  ─► owner approves in Studio > Newsroom ──────────────────────┤    once per key)         Instagram)
 Agent pack (Studio)     ─► agent ticks approve + consent ─► social service ──────────┘   /posts feed, ?src= tracking
                            or shares it on WhatsApp by hand                               deleted posts marked "removed"
```

Three rules hold everywhere:
- **Nothing posts without a human yes.** Calendar rows start `planned`, and only `approved` rows are ever due. A pack post
  needs `approve` and `consent`. News needs the owner's approval.
- **One way out.** Every post goes through `send(db, key, publish)` in `backend/app/modules/social/distribution.py`. It
  records each key in `publish_ledger`, so a retry or a restart never posts twice. An import rule forbids any other module
  from calling the Graph API to publish.
- **Code calculates, models write.** Numbers come from the listing, MahaRERA, OpenStreetMap or calculators. The creative
  guards refuse any number, price, prediction, phone number, URL or hype that is not in the Brief, and fall back to a
  deterministic draft. No AI agent publishes.

## 3. Where the code lives

| Process | Runs |
|---|---|
| API | Studio actions (approve, post now, start a campaign, make a pack, post a pack, queue a reel), public feed, interest links. |
| Worker (`python -m app.worker`) | The loops `calendar`, `marketing_runs`, `listing_reels`, `engage`, `newsroom`, `project_enrich`. Each runs under a lease so only one copy runs, and writes a heartbeat; `--check` reports a stale loop. |
| `backend/scripts/` | Owner tools that add planned rows or render previews: `calendar_admin.py`, `agent_reels.py`, `trend_reels.py`, `house_deal_golive.py`, `property_campaign.py`, `reels_admin.py`. |

| Module (`backend/app/modules/`) | Role |
|---|---|
| `creative` | The pipeline: strategist, copywriter, art director, render, critic, one regeneration. 8 card layouts, guards, Hindi and Marathi translation. Works without an LLM. |
| `marketing` | The agent pack: copy from listing facts, cards, WhatsApp text; brand fonts and mark. |
| `calendar` | The approval calendar: plan, build, store, runner, caption guards, hashtags, duplicate and deletion checks, public feed. `adapters.py` is its only link to creative, reels and agent projects. |
| `propertyfacts` | Listing campaigns: fact sheet, posts per angle, send to calendar, edit and redo; the public "Checked for you" facts. |
| `reels` | Video: compositor, slides reels, walkthrough reels, recruitment and trend reels, voice, music. |
| `social` | `distribution.py` (the one way out), `service.py` (pack posting), `reel_publish.py` (Reels upload). |
| `interest`, `engage`, `tracking` | After posting: interest links and hub, comment replies, visits and enquiries. |
| `newsroom`, `agentprojects`, `areastats` | Content sources: news and the MahaRERA register, agents' builder projects, area numbers. |
| `backend/app/platform/meta_graph` | Graph API client and settings, dry-run publisher, error sanitising. |

`backend/app/wiring.py` connects modules at startup with callbacks, so no module imports one above it.

Studio screens: Content (`frontend/app/studio/content`) for the calendar, the listing marketing screen
(`frontend/components/app/MarketingScreen.tsx`) for packs, campaigns, reels and pack posting, and Newsroom.

## 4. How content is made

### Listing campaign (LIVE)
The agent taps "Start marketing" on a listing (`MarketingRunCard.tsx`).
1. `POST /api/v1/listings/{id}/campaign` queues a job in `marketing_runs`.
2. The `marketing_runs` loop (`propertyfacts/jobs.py`) runs two steps:
   - **Facts.** The sheet is built from the listing, our MahaRERA register, live MahaRERA, OpenStreetMap places and
     calculators (rate per sq ft, guntha, EMI). Each fact keeps its sources and a trust level: official, measured,
     corroborated, single or conflict. Only the first three reach posts. The sheet is kept in `property_facts`, and the
     listing page shows it as "Checked for you".
   - **Posts.** One Brief per angle the facts support (11 angles, such as price reveal, commute, MahaRERA check, EMI), each
     run through the creative pipeline. Up to 2 slides reels come from the carousels. A walkthrough reel is queued when the
     listing has 2 or more photos, voiced in the campaign's language. Its style (tour or stack) is fixed per listing from the
     listing id, about half each (`jobs.walkthrough_style`). A failed posts step keeps the facts.
3. The agent can edit a caption (`PATCH .../campaign/posts/{angle}`; guard problems come back as warnings) or redo a post
   with a note (`POST .../posts/{angle}/redo`; the note goes to the copywriter).
4. "Send to calendar" (`POST .../campaign/calendar`) adds `planned` rows, one a day at 7 pm IST, 12 hours from other posts on
   the channel. Posts go to both channels; slides reels go to Instagram only; the walkthrough goes to both once rendered,
   tagged `experiment: walkthrough_style`, `variant: tour | stack` so its results compare the two styles. Slugs are `campaign-<listing>-<angle>` with the
   agent's id, so enquiries count per post. Facebook captions carry the listing link with `?src=fb_<angle>`. Edits reach
   planned rows only; approved rows never change.

### Brochure (BUILT)
The agent uploads the builder's brochure PDF on the listing (`POST /api/v1/listings/{id}/brochure`, up to 40 pages and 30 MB;
`propertyfacts/brochure.py`, `brochure_parse.py`, collection `brochures`). The original is kept under
`uploads/brochures/<listing>/<sha>.pdf` and read once per file: pdfium reads each page's text layer and makes a page thumbnail.
Rules find the project, builder, MahaRERA number, address, configurations, carpet area per configuration, amenities,
specifications, possession, land area, towers, floors and units, each with its page and the exact words. The free model may add
facts, but only ones whose quote is on that page and whose value is in the quote (brochure text goes in a marked data block,
never in the instructions). Pages without text are listed as image-only (no vision step yet; no paid AI).
- Every fact is a `builder_claim`, pending until the agent confirms, fixes or drops it (`PATCH .../brochure/facts/{id}`).
  Confirmed claims join the fact sheet (`gather.py`) but never override MahaRERA or the listing: a different possession month,
  unit count, carpet area or RERA number is kept as a disagreement and listed in the run's notes.
- Posts use claims only attributed: the `configurations`, `amenities` and `specifications` angles say "as per the builder's
  brochure", and their numbers are written into the Brief, so the guards accept them as stated and refuse any other.
- Registration: a brochure's MahaRERA number is looked up (`verified`), else held (`unverified`, never posted as registered).
  With no number the kit asks "registered, or exempt?" (RERA Act section 3) and keeps the answer
  (`POST .../brochure/registration`). Without a MahaRERA record the possession, MahaRERA check and project size angles are
  skipped, and captions promise no MahaRERA record.

### Agent pack (LIVE)
`POST /api/v1/listings/{id}/marketing` builds copy from listing facts only, in English, Hindi or Marathi, and renders the
cards `cover`, `facts`, `amenities` (when there are any), `cta` and a WhatsApp `status` image. One pack per listing in
`marketing_packs`, versioned. The agent copies, downloads or shares it on WhatsApp, or posts it (§5, last path).

### Walkthrough reel (LIVE)
`POST /api/v1/listings/{id}/reel` queues a job in `reel_jobs`. The `listing_reels` loop renders one at a time from the
listing's own photos, a checked script and a voice-over. 5 per agent per day. The body takes `lang` (en, hi, mr) and
`style`:
- **tour** (default): one photo per beat, slide cuts, the beat's line on each photo.
- **stack**: one screen. Each beat's line joins under the ones before and stays, the photos walk through behind it (a new
  photo with each line), and each line is spoken as it lands. The call to action and "Listed by" land last.
A stack reel is its own job and file (`listing-<id>-<lang>-stack-<short>.mp4`). Posting outside the calendar uses the tour.
In Studio the agent picks Tour or Stack under "Make my reel" and sees the latest reel of each style (`GET .../reel?style=`).
The owner's concierge reel path does not take a style yet (tour only).

### Which photos (LIVE, pixel checks only)
`photoquality.rank_photos` chooses the photos for the walkthrough reel (`listing_reel.scene_photos`, up to 5), and its hero
is the photo on the pack's cover card and on the campaign posts (`marketing.images.cover_photo_path`), so the slides reels
built from those posts get it too. Near-identical photos (a perceptual hash and a colour check) keep only the best copy.
Blurry, dark, small and "mostly floor or sky" photos are left out, and come back last only when fewer than the minimum
would remain (2 for a reel, 1 for a cover). The agent's order decides otherwise. The hero is a well-exposed landscape photo
with the best score (scores within 10 points count as equal). The enhanced copy is used when the agent kept it on. No AI is
involved; room and kind tags (AR-5) come later.

### MahaRERA on our ads (BUILT, AR-3)
**What MahaRERA requires** (researched 11 Oct 2026; MahaRERA's own site does not answer from our build sandbox, so the order's
wording comes from MahaRERA's order list and the law-firm and press summaries below, not from the PDF itself):
- **Order 46C/2025, 8 April 2025**, "Norms for QR Code and font size of MahaRERA registration number in advertisements", is the
  one in force. Every advertisement of a registered project, by a promoter or a registered agent, in any medium (print,
  hoardings, social media posts, WhatsApp, digital banners, video thumbnails) shows three things: the **MahaRERA project
  registration number**, the **website maharera.maharashtra.gov.in**, and the **project's own MahaRERA QR code**.
- **Size and place.** The number and the website are set in a font no smaller than the largest font used for the ad's contact
  details and address. The summaries place all three in the **top right** of the creative, in a visible colour, and the QR
  code keeps its aspect ratio so it stays scannable. No minimum QR size in pixels is given.
- **Earlier orders it builds on.** Order 46/2023 (May 2023) put a QR code on every project's registration certificate from
  1 Aug 2023 and required it on ads; Order 46A/2023 set the penalties; Order 46B/2023 (Aug 2023) extended the rule to agents
  (the QR code shown prominently, next to the project registration number).
- **Still applies in 2026.** No later order replaces 46C/2025; 2026 compliance checklists still cite it, and MahaRERA keeps
  fining: 628 projects for Rs 88.90 lakh in 2024, six Pune projects Rs 15,000 each. Penalties are reported as Rs 10,000 to
  Rs 50,000 per ad (section 63 of the RERA Act).
- **What the official QR opens.** Scanning a project's MahaRERA QR opens that project's public page on MahaRERA (name,
  promoter, dates, approvals). The exact URL inside the official code could not be confirmed from here.

**What we print.** `marketing/maharera.py` draws one badge with `segno` (QR) and Pillow: a white panel, the QR code with its
quiet zone, "MahaRERA: P5..." and "maharera.maharashtra.gov.in". The QR encodes the most specific official URL we can verify:
the project's public page `https://maharerait.maharashtra.gov.in/public/project/view/<MahaRERA id>` (the page MahaRERA's
own search links each project to; our code reads it, verified 3 Oct 2026) when the fact sheet or our register knows the id,
otherwise `https://maharera.maharashtra.gov.in/`, where the number under the code is searched. No other URL can be encoded.
- Where: top right of the pack's cover, cta and WhatsApp status cards; every campaign card (all seven buyer layouts, beside or
  under the kicker chip; a carousel carries it on its cover and closing slide, not the inner slides); the walkthrough reel's
  closing scene (tour) or with the closing lines (stack). QR codes are 148 to 185 px on the pack cards, 135 to 148 px on campaign cards, 222 to 225 px on a reel frame, with
  whole pixels per module. Tests decode each one back with OpenCV.
- When (`propertyfacts/advert.py`): only for a project number we trust: MahaRERA's own record of it on the fact sheet, else
  the listing's `rera_no` (the agent's data), else the brochure kit's `verified` or `registered_by_agent` number. `exempt`,
  `unknown`, an `unverified` brochure number, a number MahaRERA contradicts, a sample listing and the agent's own registration
  (A5..., which stays in "Listed by ... · RERA ...") never get a badge or a registration line. The pack and the reel ask through
  `marketing.maharera.configure` (wired in `app/wiring.py`); campaigns pass the brochure kit to `campaign.plan/make`.
- Open: the contact strip on an agent's campaign cards shows the phone at 40 px while the badge text is 24 px, below the
  order's font rule; the pack cards (no phone) use 30 px, as large as "Listed by". Owner to decide: a smaller phone or a
  larger badge. Letting the agent upload the official QR from the registration certificate would make the code identical to
  MahaRERA's; not built.
- Samples: `docs/content/showcase/maharera-qr/`.

Sources: [MahaRERA orders list](https://maharera.maharashtra.gov.in/order);
[Complinity on Order 46C/2025](https://complinity.com/legal-update/maharashtra-real-estate-regulatory-authority-maharera-issues-order-regarding-the-mandatory-display-of-qr-code-font-size-specifications-for-maharera-registration-number-and-website-address-in-advertisements-18613/);
[Desai and Diwanji](https://desaidiwanji.com/insights/articles/transparency-first-maharera-enforces-stricter-rules-for-real-estate-advertising);
[Real Estate Law Journal](https://realestatelawjournal.in/maharera-qr-code-registration-ad-guidelines-2025/);
[Palladian, 2026 checklist](https://palladian.in/maharera-advertising-rules-2026-the-compliance-checklist-to-run-before-your-next-launch/);
[TaxGuru on the 2023 order](https://taxguru.in/corporate-law/matter-non-display-quick-response-qr-code-promotions-advertisement-real-estate-projects-registered-maharera.html);
[WIRC-ICAI, Sep 2023 (46A, 46B)](https://old.wirc-icai.org/newsletters/2023/september/maharera.html);
[Housing.com, QR from 1 Aug 2023](https://housing.com/news/qr-code-display-in-all-maharera-registered-projects-mandatory-from-aug-1-2023/);
[Storyboard18, 628 projects fined](https://www.storyboard18.com/amp/how-it-works/maharera-penalises-628-projects-over-absence-of-qr-codes-in-ads-registration-number-36609.htm);
[Pune Pulse, Ravetkar fines](https://www.mypunepulse.com/pune-maharera-fines-six-ravetkar-projects-%E2%82%B990000-for-violating-advertisement-disclosure-norms/);
[99acres on the project QR](https://www.99acres.com/articles/maharera-launches-qr-code-to-access-project-details-nid.html).

### Reel formats (templates, `reels/templates.py`)
- **Tip, pitch, listing tour** ("guess the price"): scenes that replace each other.
- **Stacked list** (`stacked_list`, `listing_stack`): the hook is on screen from frame one; each fact joins under it every
  two beats of the brand theme (84 bpm, 1.43 s) and stays; the call to action lands last. `listing_stack` opens with the
  price and holds the locality back to the end. `stacked_list` takes any lines, such as a buyer requirement ("Wanted: 2 to 5
  acres..."). A listing photo is blurred into a backdrop so frame one is calm.
- Reel text: Latin text is drawn in Poppins, Devanagari in Mukta (the creative cards' font), shaped by libraqm. A Hindi or
  Marathi walkthrough (tour and stack) and `listing_stack(lang=...)` show their screen lines in Devanagari; the comment
  keyword stays INTERESTED in Roman capitals, and digits stay Western (Devanagari digits in an LLM line are read as the same
  numbers by the no-invented-number check). Without libraqm the screen text falls back to English or Hinglish, as before.
  Tip, pitch, trend and recruitment reels keep Roman text. Sample frames: `docs/content/showcase/devanagari/`.

### Owner content (LIVE, by script)
- **Brand calendar.** `calendar_admin.py plan --start <date> --weeks 4 [--llm]` lays out about 5 Instagram and 5 Facebook
  slots a week at 10:00 or 19:00 IST from the 40-post evergreen library, makes the creative and stores `planned` rows.
  `preview-plan` makes contact sheets; `--dry-check` runs the caption guards.
- **Recruitment reels.** `agent_reels.py plan` adds the 10 reels, one a day, on the Facebook Page.
- **Trend reels.** `trend_reels.py --queue` adds explainer reels whose figures come from dated, sourced facts.
- **House Deal.** `house_deal_golive.py` queues the project carousels and reels.

### Newsroom (LIVE)
The `newsroom` loop collects news and MahaRERA updates, then filters, extracts, drafts and checks them. Items wait for the
owner. Approved items post with a daily cap: a text post with our link on Facebook, the card on Instagram.

### Daily reels (BUILT, OFF)
With `CALENDAR_DAILY_REELS=on`, `calendar_admin.py daily` plans a morning area-insight reel from MahaRERA register data and an
evening reel of a consented agent's project or a buyer guide.

## 5. Approval and posting

```
planned ──approve──► approved ──due──► published ──deleted on the platform──► removed
   │                    │
   └──skip──► skipped   └──unapprove──► planned          failed (3 tries) ──retry──► approved
```

Studio > Content shows To approve, Going out, Problems and Posted. Approve, skip, unapprove, post now and retry are for the
owner only (`CALENDAR_OWNER_IDS`). Post now spaces several posts 10 minutes apart per channel, because a burst hit Meta's limit.

The calendar runner (`calendar/runner.py`, every 120 seconds in production):
- skips the pass when the owner paused posting;
- renders approved reels due within 2 hours in the background;
- posts at most one due row per channel per pass;
- holds back a row whose opening line already went out on that channel recently, and skips a row more than 48 hours late,
  so an outage never causes a burst;
- adds the interest line and the footer, and replaces the caption's hashtags with one line of the best few: 5 on Instagram,
  3 on Facebook, most specific first (locality, project, property type), from `calendar/reach.py`;
- posts by kind: an image or Instagram carousel, or a Reel. Facebook's copy of a carousel goes out as a slides Reel, because
  Facebook shows a multi-photo post as a grid. Sample-home showcase posts are retired: a leftover showcase row is never posted;
- retries a failure after 10 minutes, at most 3 tries, with a sanitised reason shown in Problems;
- adds image posts to the `/go` hub and marks posts deleted on the platform as `removed`.

The pack path is different. `POST /api/v1/social/listings/{id}/publish` posts at once when the agent ticks approve and
consent. Instagram gets the cards as a carousel; Facebook gets the cover and the listing link. One record per listing, channel
and pack version in `publications`.

Under both, `distribution.send` claims the key in `publish_ledger` (`calendar:<row>`, `social:<publication>`,
`news:<item>:<channel>`). A key already sent returns the earlier post. A key whose earlier attempt never finished is refused
as "may already be live": check the page, then delete that ledger document to allow a retry. Meta fetches media from
`PUBLIC_MEDIA_BASE_URL/uploads/...`, which must be public https.

## 6. After posting (LIVE)

- **Interest links.** Every calendar post gets a short link per post and channel. Facebook shows it; Instagram says "link in
  our bio", which opens the `/go` hub. A tap becomes an enquiry for the owning agent.
- **Interest page (`/i/<code>`).** With a WhatsApp number set (`NEXT_PUBLIC_WHATSAPP_NUMBER`), "Chat on WhatsApp" is the main
  button (the chat gives us the buyer's number without typing) and "I am interested" the second; without one, the one-tap stays
  the main button. After the tap: "Which configuration?", then "Your budget?" (one tap each, skippable), then the optional
  details form. Answers go to `POST /public/interest/<code>/answers` and become the lead's stated requirement; they never count
  toward the 3-per-hour interest limit. Works without JavaScript (`/i/<code>/tap`, `?done=1&q=budget|details`).
- **Link comment on Facebook reels.** A Facebook reel (or slides reel) gets the Page's own first comment with its interest link,
  because a reel's description link is often not tappable and a comment's is. Once per row (ledger key `calendar-comment:<row>`),
  best effort, never pinned (the Graph API cannot pin). `CALENDAR_REEL_LINK_COMMENT=off` turns it off. Instagram has no
  equivalent: comment links are not tappable there.
- **DM assistant (BUILT, OFF).** Messages to the Page (Messenger) and to Instagram are answered by the WhatsApp assistant's brain
  (`whatsapp/dms.py`, webhook `/messenger/webhook`): grounded answers in the buyer's language, the number asked with consent, a lead from
  the first message (the commenter's existing lead when the comment assistant messaged them). A person replying from the Page inbox pauses
  it in that chat for 12 hours. Setup: `docs/MESSENGER_SETUP.md`. `MESSENGER_ENABLED` (off), `MESSENGER_DRY_RUN` (on).
- **Comments.** The `engage` loop reads new comments on the Page and on Instagram, decides with rules and an LLM, and answers
  from the post's facts. Every answer is checked for numbers, phone numbers and hype. Interested commenters get a DM with
  the link. Replies are capped per hour and per person.
- **Tracking.** `?src=` on every link counts visits per post and channel.
- **Public feed.** `/posts` and `/posts/<slug>` show only published posts with a real link.

## 7. Data and switches

| Collection | Holds |
|---|---|
| `content_calendar` | One row per post per channel: slug, kind, caption, media, tags, due time, status, history. |
| `publish_ledger` | One document per publish key: sending, sent or failed. |
| `marketing_runs` | Listing campaign jobs with their posts. |
| `property_facts` | Kept fact sheets with sources and levels. |
| `brochures` | Brochure kits per listing and file: facts with page, quote and state, the registration answer (`propertyfacts/brochure.py`). |
| `marketing_packs`, `publications` | Agent packs, and pack posts with consent. |
| `reel_jobs` | Walkthrough reel jobs. |
| `engage_comments` | Each handled comment, once. |
| `admin_settings` (`controls`) | Pause switches: `posting_paused`, `comments_paused`, `news_paused`. |
| `worker_leases`, `worker_heartbeats` | Which process runs each loop, and when it last ran. |

| Switch | Production on 7 Oct | Default |
|---|---|---|
| `SOCIAL_DRY_RUN` | false (real posts) | true |
| `CALENDAR_ENABLED` | true | false |
| `CALENDAR_INTERVAL_SECONDS` | 120 | 300 |
| `CALENDAR_PACE_MINUTES` | 10 (testing pace) | 0 |
| `CALENDAR_POST_NOW_GAP_MINUTES` | 10 | 10 |
| `CALENDAR_DAILY_REELS` | unset (off) | off |
| `ENGAGE_ENABLED`, `ENGAGE_DRY_RUN` | true, false (real replies) | false, true |
| `NEWSROOM_ENABLED` | true | false |
| `PROJECT_ENRICH_ENABLED` | on | off |
| `PUBLISH_LEDGER` | unset (on) | on |
| `META_PAGE_ID`, `META_PAGE_ACCESS_TOKEN`, `META_IG_BUSINESS_ID`, `PUBLIC_MEDIA_BASE_URL` | set | unset |
| `GOOGLE_TTS_API_KEY` | set | unset |
| `IG_LOCATION_*` | unset | unset |

## 8. Open decisions

- **Two ways to post a listing.** Posting a pack goes out at once with a fixed card set, and Facebook gets only the cover.
  A campaign goes through the calendar with many angles, spacing and the duplicate check. Choose one: route pack posting
  through the calendar, or retire it in favour of campaigns.
- **Who approves agent campaigns.** Campaign rows land on the owner's calendar and only the owner approves them. Agents do not
  see their posts' approval state.
- **Measurement first.** Posts are tagged for measurement and the insights collector (PR #60) reads results back. The first
  comparison running is the walkthrough style (tour vs stack) on campaign reels.

## 9. Improvements found (11 Oct 2026)

Found while building the stacked reels. Most impact first.

| What | Why it matters | Size |
|---|---|---|
| DONE: walkthrough caption in the reel's language | `listing_reel.caption(listing, attribution, lang)`: the title line in English, Hindi or Marathi, the same price and area, 'Listed by' and RERA as before. The campaign and the concierge pass the reel's language | Small |
| DONE: voice-over sounds more natural | `reels/narration.py`: the whole script in one request (SSML with a 1.2 s `<break>` between lines; Chirp 3 HD voices take `<break>`, `<prosody>` and `<voice>`, not `<mark>`, so there are no timepoints), cut at those pauses and each line placed at its beat; when the cut does not give one piece per line, each line is synthesised on its own as before. The music is ducked under the voice (`sidechaincompress`) and comes back between lines and at the end. Hindi and Marathi rules lines are spoken sentences ("कार्पेट एरिया आहे 780 स्क्वेअर फूट, आणि हे 22 मजली इमारतीत 7व्या मजल्यावर आहे"), and the LLM prompt asks for the same. Same voice and free tier. A cloned or custom voice must be a consenting person's, and realistic AI audio gets Meta's AI label. | Medium |
| No Devanagari font for reel text | DONE (11 Oct): Hindi and Marathi walkthroughs and listing stacks show Devanagari (Mukta, §4) | Medium |
| No buyer-requirement post type | "Wanted" posts draw replies from sellers and brokers; only the reel template exists | Small to medium |
| `main` is a stale 2025 branch | Work happens on `cursor/analyze-and-fix-styling-issues-cacb`; new PRs point at `main` by default and show unrelated history. Make the working branch the default on GitHub. | Small |
| `scripts/reels_admin.py` imports a `publish` module that no longer exists | The preview command fails | Tiny |

Voice cost (Google Cloud TTS, list prices seen 11 Oct 2026): Chirp 3 HD has 1 million free characters a month (a reel's
voice-over is about 300 to 400 characters); instant custom voice is US$60 per million characters with no free tier.
