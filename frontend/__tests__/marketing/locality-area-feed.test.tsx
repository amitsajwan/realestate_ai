import React from 'react'
import { render, screen, within } from '@testing-library/react'

// The area page reads listings, projects, MahaRERA stats, posts and news from the API: replaced here.
const mockFetch = jest.fn()
jest.mock('@/lib/site/api', () => ({
  getCatalog: async () => [],
  getLocalityListings: async () => [],
  fixturesForced: () => false,
  serverApiBase: () => 'http://api',
}))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('next/navigation', () => ({
  notFound: () => { throw new Error('NOT_FOUND') },
  usePathname: () => '/',
  useRouter: () => ({ push: jest.fn() }),
}))

import LocalityPage, { generateMetadata } from '@/app/localities/[slug]/page'
import AreaLatest from '@/components/localities/AreaLatest'
import { cleanAreaNews, cleanAreaPosts, feedDate, getAreaNews, getAreaPosts } from '@/components/localities/areaFeed'

const WAGHOLI = { key: 'wagholi', slug: 'wagholi' }
const KESHAV = { key: 'keshav_nagar', slug: 'keshav-nagar' }

const POSTS = [
  { id: 'p1', slug: 'wagholi-41-projects-in-maharera-records', area: 'wagholi', kind: 'post', title: 'Wagholi: 41 projects in MahaRERA records', excerpt: 'What the register says.', published_at: '2026-10-03T05:00:00Z', extra: { ignored: true } },
  { id: 'p2', slug: 'baner-guide', area: 'baner', kind: 'post', title: 'Baner guide', excerpt: '', published_at: '2026-10-02T05:00:00Z' },
  { id: 'p3', area: 'wagholi', kind: 'reel', title: 'No slug yet', excerpt: '', published_at: '2026-10-02T05:00:00Z' },
  { id: 'p4', slug: 'Bad Slug!', area: 'wagholi', kind: 'post', title: 'Bad slug', excerpt: '', published_at: '' },
  { id: 'p5', slug: 'untagged-post', area: null, kind: 'post', title: 'Untagged', excerpt: '', published_at: '' },
  { id: 'p6', slug: 'wagholi-reel', area: 'wagholi', kind: 'reel', title: 'Wagholi in 30 seconds', excerpt: '', published_at: '2026-10-01T05:00:00Z' },
]

const NEWS = [
  { id: 'wagholi-road-widening-approved-f5ddee', kind: 'story', headline: 'Wagholi road widening approved', summary: 'PMRDA approved it.', source_name: 'PMRDA', published_at: '2026-10-02T05:00:00Z', areas: [{ slug: 'wagholi', name: 'Wagholi' }] },
  { id: 'baner-story-abc123', kind: 'story', headline: 'Baner story', summary: '', source_name: 'X', published_at: '', areas: [{ slug: 'baner', name: 'Baner' }] },
  { id: 'no-areas-abc123', kind: 'story', headline: 'No areas', summary: '', source_name: 'X', published_at: '', areas: [] },
  { id: '', headline: 'No id', areas: [{ slug: 'wagholi', name: 'Wagholi' }] },
  { id: 'digest-2026-w40', kind: 'digest', headline: 'Week 40 digest', summary: '', source_name: '', published_at: '', areas: [{ slug: 'wagholi', name: 'Wagholi' }, { slug: 'kharadi', name: 'Kharadi' }] },
]

/** Replies by endpoint; anything not listed is a 404. */
function routes(map: Record<string, { status: number; body: unknown } | Error>) {
  mockFetch.mockImplementation(async (url: string) => {
    const key = Object.keys(map).find((k) => url.includes(k))
    const r = key ? map[key] : { status: 404, body: {} }
    if (r instanceof Error) throw r
    return { ok: r.status >= 200 && r.status < 300, status: r.status, json: async () => r.body }
  })
}

beforeEach(() => {
  mockFetch.mockReset()
  global.fetch = mockFetch as unknown as typeof fetch
})

