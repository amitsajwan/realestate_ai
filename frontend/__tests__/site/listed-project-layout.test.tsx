// Every project page has one layout (docs/plan/one-project-one-page.md 1e): a project an agent lists in the catalog (Lodha
// Camelot at /projects/lodha-camelot) is drawn from its register record like any other project, at its listed address.
import React from 'react'

const mockCatalogProject = jest.fn()
jest.mock('@/lib/site/api', () => ({
  PAGE_DATA_MS: 5000,
  serverApiBase: () => 'http://api',
  getCatalog: async () => [],
  getCatalogProject: (s: string) => mockCatalogProject(s),
  getPropertyFacts: async () => null,
}))
jest.mock('@/components/site/RegisterProjectPage', () => ({ __esModule: true, ASK_NOTE: '', default: () => null }))
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: React.ReactNode }) => <div>{children}</div> }))
jest.mock('@/lib/site/facets', () => ({ getFacets: async () => [] }))
jest.mock('next/navigation', () => ({
  notFound: () => { throw new Error('NOT_FOUND') },
  permanentRedirect: (u: string) => { throw new Error('REDIRECT ' + u) },
}))

import SharedProjectPage, { generateMetadata } from '@/app/projects/[slug]/page'
import { getPageRegister, registerOfListing } from '@/lib/site/register'
import type { CatalogProject } from '@/lib/site/types'

const LISTED = { slug: 'lodha-camelot', name: 'Lodha Camelot', rera_no: 'PR1260002501386', agents: [{ slug: 'house-deal', name: 'House Deal' }] } as unknown as CatalogProject
const RECORD = { slug: 'kharadi-new-project-tower-1-wagholi', regno: 'PR1260002501386', name: 'Kharadi New Project - Tower 1',
  marketed_name: 'Lodha Camelot', area: null, paragraph: 'x', indexable: false, towers: [] }

// the register API: the MahaRERA number names the record's slug, the slug gives the record; nothing else is known
let registerUp = true
beforeEach(() => {
  registerUp = true
  mockCatalogProject.mockImplementation(async (s: string) => (s === LISTED.slug ? LISTED : null))
  global.fetch = jest.fn(async (url: string) => {
    const path = String(url).replace('http://api', '')
    const json = (status: number, body: unknown) => ({ ok: status === 200, status, json: async () => body }) as Response
    if (!registerUp) return json(503, {})
    if (path === '/api/v1/public/register/by-regno/PR1260002501386') return json(200, { slug: RECORD.slug })
    if (path === '/api/v1/public/register/projects/' + RECORD.slug) return json(200, RECORD)
    return json(404, {})
  }) as unknown as typeof fetch
})

/** The project the page hands RegisterProjectPage: the page returns <RegisterView>, run here to reach its children. */
const drawn = async (slug: string): Promise<Record<string, unknown> | null> => {
  const view = (await SharedProjectPage({ params: Promise.resolve({ slug }) })) as React.ReactElement<{ r: unknown }>
  if (typeof view.type !== 'function' || !('r' in (view.props as object))) return null   // the catalog layout
  const shell = await (view.type as (p: { r: unknown }) => Promise<React.ReactElement<{ children: React.ReactNode }>>)(view.props)
  const page = React.Children.toArray(shell.props.children).find((c) => React.isValidElement(c) && 'p' in (c.props as object))
  return page ? ((page as React.ReactElement<{ p: Record<string, unknown> }>).props.p) : null
}

describe('an agent-listed project page', () => {
  it('is drawn from its register record at its listed address, not the old catalog layout', async () => {
    expect(await drawn('lodha-camelot')).toMatchObject({ slug: 'lodha-camelot', regno: 'PR1260002501386', marketed_name: 'Lodha Camelot' })
  })

  it('keeps its listed address as canonical and stays in search, even when the register calls the record thin', async () => {
    const md = await generateMetadata({ params: Promise.resolve({ slug: 'lodha-camelot' }) })
    expect(String(md.alternates?.canonical)).toMatch(/\/projects\/lodha-camelot$/)
    expect(md.robots).toBeUndefined()
  })

  it('finds no register record when the register cannot be read, so the catalog layout still serves the page', async () => {
    registerUp = false
    await expect(registerOfListing(LISTED)).resolves.toBeNull()
  }, 20_000)   // the register read retries a down API for a few seconds first
})

describe('a slug the sub-pages and picks are given', () => {
  it('reads a listed slug as its register record, which keeps the register slug the video sitemap names', async () => {
    await expect(getPageRegister('lodha-camelot')).resolves.toMatchObject({ slug: RECORD.slug })
    await expect(getPageRegister(RECORD.slug)).resolves.toMatchObject({ slug: RECORD.slug })
    await expect(getPageRegister('no-such-project')).resolves.toBeNull()
  })
})
