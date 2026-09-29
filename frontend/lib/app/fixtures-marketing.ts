/**
 * Fixture-mode builders for the Sprint 3 features (marketing pack, reverse matching, performance, recommended actions).
 * Deterministic and fact-only, like the backend contract (docs/contracts/marketing.md): nothing is invented.
 */
import { formatInr, formatPrice } from './format'
import { budgetRange } from './leads'
import type {
  DraftLanguage,
  ImageAsset,
  LeadDetail,
  LeadMatch,
  Listing,
  MarketingPack,
  MatchingBuyer,
  PerformanceItem,
  RecommendedAction,
} from './types'

const CEILINGS: Array<[number, string]> = [
  [5_000_000, 'Rs 50 L'], [7_500_000, 'Rs 75 L'], [10_000_000, 'Rs 1 Cr'], [15_000_000, 'Rs 1.5 Cr'],
  [20_000_000, 'Rs 2 Cr'], [30_000_000, 'Rs 3 Cr'], [50_000_000, 'Rs 5 Cr'], [100_000_000, 'Rs 10 Cr'],
]

/** Smallest round ceiling above the price: "under Rs 1 Cr". Empty for rent or very large prices. */
export function budgetBucket(price: number): string {
  const hit = CEILINGS.find(([limit]) => price < limit)
  return hit ? `under ${hit[1]}` : ''
}

const TYPE_LABEL: Record<string, string> = {
  apartment: 'apartment', villa: 'villa', house: 'house', plot: 'plot', commercial: 'commercial space', office: 'office', shop: 'shop',
}

function possessionLabel(l: Listing): string {
  if (l.possession === 'ready') return 'Ready-to-move'
  if (l.possession === 'under_construction') return 'Under-construction'
  return ''
}

function unitLabel(l: Listing): string {
  const bhk = l.bhk ? `${l.bhk} BHK ` : ''
  return `${bhk}${TYPE_LABEL[l.property_type] ?? l.property_type}`
}

export function packAngle(l: Listing): string {
  const bucket = l.transaction === 'sale' ? budgetBucket(l.price_inr) : ''
  return [possessionLabel(l), unitLabel(l), `in ${l.locality}`, bucket].filter(Boolean).join(' ')
}

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

