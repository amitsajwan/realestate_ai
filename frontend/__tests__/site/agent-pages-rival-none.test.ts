/* An agent's page is in search only where no page of ours is the answer (owner 2026-11-07: "they should not compete with internal ones"). */
import { getCatalog, getSitemapEntries } from '@/lib/site/api'
import { projectForListing } from '@/lib/site/listingProject'
import { buildSitemap } from '@/lib/site/sitemap'
import { getRegisterProjects, projectPageOfListing as sitemapLookup } from '@/lib/site/register'
import type { CatalogProject } from '@/lib/site/types'

jest.mock('@/lib/site/api', () => ({ ...jest.requireActual('@/lib/site/api'), getCatalog: jest.fn(), getSitemapEntries: jest.fn() }))
jest.mock('@/lib/site/register', () => ({
  ...jest.requireActual('@/lib/site/register'),
  getRegisterProjects: jest.fn(), getRegisterPlaces: jest.fn(async () => [{ key: 'kharadi', slug: 'kharadi', name: 'Kharadi', indexable: 1 }]),
  projectPageOfListing: jest.fn(async () => null),
}))
jest.mock('@/lib/site/facets', () => ({ getFacets: jest.fn(async () => []), withoutMovedSizePages: () => [] }))
jest.mock('@/lib/site/topics', () => ({ fetchTopics: jest.fn(async () => []), topicPath: (s: string) => s }))
jest.mock('@/lib/site/filters', () => ({ livePages: () => [] }))
jest.mock('@/lib/site/hubs', () => ({ getBuilders: jest.fn(async () => []) }))
jest.mock('@/lib/news/data', () => ({ fetchNews: jest.fn(async () => ({ items: [] })) }))
jest.mock('@/lib/news/trackers', () => ({ fetchTrackers: jest.fn(async () => []), trackerPath: (s: string) => s }))

const camelot = { slug: 'lodha-camelot', name: 'Lodha Camelot', rera_no: 'PR1', locality: 'Kharadi', agents: [{ slug: 'house-deal', project_slug: 'lodha-camelot' }] } as unknown as CatalogProject

const agentUrls = async () => (await buildSitemap()).filter((g) => g.group === 'agents').map((g) => new URL(g.entry.url).pathname)

beforeEach(() => {
  jest.mocked(getCatalog).mockResolvedValue([camelot])
  jest.mocked(getRegisterProjects).mockResolvedValue([{ regno: 'P5', slug: 'in-search', indexable: true }, { regno: 'P6', slug: 'thin', indexable: false }] as never)
  jest.mocked(sitemapLookup).mockResolvedValue(null)
})

test('a listing with no number finds its project by name, by the project slug and not at all', () => {
  expect(projectForListing({ project_name: 'lodha  CAMELOT' }, [camelot])?.slug).toBe('lodha-camelot')
  expect(projectForListing({ about: { project_name: 'Lodha Camelot' } as never }, [camelot])?.slug).toBe('lodha-camelot')
  expect(projectForListing({ project_name: 'VTP Never Before' }, [camelot])).toBeNull()
})

test("the sitemap leaves out every agent page that names a project's page, and keeps the ones with no rival", async () => {
  jest.mocked(getSitemapEntries).mockResolvedValue({
    listings: [
      { agent_slug: 'a', id: 'by-number', rera_no: 'P5' },
      { agent_slug: 'a', id: 'by-name', project_name: 'Lodha Camelot' },   // no number: the page shows Camelot's page
      { agent_slug: 'a', id: 'thin-project', rera_no: 'P6' },              // that project is out of search, so the listing stands
      { agent_slug: 'a', id: 'no-project', project_name: 'VTP Never Before' },
    ],
    projects: [
      { agent_slug: 'a', slug: 'own-copy', rera_no: 'P5' },                // not on a shared page, but the project is in search
      { agent_slug: 'a', slug: 'stands-alone', rera_no: 'P6' },
      { agent_slug: 'house-deal', slug: 'lodha-camelot', rera_no: 'PR1' }, // the shared page's own copy
    ],
  })
  // the name's number is not in the register list (a tower merged into its project), so it is looked up as the page does
  jest.mocked(sitemapLookup).mockImplementation(async (r) => (r === 'PR1' ? 'lodha-camelot' : null))
  expect((await agentUrls()).sort()).toEqual([
    '/agent/a', '/agent/a/listings/no-project', '/agent/a/listings/thin-project', '/agent/a/projects/stands-alone', '/agent/house-deal',
  ])
})
