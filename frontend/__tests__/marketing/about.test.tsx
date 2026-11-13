import React from 'react'
import { render, screen, within } from '@testing-library/react'
import AboutPage, { metadata } from '@/app/about/page'
import SiteFooter from '@/components/marketing/SiteFooter'
import { buildMarketingConfig, getMarketingConfig } from '@/lib/marketing/config'
import { organizationJsonLd } from '@/lib/marketing/seo'
import { HOW } from '@/lib/site/listRules'

jest.mock('next/navigation', () => ({ useRouter: () => ({ push: jest.fn() }), usePathname: () => '/about' }))

// /about answered 404 (2026-11-04): Google and AI assistants look for who runs a money-decision site and how its lists are made
describe('About page', () => {
  it('is in search with a title and description that say what it answers', () => {
    expect(String(metadata.title)).toBe('About Avasetu: how we check Pune\'s new projects')
    expect(String(metadata.title).length).toBeLessThanOrEqual(70)
    expect(String(metadata.description).length).toBeLessThanOrEqual(160)
    // who runs it is House Deal, an agency, not a person (owner 2026-11-13)
    expect(String(metadata.description)).toMatch(/^What Avasetu is, who runs it \(House Deal, Upper Kharadi\)/)
    expect(metadata.alternates?.canonical).toMatch(/\/about$/)
    expect(metadata.robots).toBeUndefined()
  })

  it('publishes the same ranking rules the list pages show, and where the facts come from', () => {
    const { container } = render(<AboutPage />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('About Avasetu')
    expect(container.querySelector('#how-we-check')).toHaveTextContent('How we check every project')
    const rank = screen.getByRole('region', { name: 'How the lists are ranked' })
    for (const rule of [HOW.top, HOW['new-launches'], HOW['ready-to-move']]) expect(rank).toHaveTextContent(rule)
    expect(within(rank).getByRole('link', { name: 'Top projects' })).toHaveAttribute('href', '/projects/area/kharadi/top')
    expect(screen.getByRole('region', { name: 'What we never do' })).toHaveTextContent(/No builder pays to be on these lists/)
    // the phone and email are on the contact page and in the footer, not repeated in the article
    // (House Deal's MahaRERA number, A031262502865, is a registration, not a phone)
    expect(container.querySelector('article')!.textContent!.replace('A031262502865', '')).not.toMatch(/(?:\+?\d[\s\-().]*){10,}|[a-z]@[a-z]+\./i)
  })

  it('describes the organisation as an AboutPage, and every page names it as our publishing principles', () => {
    const { container } = render(<AboutPage />)
    const ld = Array.from(container.querySelectorAll('script[type="application/ld+json"]')).map((s) => JSON.parse(s.innerHTML))
    const about = ld.find((x) => x['@type'] === 'AboutPage')
    expect(about.mainEntity['@type']).toBe('Organization')
    expect(about.mainEntity.member[0]).toMatchObject({ '@type': 'RealEstateAgent', name: 'House Deal', identifier: { propertyID: 'MahaRERA', value: 'A031262502865' } })
    expect(about.mainEntity.address.postalCode).toBe('412207')
    expect(ld.find((x) => x['@type'] === 'BreadcrumbList')).toBeTruthy()
    const org = organizationJsonLd(buildMarketingConfig({}), 'd')
    expect(org.publishingPrinciples).toBe(getMarketingConfig().siteUrl + '/about#how-we-check')
  })

  it('names House Deal as the team that runs Avasetu, with its MahaRERA number and office, and says that never moves a project up a list', () => {
    render(<AboutPage />)
    const team = screen.getByTestId('about-partner')
    expect(within(team).getByRole('heading', { name: 'Who runs Avasetu' })).toBeInTheDocument()
    expect(within(team).getByRole('link', { name: 'House Deal' })).toHaveAttribute('href', '/agent/house-deal')
    expect(within(team).getByRole('link', { name: /House Deal's own website/ })).toHaveAttribute('href', 'https://house-deal.com')
    expect(within(team).getByRole('link', { name: 'Contact us' })).toHaveAttribute('href', '/contact')
    expect(team).toHaveTextContent('The team behind Avasetu is House Deal')
    expect(team).toHaveTextContent('(A031262502865)')
    expect(team).toHaveTextContent('1107, RTC Silver, Upper Kharadi, Wagholi, Pune 412207')
    expect(team).toHaveTextContent('never moves a project up our lists')
  })

  it('is linked from the footer of every page', () => {
    render(<SiteFooter cfg={buildMarketingConfig({})} />)
    expect(within(screen.getByRole('contentinfo')).getByRole('link', { name: 'About us' })).toHaveAttribute('href', '/about')
  })
})
