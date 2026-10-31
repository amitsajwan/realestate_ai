# East Pune home plan (2026-10-31, BUILT, not deployed)

Owner, 2026-10-31: a family answers a few questions and gets "the best projects for us, and why". East Pune only: traffic
comes from all over Pune, but East Pune is where we know the projects and where partner agents sell. Other areas later.

Labels: **LIVE** = running in production, **BUILT** = in the code, not deployed, **NEW** = to build.

## 1. Why

- **A lead we own, with the details that matter.** The plan needs a name, a mobile and consent, and sends an Avasetu lead
  with office, budget, size, move-in and family in the message (the owner's first worry: when we show agents' projects, how
  do we know which buyers came from us).
- **Hard to copy.** Portals rank whoever pays. The plan ranks on MahaRERA's record (the filed date and whether it moved,
  homes booked), published asking prices and the distance to the buyer's office: facts we already collect.
- **Demand data.** Answers from buyers outside East Pune are leads too, tagged "outside East Pune": over time they say where
  to recruit agents next.

## 2. How it works (BUILT)

```
/home-plan                 six questions as taps + name, mobile, consent
   │  POST /api/v1/t/inquiry   (the same lead path as every form: house agent, auto follow-up, passing to agents)
   ▼
/home-plan/result?work=…&budget=…&bhk=…&movein=…&kids=…&elders=…
   East Pune register projects still being sold → planHomes() → 3–5 picks, each with "Why it fits" and "Worth checking"
   + a site-visit checklist for this family, + WhatsApp us, + the finder with the same answers
```

No new backend module and no new collection: the answers live in the address (like the finder's, `lib/site/finder.ts`), the
lead is an ordinary enquiry, and the plan re-reads today's facts every time it is opened. The lead's message carries the
plan's link, so the team in Studio opens exactly what the buyer saw.

| Piece | Where |
|---|---|
| Questions, scoring, reasons, checklist, lead message | `frontend/lib/site/homeplan.ts` |
| The form | `frontend/components/site/homeplan/HomePlanForm.tsx` |
| The plan page (noindex, rendered per request) | `frontend/app/home-plan/result/page.tsx` |
| The questions page (noindex) | `frontend/app/home-plan/page.tsx` |
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

Code writes every sentence from the facts ("1.1 km from EON IT Park, Kharadi in a straight line", "Completion date filed on
MahaRERA: Jun 2029, never moved", "60 of 100 homes booked on MahaRERA (60%)"). No model is asked, so there is nothing to
guard and nothing to fall back from. The page says when it read the facts and that distances are straight-line.

## 3. What we measure

The leads are ordinary Studio leads whose message starts "East Pune home plan" or "Home plan (outside East Pune)".
Per week: plans sent, how many become site visits and Won, and outside-East answers by office. Compare with the plain
enquiry form on the same pages: if the plan does not bring more or better leads within a few weeks, it goes.

## 4. Next (NEW, in order)

1. Studio count of plan leads and outside-East demand by office (today: search the lead messages).
2. Nearest school and hospital for the picks when the family has school-going children or parents (the project page's
   `nearby`), read for the 3–5 picks only.
3. Partner price sheet in Studio: agents keep today's price per size for the projects they sell, dated, so fewer picks say
   "no price published".
4. The same plan in the WhatsApp bot (`whatsapp/finder_link.py` already turns a chat's area, BHK and budget into a finder link).
5. Drive times instead of straight-line km: computed per project and office once, in a background round, never per buyer.
6. Other areas, once we hold their projects as well as East Pune's.

## 5. Known limits

- The plan's address carries the answers, so anyone with the link sees the plan without leaving a number. That is the point
  of a link a family can forward; the lead comes from the form.
- Asking prices are what builders and portals publish, not registered sale prices (IGR Index-II needs a licensed feed:
  `project-pages.md`, "TARGET: registered sale prices").
- Homes booked is what the builder last filed on MahaRERA, often a quarter old.
