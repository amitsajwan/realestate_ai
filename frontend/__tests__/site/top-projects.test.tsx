import { render, screen, within } from '@testing-library/react'
import React from 'react'

// "Top projects in <place>" is the buyer's shortlist (redesign 2026-10-26, docs/plan/seo-system.md change log): ranked cards of
// projects with homes still open, rows of cards into the place's other lists, and the sold out ones apart with a resale ask.
jest.mock('@/lib/site/api', () => ({ getCatalog: async () => [] }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('next/navigation', () => ({ notFound: () => { throw new Error('NOT_FOUND') }, permanentRedirect: jest.fn(), usePathname: () => '/' }))

const row = (i: number, more: Record<string, unknown> = {}) => ({
  rank: i, slug: `p-${i}`, name: `Project ${i}`, legal_name: `PROJECT ${i}`, regno: `P${i}`, promoter: `Builder ${i}`, builder_slug: null,
  registered_on: '2024-05-06', completion_now: '2029-04-30', completion_at_registration: '2029-04-30', units_total: 100, units_booked: 80,
  units_open: 20, reason: '20 of 100 homes still open, 80 booked (80%)', source: 'MahaRERA', stage: 'under-construction', price: null, photo: null, ...more,
})
const page = (intent: string, rows: unknown[], more: Record<string, unknown> = {}) => ({
  key: `kharadi|${intent}`, path: `/projects/area/kharadi/${intent}`, place: { key: 'kharadi', slug: 'kharadi', name: 'Kharadi' }, intent,
  possession: null, builder: null, builder_name: null, bhk: null, title: 'Top Projects in Kharadi, Pune: 12 on MahaRERA', h1: 'Top projects in Kharadi, Pune',
  answer: 'As of 26 Oct 2026, 12 projects in Kharadi still have 10 or more homes open on MahaRERA.', rows, count: rows.length, changes: [],
  month: null, page_updated: null, indexable: true, as_of: '2026-10-26', source: 'MahaRERA public records', ...more,
})
const TOP = page('top', Array.from({ length: 12 }, (_, i) => row(i + 1, i === 0 ? {
  price: { bhk: 2, from_inr: 9_500_000, to_inr: 9_630_000 }, photo: { url: '/uploads/p1.webp', alt: 'Towers', source: 'brochure' }, stage: 'possession-soon' } : {})), {
  sold_out: [row(0, { slug: 'aleria', name: 'Aleria Block B', promoter: 'Kolte-Patil', units_total: 27, units_booked: 27, units_open: 0 })], sold_out_count: 1,
})
const LISTS: Record<string, unknown> = {
  top: TOP,
  'new-launches': page('new-launches', [row(21, { stage: 'new-launch' }), row(22), row(23)]),
  'ready-to-move': page('ready-to-move', [row(31)]),   // one project: too few for a row of cards
  '2-bhk': null,
}
jest.mock('@/lib/site/facets', () => ({
  ...jest.requireActual('@/lib/site/facets'),
  getFacets: async () => [],
  getFacet: async (_place: string, segs: string[]) => LISTS[segs.join('/')] ?? null,
  getFacetQuiet: async (_place: string, segs: string[]) => LISTS[segs.join('/')] ?? null,
}))
jest.mock('@/lib/site/register', () => ({
  ...jest.requireActual('@/lib/site/register'),
  getRegisterPlaces: async () => [{ key: 'kharadi', slug: 'kharadi', name: 'Kharadi', zone: 'East Pune', projects: 68, indexable: 68 }],
}))

import FacetPageView from '@/app/projects/area/[place]/[...facet]/page'
import ProjectRail from '@/components/site/ProjectRail'

const params = Promise.resolve({ place: 'kharadi', facet: ['top'] })

describe('Top projects page', () => {
  it('shows the first ten as ranked cards with price or an ask, and the rest as plain rows', async () => {
    render(await FacetPageView({ params }))
    const cards = within(screen.getByTestId('facet-cards')).getAllByTestId('ranked-card')
    expect(cards).toHaveLength(10)
    expect(cards[0]).toHaveTextContent('2 BHK ₹95')
    expect(cards[0]).toHaveTextContent('Possession soon')
    expect(cards[0]).toHaveTextContent("Artist's impression")       // a brochure render says so
    expect(cards[0]).toHaveTextContent('20 homes open')
    expect(within(cards[0]).getByRole('link', { name: 'Ask about floor plans' })).toHaveAttribute('href', '/projects/p-1#enquire')
    expect(within(cards[1]).getByRole('link', { name: 'Get the price' })).toHaveAttribute('href', '/projects/p-2#enquire')
    expect(screen.getByRole('heading', { name: 'More projects with homes open (2)' })).toBeInTheDocument()
  })

  it('lists sold out projects apart with a resale ask, and rows of cards only for lists with three or more', async () => {
    render(await FacetPageView({ params }))
    const sold = screen.getByTestId('facet-sold-out')
    expect(sold).toHaveTextContent('Sold out or nearly: 1 project')
    expect(within(sold).getByRole('link', { name: 'Ask about resale' })).toHaveAttribute('href', '/projects/aleria#enquire')
    expect(screen.getByTestId('rail-launches')).toHaveTextContent('See all 3')
    // a row never rolls by itself; on a phone it says to swipe and ends in a card to the whole list
    expect(screen.getByTestId('rail-launches')).toHaveTextContent('Swipe for more')
    expect(within(screen.getByTestId('rail-launches')).getByRole('link', { name: 'See all 3 →' })).toHaveAttribute('href', '/projects/area/kharadi/new-launches')
    expect(screen.queryByTestId('rail-ready')).toBeNull()
    expect(screen.queryByTestId('rail-two-bhk')).toBeNull()
    expect(screen.getByText(/Why is a fully booked project in Kharadi not on this list\?/)).toBeInTheDocument()
  })
})

describe('ProjectRail', () => {
  it('numbers ranked cards and hides itself under three', () => {
    const rows = [row(1), row(2), row(3)] as never[]
    const { rerender } = render(<ProjectRail id="x" title="Top" href="/projects/area/kharadi/top" count={12} rows={rows} ranked />)
    expect(screen.getAllByText(/^Rank/)).toHaveLength(3)
    expect(screen.getByRole('link', { name: 'See all 12' })).toHaveAttribute('href', '/projects/area/kharadi/top')
    rerender(<ProjectRail id="x" title="Top" href="/x" count={2} rows={rows.slice(0, 2)} />)
    expect(screen.queryByTestId('rail-x')).toBeNull()
  })
})
