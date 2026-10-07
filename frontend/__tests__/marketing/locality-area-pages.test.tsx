import React from 'react'
import { render, screen, within } from '@testing-library/react'

// The area page reads listings, projects and the MahaRERA area stats from the API: replaced here.
const mockFetch = jest.fn()
const mockCatalog = jest.fn()
const mockListings = jest.fn()
jest.mock('@/lib/site/api', () => ({
  getCatalog: (locality?: string) => mockCatalog(locality),
  getLocalityListings: (locality: string) => mockListings(locality),
  fixturesForced: () => false,
  serverApiBase: () => 'http://api',
}))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('next/navigation', () => ({
  notFound: () => { throw new Error('NOT_FOUND') },
  usePathname: () => '/',
  useRouter: () => ({ push: jest.fn() }),
}))

import LocalitiesPage from '@/app/localities/page'
import LocalityPage from '@/app/localities/[slug]/page'
import AreaRecords from '@/components/localities/AreaRecords'
import { cleanAreaStats, getAreaStats, longDate } from '@/components/localities/areaStats'

const STATS = {
  area: { key: 'wagholi', name: 'Wagholi', slug: 'wagholi', tier: 'affordable' },
  as_of: '2026-10-04',
  projects: 41,
  completing: [{ year: 2027, projects: 12 }, { year: 2026, projects: 6 }],
  units_total: 5210, units_booked: 3100,
  recent: [
    { name: 'Rohan Abhilasha 4', regno: 'P52100080076', promoter: 'Rohan Builders', completion: '2029-10-30', updated: '2026-09-28', url: 'https://maharerait.maharashtra.gov.in/public/project/view/1' },
    { name: 'Odd link', regno: 'P1', url: 'https://example.com/x' },
  ],
  source: 'MahaRERA public records',
}

function respond(status: number, body: unknown) {
  mockFetch.mockResolvedValue({ ok: status >= 200 && status < 300, status, json: async () => body })
}

beforeEach(() => {
  mockFetch.mockReset()
  mockCatalog.mockReset()
  mockListings.mockReset()
  mockCatalog.mockResolvedValue([])
  mockListings.mockResolvedValue([])
  global.fetch = mockFetch as unknown as typeof fetch
})

describe('area stats from MahaRERA', () => {
  it('reads the stats for the slug, revalidated like the other public data', async () => {
    respond(200, STATS)
    const s = await getAreaStats('wagholi')
    expect(mockFetch.mock.calls[0][0]).toBe('http://api/api/v1/public/areas/wagholi/stats')
    expect(mockFetch.mock.calls[0][1]).toMatchObject({ next: { revalidate: 30 } })
    expect(s?.projects).toBe(41)
    expect(s?.completing.map((c) => c.year)).toEqual([2026, 2027])
    expect(s?.recent[1].url).toBeNull() // only MahaRERA links are shown as links
  })

  it('gives null (the section is hidden) on 404, an outage, zero projects or a body for another area', async () => {
    respond(404, {})
    expect(await getAreaStats('wagholi')).toBeNull()
    respond(500, {})
    expect(await getAreaStats('wagholi')).toBeNull()
    mockFetch.mockRejectedValue(new Error('down'))
    expect(await getAreaStats('wagholi')).toBeNull()
    respond(200, { ...STATS, projects: 0 })
    expect(await getAreaStats('wagholi')).toBeNull()
    expect(cleanAreaStats(STATS, 'baner')).toBeNull()
    expect(cleanAreaStats('nope', 'wagholi')).toBeNull()
  })

  it('never shows a booked figure without a total, or more booked than the total', () => {
    expect(cleanAreaStats({ ...STATS, units_total: null }, 'wagholi')).toMatchObject({ units_total: null, units_booked: null })
    expect(cleanAreaStats({ ...STATS, units_booked: 9999 }, 'wagholi')).toMatchObject({ units_total: null, units_booked: null })
  })

  it('formats dates without time zone surprises', () => {
    expect(longDate('2026-10-04')).toBe('4 October 2026')
    expect(longDate('bad')).toBe('')
  })
})

