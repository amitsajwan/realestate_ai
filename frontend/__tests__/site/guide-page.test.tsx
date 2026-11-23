import React from 'react'
import { fireEvent, render, screen, within } from '@testing-library/react'

// The guide page reads its topic from the API: replaced here with a small Upper Kharadi-shaped topic.
const mockFetchTopic = jest.fn()
jest.mock('@/lib/site/topics', () => ({ ...jest.requireActual('@/lib/site/topics'), fetchTopic: (slug: string) => mockFetchTopic(slug) }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('next/navigation', () => ({
  notFound: () => { throw new Error('NOT_FOUND') },
  permanentRedirect: (to: string) => { throw new Error(`REDIRECT ${to}`) },
  usePathname: () => '/',
  useRouter: () => ({ push: jest.fn() }),
}))
// an area's guide is the area's page (components/area/AreaPage), which also reads the area's projects and listings: none here,
// and every other read answers 404 (each section then leaves itself out)
const mockCatalog = jest.fn(async () => [] as unknown[])
jest.mock('@/lib/site/api', () => ({
  getCatalog: () => mockCatalog(),
  getLocalityListings: async () => [],
  fixturesForced: () => false,
  serverApiBase: () => 'http://api',
}))
beforeAll(() => { global.fetch = jest.fn(async () => ({ ok: false, status: 404, json: async () => ({}) })) as unknown as typeof fetch })
jest.mock('@/components/site/PostsGrid', () => ({ __esModule: true, default: () => null }))

// the area's landmarks, counts and photos (an area guide names this page canonical, so they are shown here too)
const mockLandmarks = jest.fn(async () => null as unknown)
jest.mock('@/components/localities/AreaLandmarks', () => ({
  __esModule: true, ...jest.requireActual('@/components/localities/AreaLandmarks'), getAreaLandmarks: () => mockLandmarks() }))
jest.mock('@/components/localities/areaStats', () => ({ ...jest.requireActual('@/components/localities/areaStats'), getAreaStats: async () => null }))
jest.mock('@/components/localities/areaPhotoData', () => ({ ...jest.requireActual('@/components/localities/areaPhotoData'), getAreaPhotos: async () => [] }))

// the area's lists in search (the place page's own chips)
const mockFacets = jest.fn(async () => [] as unknown[])
jest.mock('@/lib/site/facets', () => ({ ...jest.requireActual('@/lib/site/facets'), getFacets: () => mockFacets() }))

import TopicPage from '@/app/guides/[slug]/page'
import { cleanAreaLandmarks } from '@/components/localities/AreaLandmarks'
import { OPEN_CHAT_EVENT } from '@/components/site/ChatWidget'

const en = (x: string) => ({ en: x })
const TOPIC = {
  slug: 'upper-kharadi', lang: 'en', status: null, checked_on: '2026-10-19',
  title: en('Upper Kharadi'), summary: en('Summary'), status_line: en('Status'), dates: [],
  sections: [
    { id: 'where', heading: en('Where is Upper Kharadi?'), items: { en: ['**PIN code reality:** Most projects carry 412207.'] } },
    {
      id: 'projects', heading: en('Projects'), items: { en: [] },
      table: {
        columns: ['Project', 'Booked'],
        rows: [
          { cells: ['Gera World of Joy M', '320 (100%)'], href: '/projects/geras-world-of-joy-m-wagholi', tag: 'resale' },
          { cells: ['Godrej Ivara', '489 (18%)'], href: '/projects/godrej-ivara-pune', tag: 'open' },
        ],
      },
    },
    {
      id: 'prices', heading: en('What does it cost?'), items: { en: [] },
      tables: [
        { title: en('Locality averages'), columns: ['What', 'Figure', 'Source'], rows: [{ cells: ['Kharadi', '₹14,199', 'Square Yards'] }] },
        { title: en('Project specifics'), columns: ['Project', 'Price', 'Source'], rows: [{ cells: ['Lodha Camelot 3 BHK', '₹2.21 crore', 'Homebazaar'], href: '/projects/lodha-camelot' }] },
      ],
    },
    {
      id: 'check', heading: en('Seven questions'), items: { en: ['What is the MahaRERA number?'] },
      cta: { text: en('Want the MahaRERA record?'), button: en('Chat with us now'), message: en('I want the MahaRERA details') },
    },
  ],
  results: null, faq: [], links: [], warning: en('Check papers'), sources: [], updates: [],
}

beforeEach(() => mockFetchTopic.mockResolvedValue({ ok: true, topic: TOPIC }))

async function page() {
  render(await TopicPage({ params: Promise.resolve({ slug: 'upper-kharadi' }) }))
}

test('an item lead-in is bold without its asterisks', async () => {
  await page()
  expect(screen.getByText('PIN code reality:').tagName).toBe('STRONG')
  expect(screen.queryByText(/\*\*/)).toBeNull()
})

test('project rows link our page and carry an availability chip and tint', async () => {
  await page()
  const row = screen.getByRole('link', { name: 'Godrej Ivara' }).closest('tr')!
  expect(row.getAttribute('data-tag')).toBe('open')
  expect(within(row).getByText('High availability')).toBeTruthy()
  const full = screen.getByRole('link', { name: 'Gera World of Joy M' }).closest('tr')!
  expect(within(full).getByText('Resale only')).toBeTruthy()
})

test('prices show two titled tables and no booking row', async () => {
  await page()
  expect(screen.getByRole('heading', { name: 'Locality averages' })).toBeTruthy()
  expect(screen.getByRole('heading', { name: 'Project specifics' })).toBeTruthy()
  expect(screen.getAllByRole('table')).toHaveLength(3)
})

test('the cta button opens the chat with its question', async () => {
  await page()
  const heard = jest.fn()
  window.addEventListener(OPEN_CHAT_EVENT, (e) => heard((e as CustomEvent).detail))
  fireEvent.click(screen.getByRole('button', { name: 'Chat with us now' }))
  expect(heard).toHaveBeenCalledWith({ message: 'I want the MahaRERA details' })
})

test("an area's guide shows its landmarks and metro, and asks the area's questions in its FAQ data", async () => {
  const at = (name: string, km: number, distance: string, extra: Record<string, unknown>) => ({ name, lat: 18.55, lon: 73.95, km, distance,
    maps: 'https://www.google.com/maps/search/?api=1&query=18.55,73.95', source: 'OpenStreetMap', ...extra })
  mockLandmarks.mockResolvedValue(cleanAreaLandmarks({
    area: { key: 'upper_kharadi', name: 'Upper Kharadi', slug: 'upper-kharadi' }, middle: { lat: 18.56, lon: 73.9685 },
    metro: [at('Ramwadi', 6.5, 'about 6.5 km west of the middle of Upper Kharadi', { kind: 'metro', line: '2', line_short: 'Aqua Line (Line 2)',
      status: 'running', running: true })],
    landmarks: [at('EON IT Park', 3, 'about 3 km west of the middle of Upper Kharadi', { kind: 'work', kind_label: 'Work' })],
    note: 'Straight-line distances.', attribution: 'Positions © OpenStreetMap contributors', checked_on: '2026-11-17',
  }, 'upper-kharadi'))
  const { container } = render(await TopicPage({ params: Promise.resolve({ slug: 'upper-kharadi' }) }))
  expect(screen.getByTestId('metro-answer').textContent).toBe(
    'The nearest running metro station to Upper Kharadi is Ramwadi (Aqua Line (Line 2)), about 6.5 km west of the middle of Upper Kharadi, as of November 2026.')
  // one list of questions: the guide's, the area's own, then the ones its landmarks answer; shown and in the FAQPage data alike
  const list = screen.getByRole('heading', { name: 'Questions people ask' }).closest('section')!
  const shown = Array.from(list.querySelectorAll('summary')).map((x) => x.textContent!.replace(/\+$/, ''))
  const faq = [...container.querySelectorAll('script[type="application/ld+json"]')].map((x) => JSON.parse(x.textContent || '{}'))
    .find((x) => x['@type'] === 'FAQPage')
  expect(faq.mainEntity.map((q: { name: string }) => q.name)).toEqual(shown)
  expect(shown).toEqual(expect.arrayContaining(['What is the difference between Kharadi and Upper Kharadi?',
    'Is there a metro station near Upper Kharadi?', 'Which IT parks and offices are near Upper Kharadi?']))
})

test('an area guide links the place page and its lists in search, which own "projects in X"', async () => {
  const facet = (intent: string, path: string, indexable: boolean, bhk: number | null = null) => ({ key: path, path, place: path.split('/')[3].replace(/-/g, '_'),
    place_slug: path.split('/')[3], intent, possession: null, builder: null, bhk, label: bhk ? `${bhk} BHK Flats` : intent, count: 9, indexable, page_updated: null })
  mockFacets.mockResolvedValueOnce([facet('top', '/projects/area/upper-kharadi/top', true), facet('all', '/projects/area/upper-kharadi/2-bhk', true, 2),
    facet('ready-to-move', '/projects/area/upper-kharadi/ready-to-move', false), facet('top', '/projects/area/wagholi/top', true)])
  await page()
  const block = screen.getByRole('heading', { name: 'Projects and flats in Upper Kharadi' }).closest('section')!
  const hrefs = Array.from(block.querySelectorAll('a')).map((a) => a.getAttribute('href'))
  expect(within(block).getByRole('link', { name: 'See every project in Upper Kharadi' }).getAttribute('href')).toBe('/projects/area/upper-kharadi')
  expect(hrefs).toEqual(expect.arrayContaining(['/projects/area/upper-kharadi/top', '/projects/area/upper-kharadi/2-bhk']))
  expect(hrefs).not.toContain('/projects/area/upper-kharadi/ready-to-move')   // not in search
  expect(hrefs).not.toContain('/projects/area/wagholi/top')
})
