import { createFixtureApi, fakeDraft } from '@/lib/app/fixtures'
import { eventLabel, sortLeads, sourceLabel } from '@/lib/app/leads'
import type { Lead } from '@/lib/app/types'
import { missingFields } from '@/lib/app/validate'

const mem = () => {
  const m: Record<string, string> = {}
  return { getItem: (k: string) => m[k] ?? null, setItem: (k: string, v: string) => void (m[k] = v) }
}

describe('fixture api', () => {
  it('runs the onboarding flow', async () => {
    const api = createFixtureApi(mem())
    const otp = await api.requestOtp('+919876543210')
    expect(otp.dev_code).toBe('123456')
    await expect(api.verifyOtp('+919876543210', '000000')).rejects.toMatchObject({ status: 400 })
    const login = await api.verifyOtp('+919876543210', '123456')
    expect(login).toMatchObject({ is_new_user: true, has_site: false })
    const site = await api.createSite({ name: 'Amit Sajwan', city: 'Pune' })
    expect(site).toMatchObject({ slug: 'amit-sajwan', created: true })
    expect((await api.verifyOtp('+919876543210', '123456')).has_site).toBe(true)
  })

  it('blocks publish with a 422 listing missing fields, then publishes when complete', async () => {
    const api = createFixtureApi(mem())
    const l = await api.createListing({ title: 'Flat', city: 'Pune' })
    const err = await api.publishListing(l.id).catch((e) => e)
    expect(err.status).toBe(422)
    expect(err.missing).toEqual(expect.arrayContaining(['price_inr', 'locality', 'media', 'description.en']))
    await api.updateListing(l.id, {
      price_inr: 5_000_000, locality: 'Baner', transaction: 'sale', property_type: 'apartment',
      description: { en: 'Nice' }, media: [{ url: 'x', kind: 'image', order: 0 }],
    })
    expect((await api.publishListing(l.id)).status).toBe('live')
    expect((await api.setListingStatus(l.id, 'sold')).status).toBe('sold')
    expect((await api.listListings('sold')).map((x) => x.id)).toContain(l.id)
  })

  it('persists through storage and never auto-publishes on create', async () => {
    const storage = mem()
    const a = createFixtureApi(storage)
    const l = await a.createListing({ title: 'Persist me' })
    expect(l.status).toBe('draft')
    const b = createFixtureApi(storage)
    expect((await b.getListing(l.id)).title).toBe('Persist me')
  })

  it('serves leads hottest first and records stage changes with notes', async () => {
    const api = createFixtureApi(mem())
    const leads = await api.listLeads()
    const scores = leads.map((l) => l.score)
    expect(scores).toEqual([...scores].sort((a, b) => b - a))
    const d = await api.updateLead(leads[0].id, 'site_visit', 'Sunday 11am')
    expect(d.stage).toBe('site_visit')
    expect(d.notes[d.notes.length - 1].text).toBe('Sunday 11am')
    expect((await api.listLeads('site_visit')).length).toBe(1)
  })
})

describe('fakeDraft', () => {
  it('extracts fields, confidence and missing', () => {
    const d = fakeDraft('2 BHK in Baner, 85 lakh, ready possession', 0, false)
    expect(d.draft).toMatchObject({ bhk: 2, price_inr: 8_500_000, locality: 'Baner', city: 'Pune', possession: 'ready', transaction: 'sale' })
    expect(d.confidence.possession).toBeLessThan(0.7)
    expect(d.missing).toContain('media')
  })
  it('uses a canned transcript for audio', () => {
    const d = fakeDraft('', 1, true)
    expect(d.transcript).toBeTruthy()
    expect(d.missing).not.toContain('media')
  })
})

describe('missingFields', () => {
  it('is live-computed from the form', () => {
    const v = { title: 'a', transaction: 'sale' as const, property_type: 'plot' as const, price_inr: 1, city: 'c', locality: 'l', description: { en: 'd' } }
    expect(missingFields(v)).toEqual(['media'])
    const media = [{ url: 'u', kind: 'image' as const, order: 0 }]
    expect(missingFields({ ...v, media })).toEqual([])
    expect(missingFields({ ...v, media, price_inr: 0 })).toEqual(['price_inr'])
  })
})

describe('leads helpers', () => {
  const now = new Date('2026-01-01T12:00:00Z')
  it('labels timeline events', () => {
    expect(eventLabel({ type: 'listing_view', listing_id: 'l1', source: 'instagram', ts: '2026-01-01T10:00:00Z' }, '2 BHK Baner', now)).toBe(
      'Viewed 2 BHK Baner - Instagram - 2h ago',
    )
    expect(eventLabel({ type: 'page_view', source: null, ts: '2026-01-01T11:00:00Z' }, null, now)).toBe('Visited your website - 1h ago')
    expect(sourceLabel('whatsapp')).toBe('WhatsApp')
  })
  it('sorts hottest first, ties most recent first', () => {
    const mk = (id: string, score: number, at: string) => ({ id, score, last_activity_at: at }) as Lead
    const out = sortLeads([mk('a', 10, '2026-01-01'), mk('b', 50, '2026-01-01'), mk('c', 10, '2026-01-02')])
    expect(out.map((l) => l.id)).toEqual(['b', 'c', 'a'])
  })
})
