import React from 'react'
import { render, screen, within } from '@testing-library/react'
import HomePage, { metadata } from '@/app/page'
import RequestInvitePage from '@/app/request-invite/page'
import HomeListings, { realListings } from '@/components/marketing/home/HomeListings'
import { FIXTURE_NEWS } from '@/lib/news/fixtures'
import { INSIGHTS } from '@/lib/marketing/insights'
import { LOCALITIES } from '@/lib/marketing/localities'
import type { PublicListing } from '@/lib/site/types'

// PostsSection is an async server component (fetches /public/posts); it is covered in __tests__/posts.
jest.mock('@/components/site/PostsSection', () => ({ __esModule: true, default: () => <section aria-labelledby="posts-stub"><h2 id="posts-stub">Latest from Avasetu</h2></section> }))
jest.mock('@/components/site/ChatWidget', () => ({ __esModule: true, default: () => null }))

const PHONE = /(?:\+?\d[\s\-().]*){10,}/

// Fixtures: news comes from lib/news/fixtures, and locality listings are always empty (never sample homes).
beforeAll(() => { process.env.SITE_USE_FIXTURES = '1' })
afterAll(() => { delete process.env.SITE_USE_FIXTURES })

const renderHome = async () => render(await HomePage())

describe('home page (buyers first)', () => {
  it('has one h1 for buyers in Kharadi, Upper Kharadi and Wagholi, with the brand and tagline', async () => {
    await renderHome()
    const h1s = screen.getAllByRole('heading', { level: 1 })
    expect(h1s).toHaveLength(1)
    expect(h1s[0].textContent).toMatch(/Kharadi, Upper Kharadi and Wagholi/)
    expect(screen.getAllByText('Avasetu').length).toBeGreaterThan(0)
    expect(screen.getAllByText('Your bridge to the right home').length).toBeGreaterThan(0)
  })

  it('puts the buyer requirement first and area guides second', async () => {
    await renderHome()
    const hero = screen.getByRole('heading', { level: 1 }).closest('section')!
    const links = within(hero).getAllByRole('link')
    expect(links[0]).toHaveTextContent('Tell us what you are looking for')
    expect(links[0]).toHaveAttribute('href', '/agent/avasetu#enquire')
    expect(links[1]).toHaveTextContent('Explore area guides')
    expect(links[1]).toHaveAttribute('href', '/localities')
  })

  it('shows sections in the buyer order, with h2 after h1 and no skipped levels', async () => {
    const { container } = await renderHome()
    const h2s = Array.from(container.querySelectorAll('h2')).map((h) => h.textContent || '')
    const order = [/latest local news/i, /area guides/i, /buyer guides/i, /latest from avasetu/i, /real estate agent in pune/i]
    let at = -1
    for (const re of order) {
      const i = h2s.findIndex((t, k) => k > at && re.test(t))
      expect(i).toBeGreaterThan(at)
      at = i
    }
    const levels = Array.from(container.querySelectorAll('h1, h2, h3, h4')).map((h) => Number(h.tagName[1]))
    levels.forEach((lvl, i) => { if (i > 0) expect(lvl - levels[i - 1]).toBeLessThanOrEqual(1) })
  })

  it('shows the three most recent news items with source and date, linking to /news', async () => {
    await renderHome()
    const news = screen.getByRole('heading', { name: /latest local news/i }).closest('section')!
    const cards = within(news).getAllByTestId('news-card')
    expect(cards).toHaveLength(3)
    FIXTURE_NEWS.slice(0, 3).forEach((n, i) => {
      expect(within(cards[i]).getByRole('link', { name: n.headline })).toHaveAttribute('href', `/news/${n.id}`)
    })
    expect(within(cards[1]).getByText(/Source: Hindustan Times/)).toBeInTheDocument()
    expect(within(cards[1]).getByText('28 Sep 2026')).toBeInTheDocument()
    expect(within(news).getByRole('link', { name: 'All news' })).toHaveAttribute('href', '/news')
  })

  it('says so honestly when news is not loading', async () => {
    delete process.env.SITE_USE_FIXTURES
    const fetchBefore = global.fetch
    global.fetch = jest.fn().mockRejectedValue(new Error('down')) as unknown as typeof fetch
    try {
      await renderHome()
      expect(screen.getByText('News is not loading right now')).toBeInTheDocument()
      expect(screen.queryByTestId('news-card')).toBeNull()
      expect(screen.getByTestId('homes-empty')).toBeInTheDocument()
    } finally {
      global.fetch = fetchBefore
      process.env.SITE_USE_FIXTURES = '1'
    }
  })

  it('links every area guide, the comparison guide and the buyer guides', async () => {
    await renderHome()
    const areas = screen.getByRole('heading', { name: /^area guides$/i }).closest('section')!
    expect(LOCALITIES.map((l) => l.slug)).toEqual(['kharadi', 'upper-kharadi', 'wagholi'])
    for (const l of LOCALITIES) {
      const card = within(areas).getByRole('heading', { level: 3, name: l.name }).closest('a')!
      expect(card).toHaveAttribute('href', `/localities/${l.slug}`)
    }
    const compare = INSIGHTS.find((i) => i.slug === 'kharadi-upper-kharadi-wagholi')!
    expect(within(areas).getByRole('link', { name: compare.title })).toHaveAttribute('href', `/insights/${compare.slug}`)
    const guides = screen.getByRole('heading', { name: /buyer guides/i }).closest('section')!
    for (const g of INSIGHTS.filter((i) => i !== compare)) {
      expect(within(guides).getByRole('link', { name: new RegExp(g.title.slice(0, 20)) })).toHaveAttribute('href', `/insights/${g.slug}`)
    }
    expect(within(guides).getByRole('link', { name: 'All guides' })).toHaveAttribute('href', '/insights')
  })

  it('shows no homes when there are no real listings, and says plainly where they will appear', async () => {
    await renderHome()
    expect(screen.queryByRole('heading', { name: /homes from local agents/i })).toBeNull()
    expect(screen.getByTestId('homes-empty')).toHaveTextContent(/appear here as they are listed/i)
    expect(document.body.textContent).not.toMatch(/sample listing|sample home/i)
  })

  it('keeps the agent story to one compact band linking to /for-agents and the demo page, with no invite form', async () => {
    await renderHome()
    const band = screen.getByRole('heading', { name: /are you a real estate agent in pune/i }).closest('section')!
    expect(within(band).getByRole('link', { name: /what we do for agents/i })).toHaveAttribute('href', '/for-agents')
    expect(within(band).getByRole('link', { name: /^see a demo agent page$/i })).toHaveAttribute('href', '/agent/demo')
    expect(screen.queryByRole('button', { name: /send request/i })).toBeNull()
    expect(document.querySelector('form')).toBeNull()
    expect(screen.queryByText(/INTERESTED/)).toBeNull()
  })

  it('never invents social proof, prices or phone numbers', async () => {
    const { container } = await renderHome()
    const text = container.textContent || ''
    for (const banned of [/testimonial/i, /\brated\b/i, /\d+\s*\+?\s*(agents|customers|users|buyers|properties)\b/i, /trusted by/i, /five.star|5.star/i, /\bbest\b/i, /guarantee/i]) {
      expect(text).not.toMatch(banned)
    }
    expect(container.querySelector('a[href^="tel:"]')).toBeNull()
    const main = Array.from(container.querySelectorAll('section')).map((s) => s.textContent || '').join(' ')
    expect(main).not.toMatch(PHONE)
  })

  it('renders on the v2 surface with Organization JSON-LD and no invented contact', async () => {
    const { container } = await renderHome()
    expect(container.querySelector('[data-surface="v2"]')).not.toBeNull()
    const ld = JSON.parse(container.querySelector('script[type="application/ld+json"]')!.textContent || '{}')
    expect(ld['@type']).toBe('Organization')
    expect(ld.name).toBeTruthy()
    expect(ld.description).toMatch(/buyers/i)
    expect(ld.contactPoint).toBeUndefined()
    expect(ld.telephone).toBeUndefined()
    expect(ld.address).toBeUndefined()
  })

  it('has buyer metadata and keeps the landing preview image', () => {
    expect(String(metadata.title)).toMatch(/^Avasetu: Kharadi, Upper Kharadi and Wagholi property news, area guides and homes/)
    expect(String(metadata.description)).toMatch(/area guides/i)
    expect(String(metadata.description)).not.toMatch(/agent.*pilot|invite/i)
    const og = metadata.openGraph as { images: Array<{ url: string; width: number; height: number }> }
    expect(og.images[0].url).toMatch(/\/brand\/og-landing\.jpg$/)
    expect(og.images[0]).toMatchObject({ width: 1200, height: 630 })
  })
})

