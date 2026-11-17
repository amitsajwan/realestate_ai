import React from 'react'
import os from 'os'
import path from 'path'
import { promises as fs } from 'fs'
import { render, screen, within } from '@testing-library/react'

// "How <area> grew": the MahaRERA registrations chart and the Sentinel-2 pictures. The page's API reads are replaced here, and
// so is the read of public/areas/<slug>.json (the real reader is tested against a temporary folder below).
const mockFetch = jest.fn()
const mockPictures = jest.fn()
jest.mock('@/lib/site/api', () => ({
  getCatalog: async () => [],
  getLocalityListings: async () => [],
  fixturesForced: () => false,
  serverApiBase: () => 'http://api',
}))
jest.mock('@/lib/site/facets', () => ({ ...jest.requireActual('@/lib/site/facets'), getFacets: async () => [] }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('next/navigation', () => ({
  notFound: () => { throw new Error('NOT_FOUND') },
  permanentRedirect: (to: string) => { throw new Error(`REDIRECT ${to}`) },
  usePathname: () => '/',
  useRouter: () => ({ push: jest.fn() }),
}))
jest.mock('@/components/localities/areaPictures', () => {
  const actual = jest.requireActual('@/components/localities/areaPictures')
  return { ...actual, readAreaPictures: (slug: string, dir?: string) => (dir ? actual.readAreaPictures(slug, dir) : mockPictures(slug)) }
})

import LocalityPage, { generateMetadata } from '@/app/localities/[slug]/page'
import AreaGrowth from '@/components/localities/AreaGrowth'
import { type AreaPicture, cleanAreaPictures, readAreaPictures } from '@/components/localities/areaPictures'
import { cleanAreaStats } from '@/components/localities/areaStats'
import { getMarketingConfig } from '@/lib/marketing/config'

const REGISTERED = [{ year: 2019, projects: 4 }, { year: 2020, projects: 0 }, { year: 2021, projects: 7 }, { year: 2022, projects: 12 }]
const STATS = {
  area: { key: 'kharadi', name: 'Kharadi', slug: 'kharadi', tier: 'it' }, as_of: '2026-10-04', projects: 23,
  completing: [], units_total: null, units_booked: null, recent: [], source: 'MahaRERA public records', registered: REGISTERED,
}
const SITE = 'https://avasetu.in'

function sidecar(years: Array<[number, string]>, slug = 'kharadi') {
  return {
    area: slug, name: 'Kharadi', box: [18.5265, 73.922, 18.5755, 73.974],
    pictures: years.map(([year, day]) => ({ year, src: `/areas/${slug}-${year}.webp`, width: 1000, height: 994,
      captured: { from: day, to: day }, month: 'ignored', cloud_filter_pct: 10, credit: `Contains modified Copernicus Sentinel data ${year}` })),
  }
}
const PAIR: AreaPicture[] = cleanAreaPictures(sidecar([[2017, '2017-03-12'], [2026, '2026-02-18']]), 'kharadi')

beforeEach(() => {
  mockFetch.mockReset()
  mockFetch.mockResolvedValue({ ok: true, status: 200, json: async () => STATS })
  global.fetch = mockFetch as unknown as typeof fetch
  mockPictures.mockReset()
  mockPictures.mockResolvedValue([])
})

describe('registrations per year, cleaned', () => {
  it('keeps whole non-negative counts, one per year, oldest first, none after the as-of year', () => {
    const s = cleanAreaStats({ ...STATS, registered: [{ year: 2022, projects: 12 }, { year: 2019, projects: 4 }, { year: 2020, projects: -1 },
      { year: 2021, projects: 2.5 }, { year: 2019, projects: 99 }, { year: 2031, projects: 3 }, { year: '2018', projects: 1 }, null] }, 'kharadi')
    expect(s?.registered).toEqual([{ year: 2019, projects: 4 }, { year: 2022, projects: 12 }])
    expect(cleanAreaStats({ ...STATS, registered: undefined }, 'kharadi')?.registered).toEqual([])
  })
})

describe('the "How <area> grew" section', () => {
  it('draws a bar per year with its value and gives the same numbers in a table, with the dated source', () => {
    render(<AreaGrowth name="Kharadi" stats={cleanAreaStats(STATS, 'kharadi')} siteUrl={SITE} />)
    const s = screen.getByRole('region', { name: 'How Kharadi grew' })
    const chart = within(s).getByTestId('growth-chart')
    expect(chart).toHaveAttribute('aria-hidden', 'true')
    const bars = chart.querySelectorAll('[data-bar]')
    expect([...bars].map((b) => b.getAttribute('data-bar'))).toEqual(['2019', '2020', '2021', '2022'])
    expect((bars[3] as HTMLElement).style.height).toBe('140px')       // the biggest year fills the chart
    expect((bars[1] as HTMLElement).style.height).toBe('0px')         // an empty year is kept, at zero
    expect(chart).toHaveTextContent('4' + '0' + '7' + '12')
    const table = within(s).getByRole('table', { name: /Projects registered with MahaRERA in Kharadi, per year, 2019 to 2022/ })
    const rows = within(table).getAllByRole('row').slice(1).map((r) => r.textContent)
    expect(rows).toEqual(['20194', '20200', '20217', '202212'])
    expect(s).toHaveTextContent('Source: MahaRERA public records, as of 4 October 2026')
    expect(within(s).queryByRole('img')).toBeNull()                    // no pictures without the list
    expect(s.querySelector('script[type="application/ld+json"]')).toBeNull()
  })

  it('leaves itself out with fewer than 3 years, or with no project in any year', () => {
    const two = render(<AreaGrowth name="Kharadi" stats={cleanAreaStats({ ...STATS, registered: REGISTERED.slice(0, 2) }, 'kharadi')} siteUrl={SITE} />)
    expect(two.container).toBeEmptyDOMElement()
    const zeros = render(<AreaGrowth name="Kharadi" stats={cleanAreaStats({ ...STATS, registered: REGISTERED.map((y) => ({ ...y, projects: 0 })) }, 'kharadi')} siteUrl={SITE} />)
    expect(zeros.container).toBeEmptyDOMElement()
    expect(render(<AreaGrowth name="Kharadi" stats={null} siteUrl={SITE} />).container).toBeEmptyDOMElement()
  })

  it('shows the oldest and newest pictures from above, lazy and sized, with month captions, credits and ImageObject data', () => {
    const three = cleanAreaPictures(sidecar([[2017, '2017-03-12'], [2021, '2021-04-02'], [2026, '2026-02-18']]), 'kharadi')
    render(<AreaGrowth name="Kharadi" stats={cleanAreaStats(STATS, 'kharadi')} pictures={three} siteUrl={SITE} />)
    const s = screen.getByRole('region', { name: 'How Kharadi grew' })
    const imgs = within(s).getAllByRole('img')
    expect(imgs.map((i) => i.getAttribute('alt'))).toEqual(['Kharadi from above, March 2017, Sentinel-2 satellite',
      'Kharadi from above, February 2026, Sentinel-2 satellite'])
    expect(imgs[0]).toHaveAttribute('src', '/areas/kharadi-2017.webp')
    expect(imgs[0]).toHaveAttribute('loading', 'lazy')
    expect(imgs[0]).toHaveAttribute('width', '1000')
    expect(imgs[0]).toHaveAttribute('height', '994')
    expect(s).toHaveTextContent('Kharadi, March 2017')
    expect(s).toHaveTextContent('Contains modified Copernicus Sentinel data 2017')
    expect(s).toHaveTextContent('Contains modified Copernicus Sentinel data 2026')
    const ld = [...s.querySelectorAll('script[type="application/ld+json"]')].map((x) => JSON.parse(x.innerHTML))
    expect(ld).toHaveLength(2)
    expect(ld[1]).toMatchObject({ '@type': 'ImageObject', contentUrl: 'https://avasetu.in/areas/kharadi-2026.webp', width: 1000,
      height: 994, dateCreated: '2026-02-18', creditText: 'Contains modified Copernicus Sentinel data 2026' })
  })

  it('shows no pictures for a single year', () => {
    render(<AreaGrowth name="Kharadi" stats={cleanAreaStats(STATS, 'kharadi')} pictures={PAIR.slice(1)} siteUrl={SITE} />)
    expect(within(screen.getByRole('region', { name: 'How Kharadi grew' })).queryByRole('img')).toBeNull()
  })
})

describe('the pictures list (public/areas/<slug>.json)', () => {
  it('reads the list, keeping only entries whose file, size and day agree; none without a list', async () => {
    const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'areas-'))
    const raw = sidecar([[2017, '2017-03-12'], [2026, '2026-02-18'], [2020, '2019-03-01']])
    raw.pictures.push({ ...raw.pictures[0], year: 2018, src: '/areas/other-2018.webp' } as never)
    await fs.writeFile(path.join(dir, 'kharadi.json'), JSON.stringify(raw))
    const got = await readAreaPictures('kharadi', dir)
    expect(got.map((p) => [p.year, p.day])).toEqual([[2017, '2017-03-12'], [2026, '2026-02-18']])
    expect(await readAreaPictures('wagholi', dir)).toEqual([])
    expect(await readAreaPictures('../kharadi', dir)).toEqual([])
    expect(cleanAreaPictures(raw, 'wagholi')).toEqual([])               // a list written for another area
  })
})

