/**
 * What a place page says first, written by code from its own numbers (docs/plan/seo-system.md "AI search"): AI answers and
 * featured snippets quote a short paragraph that leads with numbers and a date, and questions answered on the page. Nothing here
 * says a number the page's own lists do not show.
 */
import { formatPrice } from './format'
import type { PlacePrices } from './facets'
import { displayName, longDay, monthYear } from './register'
import type { RegisterListItem, RegisterPlace } from './register'

const plural = (n: number, one: string, many = one + 's') => `${n.toLocaleString('en-IN')} ${n === 1 ? one : many}`

/** Being built (not sold out) earliest filed completion first, with a date. */
function soonest(building: RegisterListItem[], n = 3): RegisterListItem[] {
  return building.filter((r) => r.completion_now).sort((a, b) => (a.completion_now as string).localeCompare(b.completion_now as string)).slice(0, n)
}

function homes(rows: RegisterListItem[]): { total: number; booked: number } | null {
  const known = rows.filter((r) => r.units_total && r.units_booked != null)
  if (known.length === 0) return null
  return { total: known.reduce((s, r) => s + (r.units_total as number), 0), booked: known.reduce((s, r) => s + (r.units_booked as number), 0) }
}

function builders(rows: RegisterListItem[], n = 3): { name: string; count: number }[] {
  const by = new Map<string, number>()
  for (const r of rows) if (r.promoter) by.set(r.promoter, (by.get(r.promoter) ?? 0) + 1)
  return [...by].map(([name, count]) => ({ name, count })).filter((b) => b.count > 1)
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name)).slice(0, n)
}

/** The 40-70 word answer at the top: counts, homes booked, the earliest completion, the lowest 2 BHK price. */
export function placeAnswer(place: RegisterPlace, building: RegisterListItem[], soldOut: RegisterListItem[], asOf: string,
  prices: PlacePrices | null): string {
  const active = building.length + soldOut.length
  const parts = [`As of ${longDay(asOf)}, MahaRERA lists ${plural(active, 'housing project')} in ${place.name}, Pune being built or recently finished${soldOut.length ? ` (${soldOut.length} sold out)` : ''}.`]
  const h = homes([...building, ...soldOut])
  if (h && h.total > 0) parts.push(`${h.booked.toLocaleString('en-IN')} of their ${h.total.toLocaleString('en-IN')} homes are booked.`)
  const first = soonest(building, 1)[0]
  if (first) parts.push(`The earliest filed completion date is ${displayName(first)} (${monthYear(first.completion_now)}).`)
  const size = prices?.sizes.find((s) => s.bhk === 2) ?? prices?.sizes[0]
  if (size) parts.push(`${size.bhk} BHK flats start from ${formatPrice(size.low)} (${size.cheapest.name}).`)
  return parts.join(' ')
}

/** Questions buyers ask about the place, answered only from the page's lists. */
export function placeFaq(place: RegisterPlace, building: RegisterListItem[], soldOut: RegisterListItem[], asOf: string,
  prices: PlacePrices | null): { q: string; a: string }[] {
  const out: { q: string; a: string }[] = []
  const active = building.length + soldOut.length
  out.push({ q: `How many new projects are there in ${place.name}, Pune?`,
    a: `${plural(active, 'project')} registered with MahaRERA ${active === 1 ? 'is' : 'are'} being built or recently finished in ${place.name} as of ${longDay(asOf)}, out of ${plural(place.projects, 'project')} MahaRERA has listed there.` })
  for (const s of prices?.sizes ?? []) {
    out.push({ q: `What is the price of a ${s.bhk} BHK flat in ${place.name}?`,
      a: `Among ${plural(s.projects, 'project')} with a published ${s.bhk} BHK price, starting prices run from ${formatPrice(s.low)}${s.high > s.low ? ` to ${formatPrice(s.high)}` : ''}; the lowest is ${s.cheapest.name}. Prices are from the builder's own site or two property sites that agree; parking, stamp duty, registration and GST are usually extra.` })
  }
  const soon = soonest(building)
  if (soon.length) {
    out.push({ q: `Which projects in ${place.name} have the earliest possession?`,
      a: `By the completion date the builder filed with MahaRERA: ${soon.map((r) => `${displayName(r)} (${monthYear(r.completion_now)})`).join(', ')}. A filed date can move; each project's page shows whether it has.` })
  }
  const top = builders([...building, ...soldOut])
  if (top.length) {
    out.push({ q: `Which builders have the most projects in ${place.name}?`,
      a: `Among projects being built or recently finished: ${top.map((b) => `${b.name} (${b.count})`).join(', ')}.` })
  }
  out.push({ q: `Where do these ${place.name} numbers come from?`,
    a: "MahaRERA's public register, read by Avasetu; each project's page shows the date we read its record. No builder pays to be listed." })
  return out
}

/** The newest change among the place's project pages (our own page dates, never MahaRERA's): the page's dateModified. */
export function placeUpdated(rows: RegisterListItem[]): string | null {
  const days = rows.map((r) => r.page_updated).filter((d): d is string => !!d).sort()
  return days.length ? days[days.length - 1] : null
}
