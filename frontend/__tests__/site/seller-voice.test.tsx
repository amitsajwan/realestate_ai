import { render, screen, within } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { backing, priceHelp, sizeHelp } from '@/lib/site/sellerHelp'
import type { RegisterProject } from '@/lib/site/register'

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => <div data-testid="enquiry-form" /> }))

const P = {
  slug: 'rose-court-wagholi', name: 'Rose Court', regno: 'P52100011111', promoter: 'B', pincode: '412207',
  area: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' }, completion_now: '2029-03-31', completion_at_registration: '2029-03-31',
  units_total: 100, units_booked: 10, details_read_at: '2026-10-03', listed_or_updated: '2026-01-02', completion_passed: false,
  maharera_url: null, paragraph: 'Rose Court is a project in Wagholi.', indexable: true, finished: false, source: 'MahaRERA', same_area: [],
  home_sizes: [{ bhk: '2 BHK', low: 800, high: 800, kind: 'carpet', one_site: true }],
  prices: { read_at: '2026-10-20', rows: [{ bhk: '2 BHK', from_inr: 6900000, to_inr: null, sources: [{ site: '99acres' }, { site: 'Housing' }] }] },
} as unknown as RegisterProject

const page = (p: RegisterProject = P, facts: unknown = null) =>
  render(<RegisterProjectPage p={p} siteUrl="https://avasetu.in" facts={facts as never} />)

describe('what a project page may promise', () => {
  const none = { closed: false, offer: false, seller: false }

  it("backs House Deal's areas by area or by place, and promises less elsewhere", () => {
    expect(backing({ area: { slug: 'upper-kharadi' } }, none)).toBe('covered')
    expect(backing({ pune_place: { key: 'keshav_nagar' } }, none)).toBe('covered')
    expect(backing({ area: { slug: 'baner' } }, none)).toBe('ask')
    expect(backing({}, none)).toBe('ask')
  })

  it("an agent's sheet or page is backed anywhere, and a closed page outranks everything", () => {
    expect(backing({ area: { slug: 'baner' } }, { ...none, offer: true })).toBe('sheet')
    expect(backing({ area: { slug: 'baner' } }, { ...none, seller: true })).toBe('covered')
    expect(backing({ area: { slug: 'wagholi' } }, { closed: true, offer: false, seller: false })).toBe('closed')
  })

  it("names the team on Avasetu's pages and the agent on theirs", () => {
    expect(priceHelp('covered', 'Avasetu')?.body).toMatch(/^The Avasetu team gets you/)
    expect(priceHelp('sheet', 'House Deal')?.body).toContain('House Deal confirms')
  })

  it('offers no confirmed size or price sheet where nobody stands behind the page', () => {
    expect(priceHelp('ask', 'Avasetu')?.body).not.toContain('price sheet')
    expect(sizeHelp('ask', 'Avasetu')).toBeNull()
    expect(priceHelp('closed', 'Avasetu')).toBeNull()
    expect(sizeHelp('closed', 'Avasetu')).toBeNull()
  })
})

describe('a project page in the seller voice', () => {
  it('never sends the buyer to the builder or names a portal in the price and size blocks', () => {
    page()
    const section = screen.getByTestId('prices-section')
    const sizes = screen.getByTestId('home-sizes')
    for (const block of [section, sizes]) {
      expect(block.textContent).not.toMatch(/confirm .*with the builder|as the sites|99acres|Housing/i)
    }
    expect(within(section).getAllByTestId('price-row')[0]).toHaveTextContent('Last checked 20 Oct 2026')
  })

  it('ends the prices on what the team does, and links the size note to the form', () => {
    page()
    expect(screen.getByTestId('price-help')).toHaveTextContent('Get the exact price for your home')
    expect(screen.getByTestId('price-help')).toHaveTextContent('The Avasetu team gets you the current price sheet')
    expect(within(screen.getByTestId('sizes-note')).getByRole('link')).toHaveAttribute('href', '#enquire')
  })

  it('keeps every source in the page, under Sources', () => {
    page()
    const box = screen.getByTestId('checks')
    expect(box).toHaveTextContent("The builder's site, or two property sites that agree (20 Oct 2026)")
    expect(box).toHaveTextContent('A size marked not yet confirmed comes from one site')
  })

  it('still marks a size only one site gives', () => {
    page()
    expect(screen.getByTestId('home-sizes')).toHaveTextContent('(not yet confirmed)')
  })

  it('promises nothing on a finished project', () => {
    page({ ...P, finished: true, completion_passed: true } as RegisterProject)
    expect(screen.queryByTestId('price-help')).toBeNull()
    expect(within(screen.getByTestId('sizes-note')).queryByRole('link')).toBeNull()
  })

  it("does not promise a price sheet outside the partner's areas", () => {
    page({ ...P, area: { key: 'baner', slug: 'baner', name: 'Baner' } } as RegisterProject)
    expect(screen.getByTestId('price-help')).toHaveTextContent('outside our main East Pune areas')
    expect(screen.getByTestId('ask-offer')).toHaveTextContent('Send your question')
    expect(within(screen.getByTestId('sizes-note')).queryByRole('link')).toBeNull()
  })
})
