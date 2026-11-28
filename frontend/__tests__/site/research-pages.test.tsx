/**
 * Pune intelligence on the site (docs/plan/pune-intelligence.md C): the research client, the "Around <project>" blocks, the
 * place research pages (/schools, /commute, /rent), the work hub pages and their sitemap entries.
 */
import React from 'react'
import { render, screen, within } from '@testing-library/react'
import AroundProject from '@/components/site/research/AroundProject'
import LivingHere from '@/components/site/research/LivingHere'
import { BeingBuilt, ChangesList, CommuteTable, RentTable, SchoolsList, WorkNearby } from '@/components/site/research/ResearchBlocks'
import { getHub, getHubs, getPlaceResearch, getProjectResearch, getResearchPages } from '@/lib/site/research'
import type { CommuteBlock, HubPage, PlaceResearch, ProjectResearch, RentBlock, SchoolsBlock } from '@/lib/site/research'
import {
  commuteHead, commuteJsonLd, hubIndexable, rentHead, rentJsonLd, researchIndexable, researchSitemap, schoolsHead, schoolsJsonLd,
  withoutPlacesOfWorship, RESEARCH_TITLE_MAX,
} from '@/lib/site/researchPages'

const src = [{ name: 'Google Routes API', read_on: '2026-11-20' }]
const COMMUTE: CommuteBlock = {
  sources: src, updated: '2026-11-20', page_ready: true,
  rows: [{ hub: 'EON IT Park', hub_slug: 'eon-it-park', km: 4.2, am: [12, 18], pm: [15, 25] },
    { hub: 'Hinjawadi', km: 31, am: [65, 90], pm: [70, 100] }, { hub: 'Pune airport', km: 9.5, am: [22, 30], pm: [25, 35] }],
}
const SCHOOLS: SchoolsBlock = {
  sources: [{ name: 'CBSE SARAS', url: 'https://saras.cbse.gov.in', read_on: '2026-11-18' }, { name: 'CISCE', read_on: '2026-11-18' }],
  updated: '2026-11-18', page_ready: true,
  schools: [{ name: 'Far School', board: 'State', km: 2.8 }, { name: 'Near School', board: 'CBSE', level: 'Up to Class 12', km: 0.8, address: 'Wagholi, Pune 412207' },
    { name: 'Mid School', board: 'ICSE', km: 1.5 }],
  total_within_km: { km: 3, count: 23, by_board: { CBSE: 12, ICSE: 5, ISC: 1, State: 5 } },
}
const RENT: RentBlock = {
  sources: [{ name: 'Rental listings', read_on: '2026-11-15' }], updated: '2026-11-15', month: '2026-11', page_ready: true,
  rows: [{ bhk: '1 BHK', low: 14000, median: 16000, high: 18000, listings: 22 },
    { bhk: '2 BHK', low: 22000, median: 26000, high: 30000, listings: 41, yield_pct: 3.2 },
    { bhk: '3 BHK', low: 32000, median: 36000, high: 42000, listings: 14 }],
}
const PLACE: PlaceResearch = {
  place: 'wagholi', blocks: { commute: COMMUTE, schools: SCHOOLS, rent: RENT,
    jobs: { sources: src, updated: '2026-11-20', hubs: [{ hub: 'EON IT Park', hub_slug: 'eon-it-park', km: 6, companies: ['Barclays', 'Credit Suisse'] }] } },
  changes: [{ slug: 'wagholi-flyover', name: 'Wagholi elevated road', status: 'Tender awarded', date: '2026-11-02' }],
  pages: { schools: true, commute: true, rent: false },
}
const PROJECT: ProjectResearch = { slug: 'x-wagholi', place: 'wagholi', pinned: true, blocks: PLACE.blocks, changes: PLACE.changes }

// ---- the client ----

