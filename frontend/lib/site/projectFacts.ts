/**
 * What a project page says first, written by code from the page's own facts (docs/plan/seo-system.md "AI search"), as place pages
 * do (./placeFacts): AI answers quote a short paragraph that leads with a date and the numbers buyers ask about (MahaRERA number,
 * possession date and whether it moved, homes booked, the price). Nothing here says a fact the page does not show.
 */
import { formatPrice } from './format'
import { bhkRange as offerBhks } from './projects'
import { acrossRegistrations, areaCompareOf, askedPrices, askedSource, completionPassedOf, displayName, extensionSentence, isExtensionOnly,
  longDay, mainRegistration, monthsApart, unitWord, wholeProject } from './register'
import type { ProjectScope, RegisterProject } from './register'
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
  /** the backend's word that the extension is the only change (absent: worked out from the dates and extensionMonths) */
  extensionOnly?: boolean | null
  completionPassed?: boolean
  unitsTotal?: number | null
  unitsBooked?: number | null
  /** "2 & 3 BHK from ₹72 lakh, an agent's price sheet": the price part, already in words */
  price?: string | null
  /** homes booked since our first dated reading of MahaRERA (seo-system.md 8b, H1): {rose, since}, only when it went up */
  bookedSince?: { rose: number; since: string } | null
  /** the share booked beside the area's projects registered within a year of it (backend pages.area_compare) */
  areaBooked?: { pct: number; area_pct: number; projects: number; place: string } | null
  /** the builder's date record over its Pune projects, only when there are enough to state it (record_ok) */
  builderRecord?: { name: string; with_dates: number; moved_later: number } | null
  /** "units" for offices or shops only: they are not homes */
  unitWord?: 'homes' | 'units'
  /** a project MahaRERA holds as several registrations: the counts above are then one part's, so the whole project's are said */
  whole?: ProjectScope | null
}

const n = (x: number) => x.toLocaleString('en-IN')

/** The 40-70 word answer at the top of a project page. */
export function projectAnswer(f: AnswerFacts): string {
  const day = longDay(f.asOf)
  const w = f.whole
  const parts = [`${day ? `As of ${day}, ` : ''}${f.name}${f.builder ? ` by ${f.builder}` : ''} in ${f.where} is registered with MahaRERA `
    + (w ? `in ${w.registrations} parts, the main one ${f.regno}.` : `as ${f.regno}.`)]
  if (w?.completion_first && w.completion_last && w.completion_first !== w.completion_last) {
    parts.push(`Its parts have filed completion dates from ${longDay(w.completion_first)} to ${longDay(w.completion_last)}.`)
  }
  if (f.completionNow) {
    if (w) parts.push(`For ${f.regno}:`)
    const at = f.completionAtRegistration
    const moved = at && at !== f.completionNow
    // the 2026 order moved most projects' dates without the builder asking: when it is the only change the builder moved nothing,
    // so the date is never said to have "moved"; inside a bigger move it is named, so the move does not read as all delay
    if (moved && isExtensionOnly(at, f.completionNow, f.extensionMonths, f.extensionOnly)) {
      parts.push(extensionSentence(f.completionNow, f.extensionMonths || monthsApart(at, f.completionNow)))
    } else {
      const ext = moved && f.extensionMonths ? ` (MahaRERA's August 2026 order added ${f.extensionMonths} months to most projects)` : ''
      parts.push(`The completion date filed with MahaRERA is ${longDay(f.completionNow)}`
        + (moved ? `, moved from ${longDay(at)} at registration${ext}.` : at ? ', not moved since registration.' : '.'))
    }
  }
  // "27 of 249 homes booked": the total is every home MahaRERA lists, never the ones still for sale. For a project in several
  // registrations, the sum over its registrations; the pace and the area comparison are the main registration's alone, so left out.
  if (w) {
    const what = f.unitWord ?? 'homes'
    if (w.units_booked != null && w.booked_of) {
      parts.push(`MahaRERA shows ${n(w.units_booked)} of ${n(w.booked_of)} ${what} booked, ${acrossRegistrations(w.booked_counted, w.registrations)}.`)
    }
  } else if (f.unitsTotal && f.unitsBooked != null && f.unitsBooked <= f.unitsTotal) {
    const what = f.unitWord ?? 'homes'
    parts.push(f.unitsBooked === f.unitsTotal ? `MahaRERA shows all ${n(f.unitsTotal)} ${what} booked.`
      : `MahaRERA shows ${n(f.unitsBooked)} of ${n(f.unitsTotal)} ${what} booked.`)
    if (f.bookedSince && f.bookedSince.rose > 0) {
      parts.push(`${n(f.bookedSince.rose)} of them were booked since ${longDay(f.bookedSince.since)}, by Avasetu's readings of MahaRERA.`)
    }
    // set beside its area: a fact no single record shows, so the sentence the page alone can say
    const c = f.areaBooked
    if (c) parts.push(`That is ${c.pct}% booked, against ${c.area_pct}% for the middle of ${n(c.projects)} ${c.place} projects registered within a year of it.`)
  }
  const b = f.builderRecord
  if (b && b.with_dates > 0) {
    parts.push(`Of ${n(b.with_dates)} ${b.name} projects in Pune with both dates on MahaRERA, `
      + `${b.moved_later ? n(b.moved_later) : 'none'} moved the completion date 3 months or more later.`)
  }
  if (f.price) parts.push(f.price.charAt(0).toUpperCase() + f.price.slice(1) + '.')
  if (f.completionPassed) parts.push('The filed completion date has passed: ask for the occupancy certificate (OC).')
  return parts.join(' ')
}

/** Homes booked between our first and latest dated readings, when the count went up (ProjectHistory shows the readings). */
export function bookedSince(r: Pick<RegisterProject, 'booked_readings'>): { rose: number; since: string } | null {
  const rows = r.booked_readings ?? []
  if (rows.length < 2) return null
  const rose = rows[rows.length - 1].booked - rows[0].booked
  return rose > 0 ? { rose, since: rows[0].on } : null
}

/** A register page's opening. `offer`: the agent's live price sheet (offerPrice), which is the page's one price when there is one. */
export function registerAnswer(p: RegisterProject, offer?: { from: string; bhks: string } | null): string {
  const asked = askedPrices(p)
  const price = offer ? `${offer.bhks ? `${offer.bhks} ` : ''}from ${offer.from} on a local agent's price sheet`
    : asked ? `${asked.bhks || 'homes'} from ${asked.from}${askedSource(asked)}` : null
  // the main registration's record, named as such: projectAnswer says the whole project's counts and dates when `whole` is set
  const main = mainRegistration(p)
  const compare = areaCompareOf(p)
  return projectAnswer({
    name: displayName(p), builder: p.builder?.name || p.promoter,
    where: p.area ? `${p.area.name}, Pune` : [p.pune_place?.name ?? p.place, 'Pune district'].filter(Boolean).join(', '),
    regno: p.regno, asOf: p.details_read_at ?? p.page_updated,
    completionNow: main.completion_now, completionAtRegistration: main.completion_at_registration,
    extensionMonths: main.details?.extension_months, extensionOnly: main.extension_only, completionPassed: completionPassedOf(p),
    unitsTotal: main.units_total, unitsBooked: main.units_booked, price, bookedSince: bookedSince(main),
    areaBooked: compare?.booked ? { ...compare.booked, place: compare.place } : null,
    builderRecord: p.builder?.record_ok ? p.builder : null, unitWord: unitWord(p), whole: wholeProject(p),
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
