import { render, screen, within } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { longDay, offerPrice, registerDescription, registerTitle } from '@/lib/site/register'
import type { RegisterProject } from '@/lib/site/register'

// the stand-in renders the section the real form does (id, heading, note, button), so the page's one-section rule can be checked
jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: (p: { topic?: string; title?: string; note?: string; submitLabel?: string; agentName: string }) => (
  <section id="enquire" data-testid="enquiry" data-agent={p.agentName}><h2>{p.title}</h2><p>{p.note}</p><button>{p.submitLabel}</button>{p.topic}</section>
) }))

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
    expect(screen.getByTestId('legal-name')).toHaveTextContent('Filed on MahaRERA as Geras World of Joy M')
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
    // with the legal name it runs past the ~160 characters Google shows, so the description leaves it to the page
    expect(registerDescription(g)).toBe('Gera World of Joy by Rohan Builders, Wagholi, Pune. Possession Oct 2029, moved from Dec 2028, 244/416 homes booked, MahaRERA P52100080076.')
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
    expect(within(ask).getByRole('link', { name: 'Get price sheet & floor plans' })).toHaveAttribute('href', '#enquire')
    expect(within(ask).getByText(/never share your number without your OK/)).toBeInTheDocument()
  })

  it('keeps the ask in the desktop side column and gives phones a bottom bar to the form', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.getByTestId('ask-prompt-side').closest('aside')).not.toBeNull()
    const bar = screen.getByTestId('sticky-join')
    expect(within(bar).getByText('Get price & plans')).toHaveAttribute('href', '#enquire')
    expect(document.getElementById('project-hero')?.tagName).toBe('HEADER')
  })

  it('has one enquiry section with one heading, and every way in uses the same words', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={null} />)
    expect(document.querySelectorAll('[id="enquire"]')).toHaveLength(1)
    const form = document.getElementById('enquire')!
    expect(within(form).getAllByRole('heading')).toHaveLength(1)
    expect(within(form).getByRole('heading').textContent).toBe(`Get the price sheet and floor plans for ${P.name}`)
    expect(within(form).getByRole('button', { name: 'Get price sheet & floor plans' })).toBeInTheDocument()
    expect(within(document.getElementById('project-hero')!).getByRole('link', { name: 'Get price sheet & floor plans' })).toHaveAttribute('href', '#enquire')
    // the promise above the form and in the form name the same people
    expect(within(form).getByText(/The Avasetu team calls or WhatsApps you back/)).toBeInTheDocument()
    expect(form).toHaveAttribute('data-agent', 'Avasetu')  // which the form words as "the Avasetu team" (components.test)
    expect(screen.queryByText(/local agent calls/)).toBeNull()
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

const PORTAL = { read_at: '2026-10-20', rows: [{ bhk: '2 BHK', from_inr: 12_900_000, to_inr: null, official: false,
  sources: [{ site: 'a.example', url: null }, { site: 'b.example', url: null }] }] }
const OFFER = { property_type: 'apartment', price_inr: 12_000_000, source: "the agent's listing",
  homes: [{ bhk: 2, label: '2 BHK', carpet_sqft: 760, price_inr: 12_000_000 }, { bhk: 3, label: '3 BHK', carpet_sqft: 1050, price_inr: 16_500_000 },
    { bhk: 4, label: '4 BHK', carpet_sqft: 1400, price_inr: 22_000_000 }] }
const SHEET = { offer: OFFER } as never

describe('one price on the page', () => {
  it("quotes the agent's price sheet in the hero and leaves the portals' prices out", () => {
    const { container } = render(<RegisterProjectPage p={{ ...P, prices: PORTAL }} siteUrl="https://avasetu.in" facts={SHEET} />)
    const hero = document.getElementById('project-hero')!
    expect(hero).toHaveTextContent('from ₹1.2 Cr')
    expect(hero).toHaveTextContent('2, 3 & 4 BHK')
    expect(container).not.toHaveTextContent('₹1.29 Cr')
    expect(screen.queryByTestId('prices')).toBeNull()
    const faq = [...container.querySelectorAll('script[type="application/ld+json"]')].map((s) => JSON.parse(s.textContent || '{}'))
      .find((x) => x['@type'] === 'FAQPage').mainEntity[0]
    expect(faq.acceptedAnswer.text).toMatch(/quotes from ₹1.2 Cr/)
    expect(registerTitle({ ...P, prices: PORTAL }, offerPrice(OFFER))).toBe('Rohan Abhilasha 4 Wagholi: from ₹1.2 Cr, Possession Oct 2029')
    expect(registerDescription({ ...P, prices: PORTAL }, offerPrice(OFFER))).toMatch(/2, 3 & 4 BHK from ₹1.2 Cr/)
  })

  it("keeps the portals' prices when no agent has a sheet, or the offer is a rent", () => {
    const { unmount } = render(<RegisterProjectPage p={{ ...P, prices: PORTAL }} siteUrl="https://avasetu.in" facts={null} />)
    expect(document.getElementById('project-hero')).toHaveTextContent('from ₹1.29 Cr')
    expect(screen.getByTestId('prices')).toBeInTheDocument()
    unmount()
    expect(offerPrice({ transaction: 'rent', price_inr: 30_000 })).toBeNull()
  })

  it('puts the price sheet in the main column right after the pictures, before About', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={SHEET} />)
    const offer = screen.getByTestId('offer')
    expect(offer.closest('aside')).toBeNull()
    const about = screen.getByRole('heading', { name: /About Rohan Abhilasha 4/ })
    expect(offer.compareDocumentPosition(about) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  })
})

