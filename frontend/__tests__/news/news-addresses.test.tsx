import React from 'react'
import { render, screen, within } from '@testing-library/react'
import NewsArticle from '@/components/news/NewsArticle'
import NewsGrid from '@/components/news/NewsGrid'
import NewsSection from '@/components/news/NewsSection'
import NewsItemPage, { generateMetadata } from '@/app/news/[id]/page'
import { buildMarketingConfig } from '@/lib/marketing/config'
import { cleanNewsItem, fetchNews, fetchNewsItem, newsPath, NEWS_TEXT } from '@/lib/news/data'
import { FIXTURE_NEWS } from '@/lib/news/fixtures'
import { newsJsonLd } from '@/lib/news/seo'

// Readable, permanent news addresses: every link uses the API's slug id; an old address (the stored hash id that captions
// already posted on Facebook and Instagram link to) answers with a permanent redirect to the slug.
jest.mock('@/components/site/ChatWidget', () => ({ __esModule: true, default: () => null }))
const mockRedirect = jest.fn((url: string) => { throw new Error('PERMANENT REDIRECT ' + url) })
jest.mock('next/navigation', () => ({
  notFound: () => { throw new Error('NOT FOUND') },
  permanentRedirect: (u: string) => mockRedirect(u),
  usePathname: () => '/',
  useRouter: () => ({ push: jest.fn() }),
}))

const cfg = buildMarketingConfig({ NEXT_PUBLIC_SITE_URL: 'https://site.example' })
const ring = FIXTURE_NEWS[0]
const digest = FIXTURE_NEWS.find((n) => n.kind === 'digest')!
const SLUG = /^[a-z0-9]+(-[a-z0-9]+)*$/

describe('with fixtures', () => {
  beforeAll(() => { process.env.SITE_USE_FIXTURES = '1' })
  afterAll(() => { delete process.env.SITE_USE_FIXTURES })

  it('fixture stories carry readable slugs ending in 6 characters of the old id, digests their own id', () => {
    for (const n of FIXTURE_NEWS) expect(n.id).toMatch(n.kind === 'digest' ? /^digest-\d{4}-w\d{2}$/ : SLUG)
    expect(ring.id).toBe('pune-ring-road-10502-crore-approved-a1b2c3')
  })

  it('an old address (a link in a post already published) permanently redirects to the readable one', async () => {
    for (const old of ['a1b2c3d4e5', 'pune-ring-road-approved-a1b2c3']) { // the stored id, an older slug
      await expect(NewsItemPage({ params: Promise.resolve({ id: old }) })).rejects.toThrow(`PERMANENT REDIRECT /news/${ring.id}`)
    }
    // the readable address and a digest's own id render without a redirect
    render(await NewsItemPage({ params: Promise.resolve({ id: ring.id }) }))
    expect(screen.getByTestId('news-article')).toBeInTheDocument()
    render(await NewsItemPage({ params: Promise.resolve({ id: digest.id }) }))
    expect(screen.getAllByTestId('news-article')).toHaveLength(2)
    expect(mockRedirect).toHaveBeenCalledTimes(2) // only the two old addresses
    await expect(NewsItemPage({ params: Promise.resolve({ id: 'no-such-story-000000' }) })).rejects.toThrow('NOT FOUND')
  })

  it('the canonical URL is the readable address, also when an old one was opened', async () => {
    const m = (await generateMetadata({ params: Promise.resolve({ id: 'a1b2c3d4e5' }) })) as any
    expect(m.alternates.canonical).toMatch(new RegExp(`^https?://[^/]+/news/${ring.id}$`))
  })

  it('fetchNews(limit, area) keeps that area\'s stories', async () => {
    const wagholi = await fetchNews(10, 'wagholi')
    expect(wagholi.ok && wagholi.items.length).toBeGreaterThan(0)
    expect(wagholi.items.every((n) => n.kind === 'story' && n.areas.some((a) => a.slug === 'wagholi'))).toBe(true)
    expect((await fetchNews(10, 'baner')).items).toEqual([])
    expect((await fetchNews(2)).items).toHaveLength(2)
  })

  it('the home section is about Pune, not two areas, and links to the readable addresses', async () => {
    render(await NewsSection())
    expect(screen.getByRole('heading', { level: 2, name: 'Pune property news' })).toBeInTheDocument()
    expect(NEWS_TEXT.homeLead.split(' ').length).toBeLessThanOrEqual(10)
    expect(screen.getByRole('link', { name: ring.headline })).toHaveAttribute('href', `/news/${ring.id}`)
    expect(document.body.textContent).not.toMatch(/Kharadi and Wagholi news/)
    expect(NEWS_TEXT.pageTitle + NEWS_TEXT.pageDescription + NEWS_TEXT.lead).not.toMatch(/Kharadi|Wagholi/)
  })
})