/** Small SVG data URI standing in for the server-rendered card. */
export function cardImage(kind: ImageAsset['kind'], lines: string[], width = 1080, height = 1080): ImageAsset {
  const palette: Record<string, [string, string]> = {
    cover: ['#1e3a8a', '#3b82f6'], facts: ['#14532d', '#22c55e'], amenities: ['#7c2d12', '#f97316'],
    cta: ['#581c87', '#a855f7'], status: ['#0f172a', '#0ea5e9'],
  }
  const [a, b] = palette[kind]
  const start = height / 2 - (lines.length * 90) / 2
  const text = lines
    .map((line, i) => `<text x="${width / 2}" y="${start + i * 90}" font-size="${i === 0 ? 72 : 52}" font-weight="${i === 0 ? 700 : 400}" text-anchor="middle" fill="#fff" font-family="sans-serif">${esc(line)}</text>`)
    .join('')
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${a}"/><stop offset="1" stop-color="${b}"/></linearGradient></defs><rect width="${width}" height="${height}" fill="url(#g)"/>${text}</svg>`
  return { kind, url: 'data:image/svg+xml;utf8,' + encodeURIComponent(svg), width, height }
}

function factsLines(l: Listing): string[] {
  return [
    formatPrice(l.price_inr, l.transaction === 'rent'),
    unitLabel(l),
    [l.locality, l.city].filter(Boolean).join(', '),
    l.carpet_sqft ? `${l.carpet_sqft} sq ft carpet` : '',
  ].filter(Boolean)
}

export function buildFixturePack(
  l: Listing, language: DraftLanguage, version: number, shareUrl: string, agentName = 'Your agent',
): MarketingPack {
  // Marathi falls back to English (allowed by the contract); `language` reports what was really used.
  const used: DraftLanguage = language === 'hi' ? 'hi' : 'en'
  const price = formatPrice(l.price_inr, l.transaction === 'rent')
  const unit = unitLabel(l)
  const place = [l.locality, l.city].filter(Boolean).join(', ')
  const area = l.carpet_sqft ? `${l.carpet_sqft} sq ft carpet` : ''
  const angle = packAngle(l)
  const amenities = l.amenities ?? []
  const tags = [l.city, l.locality, l.bhk ? `${l.bhk}BHK` : '', TYPE_LABEL[l.property_type] ?? '', l.transaction === 'rent' ? 'ForRent' : 'ForSale', 'RealEstate']
    .filter(Boolean)
    .map((x) => x.replace(/\s+/g, ''))

  const images: ImageAsset[] = [
    cardImage('cover', [angle.slice(0, 34), place]),
    cardImage('facts', factsLines(l)),
  ]
  if (amenities.length) images.push(cardImage('amenities', ['Amenities', ...amenities.slice(0, 5)]))
  images.push(cardImage('cta', ['Book a visit', agentName, 'Message me on WhatsApp']))

  const caption = used === 'hi'
    ? `${unit} ${place} में, ${price}.${area ? ` ${area}.` : ''} साइट विज़िट के लिए आज ही WhatsApp करें.`
    : `${unit} in ${place} for ${price}.${area ? ` ${area}.` : ''}${l.possession === 'ready' ? ' Ready possession.' : ''} Message me on WhatsApp to book a visit.`
  const facebook = used === 'hi'
    ? `नई प्रॉपर्टी: ${l.title}\n\n${unit} ${place} में, कीमत ${price}.${area ? ` ${area}.` : ''}\n\n${l.description.hi ?? l.description.en}\n\nविवरण: ${shareUrl}`
    : `New property: ${l.title}\n\n${unit} in ${place}, priced at ${price}.${area ? ` ${area}.` : ''}\n\n${l.description.en}\n\nSee full details and photos: ${shareUrl}`
  const message = used === 'hi'
    ? `नमस्ते! ${unit}, ${place}, ${price}. विवरण: ${shareUrl}`
    : `Hi! ${unit} in ${place}, ${price}.\nSee details and photos: ${shareUrl}\nHappy to arrange a visit.`

  return {
    listing_id: l.id,
    language: used,
    version,
    generated_at: new Date().toISOString(),
    angle,
    headline: `${unit} in ${l.locality} for ${price}`.slice(0, 90),
    instagram: { caption, hashtags: tags.slice(0, 12), images },
    facebook: { post: facebook },
    whatsapp: {
      message,
      status_text: `${unit} in ${l.locality} - ${price}`,
      status_image: cardImage('status', factsLines(l), 1080, 1920),
    },
    reel: {
      hook: `Looking for a ${unit} in ${l.locality}?`,
      beats: [
        { seconds: '0-3', text: `Looking for a ${unit} in ${l.locality}?`, visual: 'Front view of the building' },
        { seconds: '3-7', text: `${unit}${area ? `, ${area}` : ''}`, visual: 'Walk through the living room' },
        { seconds: '7-10', text: place, visual: 'Street or landmark nearby' },
        { seconds: '10-13', text: `Priced at ${price}`, visual: 'Price on screen' },
        { seconds: '13-15', text: 'Message me on WhatsApp to visit', visual: 'Your face or your number' },
      ],
      cta: 'Message me on WhatsApp to book a visit',
      duration_s: 15,
    },
    share_url: shareUrl,
  }
}

/** Reverse matching draft: only says "fits your budget" when the price is inside the stated budget. */
export function buyerDraft(l: Listing, lead: LeadDetail, shareUrl: string): string {
  const first = lead.name.split(' ')[0]
  const r = lead.requirement
  const hi = r?.budget_max_inr ?? null
  const lo = r?.budget_min_inr ?? 0
  const inBudget = hi != null && l.price_inr >= lo && l.price_inr <= hi
  const budget = budgetRange(r?.budget_min_inr, r?.budget_max_inr).replace(/₹| /g, '')
  const fit = inBudget && budget ? `; it fits your ${budget} budget` : ''
  return `Hi ${first}, I have a new ${l.title} at ${formatInr(l.price_inr).replace(' ', '')}${fit}. Details: ${shareUrl}`
}

export function matchingFor(
  l: Listing,
  leads: LeadDetail[],
  score: (r: NonNullable<LeadDetail['requirement']>, l: Listing) => LeadMatch,
  shareUrl: string,
  waUrl: (phone: string, text: string) => string,
): MatchingBuyer[] {
  return leads
    .filter((x) => x.stage !== 'won' && x.stage !== 'lost' && x.requirement)
    .map((x) => ({ lead: x, m: score(x.requirement!, l) }))
    .filter(({ m }) => m.match_pct >= 60)
    .sort((a, b) => b.m.match_pct - a.m.match_pct || b.lead.score - a.lead.score)
    .slice(0, 10)
    .map(({ lead, m }) => {
      const message = buyerDraft(l, lead, shareUrl)
      return {
        lead_id: lead.id, name: lead.name, phone: lead.phone, temperature: lead.temperature, score: lead.score,
        requirement_line: lead.requirement_line ?? null, match_pct: m.match_pct, reasons: m.reasons,
        draft: { message, whatsapp_url: waUrl(lead.phone, message) },
      }
    })
}

const VIEWS_BASE: Record<string, number> = { l1: 34, l3: 21, l4: 12, l5: 9 }
const LATE_STAGES = ['site_visit', 'negotiating', 'won']

export function performanceFor(listings: Listing[], leads: LeadDetail[]): PerformanceItem[] {
  return listings
    .filter((l) => l.status !== 'draft')
    .map((l) => {
      const enq = leads.filter((x) => x.first_listing_id === l.id)
      const viewEvents = leads.reduce((n, x) => n + x.timeline.filter((e) => e.type === 'listing_view' && e.listing_id === l.id).length, 0)
      const views = (VIEWS_BASE[l.id] ?? 0) + viewEvents
      const by_source: Record<string, number> = {}
      for (const x of enq) by_source[x.source || 'direct'] = (by_source[x.source || 'direct'] ?? 0) + 1
      const qualified = enq.filter((x) => x.temperature !== 'cold' || x.requirement?.budget_max_inr || x.requirement?.timeline).length
      return {
        listing_id: l.id, title: l.title, price_inr: l.price_inr, status: l.status, views,
        unique_visitors: Math.max(0, Math.round(views * 0.7)), enquiries: enq.length, qualified,
        site_visits: enq.filter((x) => LATE_STAGES.includes(x.stage)).length, by_source,
      }
    })
    .sort((a, b) => b.enquiries - a.enquiries || b.views - a.views)
}

export function actionsFor(
  listings: Listing[],
  leads: LeadDetail[],
  packs: Record<string, MarketingPack>,
  buyerCount: (l: Listing) => number,
): RecommendedAction[] {
  const out: RecommendedAction[] = []
  const open = leads.filter((l) => l.stage !== 'won' && l.stage !== 'lost')
  for (const l of open) {
    if (l.temperature === 'hot' && l.stage === 'new') {
      out.push({ type: 'call', title: `Call ${l.name}`, detail: 'Hot buyer who has not been contacted yet', priority: 1, lead_id: l.id })
    } else if (l.follow_up?.overdue) {
      out.push({ type: 'follow_up', title: `Follow up with ${l.name}`, detail: 'Their follow-up is overdue', priority: 1, lead_id: l.id })
    }
  }
  const live = listings.filter((l) => l.status === 'live')
  for (const l of live) {
    const n = buyerCount(l)
    const fresh = Date.now() - new Date(l.created_at).getTime() < 3 * 86_400_000
    if (fresh && n >= 1) {
      out.push({ type: 'send_property', title: `Send the ${l.title} to ${n} matching buyer${n > 1 ? 's' : ''}`, detail: 'New listing that fits what they asked for', priority: 2, listing_id: l.id, buyer_count: n })
    }
  }
  for (const l of live) {
    if (!packs[l.id]) out.push({ type: 'create_marketing', title: `Create marketing for ${l.title}`, detail: 'Get ready-to-share posts and a WhatsApp message', priority: 3, listing_id: l.id })
  }
  return out.sort((a, b) => a.priority - b.priority).slice(0, 6)
}
