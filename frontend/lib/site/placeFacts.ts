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

/** The answer's numbers as a strip of four at the top (the review's "big light number, small bold label"), each one also in
 *  the answer sentence under it, which stays for the search engines and AI answers that quote it. A number we lack is left out. */
export function placeStats(building: RegisterListItem[], soldOut: RegisterListItem[], prices: PlacePrices | null): { value: string; label: string }[] {
  const out: { value: string; label: string }[] = []
  const active = building.length + soldOut.length
  if (active) out.push({ value: active.toLocaleString('en-IN'), label: active === 1 ? 'Project being built' : 'Projects being built' })
  const h = homes([...building, ...soldOut])
  if (h && h.total > 0) out.push({ value: `${Math.round((100 * h.booked) / h.total)}%`, label: 'Homes booked' })
  const size = prices?.sizes.find((s) => s.bhk === 2) ?? prices?.sizes[0]
  if (size) out.push({ value: formatPrice(size.low), label: `${size.bhk} BHK from` })
  const passed = building.filter((r) => r.stage === 'passed').length
  if (passed) out.push({ value: passed.toLocaleString('en-IN'), label: 'Past their completion date' })
  return out
}

/** Projects whose builder moved the filed possession date by 3 months or more (net of MahaRERA's 2026 order for all projects),
 *  out of those whose dates we have read, and the middle move in months. Null with fewer than 5 to count: too few to say a
 *  place's builders do anything. */
function movedDates(rows: RegisterListItem[]): { moved: number; of: number; usual: number } | null {
  const known = rows.filter((r) => r.months_later != null)
  if (known.length < 5) return null
  const moves = known.map((r) => r.months_later as number).filter((m) => m >= 3).sort((a, b) => a - b)
  return { moved: moves.length, of: known.length, usual: moves.length ? moves[Math.floor((moves.length - 1) / 2)] : 0 }
}

/** At most this share of projects moving their date and the place's builders "mostly keep their dates". */
const KEPT_SHARE = 0.15

/** "The good and what to check" for a place, from its own lists only: whether builders keep their dates, how fast homes are
 *  booked, what is ready soon, what is past its date. A balanced pair is what buyers trust and AI answers quote (a portal's
 *  "what's great / what needs attention" block, 2026-11-18); every line here is a count the page's lists show, never a claim
 *  about roads or air we cannot check. */
export function placeGoodToKnow(place: RegisterPlace, building: RegisterListItem[], soldOut: RegisterListItem[], asOf: string,
  prices: PlacePrices | null): { good: string[]; check: string[] } {
  const good: string[] = []
  const check: string[] = []
  const active = [...building, ...soldOut]
  const m = movedDates(active)
  if (m && m.moved / m.of <= KEPT_SHARE) {
    good.push(`Builders here mostly keep their dates: ${m.moved} of ${m.of} projects have moved their possession date by 3 months or more.`)
  } else if (m) {
    check.push(`${m.moved} of ${m.of} projects have moved their possession date by 3 months or more, usually by ${plural(m.usual, 'month')} `
      + `(not counting MahaRERA's 2026 extension for all projects). See the date history on a project's page before you book.`)
  }
  const h = homes(active)
  if (h && h.total > 0) {
    const pct = Math.round((100 * h.booked) / h.total)
    good.push(pct >= 50 ? `Buyers are booking here: ${pct}% of the homes in projects being built are already booked.`
      : `Room to choose: ${(h.total - h.booked).toLocaleString('en-IN')} of ${h.total.toLocaleString('en-IN')} homes in projects being built are still open.`)
  }
  const year = new Date(new Date(asOf).getTime() + 365 * 86400000).toISOString().slice(0, 10)
  const soon = building.filter((r) => r.stage !== 'passed' && r.completion_now && r.completion_now > asOf && r.completion_now <= year)
  if (soon.length) good.push(`${plural(soon.length, 'project')} ${soon.length === 1 ? 'has' : 'have'} possession filed within the next 12 months.`)
  const passed = building.filter((r) => r.stage === 'passed').length
  if (passed) check.push(`${plural(passed, 'project')} ${passed === 1 ? 'is' : 'are'} past the completion date filed with MahaRERA: ask for the occupancy certificate (OC) before you pay.`)
  if (prices?.sizes.length) check.push(`Starting prices are for the smallest home of each size and usually leave out parking, stamp duty, registration and GST: ask for the full cost sheet.`)
  return { good, check }
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
  const m = movedDates([...building, ...soldOut])
  if (m) {
    out.push({ q: `Do builders in ${place.name} keep their possession dates?`,
      a: `${m.moved} of the ${m.of} projects being built in ${place.name} whose dates we have read have moved their MahaRERA possession date by 3 months or more${m.moved ? `, usually by ${plural(m.usual, 'month')}` : ''}, not counting MahaRERA's 2026 extension for all projects. Each project's page shows its own date history.` })
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
