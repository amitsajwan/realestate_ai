import { render, screen } from '@testing-library/react'
import React from 'react'
import { RankedCard, cardPrice } from '@/components/site/ListCard'
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

  it('says a web picture is from the web and does not repeat the homes-open line', () => {
    render(<ul><RankedCard r={row({ photo: { url: '/uploads/a.webp', alt: 'Tower', source: 'web' } } as Partial<FacetRow>)} /></ul>)
    expect(screen.getByText('Photo from the web')).toBeInTheDocument()
    expect(screen.queryByText(/20 of 100 homes still open/)).toBeNull()
    expect(screen.getByText('MahaRERA P1')).toBeInTheDocument()
  })

  it('keeps a reason that says more: homes booked lately', () => {
    render(<ul><RankedCard r={row({ reason: '47 homes booked in the last 90 days; 20 of 100 homes still open' })} /></ul>)
    expect(screen.getByText(/47 homes booked in the last 90 days/)).toBeInTheDocument()
  })
})
