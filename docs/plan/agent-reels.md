# Agent reels: the first 10 (experiment)

Goal: Reel -> agent visits Avasetu -> requests an invite -> signs up -> adds a property. These reels are for Pune property agents, not buyers.

## Format (every reel, about 11.4 s)
| Scene | Seconds | What |
|---|---|---|
| Hook | 2.0 | the agent's problem, at most 7 words; "PUNE PROPERTY AGENTS" chip on frame one; no logo |
| Pain | 2.4 | text only ("Before" on before/after reels) |
| Product | 3.4 | a real Avasetu screen in a phone (sample data; the sample phone number on the lead card is covered) |
| Result | 2.4 | one line |
| CTA | 2.8 | "AGENT comment karein" + "Pune agents ke liye free pilot"; the brand mark appears here |

On-screen text is Hinglish (Roman letters), with music and no voice-over, the same for all 10. That way the message is the only thing that changes from reel to reel.

## The 10 scripts (app/modules/reels/agent_reels.py)
Pain: A1 typing the same WhatsApp message · A2 listings lost in groups · A3 no designer
Demo: B1 voice/text to a listing · B2 one property, all its marketing · B3 photos to a Reel
Before/after: C1 leads in a diary vs lead cards · C2 who to send a new property to vs matching buyers
Result: D1 new agents get a website · D2 50+ properties, who to call first
Posting order: A1 B2 C1 D2 A2 B1 C2 D1 A3 B3, one a day.

## Claims we do not make (enforced by check_script)
No "in seconds" (a listing reel renders in minutes), no "publish/auto-post" (we prepare the posts; posting from an agent's own Page
needs Meta review), no unmeasured numbers, no 24/7, no "more leads". Captions say the screens show sample data.

## Tracking
- Every reel has a code. The Facebook caption link is `/pilot?src=reel_<code>_fb`. A comment such as "AGENT", "interested" or "how to join" gets a pilot reply and a DM with `src=reel_<code>_<fb|ig>`, and is not recorded as a buyer lead.
- `scripts/agent_reels.py report` shows views and Instagram average watch time from the Graph API. Per reel, it also counts answered agent comments, invite requests with that src, sign-ups (matched by phone) and agents who added a property.
- 1 s, 3 s and 5 s retention is not in the API. Copy the hold / skip rate from the Instagram app into the review by hand.

## Run
1. `python scripts/agent_reels.py preview`: review the 10 MP4s.
2. On the VM: `python scripts/agent_reels.py plan --start <date> [--channels facebook_page instagram]`. This adds planned rows; approve them in Studio > Calendar.
3. After 10 days: `python scripts/agent_reels.py report`. Keep the top 3 themes and test 3 new hooks on them. With a small audience, don't pick a single winner.
