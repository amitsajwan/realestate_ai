import React from 'react'
import { render, screen, within } from '@testing-library/react'
import NewsGrid from '@/components/news/NewsGrid'
import NewsArticle from '@/components/news/NewsArticle'
import InterestStrip from '@/components/news/InterestStrip'
import NewsPage from '@/app/news/page'
import NewsItemPage, { generateMetadata } from '@/app/news/[id]/page'
import sitemap from '@/app/sitemap'
import { buildMarketingConfig } from '@/lib/marketing/config'
import { cleanNewsItem, cleanNewsList, formatNewsDate, isGoogleRedirect } from '@/lib/news/data'
import { FIXTURE_NEWS } from '@/lib/news/fixtures'
import { newsJsonLd, newsMetadata } from '@/lib/news/seo'

// The shell pulls in the chat widget, a font loader and the footer: not what is under test here.
jest.mock('@/components/site/ChatWidget', () => ({ __esModule: true, default: () => null }))

const cfg = buildMarketingConfig({ NEXT_PUBLIC_SITE_URL: 'https://site.example' })
const ring = FIXTURE_NEWS[0] // source link is a long Google redirect
const direct = FIXTURE_NEWS[1] // a real article address
const digest = FIXTURE_NEWS.find((n) => n.kind === 'digest')!

beforeAll(() => { process.env.SITE_USE_FIXTURES = '1' })
afterAll(() => { delete process.env.SITE_USE_FIXTURES })

describe('news data', () => {
  it('keeps well-formed rows only and drops unsafe links', () => {
    const out = cleanNewsList([
      { id: '1', headline: ' Metro update ', areas: [{ slug: 'kharadi', name: 'Kharadi' }, { bad: 1 }], source_url: 'javascript:alert(1)', image_url: 'http://x/y.jpg',
        permalinks: [{ channel: 'facebook', url: 'https://www.facebook.com/p/1' }, { channel: 'facebook', url: 'javascript:x' }, { channel: 'tiktok', url: 'https://t.co' }] },
      { id: '', headline: 'No id' }, { id: '2', headline: '   ' }, null, 'x', 7,
    ])
    expect(out).toHaveLength(1)
    expect(out[0]).toMatchObject({ headline: 'Metro update', source_url: null, image_url: null, kind: 'story' })
    expect(out[0].areas).toEqual([{ slug: 'kharadi', name: 'Kharadi' }])
    expect(out[0].permalinks).toEqual([{ channel: 'facebook', url: 'https://www.facebook.com/p/1' }])
    expect(cleanNewsList({})).toEqual([])
    expect(cleanNewsItem(undefined)).toBeNull()
  })

  it('formats dates in India time and recognises Google redirects', () => {
    expect(formatNewsDate('2026-09-29T06:30:00+00:00')).toBe('29 Sep 2026')
    expect(formatNewsDate('2026-09-29T20:00:00+00:00')).toBe('30 Sep 2026') // already tomorrow in India
    expect(formatNewsDate('nonsense')).toBe('')
    expect(isGoogleRedirect(ring.source_url)).toBe(true)
    expect(isGoogleRedirect(direct.source_url)).toBe(false)
    expect(isGoogleRedirect(null)).toBe(false)
  })
})