describe('links', () => {
  it('the list links every story to its readable address', () => {
    render(<NewsGrid items={FIXTURE_NEWS} />)
    const hrefs = screen.getAllByRole('link').map((a) => a.getAttribute('href')!).filter((h) => h.startsWith('/news/'))
    expect(hrefs.length).toBeGreaterThan(0)
    for (const h of hrefs) expect(h.slice('/news/'.length)).toMatch(/^[a-z0-9]+(-[a-z0-9]+)*$/)
  })

  it('a story links to each of its areas\' pages', () => {
    render(<NewsArticle item={{ ...ring, areas: [{ key: 'lohegaon', slug: 'lohegaon', name: 'Lohegaon' }, { key: 'upper_kharadi', slug: 'upper-kharadi', name: 'Upper Kharadi' }] }} />)
    const nav = screen.getByTestId('news-areas')
    expect(within(nav).getByRole('link', { name: 'More about Lohegaon' })).toHaveAttribute('href', '/localities/lohegaon')
    expect(within(nav).getByRole('link', { name: 'More about Upper Kharadi' })).toHaveAttribute('href', '/localities/upper-kharadi')
  })

  it('a digest links its stories by slug, and shows a roundup project (no page of its own) without a link', () => {
    const roundup = { ...digest, id: 'maharera-20261003-103729', items: [
      { id: 'P52100012345', headline: 'Sky Homes', source_name: 'MahaRERA', line: '', linked: false },
      { id: ring.id, headline: ring.headline, source_name: 'Times of India', line: '', linked: true },
    ] }
    render(<NewsArticle item={roundup} />)
    expect(screen.queryByRole('link', { name: 'Sky Homes' })).toBeNull()
    expect(screen.getByText('Sky Homes')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: ring.headline })).toHaveAttribute('href', `/news/${ring.id}`)
  })

  it('NewsArticle json-ld names the readable address', () => {
    const ld = newsJsonLd(cfg, ring) as any
    expect(ld.mainEntityOfPage).toBe(`https://site.example/news/${ring.id}`)
    expect(ld.url).toBe(ld.mainEntityOfPage)
    expect(newsPath('digest-2026-w40')).toBe('/news/digest-2026-w40')
  })

  it('cleanNewsItem keeps area keys and the linked flag (missing means linked, as before)', () => {
    const n = cleanNewsItem({ id: 's-abcdef', headline: 'H', areas: [{ key: 'lohegaon', slug: 'lohegaon', name: 'Lohegaon' }],
      items: [{ id: 'a', headline: 'A' }, { id: 'b', headline: 'B', linked: false }, { id: '', headline: 'none' }] })!
    expect(n.areas).toEqual([{ key: 'lohegaon', slug: 'lohegaon', name: 'Lohegaon' }])
    expect(n.items.map((i) => [i.id, i.linked])).toEqual([['a', true], ['b', false]])
  })
})

describe('against the API', () => {
  const realFetch = global.fetch
  afterEach(() => { global.fetch = realFetch })

  it('fetchNews sends the area key, and fetchNewsItem returns the API\'s id for an old address', async () => {
    const calls: string[] = []
    global.fetch = jest.fn(async (url: string) => {
      calls.push(url)
      const body = url.includes('/public/news/f5ddee') ? { id: 'lohegaon-hospital-opd-awaiting-approval-f5ddee', headline: 'Lohegaon hospital OPD awaiting approval' } : []
      return { ok: true, status: 200, json: async () => body } as Response
    }) as any
    await fetchNews(5, 'upper_kharadi')
    expect(calls[0]).toMatch(/\/api\/v1\/public\/news\?limit=5&area=upper_kharadi$/)
    await fetchNews(5)
    expect(calls[1]).toMatch(/\/api\/v1\/public\/news\?limit=5$/)
    const r = await fetchNewsItem('f5ddeef0763d0726992a04d8a388e7823addd6c2')
    expect(r.ok && r.item.id).toBe('lohegaon-hospital-opd-awaiting-approval-f5ddee')
  })
})