describe('area feed data', () => {
  it('asks for this area by key, revalidated like the other public data', async () => {
    routes({ '/public/posts': { status: 200, body: POSTS }, '/public/news': { status: 200, body: NEWS } })
    await getAreaPosts(KESHAV, 6)
    await getAreaNews(KESHAV, 5)
    expect(mockFetch.mock.calls[0][0]).toBe('http://api/api/v1/public/posts?limit=6&area=keshav_nagar')
    expect(mockFetch.mock.calls[1][0]).toBe('http://api/api/v1/public/news?limit=5&area=keshav_nagar')
    expect(mockFetch.mock.calls[0][1]).toMatchObject({ next: { revalidate: 30 } })
  })

  it('keeps only posts tagged with this area that have a valid slug; unknown fields are ignored', async () => {
    routes({ '/public/posts': { status: 200, body: POSTS } })
    const posts = await getAreaPosts(WAGHOLI)
    expect(posts.map((p) => p.slug)).toEqual(['wagholi-41-projects-in-maharera-records', 'wagholi-reel'])
    expect(posts[0]).toEqual({ slug: 'wagholi-41-projects-in-maharera-records', title: 'Wagholi: 41 projects in MahaRERA records', excerpt: 'What the register says.', kind: 'post', published_at: '2026-10-03T05:00:00Z' })
    expect(posts[1].kind).toBe('reel')
  })

  it('shows nothing while the backend ignores `area` and sends no area or slug (posts as they are today)', () => {
    const today = POSTS.map(({ slug: _s, area: _a, ...rest }) => rest)
    expect(cleanAreaPosts(today, WAGHOLI)).toEqual([])
  })

  it('keeps only news about this area (by area slug or key), with an id and headline', async () => {
    routes({ '/public/news': { status: 200, body: NEWS } })
    expect((await getAreaNews(WAGHOLI)).map((n) => n.id)).toEqual(['wagholi-road-widening-approved-f5ddee', 'digest-2026-w40'])
    expect(cleanAreaNews([{ id: 'k-1', headline: 'Keshav Nagar', areas: [{ key: 'keshav_nagar' }] }, { id: 'k-2', headline: 'By key', areas: ['keshav_nagar'] }], KESHAV)
      .map((n) => n.id)).toEqual(['k-1', 'k-2'])
    expect(cleanAreaNews([{ id: 'x/../y', headline: 'Odd id', areas: ['keshav_nagar'] }], KESHAV)).toEqual([])
  })

  it('never shows more than asked for, even when the backend sends more', () => {
    const many = Array.from({ length: 10 }, (_, i) => ({ slug: `wagholi-post-${i}`, area: 'wagholi', title: `Post ${i}` }))
    expect(cleanAreaPosts(many, WAGHOLI, 6)).toHaveLength(6)
  })

  it('gives empty lists on an error status, an outage or a malformed body', async () => {
    routes({ '/public/posts': { status: 500, body: {} }, '/public/news': new Error('down') })
    expect(await getAreaPosts(WAGHOLI)).toEqual([])
    expect(await getAreaNews(WAGHOLI)).toEqual([])
    routes({ '/public/posts': { status: 200, body: { items: POSTS } }, '/public/news': { status: 200, body: 'nope' } })
    expect(await getAreaPosts(WAGHOLI)).toEqual([])
    expect(await getAreaNews(WAGHOLI)).toEqual([])
    expect(cleanAreaPosts([null, 3, 'x', []], WAGHOLI)).toEqual([])
  })

  it('formats dates in India time', () => {
    expect(feedDate('2026-10-03T20:00:00Z')).toBe('4 Oct 2026')
    expect(feedDate('')).toBe('')
    expect(feedDate('bad')).toBe('')
  })
})

describe('the "Latest from <Area>" block', () => {
  it('links each post to /posts/<slug> and each story to /news/<id>', () => {
    render(<AreaLatest name="Wagholi" posts={cleanAreaPosts(POSTS, WAGHOLI)} news={cleanAreaNews(NEWS, WAGHOLI)} />)
    const s = screen.getByRole('region', { name: 'Latest from Wagholi' })
    const posts = within(s).getByRole('group', { name: 'Our posts about Wagholi' })
    expect(within(posts).getByRole('link', { name: 'Wagholi: 41 projects in MahaRERA records' })).toHaveAttribute('href', '/posts/wagholi-41-projects-in-maharera-records')
    expect(within(posts).getByRole('link', { name: 'All posts' })).toHaveAttribute('href', '/posts')
    const news = within(s).getByRole('group', { name: 'News about Wagholi' })
    expect(within(news).getByRole('link', { name: 'Wagholi road widening approved' })).toHaveAttribute('href', '/news/wagholi-road-widening-approved-f5ddee')
    expect(news).toHaveTextContent('Source: PMRDA')
    expect(s.textContent).not.toMatch(/Baner|No slug yet|Untagged/)
  })

  it('leaves out an empty list, and the whole block when both are empty', () => {
    const { rerender, container } = render(<AreaLatest name="Wagholi" posts={[]} news={cleanAreaNews(NEWS, WAGHOLI)} />)
    expect(screen.queryByRole('group', { name: 'Our posts about Wagholi' })).toBeNull()
    expect(screen.getByRole('group', { name: 'News about Wagholi' })).toBeInTheDocument()
    rerender(<AreaLatest name="Wagholi" posts={[]} news={[]} />)
    expect(container).toBeEmptyDOMElement()
  })
})

