import { render, screen, within } from '@testing-library/react'
import React from 'react'

jest.mock('@/lib/site/api', () => ({
  getCatalog: async () => [{ slug: 'rohan-abhilasha', rera_no: 'P1', locality: 'Wagholi', name: 'Rohan Abhilasha 4', agents: [{ slug: 'house-deal' }] }],
}))
jest.mock('@/lib/site/projects', () => ({ byLocality: () => [] }))
jest.mock('@/components/site/ProjectCard', () => ({ __esModule: true, default: () => null }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('@/lib/site/register', () => ({
  getRegisterProjects: async () => [
    { slug: 'springshire-wagholi', regno: 'P2', name: 'SPRINGSHIRE', area: 'wagholi', completion_now: '2028-06-30', listed_or_updated: null, indexable: true },
    { slug: 'rohan-abhilasha-4-phase-1-wagholi', regno: 'P1', name: 'Rohan Abhilasha 4 Phase 1', area: 'wagholi', completion_now: '2029-10-30', listed_or_updated: null, indexable: true },
    { slug: 'titan-tower-kharadi', regno: 'P3', name: 'TITAN TOWER', area: 'kharadi', completion_now: null, listed_or_updated: null, indexable: true },
  ],
}))

import ProjectsPage from '@/app/projects/page'

describe('/projects lists every MahaRERA project page, by area', () => {
  it('groups by area, links our pages, and leaves out projects an agent already lists', async () => {
    render(await ProjectsPage())
    expect(screen.getByRole('heading', { name: 'Every MahaRERA project in our areas' })).toBeInTheDocument()
    const wagholi = within(screen.getByTestId('register-wagholi'))
    expect(wagholi.getByRole('link', { name: 'SPRINGSHIRE' })).toHaveAttribute('href', '/projects/springshire-wagholi')
    expect(wagholi.queryByText(/Rohan Abhilasha 4 Phase 1/)).toBeNull()   // shown above, with its agents
    expect(wagholi.getByText(/completion filed 2028/)).toBeInTheDocument()
    expect(within(screen.getByTestId('register-kharadi')).getByRole('link', { name: 'TITAN TOWER' })).toHaveAttribute('href', '/projects/titan-tower-kharadi')
    expect(screen.getByText(/2 projects so far/)).toBeInTheDocument()
  })
})