const listing = (over: Partial<PublicListing>): PublicListing => ({
  id: 'x', status: 'active', transaction: 'sale', property_type: 'apartment', title: '2 BHK in Kharadi', description: {}, price_inr: 9000000,
  city: 'Pune', locality: 'Kharadi', amenities: [], media: [], agent: { slug: 'asha-homes', agent_name: 'Asha' }, ...over,
})

describe('home listings', () => {
  it('keeps only real homes with an agent page, once each', () => {
    const items = [
      listing({ id: 'a' }),
      listing({ id: 'a' }),
      listing({ id: 'b', title: 'Sample: 3 BHK in Wagholi' }),
      listing({ id: 'c', agent: undefined }),
    ]
    expect(realListings(items).map((l) => l.id)).toEqual(['a'])
  })

  it('renders real homes linking to their agent page, and nothing when there are none', () => {
    const { container, rerender } = render(<HomeListings items={[listing({ id: 'a' })]} />)
    expect(screen.getByRole('heading', { level: 2, name: /homes from local agents/i })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /2 BHK in Kharadi/ })).toHaveAttribute('href', expect.stringContaining('asha-homes'))
    expect(container.textContent).not.toMatch(/sample/i)
    rerender(<HomeListings items={[listing({ id: 'b', title: 'Sample home' })]} />)
    expect(container.innerHTML).toBe('')
  })
})

describe('request invite page', () => {
  it('renders the form standalone with no duplicate header call to action', () => {
    const { container } = render(<RequestInvitePage />)
    expect(container.querySelector('[data-surface="v2"]')).not.toBeNull()
    expect(screen.getByRole('heading', { level: 1, name: /request an invite/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /send request/i })).toBeInTheDocument()
    expect(container.querySelector('input[name="website"]')).not.toBeNull()
    expect(within(screen.getByRole('banner')).queryByRole('link', { name: /request an invite/i })).toBeNull()
  })
})
