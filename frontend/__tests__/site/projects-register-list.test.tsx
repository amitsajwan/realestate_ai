import { render, screen, within } from '@testing-library/react'
import React from 'react'

const HD_LISTING = {
  id: 'l1', status: 'live', transaction: 'sale', property_type: 'apartment', title: 'Kolte-Patil Springshire', project_name: 'Springshire',
  price_inr: 8_400_000, locality: 'Wagholi', bhk: 2, rera_no: 'P2', media: [], amenities: [], description: {}, video_count: 1,
  configurations: [{ bhk: 2, carpet_sqft: 700, price_inr: 8_400_000 }, { bhk: 3, carpet_sqft: 950, price_inr: 11_200_000 }],
}
jest.mock('@/lib/site/api', () => ({
  getSitemapEntries: async () => ({ listings: [{ agent_slug: 'house-deal', id: 'l1', rera_no: 'P2' }], projects: [] }),
  getAgent: async () => ({ slug: 'house-deal', agent_name: 'Sharad', branding_data: { business_name: 'House Deal' } }),
  getListings: async () => ({ items: [HD_LISTING], total: 1 }),
}))
jest.mock('@/lib/site/hubs', () => ({ getAreaMap: async () => null }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('@/components/site/EnquiryForm', () => ({ __esModule: true, default: () => null }))
const mockSearch = jest.fn(async (_q: string) => [{ slug: 'gera-world-of-joy', name: 'Geras World of Joy M', marketed_name: 'Gera World of Joy', regno: 'P9',
  promoter: 'Gera', completion_now: '2029-03-31', units_total: 400, units_booked: 120 }])
jest.mock('@/lib/site/register', () => {
  const actual = jest.requireActual('@/lib/site/register')
  return {
    ...actual,
    getRegisterProjects: async () => [
      { slug: 'titan-tower-kharadi', regno: 'P3', name: 'TITAN TOWER', area: 'kharadi', completion_now: '2030-06-30', listed_or_updated: null, indexable: true,
        units_total: 100, units_booked: 10, homes: [{ bhk: '2 BHK', from_inr: 9_000_000 }], months_later: 0 },
      { slug: 'springshire-wagholi', regno: 'P2', name: 'SPRINGSHIRE', marketed_name: 'Springshire', promoter: 'Kolte', area: 'wagholi', completion_now: '2028-06-30',
        units_total: 200, units_booked: 50, listed_or_updated: null, indexable: true, months_later: 3 },
      { slug: 'old-finished-wagholi', regno: 'P4', name: 'OLD', area: 'wagholi', completion_now: '2020-01-01', listed_or_updated: null, indexable: true, active: false },
    ],
    getRegisterPlaces: async () => [{ key: 'wagholi', slug: 'wagholi', name: 'Wagholi', zone: 'East', projects: 2, indexable: 2 }],
    searchRegister: (q: string) => mockSearch(q),
  }
})

import ProjectsPage from '@/app/projects/page'

describe('/projects: the home finder over our areas', () => {
  it("lists every project by area, an agent-listed one first with the agent's sheet, photo badge and video", async () => {
    render(await ProjectsPage({}))
    const finder = screen.getByTestId('home-finder')
    expect(within(finder).getByTestId('finder-summary')).toHaveTextContent('2 projects')   // the finished one is left out
    const cards = within(finder).getAllByTestId('finder-card')
    expect(cards[0]).toHaveTextContent('Springshire')
    expect(cards[0]).toHaveTextContent('Through House Deal')
    expect(cards[0]).toHaveTextContent('2 & 3 BHK · from ₹84 L')
    expect(cards[0]).toHaveTextContent('▶ Video')
    expect(within(cards[0]).getAllByRole('link', { name: 'Springshire' })[0]).toHaveAttribute('href', '/projects/springshire-wagholi')
    expect(screen.getByText(/1 older, finished projects are left out/)).toBeInTheDocument()
    expect(mockSearch).not.toHaveBeenCalled()
  })

  it("answers a shared link: 3 BHK finds the agent's 3 BHK row and names it", async () => {
    render(await ProjectsPage({ searchParams: Promise.resolve({ bhk: '3' }) }))
    const cards = screen.getAllByTestId('finder-card')
    expect(cards).toHaveLength(1)
    expect(within(cards[0]).getByTestId('fit')).toHaveTextContent('3 BHK · 950 sq.ft · ₹1.12 Cr')
    // the view goes out on WhatsApp as one message with its link
    const send = within(screen.getByTestId('finder-share')).getByRole('link', { name: /Send this on WhatsApp/ })
    const text = decodeURIComponent(send.getAttribute('href')!.replace('https://wa.me/?text=', ''))
    expect(text).toContain('1 home for 3 BHK from Avasetu:')
    expect(text).toContain('1. Springshire, Wagholi: 3 BHK, 950 sq.ft, ₹1.12 Cr')
    expect(text).toMatch(/\/projects\?bhk=3&src=share#find$/)
  })

  it('answers ?q= on the server (the search box without JavaScript), by marketed name', async () => {
    render(await ProjectsPage({ searchParams: Promise.resolve({ q: 'gera world' }) }))
    expect(mockSearch).toHaveBeenCalledWith('gera world')
    const results = within(screen.getByTestId('project-search-results'))
    expect(results.getByText('Gera World of Joy')).toBeInTheDocument()
    expect(screen.getByRole('searchbox')).toHaveValue('gera world')
  })
})
