# Trend reels (from 2026-10-05, until we have properties of our own)

Short explainers about buying in Pune that need no property, no host on camera and no data of ours. They are made by the same
reel engine as everything else (graphics, the Avasetu theme music, voice-over when `GOOGLE_TTS_API_KEY` is set) and wait in the
calendar as **planned** until the owner approves each one.

```
cd backend && PYTHONPATH=. python scripts/trend_reels.py --out trend-reels            # render mp4s, captions, manifest.json
cd backend && PYTHONPATH=. python scripts/trend_reels.py --out trend-reels --queue    # also add them to the calendar (planned)
```

## Rule: a figure on screen has a source or a sum
`backend/app/modules/reels/trend.py` holds `FACTS` (a statement, who says it, the URL, the date, and when it expires) and two
calculators (`cost_sheet`, `area_for_budget`). `check()` refuses a reel with a number that is not in its facts, an expired fact, a weak
hook or a "don't buy" scare hook. Facts are `official` (a government release) or `secondary` (portals, advice sites): the manifest lists the
secondary ones under `confirm_before_approving`, and a human checks them against the official page before approving.

## What the blueprint's three scripts became
| Blueprint claim | Status | In the reel |
|---|---|---|
| "DON'T buy in Kharadi with ₹50L" | dropped: advice we cannot back | "₹50 lakh: Kharadi or Wagholi?" |
| "₹50L = 1BHK in Kharadi, 2BHK in Wagholi", "12 minutes away" | dropped: no source | what ₹50 lakh buys in sq ft at the portal rates, as a sum |
| "₹9,500 vs ₹6,500 per sq ft" | changed: portals disagree (Wagholi ₹5,000-6,500 entry, one listing ₹10,823 average) | ranges, "as listed on portals, Oct 2026", secondary |
| "Metro extension coming up, under 20 minutes to EON" | dropped: metro is not running, commute is not sourced | "Approved by the Union Cabinet, 25 June 2025; within 4 years; approved is not running" (official) |
| "Stamp duty ~7%" | kept as secondary: 7% for a man in municipal limits, 6% for a woman | in the cost sheet, confirm on igrmaharashtra.gov.in |
| "GST on under-construction: 5%" | changed and now official: it works out to 5% of the price (7.5% on two-thirds of it, one-third deemed land, CBIC notification 03/2019); none when the whole price is paid after the completion certificate | in the cost sheet |
| "Parking ₹3-5L, corpus ₹1.5L" | dropped: no source, differs by project | "Parking and deposits: extra. Ask for the all-in cost sheet." |
| "₹60L = ₹71L" | replaced by the sum: ₹60L becomes ₹67.5L before parking and deposits (₹64.5L when ready) | calculator, example labelled |
| "Comment COST for a DM checklist" | dropped: nothing answers that keyword | "Save this. Send it to someone buying." |

## Experiments
Each reel carries `experiment`, `variant`, `hook_type`, `engine`, `locality` and `price_band` in the calendar row's `creative`, so that when
reel measurement exists the variants of one idea (EXP-001: question vs price reveal vs myth, same facts) can be compared with each other.