describe('the "In the MahaRERA records" section', () => {
  it('shows counts, completion years, homes booked, recent projects and the dated source; never "newly registered"', () => {
    render(<AreaRecords name="Wagholi" stats={cleanAreaStats(STATS, 'wagholi')} />)
    const s = screen.getByRole('region', { name: 'In the MahaRERA records' })
    expect(s).toHaveTextContent('41 projects in Wagholi')
    expect(s).toHaveTextContent('2026')
    expect(s).toHaveTextContent('12 projects')
    expect(s).toHaveTextContent('3,100 of 5,210')
    expect(within(s).getByRole('link', { name: 'Rohan Abhilasha 4' })).toHaveAttribute('href', 'https://maharerait.maharashtra.gov.in/public/project/view/1')
    expect(within(s).queryByRole('link', { name: 'Odd link' })).toBeNull()
    expect(s).toHaveTextContent('listed or updated 28 September 2026')
    expect(s).toHaveTextContent('Source: MahaRERA public records, as of 4 October 2026')
    expect(s.textContent).not.toMatch(/newly registered|new launch/i)
  })

  it('leaves out homes booked when the totals are not known', () => {
    render(<AreaRecords name="Wagholi" stats={cleanAreaStats({ ...STATS, units_total: null, units_booked: null }, 'wagholi')} />)
    expect(screen.getByRole('region', { name: 'In the MahaRERA records' })).not.toHaveTextContent(/booked/i)
  })

  it('renders nothing without stats', () => {
    const { container } = render(<AreaRecords name="Wagholi" stats={null} />)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('area pages', () => {
  it('shows the section when the API has records, and asks for an enquiry tagged with the area', async () => {
    respond(200, STATS)
    render(await LocalityPage({ params: Promise.resolve({ slug: 'wagholi' }) }))
    expect(screen.getByRole('region', { name: 'In the MahaRERA records' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Tell us what you are looking for' })).toHaveAttribute('href', '/agent/avasetu?src=locality_wagholi#enquire')
  })

  it('still renders the page, without the section, when the stats call fails', async () => {
    mockFetch.mockRejectedValue(new Error('down'))
    render(await LocalityPage({ params: Promise.resolve({ slug: 'keshav-nagar' }) }))
    expect(screen.getByRole('heading', { level: 1, name: 'Keshav Nagar, Pune' })).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'In the MahaRERA records' })).toBeNull()
    expect(screen.getByRole('link', { name: 'Tell us what you are looking for' })).toHaveAttribute('href', '/agent/avasetu?src=locality_keshav_nagar#enquire')
  })

  it('renders a non-curated locality only from live listing/project data', async () => {
    mockListings.mockResolvedValue([{
      id: 'L1', status: 'live', transaction: 'sale', property_type: 'plot', title: 'Plot in Gulmohar City',
      description: { en: 'Residential plot.' }, price_inr: 5000000, city: 'Pune', locality: 'Gulmohar City',
      amenities: [], media: [], agent: { slug: 'house-deal', agent_name: 'House Deal' },
    }])
    render(await LocalityPage({ params: Promise.resolve({ slug: 'gulmohar-city' }) }))
    expect(mockListings).toHaveBeenCalledWith('Gulmohar City')
    expect(mockCatalog).toHaveBeenCalledWith('Gulmohar City')
    expect(screen.getByRole('heading', { level: 1, name: 'Gulmohar City, Pune' })).toBeInTheDocument()
    expect(screen.getByText(/do not have a full buyer guide for Gulmohar City yet/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Tell us what you are looking for' })).toHaveAttribute('href', '/agent/avasetu?src=locality_gulmohar_city#enquire')
    expect(screen.getByText('Plot in Gulmohar City')).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Sources' })).toBeNull()
  })

  it('404s a non-curated locality when there is no public data', async () => {
    await expect(LocalityPage({ params: Promise.resolve({ slug: 'no-public-data' }) })).rejects.toThrow('NOT_FOUND')
  })

  it('groups the index into affordable homes and the IT corridor', () => {
    render(<LocalitiesPage />)
    const affordable = screen.getByRole('region', { name: 'Affordable homes' })
    const it = screen.getByRole('region', { name: 'IT corridor' })
    expect(within(affordable).getAllByRole('link').map((a) => a.getAttribute('href'))).toEqual(
      ['/localities/upper-kharadi', '/localities/wagholi', '/localities/lohegaon', '/localities/keshav-nagar'])
    expect(within(it).getAllByRole('link').map((a) => a.getAttribute('href'))).toEqual(
      ['/localities/kharadi', '/localities/hinjawadi', '/localities/wakad', '/localities/baner'])
  })
})
