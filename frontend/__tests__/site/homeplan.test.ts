import type { FinderItem } from '@/lib/site/finder'
import {
  checklist, familyNearby, finderLink, hubSummaries, isEast, monthsUntil, parsePlan, planHomes, planInquiry, toPlanSearch, type PlanAnswers,
} from '@/lib/site/homeplan'

const TODAY = '2026-10-31'
// EON IT Park is at 18.5532, 73.9497; 0.01 degrees of latitude is about 1.1 km
const NEAR_EON = { lat: 18.5632, lon: 73.9497 }      // ~1.1 km
const MID_EON = { lat: 18.6232, lon: 73.9497 }       // ~7.8 km
const TWELVE_KM = { lat: 18.6612, lon: 73.9497 }     // ~12 km
const FAR_EON = { lat: 18.3532, lon: 73.9497 }       // ~22 km
const OUT_OF_REACH = { lat: 18.2532, lon: 73.9497 }  // ~33 km

const item = (id: string, homes: [number | null, number | null][], extra: Partial<FinderItem> = {}): FinderItem => ({
  id, href: '/projects/' + id, name: id, area: 'Kharadi', type: 'apartment', homes: homes.map(([bhk, price]) => ({ bhk, price })),
  possession: '2029-06-30', monthsLater: 0, booked: 50, total: 100, video: false, map: MID_EON, ...extra,
})

const FAMILY: PlanAnswers = { work: 'kharadi', budget: '75l-1cr', bhk: '2', kids: 'school', elders: false }

it('picks only homes whose own price row fits the size and the budget, and says the price it found', () => {
  const fits = item('fits', [[2, 8_900_000], [3, 13_000_000]])
  const dear = item('dear', [[2, 11_500_000]])
  const wrongSize = item('wrong-size', [[3, 9_500_000]])
  const picks = planHomes([fits, dear, wrongSize], FAMILY, TODAY)
  expect(picks.map((p) => p.item.id)).toEqual(['fits'])
  expect(picks[0].home).toEqual({ bhk: 2, price: 8_900_000 })
  expect(picks[0].reasons[0]).toBe('2 BHK from ₹89 L, the asking price published online')
})

it('a project near the office with a date that never moved ranks above a farther one whose builder moved the date', () => {
  const near = item('near', [[2, 9_000_000]], { map: NEAR_EON })
  const moved = item('moved', [[2, 8_000_000]], { map: FAR_EON, monthsLater: 9 })
  const picks = planHomes([moved, near], FAMILY, TODAY)
  expect(picks.map((p) => p.item.id)).toEqual(['near', 'moved'])
  expect(picks[0].reasons).toContain('1.1 km from EON IT Park, Kharadi in a straight line')
  expect(picks[0].reasons).toContain('Completion date filed on MahaRERA: Jun 2029, never moved')
  expect(picks[1].watch).toContain('The builder has moved the MahaRERA completion date 9 months later, to Jun 2029')
  expect(picks[1].watch.some((w) => w.startsWith('22.2 km from EON IT Park, Kharadi: check the drive'))).toBe(true)
})

it('leaves out a project too far for a daily commute, but keeps one whose position we have not checked, saying so', () => {
  const far = item('far', [[2, 9_000_000]], { map: OUT_OF_REACH })
  const unplaced = item('unplaced', [[2, 9_000_000]], { map: null })
  const picks = planHomes([far, unplaced], FAMILY, TODAY)
  expect(picks.map((p) => p.item.id)).toEqual(['unplaced'])
  expect(picks[0].km).toBeNull()
  expect(picks[0].watch).toContain("We have not checked this project's position yet, so there is no distance to your office")
})

it('a partner agent listing the project does not move it up: equal facts go by name', () => {
  const listed = item('zeta', [[2, 9_000_000]], { listedBy: 'House Deal', rank: 0 })
  const plain = item('alpha', [[2, 9_000_000]], { rank: 1 })
  expect(planHomes([listed, plain], FAMILY, TODAY).map((p) => p.item.id)).toEqual(['alpha', 'zeta'])
})

it('parents at home make a home due soon count for more than one far off', () => {
  const soon = item('soon', [[2, 9_000_000]], { possession: '2027-06-30', map: TWELVE_KM })
  const later = item('later', [[2, 9_000_000]], { possession: '2030-06-30', map: NEAR_EON })
  expect(planHomes([soon, later], FAMILY, TODAY).map((p) => p.item.id)).toEqual(['later', 'soon'])
  const withParents = planHomes([soon, later], { ...FAMILY, elders: true }, TODAY)
  expect(withParents.map((p) => p.item.id)).toEqual(['soon', 'later'])
  expect(withParents[0].reasons).toContain('Due for completion within a year')
})

it('tops up a short list with projects that publish no price for the size, marked as such, after the priced ones', () => {
  const priced = item('priced', [[2, 9_000_000]])
  const noPrice = item('no-price', [[2, null]])
  const nothing = item('nothing-published', [[null, null]])
  const lowestTooDear = item('too-dear', [[null, 12_000_000]])
  const picks = planHomes([noPrice, priced, nothing, lowestTooDear], FAMILY, TODAY)
  expect(picks.map((p) => p.item.id)).toEqual(['priced', 'no-price', 'nothing-published'])
  expect(picks[1].home).toBeNull()
  expect(picks[1].watch).toContain("No 2 BHK price published yet: ask our team for today's price")
})

