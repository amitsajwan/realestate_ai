import { render, screen, within } from '@testing-library/react'
import React from 'react'

jest.mock('@/lib/site/api', () => ({
  getCatalog: async () => [{ slug: 'rohan-abhilasha', rera_no: 'P1', locality: 'Wagholi', name: 'Rohan Abhilasha 4', agents: [{ slug: 'house-deal' }] }],
}))
jest.mock('@/lib/site/projects', () => ({ byLocality: () => [] }))
jest.mock('@/components/site/ProjectCard', () => ({ __esModule: true, default: () => null }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
const mockSearch = jest.fn(async (_q: string) => [{ slug: 'gera-world-of-joy', name: 'Geras World of Joy M', marketed_name: 'Gera World of Joy', regno: 'P9',
  promoter: 'Gera', completion_now: '2029-03-31', units_total: 400, units_booked: 120 }])
jest.mock('@/lib/site/register', () => {
  const actual = jest.requireActual('@/lib/site/register')
  return {
    ...actual,
    getRegisterProjects: async () => [
      { slug: 'springshire-wagholi', regno: 'P2', name: 'SPRINGSHIRE', marketed_name: 'Springshire', promoter: 'Kolte', area: 'wagholi', completion_now: '2028-06-30',
        units_total: 200, units_booked: 50, listed_or_updated: null, indexable: true },
      { slug: 'rohan-abhilasha-4-phase-1-wagholi', regno: 'P1', name: 'Rohan Abhilasha 4 Phase 1', area: 'wagholi', completion_now: '2029-10-30', listed_or_updated: null, indexable: true },
      { slug: 'titan-tower-kharadi', regno: 'P3', name: 'TITAN TOWER', area: 'kharadi', completion_now: null, listed_or_updated: null, indexable: true },
    ],
    getRegisterPlaces: async () => [{ key: 'wagholi', slug: 'wagholi', name: 'Wagholi', zone: 'East', projects: 2, indexable: 2 }],
    searchRegister: (q: string) => mockSearch(q),
  }
})

import ProjectsPage from '@/app/projects/page'

describe('/projects lists every MahaRERA project page, by area', () => {
  it('groups by area with a summary line, links the area hub, and leaves out projects an agent already lists', async () => {
    render(await ProjectsPage())
    expect(screen.getByRole('heading', { name: 'Every MahaRERA project in our areas' })).toBeInTheDocument()
    const wagholi = within(screen.getByTestId('register-wagholi'))
    expect(wagholi.getByRole('link', { name: 'Springshire' })).toHaveAttribute('href', '/projects/springshire-wagholi')
    expect(wagholi.queryByText(/Rohan Abhilasha 4 Phase 1/)).toBeNull()   // shown above, with its agents
    expect(wagholi.getByText('by Kolte · possession Jun 2028 · 50/200 booked')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /All 1 projects in Wagholi/ })).toHaveAttribute('href', '/projects/area/wagholi')
    expect(within(screen.getByTestId('register-kharadi')).getByRole('link', { name: 'TITAN TOWER' })).toHaveAttribute('href', '/projects/titan-tower-kharadi')
    expect(mockSearch).not.toHaveBeenCalled()
  })

  it('answers ?q= on the server (the search box without JavaScript), by marketed name', async () => {
    render(await ProjectsPage({ searchParams: Promise.resolve({ q: 'gera world' }) }))
    expect(mockSearch).toHaveBeenCalledWith('gera world')
    const results = within(screen.getByTestId('project-search-results'))
    expect(results.getByText('Gera World of Joy')).toBeInTheDocument()
    expect(screen.getByRole('searchbox')).toHaveValue('gera world')
  })
})