describe('on the area page', () => {
  it('puts the section after the MahaRERA records, and the pictures only when the list has them', async () => {
    render(await LocalityPage({ params: Promise.resolve({ slug: 'kharadi' }) }))
    const records = screen.getByRole('region', { name: 'In the MahaRERA records' })
    const growth = screen.getByRole('region', { name: 'How Kharadi grew' })
    expect(records.compareDocumentPosition(growth) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(within(growth).queryByRole('img')).toBeNull()
    expect(mockPictures).toHaveBeenCalledWith('kharadi')
  })

  it('uses the newest picture as the link preview when there is a pair, the brand card otherwise', async () => {
    const plain = await generateMetadata({ params: Promise.resolve({ slug: 'kharadi' }) })
    expect(JSON.stringify(plain.openGraph?.images)).toContain('/brand/og.jpg')
    mockPictures.mockResolvedValue(PAIR)
    const m = await generateMetadata({ params: Promise.resolve({ slug: 'kharadi' }) })
    const url = getMarketingConfig().siteUrl + '/areas/kharadi-2026.webp'
    expect(m.openGraph?.images).toEqual([{ url, width: 1000, height: 994, alt: 'Kharadi from above, February 2026, Sentinel-2 satellite' }])
    expect(m.twitter).toMatchObject({ images: [url] })
  })
})
