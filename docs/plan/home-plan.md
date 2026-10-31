# East Pune home plan (2026-10-31, BUILT, not deployed)

Search and the SEO rules for these pages: [seo-system.md](seo-system.md) section 4.

Owner, 2026-10-31: a family answers a few questions and gets "the best projects for us, and why". East Pune only: traffic
comes from all over Pune, but East Pune is where we know the projects and where partner agents sell. Other areas later.

Labels: **LIVE** = running in production, **BUILT** = in the code, not deployed, **NEW** = to build.

## 1. Why

- **A lead we own, with the details that matter.** The plan shows first and asks for nothing (owner 2026-10-31: "show the
  plan before asking for phone number, we can ultimately try to get it if the user wants"). Its one ask, under the picks, is
  "Get this plan on WhatsApp, with today's prices": that sends an Avasetu lead with office, budget, size, move-in and family
  in the message (the owner's first worry: when we show agents' projects, how do we know which buyers came from us). Every
  plan view is a page view on the house account, and a buyer who leaves a number later has those views on their lead.
- **Search.** `/home-plan` is in search (owner 2026-10-31: "publish, that can help us gain position"): it answers "projects
  near EON IT Park / Magarpatta / the airport" with dated counts from the register.
- **Hard to copy.** Portals rank whoever pays. The plan ranks on MahaRERA's record (the filed date and whether it moved,
  homes booked), published asking prices and the distance to the buyer's office: facts we already collect.
- **Demand data.** Answers from buyers outside East Pune are leads too, tagged "outside East Pune": over time they say where
  to recruit agents next.

## 2. How it works (BUILT)

```
/home-plan                 six questions as taps (a GET form, no number), what the register says near each office, FAQ
   ▼
/home-plan/result?work=…&budget=…&bhk=…&movein=…&kids=…&elders=…        (noindex)
   East Pune register projects still being sold → planHomes() → 3–5 picks, each with "Why it fits" and "Worth checking"
   (+ nearest school / hospital when the family asked), a site-visit checklist, then the optional ask:
   "Get this plan on WhatsApp"  →  POST /api/v1/t/inquiry (the same lead path as every form: house agent, auto
   follow-up, passing to agents)
```

No new backend module and no new collection: the answers live in the address (like the finder's, `lib/site/finder.ts`), the
lead is an ordinary enquiry, and the plan re-reads today's facts every time it is opened. The lead's message carries the
plan's link, so the team in Studio opens exactly what the buyer saw.

| Piece | Where |
|---|---|
| Questions, scoring, reasons, checklist, lead message | `frontend/lib/site/homeplan.ts` |
| The questions (a GET form) | `frontend/components/site/homeplan/HomePlanForm.tsx` |
| The optional ask on the plan | `frontend/components/site/homeplan/PlanLeadForm.tsx` |
| East Pune items and the picks' surroundings (server) | `frontend/lib/site/homeplanData.ts` |
| The plan page (noindex, rendered per request) | `frontend/app/home-plan/result/page.tsx` |
| The questions page (in search and the sitemap): the form, per-office counts with ready plans, how we pick, FAQPage | `frontend/app/home-plan/page.tsx` |
| The way in: a box on `/projects`, East Pune place pages, East Pune guides | `frontend/components/site/homeplan/HomePlanBox.tsx` |
| Which agent lists which project (shared with `/projects`) | `frontend/lib/site/offers.ts` |
| Office positions = the project pages' work hubs | `backend/app/core/work_hubs.py`, kept equal by `backend/tests/modules/areastats/test_home_plan_hubs.py` |

### The questions

1. Where the main earner works: Kharadi (EON IT Park, WTC), Magarpatta/Hadapsar, Viman Nagar/Airport, work from home;
   or Hinjawadi/Baner/Wakad, elsewhere in Pune (these get the finder for their side, not a plan, and can "plan for East Pune
   anyway").
2. Budget (the finder's five bands). 3. Size (1, 2, 3, 4+ BHK). 4. Move-in (optional, the finder's three choices).
5. Children: none, under 5, school-going, college or older. 6. Parents living with them: yes/no.

Age bands, not ages; no names of family members; never religion, caste or community.

### Which projects can be picked

Every register project whose Pune place is in the East Pune zone (`app/core/pune_places.py`), still active, not sold out
(unless a partner lists it). Then, for the answers:
- a home on its price sheet of that size inside the budget (a **priced fit**); a project whose published price for that
  size is outside the budget, or whose sheet has only other sizes, or whose lowest price is already above the budget, is out;
- if fewer than 3 priced fits, projects with no published price for the size are added after them, marked "No 2 BHK
  price published yet: ask our team";
- possession inside the move-in answer, when there is one;
- no more than 25 km from the office in a straight line (the project page's own cut-off); a project whose position we have
  not checked stays, with "no distance" said.

### Points (all from stored facts; the table is the place to tune)

| Fact | Points |
|---|---|
| Straight-line km to the office | ≤5: 30, ≤10: 22, ≤15: 12, ≤20: 5 |
| MahaRERA completion date never moved | 20 (unknown: 5, moved: 0 and a "worth checking" line) |
| Homes booked | ≥70%: 15, ≥50%: 10, ≥30%: 5; under 30% is flagged as an early project |
| Completion soon | within 12 months: 20 when parents live with them, children under 5 or move-in by 2027, else 10; 13–24 months: 60% of that; 25–36: 25% |

Ties go by name. **A partner agent's project is never scored up**: it says "Listed by …, a partner agent (not ranked higher
for it)", and its own price sheet stands for the project's prices (as on `/projects`).

### Text

For a family with children under 5 or school-going, each pick also names its nearest school; with parents at home, its
nearest hospital (the project's stored surroundings, `propertyfacts`: OpenStreetMap, straight line), read for the picks only.

Code writes every sentence from the facts ("1.1 km from EON IT Park, Kharadi in a straight line", "Completion date filed on
MahaRERA: Jun 2029, never moved", "60 of 100 homes booked on MahaRERA (60%)"). No model is asked, so there is nothing to
guard and nothing to fall back from. The page says when it read the facts and that distances are straight-line.

## 3. What we measure

Plan views are page views of `/home-plan/result` on the house account (Studio's visits). The leads are ordinary Studio leads whose message starts "East Pune home plan" or "Home plan (outside East Pune)".
Per week: plans sent, how many become site visits and Won, and outside-East answers by office. Compare with the plain
enquiry form on the same pages: if the plan does not bring more or better leads within a few weeks, it goes.

## 4. Next (NEW, in order)

1. Studio count of plan leads and outside-East demand by office (today: search the lead messages).
2. ~~Nearest school and hospital for the picks~~ BUILT 2026-10-31.
3. Partner price sheet in Studio: agents keep today's price per size for the projects they sell, dated, so fewer picks say
   "no price published".
4. The same plan in the WhatsApp bot (`whatsapp/finder_link.py` already turns a chat's area, BHK and budget into a finder link).
5. Drive times instead of straight-line km: computed per project and office once, in a background round, never per buyer.
6. Other areas, once we hold their projects as well as East Pune's.

## 5. Known limits

- Each family's plan stays noindex: thousands of answer combinations would be the "scaled content" Google filtered on
  2026-10-27. Only `/home-plan` itself, with its counted facts, is in search.
- Asking prices are what builders and portals publish, not registered sale prices (IGR Index-II needs a licensed feed:
  `project-pages.md`, "TARGET: registered sale prices").
- Homes booked is what the builder last filed on MahaRERA, often a quarter old.
