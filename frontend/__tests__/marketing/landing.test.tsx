import React from 'react'
import { render, screen, within } from '@testing-library/react'
import LandingPage from '@/app/page'
import RequestInvitePage from '@/app/request-invite/page'

// PostsSection is an async server component (fetches /public/posts); it is covered in __tests__/posts.
jest.mock('@/components/site/PostsSection', () => ({ __esModule: true, default: () => null }))
jest.mock('@/components/news/NewsSection', () => ({ __esModule: true, default: () => null }))

describe('landing page', () => {
  it('has one h1 and sends the join buttons to the form on the page', () => {
    render(<LandingPage />)
    expect(screen.getAllByRole('heading', { level: 1 })).toHaveLength(1)
    expect(screen.getByRole('heading', { level: 1 }).textContent).toMatch(/get more enquiries\.\s*know who to call first\./i)
    const hero = screen.getByRole('heading', { level: 1 }).closest('section')!
    expect(within(hero).getByRole('link', { name: /join the free pilot/i })).toHaveAttribute('href', '#invite')
    expect(within(screen.getByTestId('sticky-join')).getByRole('link', { name: /join the free pilot/i, hidden: true })).toHaveAttribute('href', '#invite')
    expect(screen.getByTestId('header-cta')).toHaveAttribute('href', '/request-invite')
    expect(document.getElementById('invite')).not.toBeNull()
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

  it('never invents social proof and ships no placeholders', () => {
    const { container } = render(<LandingPage />)
    const text = container.textContent || ''
    for (const banned of [/testimonial/i, /rated/i, /\d+\s*\+?\s*(agents|customers|users|properties)/i, /trusted by/i, /five.star|5.star/i, /\[(confirm|pilot agent|agent name|founder|one line)/i]) {
      expect(text).not.toMatch(banned)
    }
    expect(text).toMatch(/free during the pilot/i)
  })

  it('keeps it short: no publishing box, no "what is next" lists', () => {
    render(<LandingPage />)
    expect(screen.queryByRole('heading', { name: /what you get, and what is next/i })).toBeNull()
    expect(document.body.textContent).not.toMatch(/we set it all up with you/i)
    expect(document.body.textContent).not.toMatch(/is coming/i)
  })

  it('shows the lead card: the source comment, labelled fields and a next step, as sample data', () => {
    render(<LandingPage />)
    expect(screen.getByText('INTERESTED')).toBeInTheDocument()
    expect(screen.getByText('Hot')).toBeInTheDocument()
    for (const label of ['Area', 'Budget', 'Timing', 'Loan']) expect(screen.getByText(label, { selector: 'dt' })).toBeInTheDocument()
    expect(screen.getByText(/next step:/i)).toBeInTheDocument()
    expect(screen.getByText('Sample data')).toBeInTheDocument()
  })

  it('shows a real agent page with full-colour slides before the steps', () => {
    const { container } = render(<LandingPage />)
    expect(screen.getByRole('heading', { name: /see what an avasetu agent gets/i })).toBeInTheDocument()
    expect(screen.getByText(/a sample page we built for house deal/i)).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /open the example page/i })).toHaveAttribute('href', '/agent/house-deal')
    const live = Array.from(container.querySelectorAll('img')).filter((i) => (i.getAttribute('src') || '').startsWith('/landing/live/'))
    expect(live).toHaveLength(3)
    live.forEach((i) => {
      expect(i.getAttribute('alt')!.length).toBeGreaterThan(30)
      expect(i.className).not.toMatch(/grayscale/)
    })
    const order = Array.from(container.querySelectorAll('section[id]')).map((s) => s.id)
    expect(order.indexOf('live')).toBeLessThan(order.indexOf('what-it-does'))
  })

  it('links buyers to every area page, grouped by tier, then projects and news', () => {
    render(<LandingPage />)
    const strip = screen.getByRole('heading', { name: /buying a home in pune/i }).closest('section')!
    expect(within(strip).getByRole('heading', { name: 'Affordable homes' })).toBeInTheDocument()
    expect(within(strip).getByRole('heading', { name: 'IT corridor' })).toBeInTheDocument()
    for (const [name, slug] of [['Wagholi', 'wagholi'], ['Lohegaon', 'lohegaon'], ['Keshav Nagar', 'keshav-nagar'], ['Hinjawadi', 'hinjawadi'], ['Baner', 'baner']]) {
      expect(within(strip).getByRole('link', { name })).toHaveAttribute('href', `/localities/${slug}`)
    }
    expect(within(strip).getAllByRole('link').filter((l) => l.getAttribute('href')?.startsWith('/localities/'))).toHaveLength(8)
    expect(within(strip).getByRole('link', { name: 'All projects' })).toHaveAttribute('href', '/projects')
    expect(within(strip).getByRole('link', { name: 'News' })).toHaveAttribute('href', '/news')
  })

  it('tells the create, get discovered, get qualified leads, close story in order', () => {
    const { container } = render(<LandingPage />)
    const steps = container.querySelector('#what-it-does')!
    const labels = Array.from(steps.querySelectorAll('ol > li p:first-child')).map((p) => (p.textContent || '').trim())
    expect(labels).toEqual(['Create', 'Get discovered', 'Get qualified leads', 'Close'])
  })

  it('answers the first worry, cost, leads and RERA in the FAQ, and the form is short', () => {
    const { container } = render(<LandingPage />)
    for (const q of [/what happens after i ask for an invite/i, /is it really free/i, /who sees my buyer leads/i, /what about rera/i, /which languages/i]) {
      expect(screen.getByText(q)).toBeInTheDocument()
    }
    const form = container.querySelector('#invite form')!
    expect(within(form as HTMLElement).getByRole('button', { name: /send request/i })).toBeInTheDocument()
    expect(form.querySelector('input[name="city"]')).toBeNull()
    expect(form.querySelector('input[name="consent"]')).not.toBeNull()
  })

  it('has a phone-only sticky join bar, hidden until the hero scrolls away', () => {
    render(<LandingPage />)
    const bar = screen.getByTestId('sticky-join')
    expect(bar).toHaveAttribute('aria-hidden', 'true')
    expect(bar.className).toMatch(/md:hidden/)
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
