import React from 'react'
import { render, screen, within } from '@testing-library/react'
import BuyerHome, { metadata } from '@/app/page'

jest.mock('@/components/news/NewsSection', () => ({ __esModule: true, default: () => null }))
jest.mock('next/navigation', () => ({ useRouter: () => ({ push: jest.fn() }), usePathname: () => '/' }))

const API: Record<string, unknown> = {
  '/public/areas/stats': { as_of: '2026-10-21', source: 'MahaRERA', areas: [
    { area: { key: 'kharadi', name: 'Kharadi', slug: 'kharadi', tier: 'it' }, as_of: '2026-10-21', projects: 66, completing: [], units_total: null, units_booked: null, recent: [], source: 'MahaRERA' },
  ] },
  '/public/register/places': [{ key: 'kharadi', slug: 'kharadi', name: 'Kharadi', zone: 'East Pune', projects: 303, indexable: 40, current: 180 },
    { key: 'wagholi', slug: 'wagholi', name: 'Wagholi', zone: 'East Pune', projects: 80, indexable: 0 },
    { key: 'lonavala', slug: 'lonavala', name: 'Lonavala', zone: 'Pune district', projects: 900, indexable: 3, current: 600 },
    { key: 'moshi', slug: 'moshi', name: 'Moshi', zone: 'Pimpri-Chinchwad', projects: 120, indexable: 9, current: 70 },
    { key: 'ravet', slug: 'ravet', name: 'Ravet', zone: 'Pimpri-Chinchwad', projects: 150, indexable: 12, current: 95 }],
  '/public/facets': [
    { key: 'k1', path: '/projects/area/kharadi/new-launches', place: 'kharadi', place_slug: 'kharadi', intent: 'new-launches', possession: null, builder: null, label: 'New launch projects', count: 7, indexable: true, page_updated: null },
    { key: 'w1', path: '/projects/area/wagholi/new-launches', place: 'wagholi', place_slug: 'wagholi', intent: 'new-launches', possession: null, builder: null, label: 'New launch projects', count: 9, indexable: true, page_updated: null },
    { key: 'r1', path: '/projects/area/viman-nagar/ready-to-move', place: 'viman_nagar', place_slug: 'viman-nagar', intent: 'ready-to-move', possession: null, builder: null, label: 'Ready to move projects', count: 4, indexable: true, page_updated: null },
    { key: 't2', path: '/projects/area/moshi/top', place: 'moshi', place_slug: 'moshi', intent: 'top', possession: null, builder: null, label: 'Top projects', count: 40, indexable: true, page_updated: null },
    { key: 't1', path: '/projects/area/kharadi/top', place: 'kharadi', place_slug: 'kharadi', intent: 'top', possession: null, builder: null, label: 'Top projects', count: 23, indexable: true, page_updated: null },
    { key: 'b2', path: '/projects/area/ravet/2-bhk', place: 'ravet', place_slug: 'ravet', intent: 'all', possession: null, builder: null, bhk: 2, label: '2 BHK flats', count: 31, indexable: true, page_updated: null },
    { key: 'b3', path: '/projects/area/kharadi/3-bhk', place: 'kharadi', place_slug: 'kharadi', intent: 'all', possession: null, builder: null, bhk: 3, label: '3 BHK flats', count: 15, indexable: true, page_updated: null },
    { key: 'k2', path: '/projects/area/kharadi/new-launches/by-lodha', place: 'kharadi', place_slug: 'kharadi', intent: 'new-launches', possession: null, builder: 'lodha', label: 'x', count: 3, indexable: true, page_updated: null },
  ],
  '/public/facets/kharadi/top': { key: 'kharadi|top', path: '/projects/area/kharadi/top', place: { key: 'kharadi', slug: 'kharadi', name: 'Kharadi' },
    intent: 'top', count: 23, rows: [1, 2, 3].map((i) => ({ rank: i, slug: `p-${i}`, name: `Project ${i}`, units_total: 100, units_booked: 80, units_open: 20,
      completion_now: '2029-04-30', stage: 'under-construction', price: null, photo: null })) },
  '/public/facets/moshi/top': { key: 'moshi|top', path: '/projects/area/moshi/top', place: { key: 'moshi', slug: 'moshi', name: 'Moshi' },
    intent: 'top', count: 40, rows: [{ rank: 1, slug: 'moshi-one', name: 'Moshi One', units_total: 200, units_booked: 150, units_open: 50,
      completion_now: '2028-12-31', stage: 'under-construction', price: null, photo: null }] },
  '/public/project-videos': { items: [{ slug: 'the-strand-kharadi', name: 'The Strand', video: { url: '/v/a.mp4', poster: '/v/a.jpg' } },
    { slug: 'no-picture', name: 'No Picture', video: { url: '/v/b.mp4', poster: null } }] },
  '/public/register/from-space': [{ slug: 'zen-elite', name: 'Zen Elite', place: 'Kharadi', story: 's', video: null, picture: '/space/zen.jpg', years: [2021, 2026], updated: null, seasons: 4 }],
  '/public/trackers': [{ slug: 'purandar-airport', name: 'Purandar airport', status: 'Land being bought', kind: 'project', areas: [], stages: [] }],
  '/public/register/spotlight': [{ slug: 'lodha-camelot-kharadi', name: 'Lodha Camelot', area: 'Kharadi', area_slug: 'kharadi', note: 'New tower registered', fact: 'f', source: 'MahaRERA', picked: true,
    photos: [{ url: '/uploads/p1/a.webp', alt: 'Towers', source: 'builder' }, { url: '/uploads/p1/b.webp', alt: 'Clubhouse', source: 'builder' }] }],
  '/public/builders': [{ slug: 'lodha', name: 'Lodha', projects: 9, indexable: true, page_updated: null, brand: true },
    { slug: 'thin', name: 'Thin Builder', projects: 1, indexable: false, page_updated: null }],
}

