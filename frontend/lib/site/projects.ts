import { formatPrice } from './format'
import type { CatalogProject, FactSource, PublicProject } from './types'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

/** "2029-04-30" -> "30 Apr 2029"; "2028-03" -> "Mar 2028"; anything else -> "". */
export function formatDay(iso?: string | null): string {
  const m = /^(\d{4})-(\d{2})(?:-(\d{2}))?$/.exec(iso || '')
  if (!m) return ''
  const mon = MONTHS[Number(m[2]) - 1]
  if (!mon) return ''
  return m[3] ? `${Number(m[3])} ${mon} ${m[1]}` : `${mon} ${m[1]}`
}

/** "₹66 L – ₹86 L", or one price when min = max. */
export function priceRange(p: Pick<PublicProject, 'price_min' | 'price_max'>): string {
  if (p.price_min == null) return ''
  if (p.price_max == null || p.price_max === p.price_min) return formatPrice(p.price_min)
  return formatPrice(p.price_min) + ' – ' + formatPrice(p.price_max)
}

/** [2, 3] -> "2 & 3 BHK"; [2, 2.5, 3] -> "2, 2.5 & 3 BHK". */
export function bhkRange(options: number[]): string {
  if (!options.length) return ''
  const s = options.map((b) => String(b))
  return (s.length === 1 ? s[0] : s.slice(0, -1).join(', ') + ' & ' + s[s.length - 1]) + ' BHK'
}

/** Whole months between two dates (YYYY-MM or YYYY-MM-DD), b minus a. */
export function monthsBetween(a?: string | null, b?: string | null): number | null {
  const ma = /^(\d{4})-(\d{2})/.exec(a || '')
  const mb = /^(\d{4})-(\d{2})/.exec(b || '')
  if (!ma || !mb) return null
  return (Number(mb[1]) - Number(ma[1])) * 12 + (Number(mb[2]) - Number(ma[2]))
}

/**
 * Plain-language lines about possession: the builder's target (a claim), MahaRERA's date (the commitment) and how
 * far apart they are. Never says a project is late: a later MahaRERA date is the builder's own filing.
 */
export function possessionLines(p: PublicProject, agentName: string): string[] {
  const lines: string[] = []
  const target = formatDay(p.possession_target)
  const now = formatDay(p.rera?.completion_now)
  const then = formatDay(p.rera?.completion_at_registration)
  if (target) lines.push(`Builder's target: ${target} (as quoted by ${agentName}).`)
  if (now) {
    lines.push(`Date filed with MahaRERA: ${now}. This is the date the builder has committed to under RERA.`)
    if (then && then !== now) lines.push(`At registration the MahaRERA date was ${then}; it has since moved to ${now}.`)
    const gap = monthsBetween(p.possession_target, p.rera?.completion_now)
    if (target && gap != null && gap >= 3) {
      lines.push(`The two dates are about ${gap} months apart. Plan your rent, loan and move around the MahaRERA date, and ask for the possession date in writing in your agreement for sale.`)
    }
  }
  return lines
}

export const SOURCE_LABEL: Record<FactSource, string> = {
  maharera: 'MahaRERA record',
  builder: 'Builder',
  agent: 'As quoted by the agent',
  avasetu: 'Our summary',
  osm: 'OpenStreetMap',
}

export function sourceLabel(src: FactSource | undefined, agentName: string): string {
  if (src === 'agent') return 'As quoted by ' + agentName
  return src ? SOURCE_LABEL[src] : ''
}

/** Google Maps search link for a buyer to find the project (no pin is invented when we do not have one). */
export function mapsLink(p: Pick<PublicProject, 'maps_query' | 'name' | 'locality' | 'place'>): string {
  if (p.place) return `https://www.google.com/maps/search/?api=1&query=${p.place.lat},${p.place.lon}`
  const q = p.maps_query || `${p.name} ${p.locality} Pune`
  return 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(q)
}

/** Lowest price per sq ft across configurations, for the comparison table. */
export function minPerSqft(p: Pick<PublicProject, 'configurations'>): number | null {
  const v = p.configurations.map((c) => c.price_per_sqft)
  return v.length ? Math.min(...v) : null
}

export function projectWhatsAppMessage(p: Pick<PublicProject, 'name' | 'locality'>, url?: string): string {
  return `Hi, I am interested in ${p.name}, ${p.locality}.` + (url ? ' ' + url : '') + ' Please share prices and a site visit time.'
}

/** Projects grouped by locality, in the order of first appearance (the catalog is already sorted by locality, then name). */
export function byLocality(items: CatalogProject[]): Array<[string, CatalogProject[]]> {
  const groups = new Map<string, CatalogProject[]>()
  for (const p of items) {
    const k = p.locality.trim()
    groups.set(k, [...(groups.get(k) || []), p])
  }
  return [...groups]
}

/** The agent whose record the facts come from (their prices and dates are the ones quoted); enquiries go to them. */
export function mainAgent(p: CatalogProject): CatalogProject['agents'][number] {
  return p.agents.find((a) => a.project_slug === p.slug) ?? p.agents[0]
}
