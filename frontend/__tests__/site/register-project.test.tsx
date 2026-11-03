import { render, screen, within } from '@testing-library/react'
import React from 'react'
import RegisterProjectPage from '@/components/site/RegisterProjectPage'
import { longDay, offerPrice } from '@/lib/site/register'
import { registerDescription, registerTitle } from '@/lib/site/projectSeo'
import type { RegisterProject } from '@/lib/site/register'

// the stand-in renders the section the real form does (id, heading, note, button), so the page's one-section rule can be checked
type Choice = { anchor: string; label: string; title: string; topic: string; submitLabel: string }
jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: (p: { id?: string; topic?: string; title?: string; note?: string; submitLabel?: string; agentName: string; choices?: Choice[] }) => {
  // with choices the real form opens on the first and shows the others' anchors and topics only when picked
  const first = p.choices?.[0]
  return (
    <section id={p.id ?? 'enquire'} data-testid={p.id ? 'enquiry-' + p.id : 'enquiry'} data-agent={p.agentName}>
      {p.choices?.slice(1).map((c) => <span key={c.anchor} id={c.anchor} data-testid={'choice-' + c.anchor} data-title={c.title} data-topic={c.topic} data-submit={c.submitLabel} />)}
      <h2>{first?.title ?? p.title}</h2><p>{p.note}</p><button>{first?.submitLabel ?? p.submitLabel}</button>{first?.topic ?? p.topic}
    </section>
  )
} }))

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
    // the code's answer says it once; the model's old summary (paragraph) is not shown any more
    expect(screen.getByTestId('project-answer')).toHaveTextContent(/registered with MahaRERA as P52100080076/)
    expect(screen.queryByText(P.paragraph)).toBeNull()
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
    expect(registerTitle(g)).toBe('Gera World of Joy Wagholi: possession Oct 2029, MahaRERA')
    // with the legal name it runs past the ~160 characters Google shows, so the description leaves it to the page
    expect(registerDescription(g)).toBe('Gera World of Joy by Rohan Builders, Wagholi, Pune. Possession Oct 2029, 244 of 416 homes booked. MahaRERA P52100080076, checked by Avasetu.')
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
    expect(within(ask).getByRole('link', { name: "Get today's price sheet & floor plans" })).toHaveAttribute('href', '#enquire')
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
    expect(within(form).getByRole('button', { name: "Get today's price sheet & floor plans" })).toBeInTheDocument()
    expect(within(document.getElementById('project-hero')!).getByRole('link', { name: "Get today's price sheet & floor plans" })).toHaveAttribute('href', '#enquire')
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
    expect(registerTitle({ ...P, prices: PORTAL }, offerPrice(OFFER))).toBe('Rohan Abhilasha 4 Wagholi: from ₹1.2 Cr, possession Oct 2029')
    expect(registerDescription({ ...P, prices: PORTAL }, offerPrice(OFFER))).toMatch(/2, 3 & 4 BHK from ₹1.2 Cr/)
  })

  it("keeps the portals' prices when no agent has a sheet, or the offer is a rent", () => {
    const { unmount } = render(<RegisterProjectPage p={{ ...P, prices: PORTAL }} siteUrl="https://avasetu.in" facts={null} />)
    expect(document.getElementById('project-hero')).toHaveTextContent('from ₹1.29 Cr')
    expect(screen.getByTestId('prices')).toBeInTheDocument()
    unmount()
    expect(offerPrice({ transaction: 'rent', price_inr: 30_000 })).toBeNull()
  })

  it('puts the price sheet first in the main column, in "<name> price", before the location and About', () => {
    render(<RegisterProjectPage p={{ ...P, sections: [{ heading: 'The project', text: 'Two towers on the main road.' }] }} siteUrl="https://avasetu.in" facts={SHEET} />)
    const offer = screen.getByTestId('offer')
    expect(offer.closest('aside')).toBeNull()
    expect(within(screen.getByTestId('prices-section')).getByRole('heading', { level: 2 })).toHaveTextContent('Rohan Abhilasha 4 price')
    expect(screen.getByTestId('prices-section')).toContainElement(offer)
    const location = screen.getByRole('heading', { name: 'Rohan Abhilasha 4 location' })
    const about = screen.getByRole('heading', { name: /About Rohan Abhilasha 4/ })
    expect(offer.compareDocumentPosition(location) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(location.compareDocumentPosition(about) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
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

  it("puts the builder's logo where the picture would be when the project has none, and only then", () => {
    const logo = { url: '/uploads/builder_logos/godrej-properties.png', width: 480, height: 99, tone: 'dark' as const, site: 'godrejproperties.com' }
    const builder = { name: 'Godrej Properties', count: 3, with_dates: 0, moved_later: 0, avg_months_later: null, projects: [], logo }
    const { unmount } = render(<RegisterProjectPage p={{ ...P, builder }} siteUrl="https://avasetu.in" facts={null} />)
    const shown = screen.getByTestId('hero-logo')
    expect(within(shown).getByRole('img')).toHaveAttribute('src', logo.url)
    expect(within(shown).getByRole('img')).toHaveAttribute('alt', 'Godrej Properties logo')
    expect(shown).toHaveTextContent("The builder's logo, from godrejproperties.com")
    expect(shown).toHaveClass('bg-white')
    unmount()
    const profile = { highlights: [], plans: [], read_at: null, photos: [PHOTO('/m/a.webp', 'builder')] } as never
    render(<RegisterProjectPage p={{ ...P, builder, profile }} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.getByTestId('hero-photo')).toBeInTheDocument()
    expect(screen.queryByTestId('hero-logo')).toBeNull()
    expect(within(screen.getByTestId('hero-photo-logo')).getByRole('img')).toHaveAttribute('alt', 'Godrej Properties logo')
  })

  it("shows where the project is when it has no picture, with the builder's logo over the map", () => {
    const logo = { url: '/uploads/builder_logos/kohinoor-group.png', width: 257, height: 70, tone: 'light' as const, site: 'kohinoorpune.com' }
    const builder = { name: 'Kohinoor Group', count: 2, with_dates: 0, moved_later: 0, avg_months_later: null, projects: [], logo }
    const location_picture = { url: '/uploads/project_maps/p52100012345.webp', width: 960, height: 540 }
    const { unmount } = render(<RegisterProjectPage p={{ ...P, builder, location_picture }} siteUrl="https://avasetu.in" facts={null} />)
    const map = screen.getByTestId('hero-map')
    expect(within(map).getByRole('img', { name: /^Map: where/ })).toHaveAttribute('src', location_picture.url)
    expect(within(screen.getByTestId('hero-map-logo')).getByRole('img')).toHaveAttribute('alt', 'Kohinoor Group logo')
    expect(screen.queryByTestId('hero-logo')).toBeNull()
    unmount()
    const profile = { highlights: [], plans: [], read_at: null, photos: [PHOTO('/m/a.webp', 'builder')] } as never
    render(<RegisterProjectPage p={{ ...P, builder, location_picture, profile }} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.getByTestId('hero-photo')).toBeInTheDocument()
    expect(screen.queryByTestId('hero-map')).toBeNull()
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

describe('the project page leads its text with a dated answer', () => {
  it('opens the page with the answer and our last change, and says the same day in WebPage dateModified', () => {
    const { container } = render(<RegisterProjectPage p={{ ...P, page_updated: '2026-10-21' }} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.getByTestId('project-answer')).toHaveTextContent(/^As of 3 Oct 2026, Rohan Abhilasha 4 by Rohan Builders in Wagholi, Pune is registered with MahaRERA as P52100080076\./)
    expect(screen.getByTestId('updated')).toHaveTextContent('Updated 21 Oct 2026')
    const lds = [...container.querySelectorAll('script[type="application/ld+json"]')].map((s) => JSON.parse(s.textContent || '{}'))
    expect(lds.find((x) => x['@type'] === 'WebPage')).toMatchObject({ url: 'https://avasetu.in/projects/rohan-abhilasha-4-wagholi', dateModified: '2026-10-21' })
  })

  it('a page with no dates or homes read yet has no answer and no made-up update day', () => {
    const { container } = render(<RegisterProjectPage p={{ ...P, completion_now: null, completion_at_registration: null, units_total: null, units_booked: null }} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.queryByTestId('project-answer')).toBeNull()
    expect(screen.queryByTestId('updated')).toBeNull()
    expect(container.innerHTML).not.toContain('"WebPage"')
  })
})

// Park Eden Phase I, Kharadi (owner 2026-10-25: "why we have duplicate"): the page v2 of docs/plan/project-page-v2.md
const SRC = [{ site: 'parkeden.example', url: 'https://parkeden.example/eden' }]
const EDEN: RegisterProject = {
  ...P, slug: 'park-eden-phase-i-kharadi', name: 'PARK EDEN PHASE I', marketed_name: 'Park Eden', regno: 'P52100055555',
  area: { key: 'kharadi', slug: 'kharadi', name: 'Kharadi' }, completion_at_registration: '2030-10-31', completion_now: '2031-02-28',
  units_total: 249, units_booked: 27, extension_only: true,
  paragraph: 'Park Eden Phase I has 249 homes are available in Kharadi.',
  details: { towers: 2, max_floors: 32, units_total: 249, units_residential: 249, units_other: 0, booked_pct: 11, registered_on: '2024-11-02',
    completion_moved_months: 4, extension_months: 4 },
  prices: { read_at: '2026-10-20', rows: [
    { bhk: '3 BHK', from_inr: 19_900_000, to_inr: 23_000_000, official: true, sqft: 1_150, per_sqft: 17_304, sources: SRC },
    { bhk: '4 BHK', from_inr: 29_000_000, to_inr: null, official: true, sqft: 1_600, per_sqft: 18_125, sources: SRC }] },
  area_rate: { place: 'Kharadi', per_sqft: 12_400, projects: 14 },
  sales: { booked: 11, days: 60, since: '2026-08-21' },
  commute: [{ name: 'EON IT Park', km: 3.2 }, { name: 'World Trade Center', km: 4 }],
  map: { lat: 18.55, lon: 73.94 },
  web_facts: { read_at: '2026-10-19', facts: [
    { key: 'towers', label: 'Towers', text: '5', official: true, sources: [{ ...SRC[0], quote: '5 towers' }], scope: 'project' },
    { key: 'land_acres', label: 'Land', text: '7 acres', official: true, sources: [{ ...SRC[0], quote: '7 acres' }] }] },
  cautions: [{ key: 'early', text: 'Early stage: ask for the construction schedule.', source: 'rera' }],
  buildings: [{ name: 'A', wing: null, floors: 32, units_residential: 125, units_other: 0, units_total: 125 },
    { name: 'B', wing: null, floors: 30, units_residential: 124, units_other: 0, units_total: 124 }],
  builder: { name: 'Eden Developers', count: 6, record_ok: true, with_dates: 5, moved_later: 1, avg_months_later: 6, projects: [] },
  same_area: [
    { name: 'Gera World of Joy', slug: 'gera-world-of-joy', completion_now: '2029-06-30', price_from: 9_500_000, bhk: '2, 3 BHK' },
    { name: 'Kharadi Heights', slug: 'kharadi-heights', completion_now: null }],
  profile: { read_at: '2026-10-19', photos: [], plans: [], highlights: [
    { topic: 'homes', text: '3 and 4 BHK homes', official: true, sources: SRC },
    { topic: 'clubhouse', text: 'A 30,000 sq ft clubhouse', official: true, sources: SRC }] },
}

describe('project page v2: each fact once, in the order a buyer asks', () => {
  it('heads the page with the marketed name and phase, the area and the MahaRERA number, and the four chips', () => {
    render(<RegisterProjectPage p={EDEN} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Park Eden Phase I, Kharadi')
    expect(screen.getByTestId('regno')).toHaveTextContent('P52100055555')
    expect(screen.getByTestId('chip-bhk')).toHaveTextContent('3, 4 BHK')
    expect(screen.getByTestId('chip-price')).toHaveTextContent('from ₹1.99 Cr')
    expect(screen.getByTestId('chip-possession')).toHaveTextContent('Feb 2031')
    expect(screen.getByTestId('chip-booked')).toHaveTextContent('27 of 249 booked')
    expect(screen.getByTestId('chip-booked')).toHaveTextContent('11 booked in the last 60 days')
    const hero = document.getElementById('project-hero')!
    expect(within(hero).getByRole('link', { name: "Get today's price sheet & floor plans" })).toHaveAttribute('href', '#enquire')
    expect(within(hero).getByRole('link', { name: 'Book a site visit' })).toHaveAttribute('href', '#visit')
  })

  it('books a site visit as a choice in the one enquiry form, with the visit as its topic', () => {
    render(<RegisterProjectPage p={EDEN} siteUrl="https://avasetu.in" facts={null} />)
    expect(document.querySelectorAll('section[id="enquire"], section[id="visit"]')).toHaveLength(1)
    const visit = document.getElementById('visit')!
    expect(document.getElementById('enquire')).toContainElement(visit)
    expect(visit).toHaveAttribute('data-title', 'Book a site visit to PARK EDEN PHASE I')
    expect(visit).toHaveAttribute('data-topic', 'Site visit: PARK EDEN PHASE I (MahaRERA P52100055555)')
    expect(visit).toHaveAttribute('data-submit', 'Book a site visit')
  })

  it('never says the date moved when MahaRERA\'s extension is the only change, and never "homes are available"', () => {
    const { container } = render(<RegisterProjectPage p={EDEN} siteUrl="https://avasetu.in" facts={null} />)
    const ext = "The completion date filed with MahaRERA is 28 Feb 2031; MahaRERA's August 2026 order added 4 months to it (the builder has not moved it)."
    expect(screen.getByTestId('project-answer')).toHaveTextContent(ext)
    expect(screen.getByTestId('project-answer')).toHaveTextContent('MahaRERA shows 27 of 249 homes booked.')
    expect(screen.getByTestId('possession')).toHaveTextContent(ext)
    expect(within(screen.getByTestId('possession')).getByRole('heading', { level: 3 })).toHaveTextContent('Park Eden possession date')
    // what the reader sees (the structured data is the SEO work's, and keeps the old summary as its description for now)
    const seen = container.cloneNode(true) as HTMLElement
    seen.querySelectorAll('script').forEach((s) => s.remove())
    expect(seen).not.toHaveTextContent(/moved from|Moved \d+ months? later|homes are available/)
    // the FAQ (on the page and in FAQPage) says it the same way
    expect(screen.getByText(/^The completion date filed with MahaRERA is 28 Feb 2031; .*Ask the builder/)).toBeInTheDocument()
  })

  it('shows prices and sizes with ₹ per sq ft, the source and day, the area rate and the ask for the offer', () => {
    render(<RegisterProjectPage p={EDEN} siteUrl="https://avasetu.in" facts={null} />)
    const rows = screen.getAllByTestId('price-row')
    expect(rows[0]).toHaveTextContent('3 BHK')
    expect(rows[0]).toHaveTextContent('₹1.99 Cr – ₹2.3 Cr')
    expect(rows[0]).toHaveTextContent('from 1,150 sq ft · ₹17,304/sq ft')
    // the kind of source, never a site's name (owner 2026-10-30: no portals or builder domains printed on our pages)
    expect(rows[0]).toHaveTextContent("As listed on the builder's site, 20 Oct 2026")
    expect(rows[0]).not.toHaveTextContent('parkeden.example')
    expect(screen.getByTestId('area-rate')).toHaveTextContent('Kharadi average ₹12,400/sq ft across 14 projects')
    expect(screen.getByTestId('ask-offer')).toHaveTextContent('Ask for the current offer')
    expect(screen.getByTestId('ask-offer')).toHaveAttribute('href', '#enquire')
  })

  it('shows an "All homes" price as "Homes", with no BHK chip and no "All homes BHK"', () => {
    const p: RegisterProject = { ...EDEN, prices: { read_at: null, rows: [{ bhk: 'All homes', from_inr: 19_900_000, to_inr: null, official: true, sources: SRC }] } }
    const { container } = render(<RegisterProjectPage p={p} siteUrl="https://avasetu.in" facts={null} />)
    expect(container).not.toHaveTextContent('All homes BHK')
    expect(screen.queryByTestId('chip-bhk')).toBeNull()
    expect(screen.getByTestId('chip-price')).toHaveTextContent('from ₹1.99 Cr')
    expect(screen.getByTestId('price-row')).toHaveTextContent(/^Homes/)
    expect(screen.getByTestId('project-answer')).toHaveTextContent('Homes from ₹1.99 Cr')
  })

  it('gives the location its work hubs (straight line, said so) before what is nearby', () => {
    const facts = { nearby: [{ label: 'Hospital', name: 'Columbia Asia', km: 1.4 }], nearby_sources: [{ name: 'OpenStreetMap', url: 'https://osm.org' }] } as never
    render(<RegisterProjectPage p={EDEN} siteUrl="https://avasetu.in" facts={facts} />)
    const commute = screen.getByTestId('commute')
    expect(commute).toHaveTextContent('EON IT Park3.2 km')
    expect(commute.compareDocumentPosition(screen.getByTestId('nearby')) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(screen.getByTestId('distance-note')).toHaveTextContent(/Straight-line distances/)
  })

  it('lists the amenities without a bullet repeating the BHK chip', () => {
    render(<RegisterProjectPage p={EDEN} siteUrl="https://avasetu.in" facts={null} />)
    const h = screen.getByTestId('highlights')
    expect(within(h).getByRole('heading', { level: 2 })).toHaveTextContent('Park Eden amenities')
    expect(h).toHaveTextContent('A 30,000 sq ft clubhouse')
    expect(h).not.toHaveTextContent('3 and 4 BHK homes')
  })

  it('shows the model\'s sections under About and never the old summary; with no sections there is no About', () => {
    const { unmount } = render(<RegisterProjectPage p={{ ...EDEN, sections: [{ heading: 'Location', text: 'On the road to the IT parks.' }] }} siteUrl="https://avasetu.in" facts={null} />)
    expect(within(screen.getByTestId('about')).getByRole('heading', { level: 2 })).toHaveTextContent('About Park Eden')
    expect(screen.getByTestId('about')).toHaveTextContent('On the road to the IT parks.')
    expect(screen.queryByText(EDEN.paragraph)).toBeNull()
    unmount()
    render(<RegisterProjectPage p={EDEN} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.queryByTestId('about')).toBeNull()
    expect(screen.queryByRole('heading', { name: /^About / })).toBeNull()
  })

  it('checks everything in one "RERA details" section, the whole project\'s count labelled beside the registration\'s', () => {
    const facts = { maharera: { rera_no: 'P52100055555', url: 'https://x', project_type: 'Residential' } } as never
    render(<RegisterProjectPage p={EDEN} siteUrl="https://avasetu.in" facts={facts} />)
    const record = screen.getByTestId('record')
    expect(within(record).getByRole('heading', { level: 2 })).toHaveTextContent('Park Eden RERA details')
    expect(record).toHaveTextContent('Checked by us')
    for (const id of ['possession', 'checks', 'cautions', 'tower-by-tower', 'web-facts']) expect(record).toContainElement(screen.getByTestId(id))
    expect(within(record).getByText('2 in this registration')).toBeInTheDocument()
    expect(record).toHaveTextContent("5 in the whole project (builder's site)")
    expect(within(screen.getByTestId('web-facts')).queryByText('Towers')).toBeNull()   // said once, beside MahaRERA's count
    expect(screen.getByTestId('web-facts')).toHaveTextContent('7 acres')
    expect(record).toHaveTextContent('Eden Developers: track record')
    expect(within(record).getByText('Residential')).toBeInTheDocument()
    // the old side-column blocks are gone: no second "checked" panel and no separate web-facts or builder section
    expect(screen.queryByRole('heading', { name: 'Checked for you' })).toBeNull()
    expect(screen.queryByRole('heading', { name: 'About the builder' })).toBeNull()
  })

  it('compares the area\'s other projects by price from, BHK and possession', () => {
    render(<RegisterProjectPage p={EDEN} siteUrl="https://avasetu.in" facts={null} />)
    const compare = screen.getByTestId('compare')
    expect(within(compare).getByRole('heading', { level: 2 })).toHaveTextContent('Other projects in Kharadi')
    expect(within(compare).getByRole('link', { name: /Gera World of Joy/ })).toHaveTextContent('2, 3 BHK · from ₹95 L · possession Jun 2029')
    expect(within(compare).getByRole('link', { name: /Kharadi Heights/ })).toHaveTextContent(/^Kharadi Heights$/)
  })

  it('keeps the sections in the v2 order', () => {
    const profile = { ...EDEN.profile!, photos: [PHOTO('/m/a.webp', 'builder'), PHOTO('/m/b.webp', 'builder')] }
    render(<RegisterProjectPage p={{ ...EDEN, profile, sections: [{ heading: 'The project', text: 'x' }] }} siteUrl="https://avasetu.in" facts={null} />)
    const order = [document.getElementById('project-hero')!, screen.getByTestId('project-answer'), screen.getByTestId('photos'),
      screen.getByTestId('prices-section'), screen.getByTestId('plans'), screen.getByRole('heading', { name: 'Park Eden location' }),
      screen.getByTestId('highlights'), screen.getByTestId('about'), screen.getByTestId('record'), screen.getByTestId('compare'),
      screen.getByRole('heading', { name: 'FAQ' }), document.getElementById('enquire')!]
    order.slice(1).forEach((el, i) => expect(order[i].compareDocumentPosition(el) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy())
    expect(screen.getByTestId('plans')).toHaveTextContent('Park Eden floor plans')
  })

  it('shows nothing for the new fields when the backend has not sent them', () => {
    const p: RegisterProject = { ...P, prices: { read_at: null, rows: [{ bhk: '2 BHK', from_inr: 6_900_000, to_inr: null, official: false,
      sources: [{ site: 'a.example', url: null }] }] } }
    const { container } = render(<RegisterProjectPage p={p} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.queryByTestId('area-rate')).toBeNull()
    expect(screen.queryByTestId('commute')).toBeNull()
    expect(screen.queryByTestId('area-compare')).toBeNull()
    expect(screen.getByTestId('chip-booked')).toHaveTextContent(/^Booked244 of 416 booked$/)
    expect(screen.getByTestId('price-row')).not.toHaveTextContent('/sq ft')
    expect(within(screen.getByTestId('compare')).getByRole('link', { name: /Kesnand Greens/ })).toHaveTextContent('possession Mar 2029')
    expect(container).not.toHaveTextContent(/undefined|null|NaN/)
  })
})

describe('what changed, as we read it (seo-system.md 8b, H1)', () => {
  const moves = [{ seen_on: '2025-09-15', from: '2028-12-31', to: '2029-06-30', blanket: false },
    { seen_on: '2026-08-01', from: '2029-06-30', to: '2029-10-30', blanket: true }]
  const readings = [{ on: '2026-07-03', booked: 212 }, { on: '2026-09-02', booked: 230 }, { on: '2026-10-03', booked: 244 }]

  it('shows the dated booking readings with a chart and every date change, naming MahaRERA\'s order as not the builder', () => {
    render(<RegisterProjectPage p={{ ...P, booked_readings: readings, completion_moves: moves }} siteUrl="https://avasetu.in" facts={null} />)
    const h = screen.getByTestId('history')
    expect(within(h).getByTestId('booked-history')).toHaveTextContent('32 more homes booked between 3 Jul 2026 and 3 Oct 2026: 212 to 244, of 416 homes.')
    expect(within(h).getByTestId('booked-chart')).toHaveAttribute('aria-label', 'Homes booked: 212 on 3 Jul 2026, 244 on 3 Oct 2026')
    expect(within(h).getByText('3 Oct 2026: 244 booked')).toBeInTheDocument()
    const dates = within(h).getByTestId('date-history')
    expect(dates).toHaveTextContent('31 Dec 2028 → 30 Jun 2029, filed by the builder; we saw it on 15 Sep 2025')
    expect(dates).toHaveTextContent("30 Jun 2029 → 30 Oct 2029, by MahaRERA's August 2026 order for most projects (not the builder)")
    expect(within(h).getByTestId('history-source')).toHaveTextContent('Read by Avasetu from MahaRERA on each date shown.')
  })

  it('shows no history block without two readings or a date change', () => {
    render(<RegisterProjectPage p={{ ...P, booked_readings: readings.slice(0, 1), completion_moves: [] }} siteUrl="https://avasetu.in" facts={null} />)
    expect(screen.queryByTestId('history')).toBeNull()
  })
})

describe("the listing agent's videos", () => {
  it('plays the sample-flat videos from the agent site under the pictures, and nothing that is not an https mp4', () => {
    const facts = { offer: { ...OFFER, agent: { slug: 'house-deal', name: 'House Deal', listing_id: 'l1' }, videos: [
      { url: 'https://house-deal.com/wp-content/uploads/3bhk-sample-flat.mp4', label: '3 BHK sample flat' },
      { url: 'javascript:alert(1)', label: 'bad' }] } } as never
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={facts} />)
    const box = screen.getByTestId('videos')
    expect(box).toHaveTextContent('Sample flat video of')
    expect(box).toHaveTextContent('3 BHK sample flat · from House Deal')
    const v = box.querySelectorAll('video')
    expect(v).toHaveLength(1)
    expect(v[0]).toHaveAttribute('src', 'https://house-deal.com/wp-content/uploads/3bhk-sample-flat.mp4#t=0.1')
  })

  it('shows no video section without videos', () => {
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={SHEET} />)
    expect(screen.queryByTestId('videos')).toBeNull()
  })
})

describe('the listing agent at the top', () => {
  it("names a partner agent under the hero and opens their page for the listing; Avasetu's own listing gets no line", () => {
    const hd = { offer: { ...OFFER, agent: { slug: 'house-deal', name: 'House Deal', listing_id: 'l1' } } } as never
    const { unmount } = render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={hd} />)
    const line = screen.getByTestId('listed-by')
    expect(line).toHaveTextContent('Listed by House Deal')
    expect(within(line).getByRole('link', { name: /See it on House Deal's page/ })).toHaveAttribute('href', '/agent/house-deal/listings/l1')
    unmount()
    const own = { offer: { ...OFFER, agent: { slug: 'avasetu', name: 'Avasetu', listing_id: 'l2' } } } as never
    render(<RegisterProjectPage p={P} siteUrl="https://avasetu.in" facts={own} />)
    expect(screen.queryByTestId('listed-by')).toBeNull()
  })
})

describe("on the agent's own listing page", () => {
  const listing = (id: string, title: string) => ({ id, title, price_inr: 12_000_000, transaction: 'sale', locality: 'Kharadi', city: 'Pune',
    bhk: 2, property_type: 'apartment', carpet_sqft: 800, media: [], amenities: [], status: 'live' }) as never
  it("sells the agent's own homes and links to no other project, builder or area page", () => {
    const { container } = render(<RegisterProjectPage p={EDEN} siteUrl="https://avasetu.in" facts={SHEET}
      seller={{ slug: 'house-deal', name: 'House Deal', home: '/agent/house-deal', listingId: 'l1',
        others: [listing('l2', 'Venkatesh Vanaya'), listing('l3', 'Shubh Tristar')] }} />)
    const more = screen.getByTestId('more-from-agent')
    expect(more).toHaveTextContent('More from House Deal')
    expect(more.querySelector('a[href="/agent/house-deal/listings/l2"]')).not.toBeNull()
    const hrefs = [...container.querySelectorAll('a[href]')].map((a) => a.getAttribute('href') || '')
    expect(hrefs.filter((h) => h.startsWith('/') && !h.startsWith('/agent/house-deal'))).toEqual([])
    expect(screen.queryByTestId('compare')).toBeNull()
    expect(screen.queryByTestId('same-promoter')).toBeNull()
  })

  it("shows the listing's own pictures when the kept facts carry none for it (no record, or a record with no offer)", () => {
    const { container } = render(<RegisterProjectPage p={EDEN} siteUrl="https://avasetu.in" facts={null}
      seller={{ slug: 'house-deal', name: 'House Deal', home: '/agent/house-deal', listingId: 'l1',
        photos: ['/uploads/images/hd-vtp-aurelia-01.jpg', '/uploads/images/hd-vtp-aurelia-02.jpg'] }} />)
    expect(container.querySelector('img[src="/uploads/images/hd-vtp-aurelia-01.jpg"]')).not.toBeNull()
    expect(container.querySelector('img[src="/uploads/images/hd-vtp-aurelia-02.jpg"]')).not.toBeNull()
  })
})

// a project beside the rest of its area (backend pages.area_compare): what no single MahaRERA or portal record says
describe('the project against its area', () => {
  const compare = { place: 'Wagholi', booked: { pct: 59, area_pct: 41, projects: 12 },
    moved: { months: 14, area_moved: 9, area_with_dates: 31 }, rate: { per_sqft: 7_100, area_per_sqft: 7_900, projects: 18, diff_pct: -10 } }

  it('shows the share booked, the date move and the rate, each beside the area', () => {
    render(<RegisterProjectPage p={{ ...P, area_compare: compare }} siteUrl="https://avasetu.in" facts={null} />)
    const box = screen.getByTestId('area-compare')
    expect(box).toHaveTextContent('Rohan Abhilasha 4 against Wagholi')
    expect(box).toHaveTextContent('59%The middle of 12 Wagholi projects registered within a year of it: 41%.')
    expect(box).toHaveTextContent('Moved 14 months later9 of 31 Wagholi projects being built moved theirs 3 months or more.')
    expect(box).toHaveTextContent('₹7,100/sq ft10% below the Wagholi middle of ₹7,900/sq ft across 18 projects.')
  })

  it('shows only the parts the backend could compare, and says a date the builder kept was not moved', () => {
    render(<RegisterProjectPage p={{ ...P, area_compare: { ...compare, booked: null, rate: null, moved: { months: 0, area_moved: 9, area_with_dates: 31 } } }}
      siteUrl="https://avasetu.in" facts={null} />)
    const box = screen.getByTestId('area-compare')
    expect(box).toHaveTextContent('Not moved by the builder')
    expect(box).not.toHaveTextContent(/Homes booked|Asking price/)
  })
})
