import React from 'react'
import { render, screen, within } from '@testing-library/react'
import LandingPage from '@/app/page'
import RequestInvitePage from '@/app/request-invite/page'
import { SHOTS } from '@/lib/marketing/strings'

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
    expect(screen.getAllByRole('link', { name: /sign in/i })[0]).toHaveAttribute('href', '/join')
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

  it('says what is coming and that screens are sample data', () => {
    render(<LandingPage />)
    expect(screen.getByRole('heading', { name: /what is coming/i })).toBeInTheDocument()
    expect(screen.getByText(/needs approval from those platforms/i)).toBeInTheDocument()
    expect(screen.getByText(/screens show sample data/i)).toBeInTheDocument()
  })

  it('uses the six real screenshots with alt text, dimensions and lazy loading below the fold', () => {
    const { container } = render(<LandingPage />)
    const imgs = Array.from(container.querySelectorAll('img'))
    expect(imgs.map((i) => i.getAttribute('src')).sort()).toEqual(Object.values(SHOTS).map((s) => s.src).sort())
    imgs.forEach((i) => {
      expect(i.getAttribute('alt')!.length).toBeGreaterThan(20)
      expect(i).toHaveAttribute('width', '780')
      expect(i).toHaveAttribute('height', '1688')
    })
    const hero = imgs.find((i) => i.getAttribute('src') === SHOTS.home.src)!
    expect(hero).toHaveAttribute('loading', 'eager')
    imgs.filter((i) => i !== hero).forEach((i) => expect(i).toHaveAttribute('loading', 'lazy'))
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
