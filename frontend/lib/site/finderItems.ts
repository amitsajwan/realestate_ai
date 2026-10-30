import { LOCALITIES } from '@/lib/marketing/localities'
import { bhkOf, type FinderItem, type HomeType } from './finder'
import { displayName, type RegisterListItem } from './register'
import { firstImage } from './seo'
import { agentPath } from './slug'
import type { PublicListing } from './types'

/** The finder's items from the two places homes come from: an agent's listings and Avasetu's MahaRERA register. */

const TYPE: Record<string, HomeType> = { apartment: 'apartment', villa: 'villa', house: 'villa', plot: 'plot', commercial: 'commercial', office: 'commercial', shop: 'commercial' }
const areaName = (key: string | null | undefined, fallback?: string | null) => LOCALITIES.find((l) => l.key === key)?.name ?? fallback ?? null

/** An agent's live listings, each with its MahaRERA record when we hold it (possession, the date's moves, homes booked, the map). */
export function fromListings(listings: PublicListing[], slug: string, register: RegisterListItem[]): FinderItem[] {
  const byRegno = new Map(register.map((r) => [r.regno.toUpperCase(), r]))
  return listings.map((l, rank) => {
    const r = l.rera_no ? byRegno.get(l.rera_no.trim().toUpperCase()) : undefined
    const sheet = (l.configurations ?? []).filter((c) => c.bhk)
    const homes = sheet.length
      ? sheet.map((c) => ({ bhk: c.bhk, sqft: c.carpet_sqft ?? null, price: c.price_inr ?? null }))
      : [{ bhk: l.property_type === 'plot' ? null : l.bhk ?? null, sqft: l.carpet_sqft ?? null, price: l.price_inr ?? null }]
    return {
      id: l.id, href: agentPath(slug, 'listings/' + l.id), name: (l.project_name || '').trim() || l.title, builder: null,
      area: l.locality || areaName(r?.area, r?.place_name), type: TYPE[l.property_type] ?? null, homes,
      possession: r?.completion_now ?? l.possession ?? null, monthsLater: r?.months_later ?? null,
      booked: r?.units_booked ?? null, total: r?.units_total ?? null, video: (l.video_count ?? 0) > 0,
      image: firstImage(l) ?? null, map: r?.map ?? null, rank,
    }
  })
}

/** Avasetu's register in our areas: each project's published prices by size, ranked agent-listed first, then most booked. */
export function fromRegister(items: RegisterListItem[], listed: Map<string, { slug: string; agent?: string | null }>): FinderItem[] {
  const out = items.map((r) => {
    const own = listed.get(r.regno)
    return {
      id: r.slug, href: `/projects/${own?.slug ?? r.slug}`, name: displayName(r), builder: r.promoter ?? null,
      area: areaName(r.area, r.place_name), type: null,
      homes: (r.homes ?? []).length ? r.homes!.map((h) => ({ bhk: bhkOf(h.bhk), price: h.from_inr })) : [{ bhk: null, price: r.price_from ?? null }],
      possession: r.completion_now, monthsLater: r.months_later ?? null, booked: r.units_booked ?? null, total: r.units_total ?? null,
      video: false, image: null, map: r.map ?? null, listedBy: own?.agent ?? null,
    } as FinderItem
  })
  const score = (i: FinderItem) => (i.listedBy ? 1e9 : 0) + (i.homes.some((h) => h.price != null) ? 1e8 : 0) + (i.booked ?? 0)
  return out.sort((a, b) => score(b) - score(a)).map((i, rank) => ({ ...i, rank }))
}
