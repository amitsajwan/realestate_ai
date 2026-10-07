# Marketing: how it works

How content is made, approved, posted to Facebook and Instagram, and followed up. Code as of 7 Oct 2026; production settings
read from the VM the same day. Plans and work items live in `docs/CONTENT_PLATFORM.md`; the rules every module follows are in
`docs/ARCHITECTURE.md` §6 and §7. Update this file when a part changes status.

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
| Listing walkthrough reel | LIVE | Voice-over on (Google TTS key set). |
| Agent-recruitment reels | LIVE | 10 reels, 4 to 13 Oct, through the calendar. |
| Brand calendar plan (evergreen library, by script) | LIVE | Run by the owner when needed. |
| Trend reels, House Deal launch (by script) | LIVE | Run by the owner when needed. |
| Newsroom (news and MahaRERA, owner approves) | LIVE | |
| Comment replies and DMs | LIVE | Facebook and Instagram, real replies. |
| Interest links, `/go` hub, `?src=` tracking | LIVE | |
| Public feed of our posts (`/posts`) | LIVE | |
| Project page enrichment from MahaRERA | LIVE | |
| Daily reels (area insight + project, 2 a day) | BUILT, OFF | `CALENDAR_DAILY_REELS` unset. |
| Instagram location tags | BUILT, OFF | Needs `IG_LOCATION_*` place ids. |
| Reading reach, plays and watch time back from Meta | TARGET | Nothing reads results yet. |
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
     listing has 2 or more photos. A failed posts step keeps the facts.
3. The agent can edit a caption (`PATCH .../campaign/posts/{angle}`; guard problems come back as warnings) or redo a post
   with a note (`POST .../posts/{angle}/redo`; the note goes to the copywriter).
4. "Send to calendar" (`POST .../campaign/calendar`) adds `planned` rows, one a day at 7 pm IST, 12 hours from other posts on
   the channel. Posts go to both channels; slides reels go to Instagram only. Slugs are `campaign-<listing>-<angle>` with the
   agent's id, so enquiries count per post. Facebook captions carry the listing link with `?src=fb_<angle>`. Edits reach
   planned rows only; approved rows never change.

### Agent pack (LIVE)
`POST /api/v1/listings/{id}/marketing` builds copy from listing facts only, in English, Hindi or Marathi, and renders the
cards `cover`, `facts`, `amenities` (when there are any), `cta` and a WhatsApp `status` image. One pack per listing in
`marketing_packs`, versioned. The agent copies, downloads or shares it on WhatsApp, or posts it (§5, last path).

### Walkthrough reel (LIVE)
`POST /api/v1/listings/{id}/reel` queues a job in `reel_jobs`. The `listing_reels` loop renders one at a time from the
listing's own photos, a checked script and a voice-over. 5 per agent per day.

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
- **Measurement first.** Posts are tagged for measurement, but nothing reads results back. Ranking angles and hooks needs the
  Meta insights reader (TARGET).
