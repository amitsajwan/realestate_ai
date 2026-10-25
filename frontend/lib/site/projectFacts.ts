/**
 * What a project page says first, written by code from the page's own facts (docs/plan/seo-system.md "AI search"), as place pages
 * do (./placeFacts): AI answers quote a short paragraph that leads with a date and the numbers buyers ask about (MahaRERA number,
 * possession date and whether it moved, homes booked, the price). Nothing here says a fact the page does not show.
 */
import { formatPrice } from './format'
import { bhkRange as offerBhks } from './projects'
import { askedPrices, displayName, longDay } from './register'
import type { RegisterProject } from './register'
import type { CatalogProject } from './types'

/** The facts the opening is written from, the same for both kinds of project page. */
export interface AnswerFacts {
  name: string
  builder?: string | null
  where: string
  regno: string
  /** the day the facts were read: the paragraph's "As of" */
  asOf?: string | null
  completionNow?: string | null
  completionAtRegistration?: string | null
  /** months of MahaRERA's August 2026 blanket extension inside the move (0 or absent: none) */
  extensionMonths?: number | null
  completionPassed?: boolean
  unitsTotal?: number | null
  unitsBooked?: number | null
  /** "2 & 3 BHK from ₹72 lakh, an agent's price sheet": the price part, already in words */
  price?: string | null
}

const n = (x: number) => x.toLocaleString('en-IN')

/** The 40-70 word answer at the top of a project page. */
export function projectAnswer(f: AnswerFacts): string {
  const day = longDay(f.asOf)
  const parts = [`${day ? `As of ${day}, ` : ''}${f.name}${f.builder ? ` by ${f.builder}` : ''} in ${f.where} is registered with MahaRERA as ${f.regno}.`]
  if (f.completionNow) {
    const moved = f.completionAtRegistration && f.completionAtRegistration !== f.completionNow
    // the 2026 order moved most projects' dates without the builder asking: said, so a 4-month move does not read as a delay
    const ext = moved && f.extensionMonths ? ` (MahaRERA's August 2026 order added ${f.extensionMonths} months to most projects)` : ''
    parts.push(`The completion date filed with MahaRERA is ${longDay(f.completionNow)}`
      + (moved ? `, moved from ${longDay(f.completionAtRegistration)} at registration${ext}.` : f.completionAtRegistration ? ', not moved since registration.' : '.'))
  }
  if (f.unitsTotal && f.unitsBooked != null && f.unitsBooked <= f.unitsTotal) {
    parts.push(f.unitsBooked === f.unitsTotal ? `All ${n(f.unitsTotal)} homes are booked.` : `${n(f.unitsBooked)} of its ${n(f.unitsTotal)} homes are booked.`)
  }
  if (f.price) parts.push(f.price.charAt(0).toUpperCase() + f.price.slice(1) + '.')
  if (f.completionPassed) parts.push('The filed completion date has passed: ask for the occupancy certificate (OC).')
  return parts.join(' ')
}

/** A register page's opening. `offer`: the agent's live price sheet (offerPrice), which is the page's one price when there is one. */
export function registerAnswer(p: RegisterProject, offer?: { from: string; bhks: string } | null): string {
  const asked = askedPrices(p)
  const price = offer ? `${offer.bhks ? `${offer.bhks} ` : ''}from ${offer.from} on a local agent's price sheet`
    : asked ? `${asked.bhks} from ${asked.from}, as listed on ${asked.sites}${asked.on ? ` on ${longDay(asked.on)}` : ''}` : null
  return projectAnswer({
    name: displayName(p), builder: p.builder?.name || p.promoter,
    where: p.area ? `${p.area.name}, Pune` : [p.pune_place?.name ?? p.place, 'Pune district'].filter(Boolean).join(', '),
    regno: p.regno, asOf: p.details_read_at ?? p.page_updated,
    completionNow: p.completion_now, completionAtRegistration: p.completion_at_registration,
    extensionMonths: p.details?.extension_months, completionPassed: p.completion_passed,
    unitsTotal: p.units_total, unitsBooked: p.units_booked, price,
  })
}

/** An agent-listed page's opening: the MahaRERA record we hold for it, and the agents' price sheet. */
export function catalogAnswer(p: CatalogProject): string {
  const r = p.rera
  const bhks = offerBhks(p.bhk_options)
  return projectAnswer({
    name: p.name, builder: p.builder, where: `${p.locality}, Pune`, regno: p.rera_no,
    asOf: r?.checked_at ?? p.updated_at, completionNow: r?.completion_now, completionAtRegistration: r?.completion_at_registration,
    unitsTotal: r?.units_total, unitsBooked: r?.units_booked,
    price: p.price_min ? `${bhks ? `${bhks} ` : ''}from ${formatPrice(p.price_min)} on the agent's price sheet` : null,
  })
}

/** The page's "Updated" day and its WebPage dateModified: our own last change to the page, never a MahaRERA date. */
export function projectUpdated(p: { page_updated?: string | null } | { updated_at?: string | null }): string | null {
  const d = 'page_updated' in p ? p.page_updated : 'updated_at' in p ? p.updated_at : null
  return d && /^\d{4}-\d{2}-\d{2}/.test(d) ? d.slice(0, 10) : null
}
