import { getCatalog } from '@/lib/site/api'
import { projectPageOfListing } from '@/lib/site/register'

jest.mock('@/lib/site/api', () => ({ ...jest.requireActual('@/lib/site/api'), getCatalog: jest.fn() }))

const page = (over: object) => ({ slug: 'kharadi-new-project-tower-1', regno: 'PR1260002501386', indexable: true, towers: [], ...over })

function register(p: object) {
  global.fetch = jest.fn(async (url: string) => {
    const body = String(url).includes('/by-regno/') ? { slug: 'kharadi-new-project-tower-1' } : p
    return { ok: true, status: 200, json: async () => body, text: async () => JSON.stringify(body) }
  }) as never
}

test('a listing names the shared page its project redirects to, not the redirect', async () => {
  register(page({}))
  jest.mocked(getCatalog).mockResolvedValue([{ slug: 'lodha-camelot', rera_no: 'PR1260002501386', agents: [{ slug: 'house-deal' }] }] as never)
  expect(await projectPageOfListing('PR1260002501386')).toBe('lodha-camelot')
})

test('any tower of the project finds the shared page', async () => {
  register(page({ towers: [{ regno: 'P52100000002' }] }))
  jest.mocked(getCatalog).mockResolvedValue([{ slug: 'lodha-camelot', rera_no: 'P52100000002', agents: [{ slug: 'house-deal' }] }] as never)
  expect(await projectPageOfListing('PR1260002501386')).toBe('lodha-camelot')
})

test('a project with no shared page keeps its own page, and one out of search names none', async () => {
  register(page({}))
  jest.mocked(getCatalog).mockResolvedValue([])
  expect(await projectPageOfListing('PR1260002501386')).toBe('kharadi-new-project-tower-1')
  register(page({ indexable: false }))
  expect(await projectPageOfListing('PR1260002501386')).toBeNull()
})
