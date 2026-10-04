# Pune areas: plan (2026-10-04)

## Strategy (why we are doing this)
- Avasetu is **Pune real estate intelligence**: properties, prices, locality facts. The brand is Pune-wide; execution starts with 8 areas.
- Our customers are **agents**. A Pune-wide buyer audience lets us tell an agent in any area "buyers are already asking about your area on our page".
- Areas (one list: `backend/app/core/areas.py`, never hard-code another):
  - affordable belt: Upper Kharadi, Wagholi, **Lohegaon**, **Keshav Nagar** (first homes, budget buyers; where the owner sees most demand)
  - IT corridor: Kharadi, Hinjawadi, Wakad, Baner
- Daily content: **2 reels a day** (3 after two weeks of steady quality), every post still passes the approval gate.
  - Morning: an **area insight** made from MahaRERA public records ("12 projects in Wagholi finish in 2027").
  - Evening: a **real home or project** when an agent has given us one; otherwise a **buyer guide** ("3 checks before a resale flat").
- Every post links to its area page (`/localities/<slug>`), which captures the buyer's area, budget and WhatsApp number.

## Rules that do not change
- Facts only, each with its source. **No invented prices, distances, schools, predictions or "best"**. MahaRERA's search card date is
  "Last Modified": never say "newly registered" (policy.MAHARERA_PHRASE).
- Nothing is posted under an agent's name without their consent flag. House Deal has NOT given consent.
- No secrets in code, logs or chat. No deploys, VM access, pushes or posting from work branches: the main session merges and deploys.
- Tests for everything new; the full backend suite and (for frontend work) `npm run build` must pass before handing over.

## Workstreams (each owns its files; do not edit another stream's files)
| | Stream | Owns |
|---|---|---|
| W1 | MahaRERA data per area + stats API | `backend/app/modules/newsroom/{policy,register,store}.py`, `newsroom/stages/filter.py`, new `backend/app/modules/areastats/` |
| W2 | Area pages on the website + reply facts | `frontend/lib/marketing/localities.ts`, `frontend/app/localities/**`, `frontend/components/localities/**` (new), `backend/app/modules/knowledge/areas.py` + its test |
| W3 | Reach: hashtags and Instagram location per area | `backend/app/modules/calendar/reach.py` + its test; report (do not change) other hard-coded area lists |
| W4 | Daily reel rhythm + area-insight reels | `backend/app/modules/calendar/{plan,schedule,library,adapters,builder}.py`, new `backend/app/modules/calendar/area_reels.py` |

## Contract between W1 and W2/W4: area stats
Python (W4 uses this): `app.modules.areastats.service.area_stats(db, key: str) -> Optional[dict]`.
HTTP (W2 uses this): `GET /api/v1/public/areas/{slug}/stats` → 200 with the dict below, 404 for an unknown area.
```json
{
  "area": {"key": "wagholi", "name": "Wagholi", "slug": "wagholi", "tier": "affordable"},
  "as_of": "2026-10-04",
  "projects": 41,
  "completing": [{"year": 2026, "projects": 6}, {"year": 2027, "projects": 12}],
  "units_total": 5210, "units_booked": 3100,
  "recent": [{"name": "Rohan Abhilasha 4", "regno": "P52100080076", "promoter": "Rohan Builders",
              "completion": "2029-10-30", "updated": "2026-09-28", "url": "https://maharerait.maharashtra.gov.in/public/project/view/..."}],
  "source": "MahaRERA public records"
}
```
- `projects` may be 0. `units_total`/`units_booked` are null when not known for enough projects (never guess).
- `completing` counts projects by the year of their filed completion date; years before `as_of` are left out.
- `recent` has at most 5 items, newest `updated` first.
