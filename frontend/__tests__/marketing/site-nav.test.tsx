import React from 'react'
import { render, screen, within } from '@testing-library/react'
import SiteHeader from '@/components/marketing/SiteHeader'
import SiteFooter from '@/components/marketing/SiteFooter'
import LandingPage from '@/app/agents/page'
import { buildMarketingConfig } from '@/lib/marketing/config'
import { socialLinks } from '@/lib/marketing/social'
import { demoAgentPath } from '@/lib/brand'

jest.mock('@/components/site/PostsSection', () => ({ __esModule: true, default: () => null }))
jest.mock('@/components/news/NewsSection', () => ({ __esModule: true, default: () => null }))
jest.mock('@/components/marketing/BuyerProjectLinks', () => ({ __esModule: true, default: () => null }))

const cfg = buildMarketingConfig({})
const EXPECTED: Array<[RegExp, string]> = [
  [/^for agents$/i, '/agents'],
  [/^news$/i, '/news'],
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
    expect(cta).toHaveAttribute('href', '/enquire')
    expect(within(header).queryByRole('link', { name: /request an invite/i })).toBeNull()
    expect(hrefOf(header, /^for agents$/i)).toBe('/agents')  // still a normal link
  })

  it('buyer pages with their own phone bottom bar keep the header button off phones only', () => {
    const { unmount } = render(<SiteHeader businessName="Avasetu" bottomBar />)
    expect(within(screen.getByRole('banner')).getByTestId('header-cta').className).toContain('max-md:hidden')
    unmount()
    render(<SiteHeader businessName="Avasetu" />)
    expect(within(screen.getByRole('banner')).getByTestId('header-cta').className).not.toContain('max-md:hidden')
  })

  it('agent pages get "Claim your free trial"; the invite page itself gets no button', () => {
    const { unmount } = render(<SiteHeader businessName="Avasetu" cta="agent" />)
    const cta = within(screen.getByRole('banner')).getByTestId('header-cta')
    expect(cta).toHaveTextContent('Claim your free trial')
    expect(cta).toHaveAttribute('href', '/trial')
    expect(within(screen.getByRole('banner')).queryByRole('link', { name: /tell us what you need/i })).toBeNull()
    unmount()
    render(<SiteHeader businessName="Avasetu" cta="none" />)
    expect(within(screen.getByRole('banner')).queryByTestId('header-cta')).toBeNull()
  })

  it('never links the sample agent page, on buyer or agent pages', () => {
    for (const cta of ['buyer', 'agent'] as const) {
      const { unmount } = render(<SiteHeader businessName="Avasetu" cta={cta} />)
      const header = screen.getByRole('banner')
      expect(within(header).queryByRole('link', { name: /sample agent page/i })).toBeNull()
      expect(header.querySelector('a[href^="/agent/"]')).toBeNull()
      unmount()
    }
  })

  it('takes the sample page slug from NEXT_PUBLIC_DEMO_AGENT_SLUG on the agents\' own pages', () => {
    const before = process.env.NEXT_PUBLIC_DEMO_AGENT_SLUG
    process.env.NEXT_PUBLIC_DEMO_AGENT_SLUG = 'sample-homes'
    try {
      expect(demoAgentPath()).toBe('/agent/sample-homes')
    } finally {
      if (before === undefined) delete process.env.NEXT_PUBLIC_DEMO_AGENT_SLUG
      else process.env.NEXT_PUBLIC_DEMO_AGENT_SLUG = before
    }
  })
})

describe('site footer', () => {
  it('links to every main page, legal pages and the social profiles, and its only phone is the team\'s', () => {
    render(<SiteFooter cfg={cfg} />)
    const footer = screen.getByRole('contentinfo')
    for (const [name, href] of EXPECTED) expect(hrefOf(footer, name)).toBe(href)
    expect(hrefOf(footer, /^claim your free trial$/i)).toBe('/trial')
    for (const [name, href] of [[/^privacy$/i, '/privacy'], [/^terms$/i, '/terms'], [/^data deletion$/i, '/data-deletion']] as const) {
      expect(hrefOf(footer, name)).toBe(href)
    }
    const hrefs = within(footer).getAllByRole('link').map((a) => a.getAttribute('href'))
    expect(hrefs).toEqual(expect.arrayContaining([socialLinks().instagram, socialLinks().facebook]))
    // the team behind the site (House Deal, lib/site/team): its office, phone, email and MahaRERA number, and no other number
    const team = within(footer).getByTestId('team-block')
    expect(team).toHaveTextContent('House Deal, MahaRERA agent A031262502865')
    expect(team).toHaveTextContent('1107, RTC Silver, Upper Kharadi, Wagholi, Pune 412207')
    expect(Array.from(footer.querySelectorAll('a[href^="tel:"]')).map((a) => a.getAttribute('href'))).toEqual(['tel:+917447212121'])
    expect(within(team).getByRole('link', { name: 'housedealofficial@gmail.com' })).toHaveAttribute('href', 'mailto:housedealofficial@gmail.com')
    expect(within(team).getByRole('link', { name: 'Contact us' })).toHaveAttribute('href', '/contact')
    expect(hrefOf(footer, /^contact$/i)).toBe('/contact')
    const outside = footer.cloneNode(true) as HTMLElement
    outside.querySelector('[data-testid="team-block"]')!.remove()
    expect(outside.textContent).not.toMatch(/(?:\+?\d[\s\-().]*){10,}/)
    expect(footer.querySelector('a[href*="wa.me"]')).toBeNull()
    expect(within(footer).queryByRole('link', { name: /sample agent page/i })).toBeNull()
    expect(within(footer).queryByRole('link', { name: /^posts$/i })).toBeNull()   // out of search: not linked site-wide
  })
})

describe('landing hero', () => {
  it('leads with "Claim your free trial" and offers "See a sample agent page" second', () => {
    render(<LandingPage />)
    expect(screen.getAllByRole('link', { name: /^claim your free trial$/i })[0]).toHaveAttribute('href', '/trial') // WhatsApp TRIAL, code back at once
    expect(within(document.getElementById('hero-ctas')!).getByRole('link', { name: /^see a sample agent page$/i })).toHaveAttribute('href', '/agent/house-deal')
  })
})
