import React from 'react'
import { render, screen, within } from '@testing-library/react'
import SiteHeader from '@/components/marketing/SiteHeader'
import SiteFooter from '@/components/marketing/SiteFooter'
import LandingPage from '@/app/page'
import { buildMarketingConfig } from '@/lib/marketing/config'
import { socialLinks } from '@/lib/marketing/social'

jest.mock('@/components/site/PostsSection', () => ({ __esModule: true, default: () => null }))

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

  it('describes the site to buyers, not as an agent pilot, and keeps the agent links in their own column', () => {
    render(<SiteFooter cfg={cfg} />)
    const footer = screen.getByRole('contentinfo')
    expect(footer).toHaveTextContent('Your bridge to the right home. Plain-language property news, area guides and homes for Kharadi, Upper Kharadi and Wagholi, Pune.')
    expect(footer.textContent).not.toMatch(/pilot/i)
    const agents = within(footer).getByRole('heading', { name: /^for agents$/i }).parentElement as HTMLElement
    expect(within(agents).getAllByRole('link').map((a) => a.textContent)).toEqual(['For agents', 'See a demo page', 'Request an invite', 'Sign in'])
  })
})

describe('home page', () => {
  it('offers agents a "See a demo agent page" link', async () => {
    process.env.SITE_USE_FIXTURES = '1' // news from fixtures, no network
    try {
      render(await LandingPage())
    } finally {
      delete process.env.SITE_USE_FIXTURES
    }
    expect(screen.getByRole('link', { name: /^see a demo agent page$/i })).toHaveAttribute('href', '/agent/demo')
  })
})