const PHOTO = (url: string, source?: 'builder' | 'ai') => ({ url, alt: url, width: 1600, height: 900, site: 'rohan.example', page_url: null, source })

describe('the hero', () => {
  it("opens with the builder's first picture, and the gallery starts from the next one", () => {
    const profile = { highlights: [], plans: [], read_at: null, photos: [PHOTO('/m/a.webp', 'builder'), PHOTO('/m/b.webp', 'builder'), PHOTO('/m/c.webp', 'builder')] } as never
    render(<RegisterProjectPage p={{ ...P, profile }} siteUrl="https://avasetu.in" facts={null} />)
    const img = within(screen.getByTestId('hero-photo')).getByRole('img')
    expect(img).toHaveAttribute('src', '/m/a.webp')
    expect(img).toHaveAttribute('loading', 'eager')
    const gallery = within(screen.getByTestId('photos')).getAllByRole('img').map((x) => x.getAttribute('src'))
    expect(gallery).toEqual(['/m/b.webp', '/m/c.webp'])
  })

  it('never puts an AI illustration in the hero as if it were a picture of the project', () => {
    const profile = { highlights: [], plans: [], read_at: null, photos: [PHOTO('/m/ai.webp', 'ai')] } as never
    render(<RegisterProjectPage p={{ ...P, profile }} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.queryByTestId('hero-photo')).toBeNull()
    expect(within(screen.getByTestId('photos')).getAllByRole('img')).toHaveLength(1)
  })

  it('shows the registration once, the brand without the SPV, no Registered tile and a plain stage', () => {
    const p: RegisterProject = { ...P, promoter: 'Manjari Housing Projects LLP', stage: 'early',
      builder: { name: 'Godrej Properties', count: 1, with_dates: 0, moved_later: 0, avg_months_later: null, projects: [] },
      details: { towers: 4, max_floors: 30, units_total: 416, units_residential: 400, units_other: 16, booked_pct: 59, registered_on: '2025-01-10', completion_moved_months: 10 } }
    render(<RegisterProjectPage p={p} siteUrl="https://avasetu.in" facts={null} />)
    const hero = document.getElementById('project-hero')!
    expect(hero.textContent!.split('P52100080076')).toHaveLength(2)
    expect(hero).toHaveTextContent('by Godrej Properties')
    expect(hero).not.toHaveTextContent('Manjari Housing')
    expect(within(hero).queryByText('Registered')).toBeNull()
    expect(screen.getByTestId('stage')).toHaveTextContent(/^Early stage$/)
    expect(screen.getByTestId('stage')).toHaveAttribute('title', expect.stringMatching(/Stage by dates/))
    // the details sit in the one record now
    expect(screen.queryByRole('heading', { name: 'Project details' })).toBeNull()
    expect(screen.getByText('Registered on')).toBeInTheDocument()
    expect(screen.getByText('400 homes, 16 shops or offices.')).toBeInTheDocument()
  })
})

describe('a shorter page', () => {
  it('folds the tower and building tables into "Tower by tower"', () => {
    const tower = (regno: string) => ({ regno, name: regno, completion_now: null, completion_at_registration: null, units_total: 10, units_booked: 2, registered_on: null, maharera_url: null })
    const p: RegisterProject = { ...P, buildings: [{ name: 'A', wing: null, floors: 20, units_residential: 80, units_other: 0, units_total: 80 }],
      towers: [tower('P1'), tower('P2')] }
    render(<RegisterProjectPage p={p} siteUrl="https://avasetu.in" facts={null} />)
    const fold = screen.getByTestId('tower-by-tower')
    expect(fold.tagName).toBe('DETAILS')
    expect(fold).not.toHaveAttribute('open')
    expect(within(fold).getByTestId('towers')).toBeInTheDocument()
    expect(within(fold).getByRole('heading', { name: 'Buildings' })).toBeInTheDocument()
  })
})
