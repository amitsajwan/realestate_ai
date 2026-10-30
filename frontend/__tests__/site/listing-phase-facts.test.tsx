import React from 'react'

const mockFacts = jest.fn(async (_q: Record<string, unknown>) => null)
jest.mock('@/lib/site/api', () => ({
  getAgent: async () => ({ slug: 'house-deal', agent_name: 'Sharad', branding_data: { business_name: 'House Deal' } }),
  getListing: async () => ({ id: 'l2', status: 'live', transaction: 'sale', property_type: 'apartment', title: 'VJ Yashwin Enchante',
    project_name: 'VJ Yashwin Enchante', locality: 'Upper Kharadi', rera_no: 'P52100077455', media: [], amenities: [], description: {} }),
  getListings: async () => ({ items: [] }),
  getCatalog: async () => [],
  getPropertyFacts: (q: Record<string, unknown>) => mockFacts(q),
}))
// MahaRERA files the project in two phases; our page is one, under phase 1's number, with phase 2 as a tower
jest.mock('@/lib/site/register', () => ({
  getRegisterProjectByRegno: async () => ({ slug: 'yashwin-enchante-phase-1-wagholi', regno: 'P52100046510',
    towers: [{ regno: 'P52100046510' }, { regno: 'P52100077455' }] }),
}))
jest.mock('@/components/site/RegisterProjectPage', () => ({ __esModule: true, default: () => null }))
jest.mock('@/components/site/SiteShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('@/components/site/TrackingBeacon', () => ({ __esModule: true, default: () => null }))
jest.mock('@/app/agent/[slug]/DemoRibbon', () => ({ __esModule: true, default: () => null }))

import ListingPage from '@/app/agent/[slug]/listings/[id]/page'

it("a phase 2 listing on a merged project page reads its own sheet and pictures, by phase 2's number", async () => {
  await ListingPage({ params: Promise.resolve({ slug: 'house-deal', id: 'l2' }) })
  expect(mockFacts).toHaveBeenCalledWith(expect.objectContaining({ rera: 'P52100077455', listing: 'l2' }))
})
