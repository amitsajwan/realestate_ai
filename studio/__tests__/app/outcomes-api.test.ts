import { createApiClient } from '@/lib/app/api'
import { lostHint, outcomePatchError, outcomeSummary } from '@/lib/app/outcomes'

function fakeFetch(status: number, body: unknown) {
  return jest.fn(async () => ({
    ok: status >= 200 && status < 300,
    status,
    text: async () => JSON.stringify(body),
  })) as unknown as jest.MockedFunction<typeof fetch>
}
const call = (f: jest.MockedFunction<typeof fetch>) => f.mock.calls[0] as unknown as [string, RequestInit]
const client = (f: jest.MockedFunction<typeof fetch>) => createApiClient({ baseUrl: '', getToken: () => 'tok', fetchImpl: f })

describe('updateLead with an outcome', () => {
  it('PATCHes stage won with the deal price and listing, and returns suggest_listing_status', async () => {
    const body = { id: 'c1', stage: 'won', suggest_listing_status: { listing_id: 'l1', status: 'sold' } }
    const f = fakeFetch(200, body)
    const res = await client(f).updateLead('c1', { stage: 'won', outcome: { deal_price_inr: 8_500_000, listing_id: 'l1' } })
    const [url, init] = call(f)
    expect(url).toBe('/api/v1/inbox/leads/c1')
    expect(init.method).toBe('PATCH')
    expect(JSON.parse(init.body as string)).toEqual({ stage: 'won', outcome: { deal_price_inr: 8_500_000, listing_id: 'l1' } })
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer tok')
    expect(res.suggest_listing_status).toEqual({ listing_id: 'l1', status: 'sold' })
  })

  it('PATCHes stage lost with a reason', async () => {
    const f = fakeFetch(200, { id: 'c1' })
    await client(f).updateLead('c1', { stage: 'lost', outcome: { lost_reason: 'bought_elsewhere' } })
    expect(JSON.parse(call(f)[1].body as string)).toEqual({ stage: 'lost', outcome: { lost_reason: 'bought_elsewhere' } })
  })

  it('every existing call shape still sends exactly what it did before', async () => {
    const f1 = fakeFetch(200, {})
    await client(f1).updateLead('c1', 'won')
    expect(JSON.parse(call(f1)[1].body as string)).toEqual({ stage: 'won' })
    const f2 = fakeFetch(200, {})
    await client(f2).updateLead('c1', 'contacted', 'called')
    expect(JSON.parse(call(f2)[1].body as string)).toEqual({ stage: 'contacted', note: 'called' })
    const f3 = fakeFetch(200, {})
    await client(f3).updateLead('c1', { note: 'hello' })
    expect(JSON.parse(call(f3)[1].body as string)).toEqual({ note: 'hello' })
  })

  it('refuses locally, without a request, what the API would answer with 422', async () => {
    const cases: Array<Parameters<ReturnType<typeof client>['updateLead']>[1]> = [
      { outcome: { deal_price_inr: 100 } }, // no stage
      { stage: 'contacted', outcome: { lost_reason: 'price' } }, // wrong stage
      { stage: 'lost', outcome: { deal_price_inr: 100 } }, // won field with lost
      { stage: 'lost', outcome: { listing_id: 'l1' } },
      { stage: 'won', outcome: { lost_reason: 'price' } }, // lost field with won
      { stage: 'won', outcome: { deal_price_inr: 0 } }, // must be > 0
      { stage: 'won', outcome: { deal_price_inr: 85.5 } }, // integer
      { stage: 'won', outcome: { deal_price_inr: -5 } },
    ]
    for (const c of cases) {
      const f = fakeFetch(200, {})
      await expect(client(f).updateLead('c1', c)).rejects.toMatchObject({ status: 422 })
      expect(f).not.toHaveBeenCalled()
    }
    const f = fakeFetch(200, {})
    await expect(client(f).updateLead('c1', { stage: 'lost', outcome: { lost_reason: 'nope' as never } })).rejects.toMatchObject({ status: 422 })
  })

  it('surfaces the API 422 for a listing that is not the agent own', async () => {
    const f = fakeFetch(422, { detail: 'Unknown listing' })
    await expect(client(f).updateLead('c1', { stage: 'won', outcome: { listing_id: 'zz' } })).rejects.toMatchObject({
      status: 422,
      detail: 'Unknown listing',
    })
  })

  it('passes results and the new performance fields through untouched', async () => {
    const results = { period_days: 30, deals_won: 2, deal_value_inr: 17_000_000, deals_lost: 1, top_source: 'instagram', lost_reasons: { price: 1 } }
    const t = client(fakeFetch(200, { counts: {}, hot_buyers: [], follow_ups: [], headline: '', results }))
    expect((await t.getToday()).results).toEqual(results)
    const item = { listing_id: 'l1', deals: 2, deal_value_inr: 17_000_000, deals_by_source: { instagram: 2 } }
    expect(await client(fakeFetch(200, { items: [item] })).getPerformance()).toEqual([item])
  })
})

describe('outcome helpers', () => {
  it('outcomePatchError accepts valid bodies', () => {
    expect(outcomePatchError({ stage: 'won' })).toBeNull()
    expect(outcomePatchError({ stage: 'won', outcome: {} })).toBeNull()
    expect(outcomePatchError({ stage: 'won', outcome: { deal_price_inr: 1, listing_id: 'l1' } })).toBeNull()
    expect(outcomePatchError({ stage: 'lost', outcome: { lost_reason: 'other' } })).toBeNull()
  })

  it('outcomeSummary reads like a sentence', () => {
    const won = { result: 'won' as const, deal_price_inr: 8_500_000, listing_id: 'l1', lost_reason: null, closed_at: '' }
    expect(outcomeSummary(won, '2 BHK in Baner')).toBe('Won: ₹85 L on the 2 BHK in Baner')
    expect(outcomeSummary({ ...won, listing_id: null }, null)).toBe('Won: ₹85 L')
    expect(outcomeSummary({ ...won, deal_price_inr: null }, '2 BHK in Baner')).toBe('Won: on the 2 BHK in Baner')
    expect(outcomeSummary({ ...won, deal_price_inr: null, listing_id: null })).toBe('Won')
    const lost = { result: 'lost' as const, deal_price_inr: null, listing_id: null, lost_reason: 'bought_elsewhere' as const, closed_at: '' }
    expect(outcomeSummary(lost)).toBe('Lost: bought elsewhere')
    expect(outcomeSummary({ ...lost, lost_reason: null })).toBe('Lost')
  })

  it('lostHint names the top reason, or just counts when none were given', () => {
    const base = { period_days: 30, deals_won: 0, deal_value_inr: 0, top_source: null }
    expect(lostHint({ ...base, deals_lost: 0, lost_reasons: {} })).toBe('')
    expect(lostHint({ ...base, deals_lost: 3, lost_reasons: { price: 2, other: 1 } })).toBe('Most lost on price')
    expect(lostHint({ ...base, deals_lost: 1, lost_reasons: {} })).toBe('1 deal lost this month')
    expect(lostHint({ ...base, deals_lost: 2, lost_reasons: {} })).toBe('2 deals lost this month')
  })
})
