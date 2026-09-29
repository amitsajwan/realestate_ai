import { createFixtureApi } from '@/lib/app/fixtures'
import {
  budgetRange,
  buildWhatsappUrl,
  dueLabel,
  followUpAt,
  requirementChips,
  requirementSourceNote,
} from '@/lib/app/leads'

const mem = () => {
  const m: Record<string, string> = {}
  return { getItem: (k: string) => m[k] ?? null, setItem: (k: string, v: string) => void (m[k] = v) }
}

describe('fixture api: qualification', () => {
  it('lists 5 leads with requirement lines', async () => {
    const api = createFixtureApi(mem())
    const leads = await api.listLeads()
    expect(leads).toHaveLength(5)
    expect(new Set(leads.map((l) => l.temperature))).toEqual(new Set(['hot', 'warm', 'cold']))
    expect(leads.find((l) => l.name === 'Rohit Deshmukh')?.requirement_line).toBe('2 BHK · 80L-90L · Baner · 1-3 months')
    expect(leads.find((l) => l.name === 'Imran Shaikh')?.requirement_line).toBeNull()
  })

  it('getLead returns requirement, ai_summary, next_action, matches and follow_up', async () => {
    const api = createFixtureApi(mem())
    const d = await api.getLead('c1')
    expect(d.requirement).toMatchObject({ bhk: 2, source: 'stated' })
    expect(d.ai_summary).toMatch(/Wants a 2 BHK/)
    expect(d.next_action?.type).toBe('schedule_visit')
    expect(d.matches!.length).toBeGreaterThan(0)
    expect(d.matches![0]).toMatchObject({ listing_id: 'l1' })
    expect(d.matches![0].match_pct).toBeGreaterThanOrEqual(d.matches![d.matches!.length - 1].match_pct)
    expect((await api.getLead('c2')).follow_up?.overdue).toBe(true)
    expect((await api.getLead('c3')).matches).toEqual([])
    await expect(api.getLead('nope')).rejects.toMatchObject({ status: 404 })
  })

  it('getToday returns counts, hot buyers, follow-ups and a headline', async () => {
    const api = createFixtureApi(mem())
    const t = await api.getToday()
    expect(t.counts.hot).toBe(2)
    expect(t.counts.site_visits).toBe(1)
    expect(t.counts.uncontacted).toBe(2)
    expect(t.headline).toBe("2 buyers haven't been contacted today.")
    expect(t.hot_buyers.map((b) => b.name)).toEqual(['Priya Nair', 'Rohit Deshmukh'])
    expect(t.hot_buyers[0].top_match).toMatchObject({ match_pct: expect.any(Number) })
    expect(t.follow_ups.map((f) => f.id)).toContain('c2')
    expect(t.follow_ups.find((f) => f.id === 'c2')?.overdue).toBe(true)
  })

  it('updateLead accepts a patch, schedules follow-ups, and moving to contacted sets +2 days', async () => {
    const api = createFixtureApi(mem())
    const iso = followUpAt(3)
    const a = await api.updateLead('c1', { follow_up_at: iso })
    expect(a.follow_up).toEqual({ due_at: iso, overdue: false })
    const b = await api.updateLead('c3', { stage: 'contacted' })
    const due = new Date(b.follow_up!.due_at!).getTime() - Date.now()
    expect(due).toBeGreaterThan(47 * 3_600_000)
    expect(due).toBeLessThan(49 * 3_600_000)
  })

  it('createFollowupDraft builds a message, encoded wa.me url and reasons; unsupported languages fall back to en', async () => {
    const api = createFixtureApi(mem())
    const d = await api.createFollowupDraft('c1')
    expect(d.language).toBe('en')
    expect(d.message).toContain('Rohit')
    expect(d.whatsapp_url).toBe(`https://wa.me/919822012345?text=${encodeURIComponent(d.message)}`)
    expect(d.based_on.length).toBeGreaterThan(0)
    expect((await api.createFollowupDraft('c1', 'hi')).language).toBe('hi')
    expect((await api.createFollowupDraft('c1', 'mr')).language).toBe('en')
    await expect(api.createFollowupDraft('zzz')).rejects.toMatchObject({ status: 404 })
  })

  it('a brand-new agent state has no leads (today is empty)', async () => {
    const empty = mem()
    empty.setItem('app_fixture_state_v2', JSON.stringify({ listings: [], leads: [], site: null, seq: 1 }))
    const t = await createFixtureApi(empty).getToday()
    expect(t.counts).toEqual({ new_enquiries_24h: 0, hot: 0, site_visits: 0, follow_ups_due: 0, uncontacted: 0 })
    expect(t.headline).toBe("You're all caught up.")
  })
})

describe('requirement helpers', () => {
  it('formats budget ranges in lakh/crore', () => {
    expect(budgetRange(8_000_000, 9_000_000)).toBe('₹80 L - ₹90 L')
    expect(budgetRange(0, 5_000_000)).toBe('Under ₹50 L')
    expect(budgetRange(20_000_000, null)).toBe('₹2 Cr+')
    expect(budgetRange(12_000_000, 20_000_000)).toBe('₹1.2 Cr - ₹2 Cr')
    expect(budgetRange(null, null)).toBe('')
  })

  it('builds chips for what is known, and the source note', () => {
    const req = { bhk: 2, budget_min_inr: 8_000_000, budget_max_inr: 9_000_000, timeline: '1_3_months' as const, financing: 'home_loan' as const, localities: ['Baner', 'Balewadi'], source: 'inferred' as const }
    expect(requirementChips(req)).toEqual(['2 BHK', '₹80 L - ₹90 L', 'Baner', 'Balewadi', 'In 1-3 months', 'Home loan'])
    expect(requirementChips({ ...req, bhk: null, budget_min_inr: null, budget_max_inr: null, timeline: null, financing: null, localities: [] })).toEqual([])
    expect(requirementChips(null)).toEqual([])
    expect(requirementSourceNote(req)).toBe('Read from their message')
    expect(requirementSourceNote({ ...req, source: 'stated' })).toBe('Stated by the buyer')
  })

  it('builds wa.me links with encoded text', () => {
    expect(buildWhatsappUrl('+91 98220 12345', 'Hi & bye? 100%')).toBe('https://wa.me/919822012345?text=Hi%20%26%20bye%3F%20100%25')
    expect(buildWhatsappUrl('9822012345', '   ')).toBe('https://wa.me/919822012345')
  })

  it('followUpAt is N days ahead at 10:00 local; dueLabel words it', () => {
    const now = new Date(2026, 9, 1, 15, 0)
    const d = new Date(followUpAt(3, now))
    expect([d.getDate(), d.getHours()]).toEqual([4, 10])
    expect(dueLabel(null, false)).toBe('')
    expect(dueLabel(new Date(2026, 9, 1, 18).toISOString(), false, now)).toBe('Due today')
    expect(dueLabel(new Date(2026, 9, 5, 10).toISOString(), false, now)).toMatch(/^Due /)
    expect(dueLabel(new Date(2026, 8, 28, 10).toISOString(), true, now)).toMatch(/^Overdue/)
  })
})
