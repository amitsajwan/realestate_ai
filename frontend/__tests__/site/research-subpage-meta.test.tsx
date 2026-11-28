// A place research page (/projects/area/<place>/schools, /commute, /rent) is in search only when the backend's page flag is true,
// and is a 404 without research (components/site/research/PlaceResearchPage)
jest.mock('@/components/marketing/MarketingShell', () => ({ __esModule: true, default: ({ children }: { children: unknown }) => children }))
jest.mock('@/lib/site/register', () => ({
  ...jest.requireActual('@/lib/site/register'),
  getRegisterPlacesOrThrow: async () => [{ key: 'wagholi', slug: 'wagholi', name: 'Wagholi', zone: 'East Pune', projects: 90, indexable: 40 }],
}))
import { loadResearch, researchMetadata } from '@/components/site/research/PlaceResearchPage'

const RENT = { sources: [], updated: '2026-11-15', month: '2026-11', rows: [{ bhk: '2 BHK', low: 22000, median: 26000, high: 30000, listings: 41 }] }
const SCHOOLS = { sources: [], updated: '2026-11-18', schools: [{ name: 'A', board: 'CBSE', km: 1 }], total_within_km: { km: 3, count: 1, by_board: { CBSE: 1 } } }
const answer = (status: number, body: unknown = {}) => {
  global.fetch = jest.fn(async () => ({ status, ok: status < 400, json: async () => body })) as unknown as typeof fetch
}
const params = (place: string) => Promise.resolve({ place })

test('noindex while the page flag is false, indexed with its own canonical once true', async () => {
  answer(200, { place: 'wagholi', blocks: { rent: RENT, schools: SCHOOLS }, changes: [], pages: { schools: true, commute: false, rent: false } })
  const rent = await researchMetadata('rent', params('wagholi'))
  expect(rent.robots).toEqual({ index: false, follow: true })
  expect(rent.title).toBe('Rent in Wagholi, Pune (Nov 2026): 2 BHK asked rent')
  const schools = await researchMetadata('schools', params('wagholi'))
  expect(schools.robots).toBeUndefined()
  expect(schools.alternates?.canonical).toMatch(/\/projects\/area\/wagholi\/schools$/)
})

test('no research, no block of that kind, or an unknown place is not found; an outage is an error, never a 404', async () => {
  answer(404)
  expect(await loadResearch('rent', params('wagholi'))).toBeNull()
  answer(200, { place: 'wagholi', blocks: { rent: RENT }, pages: { rent: true } })
  expect(await loadResearch('commute', params('wagholi'))).toBeNull()
  expect(await loadResearch('rent', params('nowhere'))).toBeNull()
  answer(503)
  await expect(loadResearch('rent', params('wagholi'))).rejects.toThrow(/temporarily unavailable/)
})