describe('NewsGrid', () => {
  it('shows a lead story, the rest as rows, each linking to our own page, with source and as-of date', () => {
    render(<NewsGrid items={FIXTURE_NEWS.slice(0, 4)} />)
    const cards = screen.getAllByTestId('news-card')
    expect(cards).toHaveLength(4)
    expect(within(cards[0]).getByRole('link', { name: ring.headline })).toHaveAttribute('href', `/news/${ring.id}`)
    expect(within(cards[1]).getByText(/Source: Hindustan Times/)).toBeInTheDocument()
    expect(within(cards[1]).getByText('28 Sep 2026')).toBeInTheDocument()
    expect(screen.getAllByText(/News · Infrastructure/).length).toBeGreaterThan(0)
  })

  it('never shows a Google link or a bare URL in the list', () => {
    const { container } = render(<NewsGrid items={FIXTURE_NEWS} />)
    expect(container.innerHTML).not.toMatch(/news\.google\.com/)
    expect(container.textContent).not.toMatch(/https?:\/\//)
  })

  it('is honest when empty or when the service is down', () => {
    const { rerender } = render(<NewsGrid items={[]} />)
    expect(screen.getByText('No news yet')).toBeInTheDocument()
    rerender(<NewsGrid items={[]} failed />)
    expect(screen.getByText('News is not loading right now')).toBeInTheDocument()
    expect(screen.queryByTestId('news-card')).toBeNull()
  })
})

describe('NewsArticle', () => {
  it('names the source as a link and never prints the Google redirect', () => {
    const { container } = render(<NewsArticle item={ring} />)
    const a = screen.getByTestId('read-original')
    expect(a).toHaveTextContent('Read the original at Times of India')
    expect(a).toHaveAttribute('href', ring.source_url as string)
    expect(a).toHaveAttribute('target', '_blank')
    expect(a.getAttribute('rel')).toContain('noopener')
    expect(container.textContent).not.toMatch(/news\.google\.com|https?:\/\//)
  })

  it('shows headline, as-of date, summary badge, our labelled view, what to check and the disclaimer', () => {
    render(<NewsArticle item={ring} />)
    expect(screen.getByRole('heading', { level: 1, name: ring.headline })).toBeInTheDocument()
    expect(screen.getAllByText('29 Sep 2026').length).toBeGreaterThan(0)
    expect(screen.getByTestId('summary-badge')).toHaveTextContent('Summary of a news report by Times of India')
    expect(screen.getByTestId('news-our-view')).toHaveTextContent('This is our own reading, not a fact from the source.')
    expect(within(screen.getByTestId('what-to-check')).getByText(/Read the official notice/)).toBeInTheDocument()
    expect(screen.getByTestId('news-disclaimer')).toHaveTextContent('Approvals and project status change, so check the sources before you decide.')
    expect(screen.getByText(/By the PUNE Property team/)).toBeInTheDocument()
  })

  it('links to the Page post when there is one and works without an image', () => {
    render(<NewsArticle item={{ ...ring, image_url: null }} />)
    expect(screen.getByRole('link', { name: /Also on Facebook/ })).toHaveAttribute('href', 'https://www.facebook.com/PunePropertyHub/posts/1')
    expect(screen.queryByRole('img')).toBeNull()
  })

  it('renders a digest as a list of linked stories plus the buyer tip, without a source link', () => {
    render(<NewsArticle item={digest} />)
    expect(screen.getByRole('link', { name: /Pune Ring Road/ })).toHaveAttribute('href', '/news/a1b2c3d4e5')
    expect(screen.getByText('Buyer tip')).toBeInTheDocument()
    expect(screen.queryByTestId('read-original')).toBeNull()
    expect(screen.queryByTestId('summary-badge')).toBeNull()
  })
})

describe('InterestStrip', () => {
  it('offers an interested button per area to that area page, and the link-in-bio page', () => {
    render(<InterestStrip areas={[{ slug: 'kharadi', name: 'Kharadi' }, { slug: 'wagholi', name: 'Wagholi' }]} />)
    const strip = screen.getByTestId('interest-strip')
    expect(within(strip).getByText('Looking in Kharadi or Wagholi?')).toBeInTheDocument()
    expect(within(strip).getByRole('link', { name: 'I am interested in Kharadi' })).toHaveAttribute('href', '/localities/kharadi')
    expect(within(strip).getByRole('link', { name: 'I am interested in Wagholi' })).toHaveAttribute('href', '/localities/wagholi')
    expect(within(strip).getByRole('link', { name: /showing now/ })).toHaveAttribute('href', '/go')
  })

  it('falls back to Kharadi when the item names no area', () => {
    render(<InterestStrip areas={[]} />)
    expect(screen.getByRole('link', { name: 'I am interested in Kharadi' })).toBeInTheDocument()
  })
})

describe('SEO', () => {
  it('open graph is an article with our own card as the image', () => {
    const m = newsMetadata(cfg, ring) as any
    expect(m.openGraph.type).toBe('article')
    expect(m.openGraph.url).toBe(`https://site.example/news/${ring.id}`)
    expect(m.openGraph.images[0].url).toBe(ring.image_url)
    expect(m.twitter.card).toBe('summary_large_image')
    expect(m.alternates.canonical).toBe(`https://site.example/news/${ring.id}`)
  })

  it('falls back to the brand preview image when the item has no card', () => {
    const m = newsMetadata(cfg, { ...ring, image_url: null }) as any
    expect(m.openGraph.images[0].url).toMatch(/\/brand\/og\.jpg$/)
  })

  it('json-ld is a NewsArticle that says it is a summary based on a named source, without the Google redirect', () => {
    const ld = newsJsonLd(cfg, ring) as any
    expect(ld['@type']).toBe('NewsArticle')
    expect(ld.creativeWorkStatus).toBe('Summary')
    expect(ld.isBasedOn.publisher.name).toBe('Times of India')
    expect(ld.isBasedOn.url).toBeUndefined()
    expect(JSON.stringify(ld)).not.toMatch(/news\.google\.com/)
    expect(ld.author.name).toBe('PUNE Property team')
    expect(ld.dateModified).toBe(ring.as_of)
    expect((newsJsonLd(cfg, direct) as any).isBasedOn.url).toBe(direct.source_url)
    expect((newsJsonLd(cfg, digest) as any).isBasedOn).toBeUndefined()
  })
})

describe('pages', () => {
  it('the list page shows the news and how we write it', async () => {
    render(await NewsPage())
    expect(screen.getByRole('heading', { level: 1, name: 'Local property news' })).toBeInTheDocument()
    expect(screen.getAllByTestId('news-card').length).toBeGreaterThan(3)
    expect(screen.getByText('How we write news')).toBeInTheDocument()
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
  })

  it('the item page renders the article and the json-ld script; an unknown id is a 404', async () => {
    const { container } = render(await NewsItemPage({ params: Promise.resolve({ id: ring.id }) }))
    expect(screen.getByTestId('news-article')).toBeInTheDocument()
    const ld = container.querySelector('script[type="application/ld+json"]')
    expect(JSON.parse(ld!.innerHTML)['@type']).toBe('NewsArticle')
    await expect(NewsItemPage({ params: Promise.resolve({ id: 'nope' }) })).rejects.toThrow() // next/navigation notFound()
    expect(await generateMetadata({ params: Promise.resolve({ id: 'nope' }) })).toEqual({})
  })

  it('has News in the footer and the sitemap', async () => {
    render(await NewsPage())
    expect(within(screen.getByRole('contentinfo')).getByRole('link', { name: 'News' })).toHaveAttribute('href', '/news')
    expect(sitemap().some((s) => s.url.endsWith('/news'))).toBe(true)
  })
})
