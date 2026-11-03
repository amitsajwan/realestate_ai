import { render, screen } from '@testing-library/react'
import React from 'react'
import { RankedCard, cardPrice } from '@/components/site/ListCard'
import { builderLine, cardFacts } from '@/lib/site/facets'
import type { FacetRow } from '@/lib/site/facets'

const row = (more: Partial<FacetRow> = {}) => ({
  rank: 1, slug: 'p-1', name: 'Project 1', legal_name: 'PROJECT 1', regno: 'P1', promoter: null, builder_slug: null, registered_on: null,
  completion_now: '2029-04-30', completion_at_registration: null, units_total: 100, units_booked: 80, units_open: 20,
  reason: '20 of 100 homes still open, 80 booked (80%)', source: 'MahaRERA', stage: 'under-construction', price: null, photo: null, ...more,
}) as unknown as FacetRow

describe('a project card', () => {
  it("shows a size list's own price, not the cheapest of any size (96 Arrcade's 1 BHK on the 2 BHK row)", () => {
    const r = row({ price: { bhk: 1, from_inr: 3_499_000, to_inr: null }, price_from: 4_575_000, price_to: null } as Partial<FacetRow>)
    expect(cardPrice(r)).not.toMatch(/1 BHK/)
    expect(cardPrice(row({ price: { bhk: 1, from_inr: 3_499_000, to_inr: null } } as Partial<FacetRow>))).toMatch(/^1 BHK/)
  })

  it("says a brochure render is an artist's impression and does not repeat the homes-open line", () => {
    render(<ul><RankedCard r={row({ photo: { url: '/uploads/a.webp', alt: 'Tower', source: 'brochure' } } as Partial<FacetRow>)} /></ul>)
    expect(screen.getByText("Artist's impression")).toBeInTheDocument()
    expect(screen.queryByText('Photo from the web')).toBeNull()
    expect(screen.queryByText(/20 of 100 homes still open/)).toBeNull()
    expect(screen.getByText('MahaRERA P1')).toBeInTheDocument()
  })

  it('draws the skyline, with no picture and no note, when the project has no picture we may show', () => {
    const { container } = render(<ul><RankedCard r={row({ photo: null })} /></ul>)
    expect(container.querySelector('img')).toBeNull()
    expect(container.querySelector('svg')).not.toBeNull()
    expect(screen.queryByText(/photo from the web|artist's impression|ai illustration/i)).toBeNull()
  })

  it('keeps a reason that says more: homes booked lately', () => {
    render(<ul><RankedCard r={row({ reason: '47 homes booked in the last 90 days; 20 of 100 homes still open' })} /></ul>)
    expect(screen.getByText(/47 homes booked in the last 90 days/)).toBeInTheDocument()
  })

  it('names the brand buyers search and the company MahaRERA files it under (Godrej Aqua Vista, Oxford Realty LLP)', () => {
    render(<ul><RankedCard r={row({ builder_name: 'Godrej Properties', promoter: 'Oxford Realty LLP', builder_slug: 'godrej-properties' })} /></ul>)
    expect(screen.getByRole('link', { name: 'Godrej Properties' })).toHaveAttribute('href', '/builders/godrej-properties')
    expect(screen.getByText(/filed by Oxford Realty LLP/)).toBeInTheDocument()
  })

  it('says the ranking fact and the date record as a sentence, without the homes open part', () => {
    render(<ul><RankedCard r={row({ reason: 'about 23 homes booked a month since registration (May 2024); 140 of 835 homes still open; completion date not moved by the builder; the builder kept the date on 31 of 32 Pune projects' })} /></ul>)
    expect(screen.getByTestId('card-facts')).toHaveTextContent(
      'About 23 homes booked a month since registration (May 2024); completion date not moved by the builder; the builder kept the date on 31 of 32 Pune projects.')
    expect(screen.queryByText(/140 of 835 homes still open/)).toBeNull()
  })
})

describe('the builder named on a card', () => {
  it('is the brand, with the filing company only when it is another name', () => {
    expect(builderLine({ builder_name: 'Godrej Properties', promoter: 'Oxford Realty LLP' })).toEqual({ name: 'Godrej Properties', filedBy: 'Oxford Realty LLP' })
    expect(builderLine({ builder_name: 'Duville Estates', promoter: 'Duville Estates Private Limited' })).toEqual({ name: 'Duville Estates', filedBy: null })
    expect(builderLine({ builder_name: 'Vilas Javdekar Developers', promoter: 'Vilas Javdekar Greenscape Developers LLP' }).name).toBe('Vilas Javdekar Developers')
    expect(builderLine({ builder_name: 'SSPL Landmarks LLP', promoter: 'SSPL Landmarks LLP' })).toEqual({ name: 'SSPL Landmarks LLP', filedBy: null })
    expect(builderLine({ promoter: null })).toEqual({ name: null, filedBy: null })
  })

  it('has no fact line when the reason is only what is left', () => {
    expect(cardFacts('20 of 100 homes still open, 80 booked (80%)')).toBeNull()
    expect(cardFacts('')).toBeNull()
  })
})