it('a move-in answer leaves out homes due outside it; an early project is flagged, a passed date asks for the OC', () => {
  const ready = item('ready', [[2, 9_000_000]], { possession: '2026-06-30', booked: 10, total: 100 })
  const late = item('late', [[2, 9_000_000]], { possession: '2030-06-30' })
  const picks = planHomes([ready, late], { ...FAMILY, movein: 'by-2027' }, TODAY)
  expect(picks.map((p) => p.item.id)).toEqual(['ready'])
  expect(picks[0].watch).toContain("10% of homes booked so far: an early project, so look at the builder's past deliveries")
  expect(picks[0].watch).toContain('The filed completion date has passed: ask whether the occupancy certificate (OC) is issued')
})

it('makes no plan for someone working outside East Pune: they get the finder for their side of the city', () => {
  const west: PlanAnswers = { ...FAMILY, work: 'west' }
  expect(isEast(west)).toBe(false)
  expect(planHomes([item('x', [[2, 9_000_000]])], west, TODAY)).toEqual([])
  expect(finderLink(west)).toBe('/projects?area=hinjawadi&budget=75l-1cr&bhk=2')
  expect(isEast({ ...FAMILY, work: 'home' })).toBe(true)
})

it('the answers round-trip through the address and unknown values are dropped', () => {
  const a: PlanAnswers = { work: 'magarpatta', budget: '1-1.5cr', bhk: '3', movein: '2028-29', kids: 'young', elders: true }
  const sp = Object.fromEntries(new URLSearchParams(toPlanSearch(a).slice(1)))
  expect(parsePlan(sp)).toEqual(a)
  expect(parsePlan({ work: 'mars', budget: 'lots', bhk: '9', elders: 'maybe' })).toEqual({})
})

it('the checklist follows the family: school runs, play areas, lifts and the OC', () => {
  expect(checklist(FAMILY)).toContain('Ask which schools run buses to the society, and time the school run in the morning')
  const c = checklist({ ...FAMILY, kids: 'young', elders: true, movein: 'by-2027' })
  expect(c.some((x) => x.startsWith('Check that the play area'))).toBe(true)
  expect(c.some((x) => x.startsWith('Check the lifts have power backup'))).toBe(true)
  expect(c.some((x) => x.includes('occupancy certificate'))).toBe(true)
  expect(checklist({ ...FAMILY, kids: 'none' }).length).toBe(2)
})

it('the lead carries the answers, the plan link and the stated size and budget', () => {
  const lead = planInquiry(FAMILY, 'https://avasetu.in/home-plan/result?work=kharadi')
  expect(lead.message).toBe('East Pune home plan: works: Kharadi (EON IT Park, WTC); 2 BHK; ₹75 L – 1 Cr; move in: any time; '
    + 'children: school-going; parents living with them: no. Plan: https://avasetu.in/home-plan/result?work=kharadi')
  expect(lead).toMatchObject({ bhk: 2, budget_min_inr: 7_500_000, budget_max_inr: 10_000_000 })
  expect(planInquiry({ ...FAMILY, budget: 'above-2.5cr' }, 'u').budget_max_inr).toBeNull()
  expect(planInquiry({ ...FAMILY, work: 'west' }, 'u').message.startsWith('Home plan (outside East Pune)')).toBe(true)
})

it('counts months to a filed date', () => {
  expect(monthsUntil(TODAY, '2027-10-31')).toBe(12)
  expect(monthsUntil(TODAY, '2026-06')).toBe(-4)
  expect(monthsUntil(TODAY, null)).toBeNull()
})

it('shows the nearest school for young or school-going children and the nearest hospital for parents, nothing else', () => {
  const near = [
    { label: 'School', name: 'Far School', km: 2.4 }, { label: 'School', name: 'Near School', km: 0.8 },
    { label: 'Hospital', name: 'City Hospital', km: 1.5 }, { label: 'Bank', name: 'A Bank', km: 0.1 },
  ]
  expect(familyNearby({ ...FAMILY, elders: true }, near)).toEqual([
    'Nearest school: Near School, 0.8 km in a straight line (OpenStreetMap)',
    'Nearest hospital: City Hospital, 1.5 km in a straight line (OpenStreetMap)',
  ])
  expect(familyNearby({ ...FAMILY, kids: 'grown' }, near)).toEqual([])
  expect(familyNearby({ ...FAMILY, kids: 'young' }, [])).toEqual([])
})

it('counts, for each East Pune office, the projects within 10 km from a checked position and where most of them are', () => {
  const s = hubSummaries([
    item('a', [[2, 9_000_000]], { map: NEAR_EON }),
    item('b', [[2, null]], { map: MID_EON, area: 'Wagholi' }),
    item('c', [[2, 9_000_000]], { map: NEAR_EON, area: 'Wagholi' }),
    item('far', [[2, 9_000_000]], { map: FAR_EON }),
    item('unplaced', [[2, 9_000_000]], { map: null }),
  ])
  expect(s.map((x) => x.key)).toEqual(['kharadi', 'magarpatta', 'airport'])
  expect(s[0]).toEqual({ key: 'kharadi', hub: 'EON IT Park, Kharadi', near: 3, priced: 2,
    places: [{ name: 'Wagholi', count: 2 }, { name: 'Kharadi', count: 1 }] })
})
