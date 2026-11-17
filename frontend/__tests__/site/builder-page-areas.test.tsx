import { render, screen } from '@testing-library/react'
import React from 'react'

// A builder's page names the areas it builds in: each opens that area's project list where we have one.
const mockBuilder = jest.fn()
jest.mock('@/lib/site/hubs', () => ({ getBuilder: (s: string) => mockBuilder(s) }))
jest.mock('@/lib/site/register', () => ({
  ...jest.requireActual('@/lib/site/register'),
  getRegisterPlaces: async () => [
    { key: 'kharadi', slug: 'kharadi', name: 'Kharadi', zone: 'East Pune', projects: 40, indexable: 30 },
    { key: 'baner', slug: 'baner', name: 'Baner', zone: 'West Pune', projects: 0, indexable: 0 },
  ],
}))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('next/navigation', () => ({ notFound: () => { throw new Error('NOT_FOUND') }, permanentRedirect: jest.fn() }))

import BuilderPageView from '@/app/builders/[slug]/page'

const B = {
  slug: 'kolte-patil', name: 'Kolte-Patil', projects_count: 3, areas: ['Baner', 'Kharadi', 'Wagholi'], active: 2,
  units_total: 900, units_booked: 600, with_dates: 2, moved_later: 0, avg_months_later: null, record_ok: false, moved_min: 3,
  brand: false, companies: [], projects: [],
}

it("links each of the builder's areas to its project list, and leaves an area without one as text", async () => {
  mockBuilder.mockResolvedValue(B)
  render(await BuilderPageView({ params: Promise.resolve({ slug: 'kolte-patil' }) }))
  const line = screen.getByText(/Our MahaRERA register holds 3 Pune projects/)
  expect(line).toHaveTextContent('in Baner, Kharadi, Wagholi; 2 still being built')
  expect(screen.getByRole('link', { name: 'Kharadi' })).toHaveAttribute('href', '/projects/area/kharadi')
  expect(screen.queryByRole('link', { name: 'Baner' })).toBeNull()     // no projects listed there: no page to open
  expect(screen.queryByRole('link', { name: 'Wagholi' })).toBeNull()   // not a place we list
})
