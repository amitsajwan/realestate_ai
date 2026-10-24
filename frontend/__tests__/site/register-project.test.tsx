import { render, screen, within } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { longDay, registerDescription, registerTitle } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'

jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: (p: { topic?: string }) => <div data-testid="enquiry">{p.topic}</div> }))

const P: RegisterProject = {
  slug: 'rohan-abhilasha-4-wagholi', name: 'Rohan Abhilasha 4', regno: 'P52100080076', promoter: 'Rohan Builders', pincode: '412207',
  area: { key: 'wagholi', slug: 'wagholi', name: 'Wagholi' }, completion_now: '2029-10-30', completion_at_registration: '2028-12-31',
  units_total: 416, units_booked: 244, details_read_at: '2026-10-03', listed_or_updated: '2026-09-28',
  maharera_url: 'https://maharerait.maharashtra.gov.in/public/project/view/80076',
  paragraph: 'Rohan Abhilasha 4 is a project by Rohan Builders in Wagholi, Pune, registered with MahaRERA as P52100080076.',
  indexable: true, same_area: [{ name: 'Kesnand Greens', slug: 'kesnand-greens-wagholi', completion_now: '2029-03-31' }], source: 'MahaRERA public records',
}

describe('Avasetu project page from the MahaRERA register', () => {
  it('shows our facts with source and date, then the official record last', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Rohan Abhilasha 4')
    expect(screen.getByTestId('paragraph')).toHaveTextContent(/registered with MahaRERA as P52100080076/)
    expect(screen.getAllByText('30 Oct 2029').length).toBeGreaterThan(0)
    expect(screen.getByText(/At registration: 31 Dec 2028./)).toBeInTheDocument()
    expect(screen.getByText('244 of 416')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /Kesnand Greens/ })).toHaveAttribute('href', '/projects/kesnand-greens-wagholi')
    expect(screen.getAllByRole('link', { name: /Wagholi/ })[0]).toHaveAttribute('href', '/localities/wagholi')
    expect(screen.getByTestId('enquiry')).toHaveTextContent('Rohan Abhilasha 4 (MahaRERA P52100080076)')
    const official = screen.getByRole('link', { name: /official MahaRERA record/ })
    expect(official).toHaveAttribute('href', P.maharera_url)
    expect(within(official.closest('footer')!).getByText(/Source: MahaRERA public records/)).toBeInTheDocument()
  })

  it('a thin page says it is still filling in and shows no empty facts', () => {
    render(<RegisterProjectPage p={{ ...P, completion_now: null, completion_at_registration: null, units_total: null, units_booked: null, indexable: false, same_area: [] }} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.getByText(/still reading this project/)).toBeInTheDocument()
    expect(screen.queryByText(/Homes booked/)).toBeNull()
  })

  it('shows the agent offer the posts quote, labelled with its source', () => {
    const facts = { offer: { property_type: 'plot', price_inr: 3230000, plot_sqft: 1000, source: "the agent's listing", read_at: '2026-10-06' } } as never
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={facts} />)
    expect(screen.getByTestId('offer')).toHaveTextContent(/plot · plot 1,000 sq ft/)
    expect(screen.getByTestId('offer')).toHaveTextContent(/From the agent's listing, 6 Oct 2026/)
  })

  it('leads with the marketed name, keeps the MahaRERA name and aliases, and its JSON-LD matches', () => {
    const g: RegisterProject = { ...P, name: 'Geras World of Joy M', marketed_name: 'Gera World of Joy', aliases: ['Gera World of Joy', 'World of Joy Kharadi'],
      same_promoter: [{ name: 'GERAS SONG OF JOY', marketed_name: 'Gera Song of Joy', slug: 'gera-song-of-joy', completion_now: '2027-06-30' }] }
    const { container } = render(<RegisterProjectPage p={g} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Gera World of Joy, Wagholi')
    expect(screen.getByTestId('legal-name')).toHaveTextContent('Filed on MahaRERA as Geras World of Joy M · P52100080076')
    expect(screen.getByTestId('aka')).toHaveTextContent('Also known as: World of Joy Kharadi')
    expect(within(screen.getByTestId('same-promoter')).getByRole('link', { name: /Gera Song of Joy/ })).toHaveAttribute('href', '/projects/gera-song-of-joy')
    const lds = [...container.querySelectorAll('script[type="application/ld+json"]')].map((s) => JSON.parse(s.textContent || '{}'))
    const complex = lds.find((x) => x['@type'] === 'ApartmentComplex')
    expect(complex.name).toBe('Gera World of Joy')
    expect(complex.alternateName).toEqual(['World of Joy Kharadi', 'Geras World of Joy M'])
    expect(complex.builder).toEqual({ '@type': 'Organization', name: 'Rohan Builders' })
    expect(lds.find((x) => x['@type'] === 'BreadcrumbList').itemListElement.map((i: { name: string }) => i.name)).toEqual(['Home', 'Projects', 'Wagholi', 'Gera World of Joy'])
    const faq = lds.find((x) => x['@type'] === 'FAQPage').mainEntity[0]
    expect(faq.name).toBe('What is the price of Gera World of Joy?')
    expect(screen.getByText(faq.acceptedAnswer.text)).toBeInTheDocument()   // the same words on the page
    expect(registerTitle(g)).toBe('Gera World of Joy Wagholi: Possession Oct 2029, MahaRERA')
    expect(registerDescription(g)).toBe('Gera World of Joy (Geras World of Joy M) by Rohan Builders, Wagholi, Pune. Possession Oct 2029, moved from Dec 2028, 244/416 homes booked, MahaRERA P52100080076.')
  })

  it('formats days', () => {
    expect(longDay('2029-10-30')).toBe('30 Oct 2029')
    expect(longDay(null)).toBe('')
  })
})

describe('asking about a project without scrolling to the end', () => {
  it('puts the ask right after the record, before the long sections, and it jumps to the form', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} />)
    const ask = screen.getByTestId('ask-prompt')
    const record = screen.getByRole('heading', { name: 'The record' })
    const faq = screen.getByRole('heading', { name: 'FAQ' })
    expect(record.compareDocumentPosition(ask) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(ask.compareDocumentPosition(faq) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(within(ask).getByRole('link', { name: 'Ask about this project' })).toHaveAttribute('href', '#enquire')
    expect(within(ask).getByText(/never share your number without your OK/)).toBeInTheDocument()
  })

  it('keeps the ask in the desktop side column and gives phones a bottom bar to the form', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.getByTestId('ask-prompt-side').closest('aside')).not.toBeNull()
    const bar = screen.getByTestId('sticky-join')
    expect(within(bar).getByText('Ask about this project')).toHaveAttribute('href', '#enquire')
    expect(document.getElementById('project-hero')?.tagName).toBe('HEADER')
  })

  it('offers WhatsApp only when the site has a number for it', () => {
    const { unmount } = render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} />)
    expect(within(screen.getByTestId('ask-prompt')).queryByText('WhatsApp')).toBeNull()
    unmount()
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} whatsappUrl="https://wa.me/919800000000" />)
    expect(within(screen.getByTestId('ask-prompt')).getByText('WhatsApp').closest('a')).toHaveAttribute('href', 'https://wa.me/919800000000')
    expect(within(screen.getByTestId('sticky-join')).getByText('WhatsApp').closest('a')).toHaveAttribute('href', 'https://wa.me/919800000000')
  })
})
