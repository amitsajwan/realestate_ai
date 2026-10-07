import { createFixtureApi } from '@/lib/app/fixtures'

const mem = () => {
  const m: Record<string, string> = {}
  return { m, getItem: (k: string) => m[k] ?? null, setItem: (k: string, v: string) => void (m[k] = v) }
}

describe('fixture deal outcomes', () => {
  it('uses a new storage key so old demo state is not mixed with outcomes', async () => {
    const s = mem()
    const api = createFixtureApi(s)
    await api.updateLead('c1', { stage: 'contacted' })
    expect(Object.keys(s.m)).toEqual(['app_fixture_state_v6'])
  })

  it('leads start with no outcome, in the list and in the detail', async () => {
    const api = createFixtureApi(mem())
    expect((await api.getLead('c1')).outcome).toBeNull()
    expect((await api.listLeads()).every((l) => !l.outcome)).toBe(true)
  })

  it('won with a price and listing stores the outcome and suggests marking the listing sold', async () => {
    const api = createFixtureApi(mem())
    const d = await api.updateLead('c1', { stage: 'won', outcome: { deal_price_inr: 8_200_000, listing_id: 'l1' } })
    expect(d.stage).toBe('won')
    expect(d.outcome).toMatchObject({ result: 'won', deal_price_inr: 8_200_000, listing_id: 'l1', lost_reason: null })
    expect(new Date(d.outcome!.closed_at).getTime()).toBeGreaterThan(Date.now() - 5000)
    expect(d.suggest_listing_status).toEqual({ listing_id: 'l1', status: 'sold' })
    // the suggestion is only in the response, and the listing itself is never changed
    expect((await api.getLead('c1')).suggest_listing_status).toBeUndefined()
    expect((await api.getListing('l1')).status).toBe('live')
    expect((await api.listLeads()).find((l) => l.id === 'c1')!.outcome).toMatchObject({ result: 'won' })
  })

  it('the listing defaults to the lead first listing; the price is never guessed', async () => {
    const api = createFixtureApi(mem())
    const d = await api.updateLead('c2', { stage: 'won', outcome: {} })
    expect(d.outcome).toMatchObject({ deal_price_inr: null, listing_id: 'l4' })
    expect(d.suggest_listing_status).toEqual({ listing_id: 'l4', status: 'sold' })
  })

  it('won without an outcome stores only the result: no price, no listing, no suggestion', async () => {
    const api = createFixtureApi(mem())
    const d = await api.updateLead('c1', 'won')
    expect(d.outcome).toMatchObject({ result: 'won', deal_price_inr: null, listing_id: null })
    expect(d.suggest_listing_status).toBeUndefined()
  })

  it('suggests rented for a rent listing', async () => {
    const api = createFixtureApi(mem())
    const l = await api.createListing({ title: 'Rental', transaction: 'rent', price_inr: 25_000 })
    const d = await api.updateLead('c3', { stage: 'won', outcome: { listing_id: l.id } })
    expect(d.suggest_listing_status).toEqual({ listing_id: l.id, status: 'rented' })
  })

  it('lost stores the reason (or none)', async () => {
    const api = createFixtureApi(mem())
    const a = await api.updateLead('c3', { stage: 'lost', outcome: { lost_reason: 'price' } })
    expect(a.outcome).toMatchObject({ result: 'lost', lost_reason: 'price', deal_price_inr: null, listing_id: null })
    expect(a.suggest_listing_status).toBeUndefined()
    const b = await api.updateLead('c5', 'lost')
    expect(b.outcome).toMatchObject({ result: 'lost', lost_reason: null })
  })

  it('moving out of won or lost (reopen) clears the outcome and schedules a follow-up when contacted', async () => {
    const api = createFixtureApi(mem())
    await api.updateLead('c1', { stage: 'won', outcome: { deal_price_inr: 8_200_000, listing_id: 'l1' } })
    const back = await api.updateLead('c1', { stage: 'contacted' })
    expect(back.stage).toBe('contacted')
    expect(back.outcome).toBeNull()
    expect(back.follow_up?.due_at).toBeTruthy()
    expect((await api.getToday()).results).toMatchObject({ deals_won: 0, deal_value_inr: 0 })
  })

  it('a note alone keeps the stored outcome', async () => {
    const api = createFixtureApi(mem())
    await api.updateLead('c1', { stage: 'won', outcome: { deal_price_inr: 8_200_000, listing_id: 'l1' } })
    const d = await api.updateLead('c1', { note: 'Sent the agreement' })
    expect(d.stage).toBe('won')
    expect(d.outcome).toMatchObject({ deal_price_inr: 8_200_000 })
  })

  it('refuses what the contract refuses (422)', async () => {
    const api = createFixtureApi(mem())
    await expect(api.updateLead('c1', { outcome: { deal_price_inr: 5 } })).rejects.toMatchObject({ status: 422 })
    await expect(api.updateLead('c1', { stage: 'contacted', outcome: { lost_reason: 'price' } })).rejects.toMatchObject({ status: 422 })
    await expect(api.updateLead('c1', { stage: 'lost', outcome: { deal_price_inr: 5 } })).rejects.toMatchObject({ status: 422 })
    await expect(api.updateLead('c1', { stage: 'won', outcome: { lost_reason: 'price' } })).rejects.toMatchObject({ status: 422 })
    await expect(api.updateLead('c1', { stage: 'won', outcome: { deal_price_inr: 0 } })).rejects.toMatchObject({ status: 422 })
    await expect(api.updateLead('c1', { stage: 'won', outcome: { listing_id: 'someone-elses' } })).rejects.toMatchObject({ status: 422 })
    expect((await api.getLead('c1')).stage).toBe('new') // nothing was applied
  })

  it('getToday results: deals, value, best channel (ties alphabetical), lost reasons', async () => {
    const api = createFixtureApi(mem())
    expect((await api.getToday()).results).toEqual({
      period_days: 30, deals_won: 0, deal_value_inr: 0, deals_lost: 0, top_source: null, lost_reasons: {},
    })
    await api.updateLead('c1', { stage: 'won', outcome: { deal_price_inr: 8_500_000, listing_id: 'l1' } }) // instagram
    await api.updateLead('c2', { stage: 'won', outcome: { deal_price_inr: 12_000_000 } }) // whatsapp
    await api.updateLead('c4', 'won') // whatsapp, no price
    await api.updateLead('c3', { stage: 'lost', outcome: { lost_reason: 'price' } })
    await api.updateLead('c5', { stage: 'lost', outcome: { lost_reason: 'price' } })
    const r = (await api.getToday()).results!
    expect(r).toMatchObject({ deals_won: 3, deal_value_inr: 20_500_000, deals_lost: 2, top_source: 'whatsapp', lost_reasons: { price: 2 } })
  })

  it('results break a tie alphabetically and ignore deals closed more than 30 days ago', async () => {
    const s = mem()
    const api = createFixtureApi(s)
    await api.updateLead('c1', { stage: 'won' }) // instagram
    await api.updateLead('c2', { stage: 'won' }) // whatsapp
    expect((await api.getToday()).results!.top_source).toBe('instagram')
    const state = JSON.parse(s.m.app_fixture_state_v6)
    state.leads.find((l: { id: string }) => l.id === 'c1').outcome.closed_at = new Date(Date.now() - 40 * 86_400_000).toISOString()
    const later = createFixtureApi({ getItem: () => JSON.stringify(state), setItem: () => undefined })
    expect((await later.getToday()).results).toMatchObject({ deals_won: 1, top_source: 'whatsapp' })
  })

  it('performance rows gain deals, deal_value_inr and deals_by_source', async () => {
    const api = createFixtureApi(mem())
    let l1 = (await api.getPerformance()).find((p) => p.listing_id === 'l1')!
    expect(l1).toMatchObject({ deals: 0, deal_value_inr: 0, deals_by_source: {} })
    await api.updateLead('c1', { stage: 'won', outcome: { deal_price_inr: 8_500_000, listing_id: 'l1' } })
    await api.updateLead('c4', { stage: 'won', outcome: { listing_id: 'l1' } }) // no price: counted, value ignored
    l1 = (await api.getPerformance()).find((p) => p.listing_id === 'l1')!
    expect(l1).toMatchObject({ deals: 2, deal_value_inr: 8_500_000, deals_by_source: { instagram: 1, whatsapp: 1 } })
    // c5 enquired about l5 and is won without a listing: credited to its first listing
    await api.updateLead('c5', 'won')
    expect((await api.getPerformance()).find((p) => p.listing_id === 'l5')).toMatchObject({ deals: 1, deal_value_inr: 0 })
  })
})
