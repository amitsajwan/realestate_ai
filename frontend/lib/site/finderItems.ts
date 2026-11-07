import { LOCALITIES } from '@/lib/marketing/localities'
import { bhkOf, type FinderItem, type HomeType } from './finder'
import { displayName, type RegisterListItem } from './register'
import { readableName } from './format'
import { firstImage } from './seo'
import { agentPath } from './slug'
import type { PublicListing } from './types'

/** The finder's items from the two places homes come from: an agent's listings and Avasetu's MahaRERA register. */

const TYPE: Record<string, HomeType> = { apartment: 'apartment', villa: 'villa', house: 'villa', plot: 'plot', commercial: 'commercial', office: 'commercial', shop: 'commercial' }
const areaName = (key: string | null | undefined, fallback?: string | null) => LOCALITIES.find((l) => l.key === key)?.name ?? fallback ?? null

// the same list as ai_listing.register.DESCRIBES: these only say what kind of building it is, so the record's name is the better one
const DESCRIBES = new Set(['the', 'a', 'new', 'commercial', 'residential', 'complex', 'project', 'projects', 'building', 'buildings', 'tower',
  'towers', 'shop', 'shops', 'office', 'offices', 'flat', 'flats', 'apartment', 'apartments', 'and', 'for', 'sale'])
const words = (s: string) => s.toLowerCase().match(/[a-z0-9]+/g) ?? []
const genericName = (s: string) => words(s).length > 0 && words(s).every((w) => DESCRIBES.has(w))
const squash = (s: string) => words(s).join('')

/** The card's area for a listing: MahaRERA's place when the agent's says something else, so the card and the page behind it agree
 *  ("Undri" on the card, Mohammadwadi on the page). One inside the other ("Upper Kharadi" / "Kharadi") keeps the agent's detail. */
function listingArea(own: string | null | undefined, record: string | null): string | null {
  if (!own || !record) return own || record
  const [a, b] = [squash(own), squash(record)]
  return a.includes(b) || b.includes(a) ? own : record
}

/** An agent's live listings, each with its MahaRERA record when we hold it (possession, the date's moves, homes booked, the map). */
export function fromListings(listings: PublicListing[], slug: string, register: RegisterListItem[]): FinderItem[] {
  const byRegno = new Map(register.map((r) => [r.regno.toUpperCase(), r]))
  // the agent's order (newest first), but a home with a price before one without (a "price on request" villa does not lead)
  const ordered = [...listings].sort((a, b) => Number(!a.price_inr) - Number(!b.price_inr))
  return ordered.map((l, rank) => {
    const r = l.rera_no ? byRegno.get(l.rera_no.trim().toUpperCase()) : undefined
    const sheet = (l.configurations ?? []).filter((c) => c.bhk)
    const homes = sheet.length
      ? sheet.map((c) => ({ bhk: c.bhk, sqft: c.carpet_sqft ?? null, price: c.price_inr ?? null }))
      : [{ bhk: l.property_type === 'plot' ? null : l.bhk ?? null, sqft: l.carpet_sqft ?? null, price: l.price_inr ?? null }]
    return {
      id: l.id, href: agentPath(slug, 'listings/' + l.id),
      name: r && genericName(l.project_name || '') ? displayName(r) : (l.project_name || '').trim() || l.title, builder: null,
      area: listingArea(l.locality, areaName(r?.area, r?.place_name)), type: TYPE[l.property_type] ?? null, homes,
      possession: r?.completion_now ?? l.possession ?? null, monthsLater: r?.months_later ?? null,
      booked: r?.units_booked ?? null, total: r?.units_total ?? null, video: (l.video_count ?? 0) > 0,
      image: firstImage(l) ?? null, map: r?.map ?? null, rank,
    }
  })
}

/** An agent's listing of a register project, for Avasetu's list: their sheet, photo and video stand for the project. */
export interface AgentOffer { agentName: string; listing: PublicListing }

/** Avasetu's register in our areas, ranked agent-listed first, then priced, then most booked. A project an agent lists takes the
 *  agent's price sheet, photo and video (what a buyer can actually book) and says whose it is; the link stays the project page. */
export function fromRegister(items: RegisterListItem[], offers: Map<string, AgentOffer>): FinderItem[] {
  const out = items.map((r): FinderItem => {
    const own = offers.get(r.regno.toUpperCase())
    const agent = own ? fromListings([own.listing], 'x', [r])[0] : null
    return {
      id: r.slug, href: `/projects/${r.slug}`, name: displayName(r),
      // "INTOFINITY PROMOTERS PRIVATE LIMITED" as MahaRERA files it reads as shouting on a card
      builder: r.promoter ? readableName(r.promoter).replace(/\s+(private|pvt\.?)\s+(limited|ltd\.?)$/i, '').replace(/\s+(llp|limited|ltd\.?)$/i, '') : null,
      area: areaName(r.area, r.place_name), type: agent?.type ?? null,
      homes: agent?.homes ?? ((r.homes ?? []).length ? r.homes!.map((h) => ({ bhk: bhkOf(h.bhk), price: h.from_inr })) : [{ bhk: null, price: r.price_from ?? null }]),
      possession: r.completion_now, monthsLater: r.months_later ?? null, booked: r.units_booked ?? null, total: r.units_total ?? null,
      video: agent?.video ?? false, image: agent?.image ?? r.photo ?? null, map: r.map ?? null, listedBy: own?.agentName ?? null,
    }
  })
  const score = (i: FinderItem) => (i.listedBy ? 1e9 : 0) + (i.homes.some((h) => h.price != null) ? 1e8 : 0) + (i.booked ?? 0)
  return out.sort((a, b) => score(b) - score(a)).map((i, rank) => ({ ...i, rank }))
}
