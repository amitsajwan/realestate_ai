import { createFixtureApi } from '@/lib/app/fixtures'
import { budgetBucket } from '@/lib/app/fixtures-marketing'
import {
  actionHref,
  buyerDraftUrl,
  buyerWhatsappUrl,
  hashtagsLine,
  imageFilename,
  instagramCopyText,
  reelScriptText,
  whatsappPackUrl,
} from '@/lib/app/marketing'

const mem = () => {
  const m: Record<string, string> = {}
  return { getItem: (k: string) => m[k] ?? null, setItem: (k: string, v: string) => void (m[k] = v) }
}

describe('fixture marketing pack', () => {
  it('404s before generation, then creates a full pack and bumps the version on regenerate', async () => {
    const api = createFixtureApi(mem())
    await expect(api.getMarketingPack('l1')).rejects.toMatchObject({ status: 404 })
    const p = await api.createMarketingPack('l1')
    expect(p).toMatchObject({ listing_id: 'l1', language: 'en', version: 1 })
    expect(p.angle).toBe('Ready-to-move 2 BHK apartment in Baner under Rs 1 Cr')
    expect(p.headline.length).toBeLessThanOrEqual(90)
    expect(p.instagram.caption.length).toBeLessThanOrEqual(900)
    expect(p.instagram.caption).toMatch(/₹85 L/)
    expect(p.instagram.hashtags.length).toBeLessThanOrEqual(12)
    expect(p.instagram.images.map((i) => i.kind)).toEqual(['cover', 'facts', 'amenities', 'cta'])
    p.instagram.images.forEach((i) => {
      expect(i.url).toMatch(/^data:image\/svg\+xml/)
      expect([i.width, i.height]).toEqual([1080, 1080])
    })
    expect(p.facebook.post).toContain(p.share_url)
    expect(p.whatsapp.message).toContain(p.share_url)
    expect(p.whatsapp.status_text).not.toBe('')
    expect(p.whatsapp.status_image).toMatchObject({ kind: 'status', width: 1080, height: 1920 })
    expect(p.reel.beats.length).toBeGreaterThanOrEqual(4)
    expect(p.reel.beats[0]).toEqual(expect.objectContaining({ seconds: expect.any(String), text: expect.any(String), visual: expect.any(String) }))
    expect(p.share_url).toContain('?src=whatsapp')
    expect((await api.getMarketingPack('l1')).version).toBe(1)
    expect((await api.createMarketingPack('l1', 'hi')).version).toBe(2)
  })

  it('reports the language actually used (mr falls back to en) and refuses non-live listings', async () => {
    const api = createFixtureApi(mem())
    expect((await api.createMarketingPack('l1', 'hi')).language).toBe('hi')
    expect((await api.createMarketingPack('l1', 'mr')).language).toBe('en')
    await expect(api.createMarketingPack('l2')).rejects.toMatchObject({ status: 409 }) // draft
    await expect(api.createMarketingPack('nope')).rejects.toMatchObject({ status: 404 })
  })

  it('only claims facts from the listing', async () => {
    const api = createFixtureApi(mem())
    const p = await api.createMarketingPack('l4')
    const all = JSON.stringify([p.instagram.caption, p.facebook.post, p.whatsapp.message, p.reel])
    expect(all).toMatch(/₹1\.4 Cr/)
    expect(all).not.toMatch(/best|guaranteed|lowest/i)
  })
})

describe('fixture matching buyers', () => {
  it('returns matching buyers sorted by match with an honest draft', async () => {
    const api = createFixtureApi(mem())
    const r = await api.getMatchingLeads('l1')
    expect(r.listing).toMatchObject({ id: 'l1', locality: 'Baner', price_inr: 8_500_000 })
    expect(r.buyers.length).toBeGreaterThanOrEqual(2)
    const pcts = r.buyers.map((b) => b.match_pct)
    expect([...pcts].sort((a, b) => b - a)).toEqual(pcts)
    pcts.forEach((p) => expect(p).toBeGreaterThanOrEqual(60))
    const rohit = r.buyers.find((b) => b.lead_id === 'c1')!
    expect(rohit.reasons.length).toBeGreaterThan(0)
    expect(rohit.draft.message).toContain('fits your 80L-90L budget')
    expect(rohit.draft.message).toContain(r.listing.share_url)
    expect(rohit.draft.whatsapp_url).toMatch(/^https:\/\/wa\.me\/919822012345\?text=/)
  })

  it('never says "fits your budget" when the price is outside it, and skips buyers who do not match', async () => {
    const api = createFixtureApi(mem())
    const r = await api.getMatchingLeads('l3') // 92 L vs Rohit 80-90 L
    const rohit = r.buyers.find((b) => b.lead_id === 'c1')
    if (rohit) expect(rohit.draft.message).not.toMatch(/fits your/)
    expect((await api.getMatchingLeads('l1')).buyers.map((b) => b.lead_id)).not.toContain('c5')
    expect((await api.getMatchingLeads('l2')).buyers.length).toBeGreaterThanOrEqual(0)
    await expect(api.getMatchingLeads('nope')).rejects.toMatchObject({ status: 404 })
  })
})