describe('area page as the hub', () => {
  it('renders the latest posts and news for the area', async () => {
    routes({ '/public/posts': { status: 200, body: POSTS }, '/public/news': { status: 200, body: NEWS } })
    render(await LocalityPage({ params: Promise.resolve({ slug: 'wagholi' }) }))
    const s = screen.getByRole('region', { name: 'Latest from Wagholi' })
    expect(within(s).getAllByRole('link').map((a) => a.getAttribute('href'))).toEqual([
      '/posts/wagholi-41-projects-in-maharera-records', '/posts/wagholi-reel', '/posts',
      '/news/wagholi-road-widening-approved-f5ddee', '/news/digest-2026-w40', '/news',
    ])
  })

  it('still renders, without the block, when posts and news fail', async () => {
    routes({ '/public/posts': new Error('down'), '/public/news': { status: 503, body: {} } })
    render(await LocalityPage({ params: Promise.resolve({ slug: 'wagholi' }) }))
    expect(screen.getByRole('heading', { level: 1, name: 'Wagholi, Pune' })).toBeInTheDocument()
    expect(screen.queryByRole('region', { name: 'Latest from Wagholi' })).toBeNull()
  })

  it('links to the other areas of the same tier, and to all guides', async () => {
    routes({})
    render(await LocalityPage({ params: Promise.resolve({ slug: 'wagholi' }) }))
    const other = screen.getByRole('region', { name: 'Other affordable areas we cover' })
    expect(within(other).getAllByRole('link').map((a) => a.getAttribute('href'))).toEqual(
      ['/localities/upper-kharadi', '/localities/lohegaon', '/localities/keshav-nagar', '/localities'])
  })

  it('names the IT corridor for IT areas', async () => {
    routes({})
    render(await LocalityPage({ params: Promise.resolve({ slug: 'hinjawadi' }) }))
    const other = screen.getByRole('region', { name: 'Other IT corridor areas we cover' })
    expect(within(other).getAllByRole('link').map((a) => a.getAttribute('href'))).toEqual(
      ['/localities/kharadi', '/localities/wakad', '/localities/baner', '/localities'])
  })

  it('has valid FAQPage and BreadcrumbList JSON-LD', async () => {
    routes({})
    const { container } = render(await LocalityPage({ params: Promise.resolve({ slug: 'lohegaon' }) }))
    const ld = Array.from(container.querySelectorAll('script[type="application/ld+json"]')).map((s) => JSON.parse(s.innerHTML))
    const faq = ld.find((x) => x['@type'] === 'FAQPage')
    const crumbs = ld.find((x) => x['@type'] === 'BreadcrumbList')
    expect(faq.mainEntity.length).toBeGreaterThan(0)
    expect(faq.mainEntity[0]).toMatchObject({ '@type': 'Question', acceptedAnswer: { '@type': 'Answer' } })
    expect(crumbs.itemListElement.map((i: { position: number }) => i.position)).toEqual([1, 2, 3])
    expect(String(crumbs.itemListElement[2].item)).toMatch(/\/localities\/lohegaon$/)
  })

  it('has a title and description buyers search for, and a canonical URL', async () => {
    const m = await generateMetadata({ params: Promise.resolve({ slug: 'keshav-nagar' }) })
    expect(m.title).toBe('Keshav Nagar, Pune: projects, MahaRERA records and buyer guide')
    expect(String(m.description)).toMatch(/^[^.]+\. Projects, MahaRERA records, getting around and what to check before you buy\.$/)
    expect(String(m.alternates?.canonical)).toMatch(/\/localities\/keshav-nagar$/)
  })
})