describe('the research client', () => {
  const realFetch = global.fetch
  afterEach(() => { global.fetch = realFetch })
  const answer = (status: number, body: unknown = {}) => {
    global.fetch = jest.fn(async () => ({ status, ok: status < 400, json: async () => body })) as unknown as typeof fetch
  }

  test('a 404 is "no research yet": data null, never an outage', async () => {
    answer(404)
    expect(await getPlaceResearch('wagholi')).toEqual({ ok: true, data: null })
    expect(await getProjectResearch('x-wagholi')).toEqual({ ok: true, data: null })
    expect(await getHub('eon-it-park')).toEqual({ ok: true, data: null })
  })

  test('an outage (5xx or no answer) is ok false, so a page is never cached as a 404', async () => {
    answer(503)
    expect(await getPlaceResearch('wagholi')).toEqual({ ok: false })
    global.fetch = jest.fn(async () => { throw new Error('down') }) as unknown as typeof fetch
    expect(await getPlaceResearch('wagholi')).toEqual({ ok: false })
    expect(await getProjectResearch('x-wagholi')).toEqual({ ok: false })
  })

  test('a place read fills what the backend left out, and a bad slug is never sent', async () => {
    answer(200, { place: 'wagholi', blocks: {} })
    expect(await getPlaceResearch('wagholi')).toEqual({ ok: true, data: { place: 'wagholi', blocks: {}, changes: [], pages: { schools: false, commute: false, rent: false } } })
    const f = jest.fn()
    global.fetch = f as unknown as typeof fetch
    expect(await getPlaceResearch('../etc')).toEqual({ ok: true, data: null })
    expect(f).not.toHaveBeenCalled()
  })

  test('the hub list takes the backend\'s { hubs } and leaves out hubs not ready; lists are empty on any failure', async () => {
    answer(200, { hubs: [{ slug: 'eon-it-park', name: 'EON', place: 'kharadi', kind: 'it_park' }, { slug: 'thin', name: 'T', place: 'x', kind: 'it_park', ready: false }] })
    expect((await getHubs()).map((h) => h.slug)).toEqual(['eon-it-park'])
    answer(404)
    expect(await getHubs()).toEqual([])
    expect(await getResearchPages()).toEqual([])
    answer(200, { pages: [{ place: 'wagholi', kind: 'schools' }, { place: 'wagholi', kind: 'temples' }] })
    expect(await getResearchPages()).toEqual([{ place: 'wagholi', kind: 'schools' }])
  })
})

// ---- the blocks ----