describe('fixture performance and actions', () => {
  it('returns performance rows for non-draft listings, most enquiries first', async () => {
    const api = createFixtureApi(mem())
    const rows = await api.getPerformance()
    expect(rows.map((r) => r.listing_id)).not.toContain('l2')
    const l1 = rows.find((r) => r.listing_id === 'l1')!
    expect(l1).toMatchObject({ enquiries: 3, status: 'live' })
    expect(l1.views).toBeGreaterThan(0)
    expect(l1.unique_visitors).toBeLessThanOrEqual(l1.views)
    expect(l1.qualified).toBeLessThanOrEqual(l1.enquiries)
    expect(l1.by_source).toEqual({ instagram: 1, facebook: 1, whatsapp: 1 })
    const enq = rows.map((r) => r.enquiries)
    expect([...enq].sort((a, b) => b - a)).toEqual(enq)
  })

  it('getToday carries prioritised actions of every type, then drops create_marketing once a pack exists', async () => {
    const api = createFixtureApi(mem())
    const { actions } = await api.getToday()
    const list = actions!
    expect(list.length).toBeLessThanOrEqual(6)
    const pri = list.map((a) => a.priority)
    expect([...pri].sort()).toEqual(pri)
    const byType = (t: string) => list.filter((a) => a.type === t)
    expect(byType('call')[0]).toMatchObject({ lead_id: 'c1', priority: 1 })
    expect(byType('follow_up')[0]).toMatchObject({ lead_id: 'c2', priority: 1 })
    expect(byType('send_property')[0]).toMatchObject({ listing_id: 'l1', priority: 2 })
    expect(byType('send_property')[0].buyer_count).toBeGreaterThanOrEqual(1)
    expect(byType('create_marketing').some((a) => a.listing_id === 'l1')).toBe(true)

    await api.createMarketingPack('l1')
    const after = (await api.getToday()).actions!
    expect(after.some((a) => a.type === 'create_marketing' && a.listing_id === 'l1')).toBe(false)
  })

  it('persists packs through storage', async () => {
    const storage = mem()
    await createFixtureApi(storage).createMarketingPack('l1')
    expect((await createFixtureApi(storage).getMarketingPack('l1')).version).toBe(1)
  })
})

describe('marketing helpers', () => {
  it('budgetBucket picks the smallest round ceiling above the price', () => {
    expect(budgetBucket(4_200_000)).toBe('under Rs 50 L')
    expect(budgetBucket(8_500_000)).toBe('under Rs 1 Cr')
    expect(budgetBucket(12_500_000)).toBe('under Rs 1.5 Cr')
    expect(budgetBucket(10_000_000)).toBe('under Rs 1.5 Cr')
  })

  it('hashtagsLine adds #, strips spaces and drops empties and duplicates', () => {
    expect(hashtagsLine(['Baner', '#Pune', ' 2 BHK ', '', 'baner'])).toBe('#Baner #Pune #2BHK')
    expect(hashtagsLine([])).toBe('')
  })

  it('instagramCopyText and reelScriptText join the parts', () => {
    expect(instagramCopyText({ caption: 'Hi', hashtags: ['a', 'b'], images: [] })).toBe('Hi\n\n#a #b')
    expect(instagramCopyText({ caption: 'Hi', hashtags: [], images: [] })).toBe('Hi')
    const text = reelScriptText({
      hook: 'H', cta: 'C', duration_s: 15,
      beats: [{ seconds: '0-3', text: 'one', visual: 'v1' }, { seconds: '3-6', text: 'two', visual: 'v2' }],
    })
    expect(text).toBe('Hook: H\n1. (0-3) one\n   Show: v1\n2. (3-6) two\n   Show: v2\nCall to action: C')
  })

  it('builds wa.me links with encoded text', () => {
    expect(whatsappPackUrl('Hi & bye ₹85 L')).toBe('https://wa.me/?text=Hi%20%26%20bye%20%E2%82%B985%20L')
    expect(buyerWhatsappUrl('+91 98220 12345', 'Hello there')).toBe('https://wa.me/919822012345?text=Hello%20there')
    expect(buyerWhatsappUrl('9822012345', '  ')).toBe('https://wa.me/919822012345')
    const buyer = { phone: '+919822012345', draft: { message: 'orig', whatsapp_url: 'https://wa.me/server' } } as never
    expect(buyerDraftUrl(buyer, 'orig')).toBe('https://wa.me/server')
    expect(buyerDraftUrl(buyer, 'edited?')).toBe('https://wa.me/919822012345?text=edited%3F')
  })

  it('imageFilename picks the extension and actionHref targets', () => {
    const img = (url: string) => ({ kind: 'cover' as const, url, width: 1, height: 1 })
    expect(imageFilename(img('data:image/svg+xml;utf8,x'), 'l1')).toBe('l1-cover.svg')
    expect(imageFilename(img('https://x/a/cover.jpg'), 'l1')).toBe('l1-cover.jpg')
    expect(imageFilename(img('https://x/a/cover.png?v=1'), 'l1')).toBe('l1-cover.png')
    const a = (type: string, extra = {}) => actionHref({ type, title: '', detail: '', priority: 1, ...extra } as never)
    expect(a('call', { lead_id: 'c1' })).toBe('/studio/leads/c1')
    expect(a('follow_up', { lead_id: 'c2' })).toBe('/studio/leads/c2')
    expect(a('send_property', { listing_id: 'l1' })).toBe('/studio/listings/l1/marketing')
    expect(a('create_marketing', { listing_id: 'l3' })).toBe('/studio/listings/l3/marketing')
    expect(a('call')).toBe('/studio/leads')
  })
})
