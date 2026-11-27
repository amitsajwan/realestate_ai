import React from 'react'
import { render, screen, within } from '@testing-library/react'
import ContactPage, { metadata } from '@/app/contact/page'

jest.mock('next/navigation', () => ({ useRouter: () => ({ push: jest.fn() }), usePathname: () => '/contact' }))

// /contact answered 404 and the site named no one behind it (2026-11-13). Google's raters look for who is responsible for a
// site about a money decision and a way to reach them. From 2026-11-13 that was House Deal, an agent; the owner ended it on
// 2026-11-27 ("we don't need a partner yet"): the Avasetu team, reached on the site's own WhatsApp and email (lib/site/team).
const env = { ...process.env }
beforeEach(() => { process.env.NEXT_PUBLIC_WHATSAPP_NUMBER = '919834256406'; process.env.NEXT_PUBLIC_CONTACT_EMAIL = 'hello@avasetu.in' })
afterEach(() => { process.env = { ...env } })

describe('Contact page', () => {
  it('is in search, says who runs the site, and fits the result', () => {
    expect(String(metadata.title)).toBe('Contact Avasetu: the Avasetu team, Pune')
    expect(String(metadata.title).length).toBeLessThanOrEqual(70)
    expect(String(metadata.description).length).toBeLessThanOrEqual(160)
    expect(String(metadata.description)).not.toMatch(/House Deal|A031262502865/)
    expect(metadata.alternates?.canonical).toMatch(/\/contact$/)
    expect(metadata.robots).toBeUndefined()
  })

  it("names the Avasetu team and the site's own WhatsApp and email, and no agent as the team", () => {
    const { container } = render(<ContactPage />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Contact Avasetu')
    expect(container).toHaveTextContent('Avasetu is run by the Avasetu team in Pune')
    const reach = screen.getByTestId('contact-team')
    expect(within(reach).getByRole('link', { name: '+91 98342 56406' })).toHaveAttribute('href', 'https://wa.me/919834256406')
    expect(within(reach).getByRole('link', { name: 'hello@avasetu.in' })).toHaveAttribute('href', 'mailto:hello@avasetu.in')
    expect(within(reach).getByRole('link', { name: 'tell us what you need' })).toHaveAttribute('href', '/enquire?src=contact')
    expect(container.textContent).not.toMatch(/House Deal|A031262502865|74472|RTC Silver|partner/i)
  })

  it('leaves out a way to reach us that is not set', () => {
    delete process.env.NEXT_PUBLIC_WHATSAPP_NUMBER
    render(<ContactPage />)
    expect(within(screen.getByTestId('contact-team')).queryByText('WhatsApp')).toBeNull()
    expect(within(screen.getByTestId('contact-team')).getByRole('link', { name: 'hello@avasetu.in' })).toBeInTheDocument()
  })

  it('describes the organisation with its own WhatsApp and email and no parent organisation', () => {
    const { container } = render(<ContactPage />)
    const ld = Array.from(container.querySelectorAll('script[type="application/ld+json"]')).map((s) => JSON.parse(s.innerHTML))
    const page = ld.find((x) => x['@type'] === 'ContactPage')
    expect(page.mainEntity).toMatchObject({ '@type': 'Organization', name: 'Avasetu' })
    expect(page.mainEntity.contactPoint[0]).toMatchObject({ telephone: '+919834256406', email: 'hello@avasetu.in' })
    expect(page.mainEntity.parentOrganization).toBeUndefined()
    expect(ld.find((x) => x['@type'] === 'BreadcrumbList')).toBeTruthy()
  })
})
