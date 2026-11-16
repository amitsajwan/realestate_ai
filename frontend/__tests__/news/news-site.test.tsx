import React from 'react'
import { render, screen, within } from '@testing-library/react'
import NewsGrid from '@/components/news/NewsGrid'
import NewsArticle from '@/components/news/NewsArticle'
import InterestStrip from '@/components/news/InterestStrip'
import NewsPage from '@/app/news/page'
import NewsItemPage, { generateMetadata } from '@/app/news/[id]/page'
import sitemap from '@/lib/site/sitemap'
import { buildMarketingConfig } from '@/lib/marketing/config'
import { cleanNewsItem, cleanNewsList, formatNewsDate, isGoogleRedirect } from '@/lib/news/data'
import { FIXTURE_NEWS } from '@/lib/news/fixtures'
import { newsJsonLd, newsMetadata } from '@/lib/news/seo'
import { newsSitemapXml, recentNews } from '@/lib/news/sitemap'

// The shell pulls in the chat widget, a font loader and the footer: not what is under test here.
jest.mock('@/components/site/ChatWidget', () => ({ __esModule: true, default: () => null }))

const cfg = buildMarketingConfig({ NEXT_PUBLIC_SITE_URL: 'https://site.example' })
const ring = FIXTURE_NEWS[0] // source link is a long Google redirect
const direct = FIXTURE_NEWS[1] // a real article address
const digest = FIXTURE_NEWS.find((n) => n.kind === 'digest')!
const researched = FIXTURE_NEWS.find((n) => n.body.length > 0)! // a full article written from several reports

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

  it('keeps the wide card only as an https address', () => {
    expect(cleanNewsItem({ id: '1', headline: 'H', image_wide_url: 'https://m/x-web.jpg' })!.image_wide_url).toBe('https://m/x-web.jpg')
    expect(cleanNewsItem({ id: '1', headline: 'H', image_wide_url: 'http://m/x-web.jpg' })!.image_wide_url).toBeNull()
    expect(cleanNewsItem({ id: '1', headline: 'H' })!.image_wide_url).toBeNull()
  })

  it('carries the buyer line from the API, null when missing, blank or not text', () => {
    const line = 'Worth checking: ask your bank how this applies to your loan before you decide.'
    expect(cleanNewsItem({ id: '1', headline: 'H', buyer_line: line })!.buyer_line).toBe(line)
    for (const v of [undefined, null, '', '  ', 7]) expect(cleanNewsItem({ id: '1', headline: 'H', buyer_line: v })!.buyer_line).toBeNull()
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

  it('shows the "Worth checking" line under the summary when the item has one, and nothing when it does not', () => {
    const noLine = { ...direct, id: 'x9', buyer_line: null }
    render(<NewsGrid items={[ring, noLine, digest]} />)
    const cards = screen.getAllByTestId('news-card')
    expect(within(cards[0]).getByTestId('buyer-line')).toHaveTextContent(ring.buyer_line as string)
    expect(ring.buyer_line).toMatch(/^Worth checking: /)
    expect(within(cards[1]).queryByTestId('buyer-line')).toBeNull()
    expect(within(cards[2]).queryByTestId('buyer-line')).toBeNull()  // digest
    // under the summary, not above it
    const summary = within(cards[0]).getByText(ring.summary)
    expect(summary.compareDocumentPosition(within(cards[0]).getByTestId('buyer-line')) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
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
    expect(screen.getByText(/By the Avasetu team/)).toBeInTheDocument()
  })

  it('shows the "Worth checking" line as a callout right under the summary, and none when the item has no line', () => {
    const { unmount } = render(<NewsArticle item={ring} />)
    const line = screen.getByTestId('buyer-line')
    expect(line).toHaveTextContent('Worth checking: how far your shortlisted project is from this road or line.')
    expect(screen.getByTestId('news-summary').compareDocumentPosition(line) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(line.compareDocumentPosition(screen.getByTestId('what-to-check')) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    unmount()
    render(<NewsArticle item={{ ...ring, buyer_line: null }} />)
    expect(screen.queryByTestId('buyer-line')).toBeNull()
  })

  it('shows the wide card as the picture, and the square one for a story drawn before it existed', () => {
    const { unmount } = render(<NewsArticle item={ring} />)
    const wide = screen.getByRole('img', { name: ring.headline })
    expect(wide).toHaveAttribute('src', ring.image_wide_url as string)
    expect(wide).toHaveAttribute('width', '1200')
    expect(wide.className).toContain('aspect-video')
    unmount()
    render(<NewsArticle item={direct} />)
    const square = screen.getByRole('img', { name: direct.headline })
    expect(square).toHaveAttribute('src', direct.image_url as string)
    expect(square.className).toContain('aspect-square')
  })

  it('links to the Page post when there is one and works without an image', () => {
    render(<NewsArticle item={{ ...ring, image_url: null, image_wide_url: null }} />)
    expect(screen.getByRole('link', { name: /Also on Facebook/ })).toHaveAttribute('href', 'https://www.facebook.com/PunePropertyHub/posts/1')
    expect(screen.queryByRole('img')).toBeNull()
  })

  it('renders a researched article: standfirst, paragraphs, every source it was written from, no bare links', () => {
    const { container } = render(<NewsArticle item={researched} />)
    expect(screen.getByTestId('news-summary')).toHaveTextContent(researched.summary)
    const body = screen.getByTestId('news-body')
    expect(within(body).getAllByText(/./)).toHaveLength(researched.body.length)
    expect(screen.getByTestId('news-summary').compareDocumentPosition(body) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(screen.getByTestId('summary-badge')).toHaveTextContent('Written from 3 news reports')
    expect(screen.getByRole('heading', { name: 'Sources' })).toBeInTheDocument()
    const sources = within(screen.getByTestId('news-sources')).getAllByRole('listitem')
    expect(sources).toHaveLength(3)
    expect(within(sources[0]).getByRole('link', { name: /Read the original at Punekar News/ })).toHaveAttribute('href', researched.sources[0].url as string)
    expect(within(sources[1]).getByRole('link', { name: /Read the original at Hindustan Times/ })).toBeInTheDocument()
    expect(within(sources[2]).queryByRole('link')).toBeNull() // also reported it, but we could not read it: named, not linked
    expect(container.textContent).not.toMatch(/https?:\/\//)
  })

  it('shows background from our area guide labelled as ours, and nothing when there is none', () => {
    const { unmount } = render(<NewsArticle item={researched} />)
    expect(screen.queryByTestId('news-background')).toBeNull()
    unmount()
    render(<NewsArticle item={{ ...researched, background: 'Corridor 2B has been approved, but approved is not the same as running.' }} />)
    expect(screen.getByTestId('news-background')).toHaveTextContent('From our own area guide, not from the reports.')
  })

  it('reads body, background and sources from the API and drops unsafe source links', () => {
    const item = cleanNewsItem({ id: '1', headline: 'H', body: ['One.', ' ', 7, 'Two.'], background: 'B',
      sources: [{ name: 'A', url: 'https://a.example/x', is_redirect: false }, { name: 'B', url: 'javascript:x' }, { url: 'https://c.example' }] })!
    expect(item.body).toEqual(['One.', 'Two.'])
    expect(item.background).toBe('B')
    expect(item.sources).toEqual([{ name: 'A', url: 'https://a.example/x', is_redirect: false }, { name: 'B', url: null, is_redirect: false }])
    expect(cleanNewsItem({ id: '1', headline: 'H' })).toMatchObject({ body: [], background: '', sources: [] })
  })

  it('renders a digest as a list of linked stories plus the buyer tip, without a source link', () => {
    render(<NewsArticle item={digest} />)
    expect(screen.getByRole('link', { name: /Pune Ring Road/ })).toHaveAttribute('href', '/news/pune-ring-road-10502-crore-approved-a1b2c3')
    expect(screen.getByText('Buyer tip')).toBeInTheDocument()
    expect(screen.queryByTestId('read-original')).toBeNull()
    expect(screen.queryByTestId('summary-badge')).toBeNull()
    expect(screen.queryByTestId('buyer-line')).toBeNull()
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
  it('open graph is an article with our own cards as the images, the wide one first', () => {
    const m = newsMetadata(cfg, ring) as any
    expect(m.openGraph.type).toBe('article')
    expect(m.openGraph.url).toBe(`https://site.example/news/${ring.id}`)
    // Google Discover wants a picture 1200 px or wider: the 16:9 card leads, the square social card follows
    expect(m.openGraph.images).toEqual([
      { url: ring.image_wide_url, width: 1200, height: 675, alt: ring.headline },
      { url: ring.image_url, width: 1080, height: 1080, alt: ring.headline },
    ])
    expect(m.twitter.card).toBe('summary_large_image')
    expect(m.twitter.images).toEqual([ring.image_wide_url])
    expect(m.openGraph.publishedTime).toBe(ring.published_at)
    expect(m.alternates.canonical).toBe(`https://site.example/news/${ring.id}`)
  })

  it('a story drawn before the wide card existed still previews with its square card', () => {
    const m = newsMetadata(cfg, direct) as any
    expect(direct.image_wide_url).toBeNull()
    expect(m.openGraph.images).toEqual([{ url: direct.image_url, width: 1080, height: 1080, alt: direct.headline }])
    expect((newsJsonLd(cfg, direct) as any).image).toEqual([direct.image_url])
    expect((newsJsonLd(cfg, ring) as any).image).toEqual([ring.image_wide_url, ring.image_url])
  })

  it('falls back to the brand preview image when the item has no card', () => {
    const m = newsMetadata(cfg, { ...ring, image_url: null, image_wide_url: null }) as any
    expect(m.openGraph.images[0].url).toMatch(/\/brand\/og\.jpg$/)
  })

  it('json-ld is a NewsArticle that says it is a summary based on a named source, without the Google redirect', () => {
    const ld = newsJsonLd(cfg, ring) as any
    expect(ld['@type']).toBe('NewsArticle')
    expect(ld.creativeWorkStatus).toBe('Summary')
    expect(ld.isBasedOn.publisher.name).toBe('Times of India')
    expect(ld.isBasedOn.url).toBeUndefined()
    expect(JSON.stringify(ld)).not.toMatch(/news\.google\.com/)
    expect(ld.author.name).toBe('Avasetu team')
    expect(ld.dateModified).toBe(ring.as_of)
    expect((newsJsonLd(cfg, direct) as any).isBasedOn.url).toBe(direct.source_url)
    expect((newsJsonLd(cfg, digest) as any).isBasedOn).toBeUndefined()
  })
})

describe('news sitemap (Google News)', () => {
  const now = new Date('2026-09-30T12:00:00Z').getTime()

  it('lists the last two days of stories with publication, language, date and headline, newest first', () => {
    const xml = newsSitemapXml('https://site.example', FIXTURE_NEWS, now)
    expect(xml).toContain('xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"')
    const ids = recentNews(FIXTURE_NEWS, now).map((r) => r.item.id)
    expect(ids.length).toBeGreaterThan(0)
    expect(ids).toContain(ring.id)   // 29 Sep
    expect(ids).not.toContain(FIXTURE_NEWS[2].id)   // 27 Sep: older than two days
    expect(ids).toEqual([...ids].sort((a, b) => (FIXTURE_NEWS.find((n) => n.id === b)!.published_at! > FIXTURE_NEWS.find((n) => n.id === a)!.published_at! ? 1 : -1)))
    expect(xml).toContain(`<loc>https://site.example/news/${ring.id}</loc>`)
    expect(xml).toContain('<news:name>Avasetu</news:name><news:language>en</news:language>')
    expect(xml).toContain(`<news:publication_date>${new Date(ring.published_at!).toISOString()}</news:publication_date>`)
    expect(xml).toContain(`<news:title>${ring.headline.replace(/&/g, '&amp;')}</news:title>`)
    expect(xml).not.toMatch(/news\.google\.com/)
  })

  it('is a valid, empty sitemap when nothing was published in two days', () => {
    const xml = newsSitemapXml('https://site.example', FIXTURE_NEWS, new Date('2027-01-01T00:00:00Z').getTime())
    expect(xml).toMatch(/<urlset [^>]+>\n<\/urlset>\n$/)
  })
})

describe('pages', () => {
  it('the list page shows the news and how we write it', async () => {
    render(await NewsPage())
    expect(screen.getByRole('heading', { level: 1, name: 'Pune property news' })).toBeInTheDocument()
    expect(screen.getAllByTestId('news-card').length).toBeGreaterThan(3)
    expect(screen.getByText('How we write news')).toBeInTheDocument()
    expect(screen.getByRole('contentinfo')).toBeInTheDocument()
    // a buyer page: the header asks what the visitor needs, not for an agent invite
    expect(within(screen.getByRole('banner')).getByTestId('header-cta')).toHaveAccessibleName('Enquire: tell us what you need')
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
    expect((await sitemap()).some((s) => s.url.endsWith('/news'))).toBe(true)
  })
})