describe('Around <project>', () => {
  test('shows the blocks in order, says where it measures from, and links only the place pages worth indexing', () => {
    render(<AroundProject research={PROJECT} name="X Towers" placeName="Wagholi" pages={PLACE.pages} />)
    const box = screen.getByTestId('around')
    expect(within(box).getByRole('heading', { level: 2 })).toHaveTextContent('Around X Towers')
    const order = ['research-commute', 'research-changes', 'research-schools', 'research-rent', 'research-jobs']
      .map((id) => box.innerHTML.indexOf(`data-testid="${id}"`))
    expect(order.every((x, i) => x > 0 && (i === 0 || x > order[i - 1]))).toBe(true)
    expect(box.textContent).toContain("from the project's pin")
    expect(screen.getByRole('link', { name: 'Commute from Wagholi' })).toHaveAttribute('href', '/projects/area/wagholi/commute')
    expect(screen.getByRole('link', { name: 'All schools in Wagholi' })).toHaveAttribute('href', '/projects/area/wagholi/schools')
    expect(screen.queryByRole('link', { name: 'Rent in Wagholi' })).toBeNull()   // pages.rent is false
    expect(screen.getByRole('link', { name: 'Wagholi elevated road' })).toHaveAttribute('href', '/news/track/wagholi-flyover')
    expect(screen.getAllByRole('link', { name: 'EON IT Park' })[0]).toHaveAttribute('href', '/work-hubs/eon-it-park')
    expect(screen.getByTestId('rent-label')).toHaveTextContent('Asked rent, from 77 listings, Nov 2026')
    expect(screen.getByTestId('commute-print')).toHaveTextContent('measured 20 Nov 2026')
  })

  test('says "from the <place> centre" without a pin', () => {
    render(<AroundProject research={{ ...PROJECT, pinned: false }} name="X" placeName="Wagholi" />)
    expect(screen.getByTestId('around').textContent).toContain('from the Wagholi centre')
  })

  test('draws nothing with no research or nothing measured', () => {
    expect(render(<AroundProject research={null} name="X" placeName="W" />).container.innerHTML).toBe('')
    expect(render(<AroundProject research={{ ...PROJECT, blocks: {}, changes: [] }} name="X" placeName="W" />).container.innerHTML).toBe('')
  })

  test('each block hides itself when absent or empty', () => {
    const empties = [
      <CommuteTable key="c" b={undefined} from="x" />, <CommuteTable key="c2" b={{ ...COMMUTE, rows: [] }} from="x" />,
      <SchoolsList key="s" b={undefined} from="x" />, <SchoolsList key="s2" b={{ ...SCHOOLS, schools: [] }} from="x" />,
      <RentTable key="r" b={undefined} />, <RentTable key="r2" b={{ ...RENT, rows: [] }} />,
      <BeingBuilt key="b" b={undefined} />, <WorkNearby key="w" b={undefined} />, <ChangesList key="ch" changes={[]} />,
    ]
    for (const el of empties) expect(render(el).container.innerHTML).toBe('')
  })

  test('schools are nearest first with the board as a chip; rent shows yield only when known', () => {
    render(<SchoolsList b={SCHOOLS} from="from the Wagholi centre" />)
    const names = screen.getByTestId('research-schools').querySelectorAll('li')
    expect(names[0].textContent).toContain('Near School')
    expect(screen.getAllByTestId('board').map((x) => x.textContent)).toEqual(['CBSE', 'ICSE', 'State board'])
    render(<RentTable b={RENT} />)
    expect(screen.getByText('3.2%')).toBeInTheDocument()
    render(<RentTable b={{ ...RENT, rows: RENT.rows.map(({ yield_pct, ...r }) => r) }} />)
    expect(screen.getAllByTestId('research-rent')[1].textContent).not.toContain('Yield')
  })
})

test('the project page\'s nearby list never names a place of worship', () => {
  const near = [{ label: 'Temple', name: 'X', km: 1 }, { label: 'Hospital', name: 'Sai Hospital', km: 2 }, { label: 'Place of worship', name: 'Y', km: 1 },
    { label: 'School', name: 'St. Mary School', km: 1 }]
  expect(withoutPlacesOfWorship(near).map((x) => x.name)).toEqual(['Sai Hospital', 'St. Mary School'])
})

test('the place page\'s "Living in" strip links only the research pages worth indexing, the hubs and the trackers', () => {
  render(<LivingHere research={PLACE} placeName="Wagholi" />)
  const box = screen.getByTestId('living-here')
  expect(within(box).getAllByRole('link').map((a) => a.getAttribute('href'))).toEqual([
    '/projects/area/wagholi/schools', '/projects/area/wagholi/commute', '/work-hubs/eon-it-park', '/news/track/wagholi-flyover'])
  expect(render(<LivingHere research={{ ...PLACE, blocks: {}, changes: [] }} placeName="Wagholi" />).container.innerHTML).toBe('')
})

// ---- titles and words ----

