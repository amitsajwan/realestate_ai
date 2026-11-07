import { asked, bhkRange, byArea, describe as say, facets, findHomes, matchingHomes, parseQuery, toSearch, type FinderItem } from '@/lib/site/finder'

const item = (id: string, area: string, homes: [number | null, number | null][], extra: Partial<FinderItem> = {}): FinderItem => ({
  id, href: '/x/' + id, name: id, area, type: 'apartment', homes: homes.map(([bhk, price]) => ({ bhk, price })),
  possession: '2029-06-30', monthsLater: 0, booked: 10, total: 100, video: false, ...extra,
})

const EVOLVUS = item('evolvus', 'Kharadi', [[2, 13_600_000], [3, 18_400_000], [4, 27_000_000]], { monthsLater: 0, booked: 80, total: 100, video: true })
const VANAYA = item('vanaya', 'Kharadi', [[2, 11_500_000], [3, 16_000_000]], { monthsLater: 6, possession: '2027-12-31' })
const ENCHANTE = item('enchante', 'Upper Kharadi', [[2, 9_000_000]], { possession: '2030-03-31' })
const PLOTS = item('gulmohar', 'Wagholi', [[null, 3_000_000]], { type: 'plot', possession: null, monthsLater: null, booked: null, total: null })
const ALL = [EVOLVUS, VANAYA, ENCHANTE, PLOTS]

it('matches the price sheet row, not the lowest price: a 3 BHK under 1.5 Cr is not Evolvus, whose 2 BHK is', () => {
  const found = findHomes(ALL, { bhk: '3', budget: '1-1.5cr' })
  expect(found.map((i) => i.id)).toEqual([])
  expect(findHomes(ALL, { bhk: '3', budget: '1.5-2.5cr' }).map((i) => i.id).sort()).toEqual(['evolvus', 'vanaya'])
  expect(matchingHomes(EVOLVUS, { bhk: '3', budget: '1.5-2.5cr' })).toEqual([{ bhk: 3, price: 18_400_000 }])
})

it('a plot has no BHK: asking for 2 BHK leaves plots out, and the type question shows only because plots are there', () => {
  expect(findHomes(ALL, { bhk: '2' }).map((i) => i.id)).not.toContain('gulmohar')
  expect(facets(ALL, {}).type.map((t) => t.key)).toEqual(['apartment', 'plot'])
  expect(facets([EVOLVUS, VANAYA], {}).type).toEqual([])
})

it('MahaRERA filters: date not moved and half or more booked', () => {
  expect(findHomes(ALL, { held: true }).map((i) => i.id).sort()).toEqual(['enchante', 'evolvus'])
  expect(findHomes(ALL, { fast: true }).map((i) => i.id)).toEqual(['evolvus'])
  expect(findHomes(ALL, { movein: 'by-2027' }).map((i) => i.id)).toEqual(['vanaya'])
})

it('counts each choice with the other answers kept, and offers a question only when it splits the list', () => {
  const f = facets(ALL, { area: 'kharadi' })
  expect(f.bhk.find((b) => b.key === '3')).toMatchObject({ count: 2 })
  expect(f.bhk.find((b) => b.key === '4')).toMatchObject({ count: 1 })
  expect(f.area.find((a) => a.key === 'upper-kharadi')).toMatchObject({ count: 1, on: false })
  expect(f.area.find((a) => a.key === 'kharadi')).toMatchObject({ count: 2, on: true })
  expect(f.toggles.map((t) => t.key)).toEqual(['held', 'fast', 'video'])
})

it('lives in the address: a shared link opens the same answers, and junk is dropped', () => {
  const q = parseQuery({ area: 'Wagholi', bhk: '2', budget: '75l-1cr', held: '1', compare: 'a,b,a,c,d', sort: 'price', evil: '<x>', more: '9999' })
  expect(q).toEqual({ area: 'wagholi', bhk: '2', budget: '75l-1cr', held: true, compare: ['a', 'b', 'c'], sort: 'price' })
  expect(toSearch(q, { bhk: '3' })).toBe('?area=wagholi&budget=75l-1cr&bhk=3&held=1&sort=price&compare=a%2Cb%2Cc')
  expect(toSearch(q, { area: undefined, held: undefined })).toBe('?budget=75l-1cr&bhk=2&sort=price&compare=a%2Cb%2Cc')
  expect(asked({ sort: 'price', compare: ['a'] })).toBe(false)
  expect(say(q, 'Wagholi')).toBe('2 BHK, ₹75 L – 1 Cr, in Wagholi, date not moved')
})

it('with nothing asked the page is grouped by area, biggest first', () => {
  expect(byArea(ALL).map((g) => [g.area, g.items.length])).toEqual([['Kharadi', 2], ['Upper Kharadi', 1], ['Wagholi', 1]])
})

it("an agent's homes with a price come before 'price on request', and MahaRERA's capitals read as a name", () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { fromListings, fromRegister } = require('@/lib/site/finderItems')
  const l = (id: string, price: number | null) => ({ id, title: id, price_inr: price, property_type: 'apartment', locality: 'Wagholi', media: [] })
  expect(fromListings([l('villa', null), l('flat', 9_000_000)], 'house-deal', []).map((i: { id: string }) => i.id)).toEqual(['flat', 'villa'])
  const reg = [{ slug: 'r', regno: 'P1', name: 'R', area: 'wagholi', completion_now: null, listed_or_updated: null, indexable: true, promoter: 'INTOFINITY PROMOTERS PRIVATE LIMITED' }]
  expect(fromRegister(reg, new Map())[0].builder).toBe('Intofinity Promoters')
})

it('writes the WhatsApp message an agent sends: what was asked, the home that fits with its price, and the link', () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const { shareText } = require('@/lib/site/finder')
  const fmt = { price: (n: number) => `₹${n / 1e5} L`, area: (n: number) => `${n} sq.ft`, month: (d: string) => d.slice(0, 7) }
  const text = shareText(findHomes(ALL, { bhk: '3', area: 'kharadi' }), { bhk: '3', area: 'kharadi' },
    { who: 'House Deal', url: 'https://avasetu.in/agent/house-deal?area=kharadi&bhk=3&src=share', areaName: 'Kharadi', fmt })
  expect(text).toBe([
    '2 homes for 3 BHK, in Kharadi from House Deal:', '',
    '1. evolvus, Kharadi: 3 BHK, ₹184 L (possession 2029-06, date not moved on MahaRERA)',
    '2. vanaya, Kharadi: 3 BHK, ₹160 L (possession 2027-12)', '',
    'All of them with prices and MahaRERA checks: https://avasetu.in/agent/house-deal?area=kharadi&bhk=3&src=share',
  ].join('\n'))
})

it('a shop or office with no BHK says so instead of Homes; a flat with none still says Homes', () => {
  expect(bhkRange(item('ubc', 'Mohammadwadi', [[null, 5_500_000]], { type: 'commercial' }))).toBe('Shops & offices')
  expect(bhkRange(item('flat', 'Kharadi', [[null, 5_500_000]]))).toBe('Homes')
})
