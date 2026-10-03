import React from 'react'
import { render, screen, within } from '@testing-library/react'
import LandingPage from '@/app/page'
import RequestInvitePage from '@/app/request-invite/page'
import { SHOTS } from '@/lib/marketing/strings'

// PostsSection is an async server component (fetches /public/posts); it is covered in __tests__/posts.
jest.mock('@/components/site/PostsSection', () => ({ __esModule: true, default: () => null }))

describe('landing page', () => {
  it('has one h1 and a primary call to action to /request-invite', () => {
    render(<LandingPage />)
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    const ctas = screen.getAllByRole('link', { name: /request an invite/i })
    expect(ctas.length).toBeGreaterThanOrEqual(2)
    ctas.forEach((a) => expect(a).toHaveAttribute('href', '/request-invite'))
  })

  it('links to sign in and the legal pages', () => {
    render(<LandingPage />)
    expect(screen.getAllByRole('link', { name: /sign in/i })[0]).toHaveAttribute('href', '/studio') // header: studio sends a signed-out agent to /join
    expect(screen.getByRole('link', { name: /already invited\? sign in/i })).toHaveAttribute('href', '/join')
    const footer = screen.getByRole('contentinfo')
    expect(within(footer).getByRole('link', { name: 'Privacy' })).toHaveAttribute('href', '/privacy')
    expect(within(footer).getByRole('link', { name: 'Terms' })).toHaveAttribute('href', '/terms')
    expect(within(footer).getByRole('link', { name: 'Data deletion' })).toHaveAttribute('href', '/data-deletion')
  })

  it('never invents social proof', () => {
    const { container } = render(<LandingPage />)
    const text = container.textContent || ''
    for (const banned of [/testimonial/i, /\brated\b/i, /\d+\s*\+?\s*(agents|customers|users|properties)\b/i, /trusted by/i, /five.star|5.star/i]) {
      expect(text).not.toMatch(banned)
    }
    expect(container.textContent).toMatch(/free during the pilot/i)
    expect(container.textContent).toMatch(/invite-only/i)
  })

  it('says what is coming, and makes clear early that posts go out through Avasetu, not the agent\'s own accounts', () => {
    render(<LandingPage />)
    expect(screen.getByRole('heading', { name: /what is coming/i })).toBeInTheDocument()
    expect(screen.getByText(/needs approval from meta/i)).toBeInTheDocument()
    const hero = screen.getByRole('heading', { level: 1 }).closest('section')!
    expect(within(hero).getByText(/publish it through avasetu/i)).toBeInTheDocument()
    expect(within(hero).getByText(/posting to your own page and instagram is coming/i)).toBeInTheDocument()
  })

  it('keeps the page short: no screenshot strip, no posts feed (they live on /posts)', () => {
    const { container } = render(<LandingPage />)
    expect(container.querySelector('#screens-title')).toBeNull()
    expect(screen.queryByTestId('post-card')).toBeNull()
  })

  it('leads with the agent problem and an HTML phone mock of the lead card, labelled as sample', () => {
    render(<LandingPage />)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toMatch(/more property enquiries/i)
    expect(screen.getAllByText('INTERESTED').length).toBeGreaterThan(0)
    expect(screen.getByText('HOT')).toBeInTheDocument()
    expect(screen.getByText('Sample data')).toBeInTheDocument()
  })

  it('shows a real agent live today, with their pages and real slides, and says it is with their permission', () => {
    const { container } = render(<LandingPage />)
    expect(screen.getByRole('heading', { name: /see what an avasetu agent actually gets/i })).toBeInTheDocument()
    expect(screen.getByText(/live today: house deal, upper kharadi/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /open house deal's page/i })).toHaveAttribute('href', '/agent/house-deal')
    expect(screen.getByRole('link', { name: /compare the 5 projects/i })).toHaveAttribute('href', '/agent/house-deal/projects/compare')
    expect(screen.getByText(/with house deal's permission/i)).toBeInTheDocument()
    const live = Array.from(container.querySelectorAll('img')).filter((i) => (i.getAttribute('src') || '').startsWith('/landing/live/'))
    expect(live).toHaveLength(3)
    live.forEach((i) => expect(i.getAttribute('alt')!.length).toBeGreaterThan(30))
  })

  it('gives buyers two doors: area guides and news', () => {
    render(<LandingPage />)
    const strip = screen.getByRole('heading', { name: /buying a home in kharadi or wagholi/i }).closest('section')!
    expect(within(strip).getByRole('link', { name: 'Area guides' })).toHaveAttribute('href', '/localities')
    expect(within(strip).getByRole('link', { name: 'News' })).toHaveAttribute('href', '/news')
  })

  it('tells the create, get discovered, get qualified leads, close story in order', () => {
    const { container } = render(<LandingPage />)
    const steps = container.querySelector('#what-it-does')!
    const labels = Array.from(steps.querySelectorAll('ol > li > p:first-child')).map((p) => (p.textContent || '').replace(/^\d/, '').trim())
    expect(labels).toEqual(['Create', 'Get discovered', 'Get qualified leads', 'Close'])
  })

  it('answers cost, lead visibility, RERA and data in the FAQ, and puts the short form on the page', () => {
    render(<LandingPage />)
    for (const q of [/what does it cost/i, /who sees my buyer leads/i, /what about rera/i, /what happens to my buyers/i]) {
      expect(screen.getByText(q)).toBeInTheDocument()
    }
    expect(screen.getByRole('button', { name: /send request/i })).toBeInTheDocument()
  })

  it('renders standalone on the v2 surface and embeds Organization JSON-LD without contact invented', () => {
    const { container } = render(<LandingPage />)
    expect(container.querySelector('[data-surface="v2"]')).not.toBeNull()
    const ld = JSON.parse(container.querySelector('script[type="application/ld+json"]')!.textContent || '{}')
    expect(ld['@type']).toBe('Organization')
    expect(ld.name).toBeTruthy()
    expect(ld.contactPoint).toBeUndefined()
    expect(ld.telephone).toBeUndefined()
    expect(ld.address).toBeUndefined()
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