describe('titles, H1s and answers', () => {
  test('schools say the count and the boards', () => {
    const h = schoolsHead('Wagholi', SCHOOLS)
    expect(h.h1).toBe('Schools in Wagholi, Pune: 23 CBSE, ICSE and State board schools')
    expect(h.title.length).toBeLessThanOrEqual(RESEARCH_TITLE_MAX)
    expect(h.answer).toContain('23 schools within 3 km of the Wagholi centre: 12 CBSE, 6 ICSE and 5 State board.')
    expect(h.answer).toContain('The nearest is Near School (CBSE, up to class 12), 0.8 km away.')
  })

  test('commute names the first three hubs', () => {
    const h = commuteHead('Kharadi', COMMUTE)
    expect(h.h1).toBe('Commute from Kharadi: drive times to EON IT Park, Hinjawadi, Pune airport')
    expect(h.title.length).toBeLessThanOrEqual(RESEARCH_TITLE_MAX)
    expect(h.answer).toContain('EON IT Park is 4.2 km by road: 12-18 min at 9 am and 15-25 min back at 6 pm')
  })

  test('rent names the month and sizes and says it is asked rent', () => {
    const h = rentHead('Kharadi', RENT)
    expect(h.h1).toBe('Rent in Kharadi, Pune (Nov 2026): 1, 2 and 3 BHK asked rent')
    expect(h.title.length).toBeLessThanOrEqual(RESEARCH_TITLE_MAX)
    expect(h.answer).toContain('not what tenants pay')
    expect(h.description.length).toBeLessThanOrEqual(160)
  })

  test('a long place name still gives a title of 65 characters or fewer', () => {
    const long = 'Pimpri Chinchwad Nigdi Pradhikaran'
    for (const t of [schoolsHead(long, SCHOOLS).title, commuteHead(long, COMMUTE).title, rentHead(long, RENT).title]) {
      expect(t.length).toBeLessThanOrEqual(RESEARCH_TITLE_MAX)
    }
  })

  test('a sub-page is indexed only when the backend\'s page flag is true', () => {
    expect(researchIndexable('schools', PLACE)).toBe(true)
    expect(researchIndexable('rent', PLACE)).toBe(false)
  })
})

// ---- structured data ----

describe('structured data', () => {
  const site = 'https://avasetu.in'
  test('schools are an ItemList of School with name and address', () => {
    const ld = schoolsJsonLd(site, '/projects/area/wagholi/schools', 'h1', 'Wagholi', SCHOOLS) as { '@type': string; itemListElement: Array<{ item: Record<string, unknown> }> }
    expect(ld['@type']).toBe('ItemList')
    expect(ld.itemListElement[1].item).toEqual({ '@type': 'School', name: 'Near School', address: 'Wagholi, Pune 412207' })
    expect(ld.itemListElement[0].item.address).toBe('Wagholi, Pune')
  })

  test('commute is an Article and rent a Dataset, both dated by the measure', () => {
    const c = commuteJsonLd(site, '/p', commuteHead('Kharadi', COMMUTE), 'Kharadi', COMMUTE)
    expect(c).toMatchObject({ '@type': 'Article', dateModified: '2026-11-20', about: { '@type': 'Place', name: 'Kharadi, Pune' } })
    const r = rentJsonLd(site, '/p', rentHead('Kharadi', RENT), 'Kharadi', RENT)
    expect(r).toMatchObject({ '@type': 'Dataset', dateModified: '2026-11-15', temporalCoverage: '2026-11', spatialCoverage: { name: 'Kharadi, Pune' } })
    expect(String(r.description).length).toBeGreaterThanOrEqual(50)   // Google's Dataset minimum
  })
})

// ---- hubs and the sitemap ----

test('a hub page is indexed by the backend\'s word, else once it has three companies or three places\' drive times', () => {
  const h: HubPage = { slug: 'eon', name: 'EON', place: 'kharadi', kind: 'it_park', summary: '', companies: ['a', 'b'], commute_from: [],
    homes_nearby: [], changes: [], sources: [], updated: '2026-11-20' }
  expect(hubIndexable(h)).toBe(false)
  expect(hubIndexable({ ...h, companies: ['a', 'b', 'c'] })).toBe(true)
  expect(hubIndexable({ ...h, companies: ['a', 'b', 'c'], page_ready: false })).toBe(false)
})

test('the sitemap lists only the place pages the backend calls ready, and ready hubs with their list', () => {
  const out = researchSitemap([{ place: 'wagholi', kind: 'schools', updated: '2026-11-18' }],
    [{ slug: 'eon', name: 'EON', place: 'kharadi', kind: 'it_park' }, { slug: 'thin', name: 'T', place: 'x', kind: 'it_park', ready: false }])
  expect(out).toEqual([
    { group: 'area-wagholi', path: '/projects/area/wagholi/schools', date: '2026-11-18' },
    { group: 'core', path: '/work-hubs' },
    { group: 'core', path: '/work-hubs/eon', date: undefined },
  ])
  expect(researchSitemap([], [])).toEqual([])
})
