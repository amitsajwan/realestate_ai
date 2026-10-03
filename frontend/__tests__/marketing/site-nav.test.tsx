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
  it('links to every main page, the invite form and the social profiles', () => {
    render(<SiteHeader businessName="Avasetu" />)
    const header = screen.getByRole('banner')
    for (const [name, href] of EXPECTED) expect(hrefOf(header, name)).toBe(href)
    expect(hrefOf(header, /request an invite/i)).toBe('/request-invite')
    expect(hrefOf(header, /^instagram/i)).toBe(socialLinks().instagram)
    expect(hrefOf(header, /^facebook/i)).toBe(socialLinks().facebook)
    expect(header).toHaveAttribute('data-print', 'hide')
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
