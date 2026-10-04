import React from 'react'
import { render, screen, within } from '@testing-library/react'
import SiteHeader from '@/components/marketing/SiteHeader'
import SiteFooter from '@/components/marketing/SiteFooter'
import LandingPage from '@/app/page'
import { buildMarketingConfig } from '@/lib/marketing/config'
import { socialLinks } from '@/lib/marketing/social'

jest.mock('@/components/site/PostsSection', () => ({ __esModule: true, default: () => null }))
jest.mock('@/components/news/NewsSection', () => ({ __esModule: true, default: () => null }))

const cfg = buildMarketingConfig({})
const EXPECTED: Array<[RegExp, string]> = [
  [/^for agents$/i, '/for-agents'],
  [/^see a demo page$/i, '/agent/demo'],
  [/^news$/i, '/news'],
  [/^posts$/i, '/posts'],
  [/^area guides$/i, '/localities'],
  [/^insights$/i, '/insights'],
  [/^sign in$/i, '/studio'],
]

function hrefOf(scope: HTMLElement, name: RegExp): string | null {
  return within(scope).getAllByRole('link', { name })[0].getAttribute('href')
}

describe('site header', () => {
  it('links to every main page and the social profiles', () => {
    render(<SiteHeader businessName="Avasetu" />)
    const header = screen.getByRole('banner')
    for (const [name, href] of EXPECTED) expect(hrefOf(header, name)).toBe(href)
    expect(hrefOf(header, /^instagram/i)).toBe(socialLinks().instagram)
    expect(hrefOf(header, /^facebook/i)).toBe(socialLinks().facebook)
    expect(header).toHaveAttribute('data-print', 'hide')
  })

  it('buyer pages (the default) get the buyer button, to the existing enquiry form, and no invite button', () => {
    render(<SiteHeader businessName="Avasetu" />)
    const header = screen.getByRole('banner')
    const cta = within(header).getByTestId('header-cta')
    expect(cta).toHaveAccessibleName('Enquire: tell us what you need')
    expect(cta).toHaveAttribute('href', '/agent/avasetu#enquire')
    expect(within(header).queryByRole('link', { name: /request an invite/i })).toBeNull()
    expect(hrefOf(header, /^for agents$/i)).toBe('/for-agents')  // still a normal link
  })

  it('agent pages get "Request an invite"; the invite page itself gets no button', () => {
    const { unmount } = render(<SiteHeader businessName="Avasetu" cta="agent" />)
    const cta = within(screen.getByRole('banner')).getByTestId('header-cta')
    expect(cta).toHaveTextContent('Request an invite')
    expect(cta).toHaveAttribute('href', '/request-invite')
    expect(within(screen.getByRole('banner')).queryByRole('link', { name: /tell us what you need/i })).toBeNull()
    unmount()
    render(<SiteHeader businessName="Avasetu" cta="none" />)
    expect(within(screen.getByRole('banner')).queryByTestId('header-cta')).toBeNull()
  })

  it('takes the demo slug from NEXT_PUBLIC_DEMO_AGENT_SLUG', () => {
    const before = process.env.NEXT_PUBLIC_DEMO_AGENT_SLUG
    process.env.NEXT_PUBLIC_DEMO_AGENT_SLUG = 'sample-homes'
    try {
      render(<SiteHeader businessName="Avasetu" />)
      expect(hrefOf(screen.getByRole('banner'), /^see a demo page$/i)).toBe('/agent/sample-homes')
    } finally {
      if (before === undefined) delete process.env.NEXT_PUBLIC_DEMO_AGENT_SLUG
      else process.env.NEXT_PUBLIC_DEMO_AGENT_SLUG = before
    }
  })
})

describe('site footer', () => {
  it('links to every main page, legal pages and the social profiles, with no phone number', () => {
    render(<SiteFooter cfg={cfg} />)
    const footer = screen.getByRole('contentinfo')
    for (const [name, href] of EXPECTED) expect(hrefOf(footer, name)).toBe(href)
    expect(hrefOf(footer, /^request an invite$/i)).toBe('/request-invite')
    for (const [name, href] of [[/^privacy$/i, '/privacy'], [/^terms$/i, '/terms'], [/^data deletion$/i, '/data-deletion']] as const) {
      expect(hrefOf(footer, name)).toBe(href)
    }
    const hrefs = within(footer).getAllByRole('link').map((a) => a.getAttribute('href'))
    expect(hrefs).toEqual(expect.arrayContaining([socialLinks().instagram, socialLinks().facebook]))
    expect(footer.textContent).not.toMatch(/(?:\+?\d[\s\-().]*){10,}/)
    expect(footer.querySelector('a[href^="tel:"], a[href*="wa.me"]')).toBeNull()
  })
})

describe('landing hero', () => {
  it('leads with "Join the free pilot" and offers "See an example agent page" second', () => {
    render(<LandingPage />)
    expect(screen.getAllByRole('link', { name: /^join the free pilot$/i })[0]).toHaveAttribute('href', '#invite') // the short form on the page
    expect(screen.getByRole('link', { name: /^see an example agent page$/i })).toHaveAttribute('href', '/agent/house-deal')
  })
})
