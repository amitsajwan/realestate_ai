import React from 'react'
import { render, screen, within } from '@testing-library/react'
import ContactPage, { metadata } from '@/app/contact/page'
import { TEAM } from '@/lib/site/team'

jest.mock('next/navigation', () => ({ useRouter: () => ({ push: jest.fn() }), usePathname: () => '/contact' }))

// /contact answered 404 and the site named no one behind it (2026-11-13). Google's raters look for who is responsible for a
// site about a money decision, with an address and a phone; House Deal is that team (owner 2026-11-13).
describe('Contact page', () => {
  it('is in search, says who runs the site, and fits the result', () => {
    expect(String(metadata.title)).toBe('Contact Avasetu: House Deal, Upper Kharadi, Pune')
    expect(String(metadata.title).length).toBeLessThanOrEqual(70)
    expect(String(metadata.description).length).toBeLessThanOrEqual(160)
    expect(String(metadata.description)).toContain('A031262502865')
    expect(metadata.alternates?.canonical).toMatch(/\/contact$/)
    expect(metadata.robots).toBeUndefined()
  })

  it('gives House Deal\'s office, phone, email, MahaRERA number and website, each as House Deal publishes them', () => {
    render(<ContactPage />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Contact Avasetu')
    const reach = screen.getByTestId('contact-team')
    expect(reach).toHaveTextContent('House Deal1107, RTC Silver, Upper Kharadi, Wagholi, Pune 412207')
    expect(within(reach).getByRole('link', { name: '+91 74472 12121' })).toHaveAttribute('href', 'tel:+917447212121')
    expect(within(reach).getByRole('link', { name: 'housedealofficial@gmail.com' })).toHaveAttribute('href', 'mailto:housedealofficial@gmail.com')
    expect(reach).toHaveTextContent('A031262502865')
    expect(within(reach).getByRole('link', { name: /house-deal\.com/ })).toHaveAttribute('href', 'https://house-deal.com')
    expect(within(reach).getByRole('link', { name: 'tell us what you need' })).toHaveAttribute('href', '/enquire?src=contact')
    expect(screen.getAllByRole('link', { name: 'House Deal' })[0]).toHaveAttribute('href', TEAM.page)
  })

  it('describes the organisation with House Deal as the team, its address and a phone that answers', () => {
    const { container } = render(<ContactPage />)
    const ld = Array.from(container.querySelectorAll('script[type="application/ld+json"]')).map((s) => JSON.parse(s.innerHTML))
    const page = ld.find((x) => x['@type'] === 'ContactPage')
    expect(page.mainEntity).toMatchObject({ '@type': 'Organization', name: 'Avasetu', address: { postalCode: '412207', addressCountry: 'IN' } })
    expect(page.mainEntity.contactPoint[0]).toMatchObject({ telephone: '+917447212121', email: 'housedealofficial@gmail.com' })
    expect(page.mainEntity.member[0]).toMatchObject({ '@type': 'RealEstateAgent', name: 'House Deal', url: 'https://house-deal.com' })
    expect(ld.find((x) => x['@type'] === 'BreadcrumbList')).toBeTruthy()
  })
})
