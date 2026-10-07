import React from 'react'

const mockCatalogProject = jest.fn()
const mockRegister = jest.fn()
jest.mock('@/lib/site/api', () => ({
  getCatalog: async () => [],
  getCatalogProject: (s: string) => mockCatalogProject(s),
  getPropertyFacts: async () => null,
}))
jest.mock('@/lib/site/register', () => ({ getRegisterProject: (s: string) => mockRegister(s), longDay: () => '' }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('@/components/site/RegisterProjectPage', () => ({ __esModule: true, default: () => <p>register page</p> }))
jest.mock('next/navigation', () => ({
  notFound: () => { throw new Error('NOT_FOUND') },
  permanentRedirect: (u: string) => { throw new Error('REDIRECT ' + u) },
}))

import SharedProjectPage from '@/app/projects/[slug]/page'

const REG = { slug: 'ivy-estate-nia-wagholi', regno: 'P1', name: 'Ivy', area: null, paragraph: 'x', indexable: true }

describe('project page when the agent catalog is briefly unreachable', () => {
  it('still shows our register page', async () => {
    mockCatalogProject.mockRejectedValue(new Error('Agent site data is temporarily unavailable'))
    mockRegister.mockResolvedValue(REG)
    const el = await SharedProjectPage({ params: Promise.resolve({ slug: 'ivy-estate-nia-wagholi' }) })
    expect(el).toBeTruthy()
  })

  it('keeps the temporary error (never a 404) when neither can be read', async () => {
    mockCatalogProject.mockRejectedValue(new Error('Agent site data is temporarily unavailable'))
    mockRegister.mockResolvedValue(null)
    await expect(SharedProjectPage({ params: Promise.resolve({ slug: 'ivy-estate-nia-wagholi' }) })).rejects.toThrow('temporarily unavailable')
  })
})