beforeEach(() => {
  global.fetch = jest.fn(async (url: string) => {
    const key = Object.keys(API).find((k) => new URL(String(url)).pathname.endsWith(k))
    return key ? ({ ok: true, status: 200, json: async () => API[key] } as Response) : ({ ok: false, status: 404, json: async () => ({}) } as Response)
  }) as unknown as typeof fetch
})

describe("buyers' home", () => {
  it('is about new projects in Pune, for Google and for people', async () => {
    // the brand first, then what a buyer does here (owner 2026-10-29: someone who searches avasetu should be able to search projects)
    expect(String(metadata.title)).toBe('Avasetu: Search New Projects in Pune, Checked Against MahaRERA')
    // all of Pune, not one corner of it (owner 2026-11-21: the page every profile links to)
    expect(String(metadata.description)).toMatch(/^Search new projects across Pune/)
    expect((metadata.openGraph as { title?: string; siteName?: string }).title).toBe(metadata.title)
    expect((metadata.openGraph as { siteName?: string }).siteName).toBe('Avasetu')
    // Google shows about 70 and 160 characters: nothing past that is read in a search result
    expect(String(metadata.title).length).toBeLessThanOrEqual(70)
    expect(String(metadata.description).length).toBeLessThanOrEqual(160)
    expect(metadata.alternates?.canonical).toMatch(/\/?$/)
    render(await BuyerHome())
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(/new projects in pune/i)
    // the count is the whole city's (being built or just finished, else every registration), and opens the tracker
    const tracked = screen.getByRole('link', { name: '1,025 projects being built across Pune' })
    expect(tracked).toHaveAttribute('href', '/pune-maharera-tracker')
    expect(tracked.parentElement).toHaveTextContent(/across Pune, read from MahaRERA on/i)
    const ask = screen.getAllByRole('link', { name: /tell us what you need/i })   // the header button and the hero's
    expect(ask.length).toBe(2)
    for (const a of ask) expect(a).toHaveAttribute('href', '/enquire')
  })

  it("gives each hot project's card its pictures, stepped through with arrows", async () => {
    render(await BuyerHome())
    const hot = within(screen.getByTestId('home-hot'))
    expect(hot.getByAltText('Towers')).toHaveAttribute('src', '/uploads/p1/a.webp')
    expect(hot.getByRole('button', { name: 'Next picture of Lodha Camelot' })).toBeInTheDocument()
    expect(hot.getAllByRole('link', { name: /lodha camelot/i })).toHaveLength(1)   // the picture's own link is not read out twice
  })

  it("opens an agent-listed hot project at its listed page, never through its register page's redirect", async () => {
    // live 2026-11-04: Lodha Camelot's card linked /projects/kharadi-new-project-tower-1-wagholi, which 308s to /projects/lodha-camelot
    const before = API['/public/register/spotlight']
    API['/public/register/spotlight'] = [{ slug: 'kharadi-new-project-tower-1-wagholi', regnos: ['P52100012345'], name: 'Lodha Camelot', area: 'Kharadi',
      area_slug: 'kharadi', note: null, fact: 'f', source: 'MahaRERA', picked: true, photos: [] }]
    API['/public/projects'] = { items: [{ slug: 'lodha-camelot', rera_no: 'P52100012345', agents: [{ slug: 'house-deal' }] }] }
    try {
      render(await BuyerHome())
      for (const a of within(screen.getByTestId('home-hot')).getAllByRole('link')) expect(a).toHaveAttribute('href', '/projects/lodha-camelot')
    } finally {
      API['/public/register/spotlight'] = before
      delete API['/public/projects']
    }
  })

  it('says what "Hot right now" and the Top lists each rank, so the two never read as the same list', async () => {
    render(await BuyerHome())
    expect(screen.getByTestId('home-hot')).toHaveTextContent(/picked by our team, or drawing the most bookings/i)
    expect(screen.getByRole('region', { name: /find projects by what you need/i })).toHaveTextContent(/top: most homes booked, with homes still open/i)
  })

  it('links the hottest projects, every area, the live lists and builders with pages', async () => {
    render(await BuyerHome())
    expect(within(screen.getByTestId('home-hot')).getByRole('link', { name: /lodha camelot/i })).toHaveAttribute('href', '/projects/lodha-camelot-kharadi')
    expect(screen.queryByTestId('hot-strip')).toBeNull()   // the section replaces the banner here: the same links once
    const zones = within(screen.getByTestId('home-zones'))
    // named as the page it opens ("Flats and residential projects in Kharadi"); "new projects" is the new-launches list's search
    expect(zones.getByRole('link', { name: /^Projects in Kharadi/ })).toHaveAttribute('href', '/projects/area/kharadi')
    // the count is of new projects: it leaves out the older ones (every registration was 303)
    expect(zones.getByRole('link', { name: /^Projects in Kharadi/ })).toHaveTextContent('180')
    expect(screen.getByTestId('home-zones')).not.toHaveTextContent('303')
    // an area whose list is not in search yet is not linked from here: a noindex page never gets the home page's link
    expect(zones.queryByRole('link', { name: /Wagholi/ })).toBeNull()
    // every area guide, whatever the API says
    expect(within(screen.getByTestId('home-guides')).getByRole('link', { name: 'Wagholi' })).toHaveAttribute('href', '/localities/wagholi')
    const launches = within(screen.getByTestId('home-launches')).getAllByRole('link')
    // our areas in the area list's order (east Pune first), not the biggest list first; builder lists stay on their place
    expect(launches.map((a) => a.getAttribute('href'))).toEqual(['/projects/area/kharadi/new-launches', '/projects/area/wagholi/new-launches'])
    // every list has the same label, so each chip names its area or they all read alike
    expect(launches.map((a) => a.textContent)).toEqual(['New launches in Kharadi (7)', 'New launches in Wagholi (9)'])
    expect(screen.getByRole('link', { name: 'Ready to move in Viman Nagar (4)' })).toHaveAttribute('href', '/projects/area/viman-nagar/ready-to-move')
    // the size lists, each chip naming its area
    expect(within(screen.getByTestId('home-2bhk')).getByRole('link', { name: '2 BHK in Ravet (31)' })).toHaveAttribute('href', '/projects/area/ravet/2-bhk')
    expect(within(screen.getByTestId('home-3bhk')).getByRole('link', { name: '3 BHK in Kharadi (15)' })).toHaveAttribute('href', '/projects/area/kharadi/3-bhk')
    const builders = within(screen.getByTestId('home-builders')).getAllByRole('link')
    expect(builders.map((a) => a.getAttribute('href'))).toEqual(['/builders/lodha'])
  })

  it("links the Top list of every area and shows the first of each zone's, east Pune first", async () => {
    render(await BuyerHome())
    const chips = within(screen.getByTestId('home-tops')).getAllByRole('link')
    expect(chips.map((a) => a.getAttribute('href'))).toEqual(['/projects/area/kharadi/top', '/projects/area/moshi/top'])
    const leads = screen.getByTestId('home-leads')
    expect(leads).toHaveTextContent(/most booked in each part of pune/i)
    const cards = within(leads).getAllByRole('link', { name: /Project 1|Moshi One/ }).map((a) => a.getAttribute('href'))
    expect([...new Set(cards)]).toEqual(['/projects/p-1', '/projects/moshi-one'])
    expect(within(leads).getByRole('link', { name: 'Top 40 in Moshi' })).toHaveAttribute('href', '/projects/area/moshi/top')
  })

  it("speaks for all of Pune: each zone in the hero, east Pune first and the district's towns last", async () => {
    render(await BuyerHome())
    const hero = within(screen.getByTestId('hero-zones'))
    const zones = hero.getAllByRole('link')
    expect(zones.map((a) => a.getAttribute('href'))).toEqual(['#zone-east-pune', '#zone-pimpri-chinchwad', '#zone-pune-district'])
    expect(zones[1]).toHaveTextContent(/Pimpri-Chinchwad.*Ravet, Moshi.*165/)
    // each opens its own block of areas further down
    expect(document.getElementById('zone-pimpri-chinchwad')).toHaveTextContent(/Projects in Ravet/)
    // the east Pune corridor is on the east area guides now, not here
    expect(screen.queryByTestId('corridor-map')).toBeNull()
  })

  it('leads to the home plan from the hero and with one tap per office, east and west', async () => {
    render(await BuyerHome())
    expect(screen.getByRole('link', { name: 'Get a free home plan for your family' })).toHaveAttribute('href', '/home-plan')
    const offices = within(screen.getByTestId('home-plan')).getAllByRole('link').filter((l) => l.textContent?.startsWith('I work'))
    expect(offices.map((l) => l.getAttribute('href'))).toEqual(['/home-plan?work=kharadi', '/home-plan?work=magarpatta', '/home-plan?work=airport',
      '/home-plan?work=west', '/home-plan?work=elsewhere'])
  })

  it('shows the videos that have a picture, the projects from space and every tracker', async () => {
    render(await BuyerHome())
    const videos = within(screen.getByTestId('home-videos')).getAllByRole('link')
    expect(videos.map((a) => a.getAttribute('href'))).toEqual(['/projects/the-strand-kharadi/video'])
    expect(screen.getByRole('link', { name: /pune projects from space/i })).toHaveAttribute('href', '/projects/from-space')
    expect(within(screen.getByTestId('home-trackers')).getByRole('link', { name: /Purandar airport/ })).toHaveAttribute('href', '/news/track/purandar-airport')
  })

  it('names the search box target for Google and sends agents to /agents', async () => {
    const { container } = render(await BuyerHome())
    const ld = Array.from(container.querySelectorAll('script[type="application/ld+json"]')).map((s) => JSON.parse(s.textContent || '{}'))
    expect(ld.map((x) => x['@type'])).toEqual(['Organization', 'WebSite'])
    expect(ld[1].potentialAction.target.urlTemplate).toMatch(/\/projects\?q=\{search_term_string\}$/)
    // who answers for the site: House Deal's office and phone (lib/site/team, owner 2026-11-13)
    expect(ld[0].contactPoint).toEqual([expect.objectContaining({ telephone: '+917447212121', email: 'housedealofficial@gmail.com' })])
    // the office is House Deal's, so the address sits on House Deal only, and House Deal is said once (owner 2026-11-21)
    expect(ld[0].address).toBeUndefined()
    expect(ld[0].member).toBeUndefined()
    // Avasetu belongs to House Deal (owner's plan 2026-11-20), and the WebSite's publisher is this Organization, by its id
    expect(ld[0].parentOrganization).toMatchObject({ '@type': 'RealEstateAgent', '@id': 'https://house-deal.com/#organization',
      name: 'House Deal', url: 'https://house-deal.com', identifier: { propertyID: 'MahaRERA', value: 'A031262502865' }, address: { postalCode: '412207' } })
    expect(ld[0]['@id']).toMatch(/\/#organization$/)
    expect(ld[1].publisher).toEqual({ '@id': ld[0]['@id'] })
    // the brand's own profiles and its Devanagari name, so Google ties "Avasetu" to this page; no WhatsApp chat link
    expect(ld[0].name).toBe('Avasetu')
    expect(ld[0].sameAs).toEqual(['https://www.facebook.com/profile.php?id=61594653947865', 'https://www.instagram.com/avasetu_/',
      'https://www.linkedin.com/company/avasetu/', 'https://www.youtube.com/@avasetu'])
    expect(ld[0].alternateName).toEqual(['आवासेतु'])
    expect(ld[1].alternateName).toEqual(['आवासेतु'])
    expect(JSON.stringify(ld)).not.toMatch(/wa\.me/)
    expect(screen.getAllByRole('link', { name: /^for agents$/i }).every((a) => a.getAttribute('href') === '/agents')).toBe(true)
  })

  it('still renders, with the areas, when the API is down', async () => {
    global.fetch = jest.fn(async () => { throw new Error('down') }) as unknown as typeof fetch
    render(await BuyerHome())
    expect(screen.getByRole('heading', { level: 1 })).toBeInTheDocument()
    expect(within(screen.getByTestId('home-guides')).getByRole('link', { name: 'Kharadi' })).toHaveAttribute('href', '/localities/kharadi')
    expect(screen.queryByTestId('hero-zones')).toBeNull()
    expect(screen.queryByTestId('home-hot')).toBeNull()
  }, 30000)   // the register reads wait out their retries (lib/site/retry) before giving up
})
