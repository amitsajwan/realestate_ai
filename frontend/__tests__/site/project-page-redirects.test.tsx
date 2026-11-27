import React from 'react'

const mockCatalog = jest.fn()
const mockRegister = jest.fn()
jest.mock('@/lib/site/api', () => ({
  getCatalog: () => mockCatalog(),
  getCatalogProject: async () => null,
  getPropertyFacts: async () => null,
}))
jest.mock('@/lib/site/register', () => ({ getRegisterProject: (s: string) => mockRegister(s), getRegisterPlaces: async () => [], longDay: () => '' }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('@/components/site/RegisterProjectPage', () => ({ __esModule: true, default: () => <p>register page</p> }))
jest.mock('next/navigation', () => ({
  notFound: () => { throw new Error('NOT_FOUND') },
  permanentRedirect: (u: string) => { throw new Error('REDIRECT ' + u) },
}))

import SharedProjectPage from '@/app/projects/[slug]/page'

// the register answers a tower's or an old address with the project's page, whose own address differs
const CAMELOT = { slug: 'kharadi-new-project-tower-1-wagholi', regno: 'PR1', name: 'Kharadi New Project - Tower 1', area: null, paragraph: 'x',
  indexable: true, towers: [{ regno: 'PR5' }] }
const page = (slug: string) => SharedProjectPage({ params: Promise.resolve({ slug }) })

describe('a project reached by an old or a tower address (docs/plan/one-project-one-page.md 1d)', () => {
  it('goes straight to the page an agent lists it on, in one redirect, never through the project page first', async () => {
    mockCatalog.mockResolvedValue([{ slug: 'lodha-camelot', rera_no: 'PR5', agents: [{ slug: 'house-deal' }] }])
    mockRegister.mockResolvedValue(CAMELOT)
    await expect(page('kharadi-new-project-tower-5-wagholi')).rejects.toThrow('REDIRECT /projects/lodha-camelot')
    await expect(page('kharadi-new-project-tower-1-wagholi')).rejects.toThrow('REDIRECT /projects/lodha-camelot')
  })

  it('goes to the project page when no agent lists it', async () => {
    mockCatalog.mockResolvedValue([])
    mockRegister.mockResolvedValue(CAMELOT)
    await expect(page('kharadi-new-project-tower-5-wagholi')).rejects.toThrow('REDIRECT /projects/kharadi-new-project-tower-1-wagholi')
  })
})
