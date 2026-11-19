/** Demo mode answers every owner screen from fixtures-owner.ts without a server, so no owner screen shows a server error. */
import { getEnrichment } from '@/lib/app/enrichment'
import { getAudit, getFound, getGrownPages, getHot, getRankings, getSystem, revertPage } from '@/lib/app/insights'
import { boardApi } from '@/lib/app/leadBoard'
import { pressApi } from '@/lib/app/press'
import { radarApi } from '@/lib/app/radar'

const fetchSpy = jest.fn(() => { throw new Error('no network in demo mode') })

beforeEach(() => {
  window.localStorage.clear()
  window.localStorage.setItem('app_fixtures', '1')
  fetchSpy.mockClear()
  ;(global as { fetch?: unknown }).fetch = fetchSpy
})

it('SEO: every tab has numbers, the scoreboard included', async () => {
  const r = await getRankings()
  expect(r.week.now?.clicks).toBeGreaterThan(0)
  expect(r.scoreboard?.at).toBeTruthy()
  expect(r.targets.length).toBeGreaterThan(0)
  expect((await getAudit()).rows.length).toBeGreaterThan(0)
  expect((await getAudit(true)).configured).toBe(true)
  expect((await getHot()).items.length).toBeGreaterThan(0)
  expect((await getFound()).items.length).toBeGreaterThan(0)
  expect((await getSystem()).loops.length).toBeGreaterThan(0)
  expect((await getGrownPages()).live.length).toBeGreaterThan(0)
  expect(await revertPage('/projects/x')).toEqual({ reverted: 1 })
  expect(fetchSpy).not.toHaveBeenCalled()
})

it('project pages filter by status', async () => {
  expect((await getEnrichment()).items).toHaveLength(4)
  expect((await getEnrichment('failed')).items.map((i) => i.status)).toEqual(['failed'])
})

it('buyer radar, press and the lead board answer, and a pitch edit sticks', async () => {
  expect((await radarApi.signals()).length).toBeGreaterThan(0)
  expect((await radarApi.metrics()).llm_today).toBeGreaterThanOrEqual(0)
  expect(await radarApi.followups()).toEqual([])
  expect((await radarApi.watches()).length).toBeGreaterThan(0)
  expect((await pressApi.story()).facts.length).toBeGreaterThan(0)
  const [p] = await pressApi.pitches()
  expect((await pressApi.patch(p.id, { status: 'sent' })).status).toBe('sent')
  expect((await pressApi.summary()).sent).toBe(1)
  const b = await boardApi.get()
  expect(b.owner).toBe(true)
  expect(b.items[0].lead_id).toBeTruthy()
  expect(fetchSpy).not.toHaveBeenCalled()
})

it('the lead board is an agent\'s view when demo mode plays an agent', async () => {
  window.localStorage.setItem('app_fixture_agent', '1')
  const b = await boardApi.get()
  expect(b.owner).toBe(false)
  expect(b.items.every((c) => c.lead_id === undefined)).toBe(true)
})
