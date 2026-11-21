import { allInCost } from './allin'
import { formatPrice, groupIndian, readableName } from './format'
import {
  askedPrices, completionChange, headingName, homesOf, lowestPriceInr, mainRegistration, monthYear, monthsApart, possessionLabel,
  possessionOf, soldOutOf, stageOf, STAGE_LABEL, wholeProject, completionPassedOf,
} from './register'
import type { RegisterProject } from './register'
import { forPin, fromRecord } from './fromAbove'

/** The public side-by-side of up to three project pages (/compare): every cell is a fact the project page itself says, read
 *  through the same accessors (lib/site/register), so a page of several MahaRERA registrations is compared as the whole project
 *  (CLAUDE.md rule 11) and a fact we do not have is a dash, never a guess. Plan: seo-system.md section 8, "Compare and shortlist". */

export interface Cell { text: string; sub?: string; href?: string }
export interface CompareRow { key: string; label: string; cells: (Cell | null)[] }

const pct = (a: number, b: number) => Math.round((100 * a) / b)

function price(p: RegisterProject): Cell | null {
  const a = askedPrices(p)
  if (!a) return null
  return { text: `From ${a.from}`, sub: [a.bhks, a.on ? `read ${monthYear(a.on)}` : null].filter(Boolean).join(' · ') || undefined }
}

/** The lowest published price with GST, stamp duty and registration on top (lib/site/allin), before the builder's own charges. */
function allIn(p: RegisterProject): Cell | null {
  const low = lowestPriceInr(p)
  if (!low) return null
  const row = (p.prices?.rows ?? []).find((r) => r.from_inr === low)
  const c = allInCost(low, completionPassedOf(p) ? 'completion_passed' : 'building', row?.sqft ?? null)
  return { text: `About ${formatPrice(c.total)}${c.gstLeftOut ? ' + GST if any' : ''}`, sub: 'GST, stamp duty, registration; before the builder\'s charges' }
}

function perSqft(p: RegisterProject): Cell | null {
  const rows = (p.prices?.rows ?? []).filter((r) => r.per_sqft && r.per_sqft > 0)
  const own = rows.length ? Math.min(...rows.map((r) => r.per_sqft as number)) : null
  const area = p.area_rate && p.area_rate.per_sqft > 0 ? p.area_rate : null
  if (!own && !area) return null
  return {
    text: own ? `₹${groupIndian(own)}` : '—',
    sub: area ? `${area.place} middle ₹${groupIndian(area.per_sqft)} (${area.projects} projects)` : undefined,
  }
}

function possession(p: RegisterProject): Cell | null {
  const x = possessionOf(p)
  if (!x.date && !x.from) return null
  return { text: possessionLabel(p), sub: x.to ? `to ${monthYear(x.to)}, by registration` : 'filed with MahaRERA' }
}

/** Whether the builder moved the filed date: one registration's record, so a page of several says to see each part's. */
function moved(p: RegisterProject): Cell | null {
  if (wholeProject(p)) return { text: 'See each registration', sub: 'dates differ by tower or phase', href: `/projects/${p.slug}#regs-title` }
  const c = completionChange(mainRegistration(p))
  if (!c || c.kind === 'unknown') return null
  if (c.kind === 'same') return { text: 'Not moved', sub: 'same date as at registration' }
  if (c.kind === 'extension') return { text: 'Not moved by the builder', sub: `MahaRERA's 2026 order added ${c.months ?? 'some'} months` }
  const months = monthsApart(c.from, mainRegistration(p).completion_now)
  return { text: months ? `Moved ${months} months later` : 'Moved later', sub: `first filed for ${monthYear(c.from)}` }
}

function booked(p: RegisterProject): Cell | null {
  const h = homesOf(p)
  if (h.booked == null || !h.of) return null
  return { text: `${pct(h.booked, h.of)}% booked`, sub: `${groupIndian(h.booked)} of ${groupIndian(h.of)} homes${h.across ? `, ${h.across}` : ''}` }
}

function open(p: RegisterProject): Cell | null {
  const h = homesOf(p)
  if (soldOutOf(p)) return { text: 'Sold out on MahaRERA' }
  if (h.booked == null || !h.of) return null
  return { text: `${groupIndian(h.of - h.booked)} homes`, sub: 'not yet booked on MahaRERA' }
}

/** Towers and the tallest one: from the record of one registration, so only for a page that is one. */
function towers(p: RegisterProject): Cell | null {
  if (wholeProject(p)) return null
  const d = mainRegistration(p).details
  if (!d || (!d.towers && !d.max_floors)) return null
  return { text: [d.towers ? `${d.towers} tower${d.towers === 1 ? '' : 's'}` : null, d.max_floors ? `up to ${d.max_floors} floors` : null].filter(Boolean).join(', ') }
}

function stage(p: RegisterProject): Cell | null {
  const s = stageOf(p)
  return s ? { text: STAGE_LABEL[s], sub: 'by dates, registration to filed completion' } : null
}

function builderRecord(p: RegisterProject): Cell | null {
  const b = p.builder
  if (!b || !b.count) return null
  const href = b.slug ? `/builders/${b.slug}` : undefined
  if (!b.record_ok) return { text: `${b.count} project${b.count === 1 ? '' : 's'} on MahaRERA`, sub: 'too few with both dates to judge', href }
  return { text: `${b.moved_later} of ${b.with_dates} moved their date`, sub: `${readableName(b.name)}, ${b.count} projects`, href }
}

/** The newest look from space (backend areastats/fromabove.py), with its season line, when the page has the section. */
function fromSpace(p: RegisterProject): Cell | null {
  const v = forPin(fromRecord(p.from_above, p.slug), p.map)
  if (!v) return null
  const last = v.seasons[v.seasons.length - 1]
  return { text: last ? last.label : v.updated ? `Seen ${monthYear(v.updated)}` : 'Seen from space', sub: last?.line, href: `/projects/${p.slug}/from-space` }
}

const ROWS: { key: string; label: string; cell: (p: RegisterProject) => Cell | null }[] = [
  { key: 'price', label: 'Starting price', cell: price },
  { key: 'all-in', label: 'All-in cost, lowest price', cell: allIn },
  { key: 'per-sqft', label: 'Per sq ft, as published', cell: perSqft },
  { key: 'possession', label: 'Possession filed', cell: possession },
  { key: 'moved', label: 'Date moved by the builder', cell: moved },
  { key: 'booked', label: 'Homes booked', cell: booked },
  { key: 'open', label: 'Homes left', cell: open },
  { key: 'towers', label: 'Towers', cell: towers },
  { key: 'stage', label: 'Stage', cell: stage },
  { key: 'builder', label: "Builder's date record", cell: builderRecord },
  { key: 'from-space', label: 'Latest look from space', cell: fromSpace },
]

/** The table's rows; a row no project has a fact for is left out. */
export function compareRows(projects: RegisterProject[]): CompareRow[] {
  return ROWS.map((r) => ({ key: r.key, label: r.label, cells: projects.map(r.cell) }))
    .filter((r) => r.cells.some(Boolean))
}

export const compareName = (p: RegisterProject): string => headingName(p)

/** One project's line in the brief: its starting price, the possession filed and how much is booked, each only when known. */
export function briefLine(p: RegisterProject): string {
  const price = askedPrices(p)
  const h = homesOf(p)
  return [
    price ? `from ${price.from}${price.bhks ? ` (${price.bhks})` : ''}` : null,
    possessionLabel(p) ? `possession filed ${possessionLabel(p)}` : null,
    h.booked != null && h.of ? `${Math.round((100 * h.booked) / h.of)}% booked` : null,
  ].filter(Boolean).join(' · ')
}

/** "Want possession sooner?": projects in the same area whose filed date is at least `months` before this one's, soonest first.
 *  Only projects still being built are in same_area, and only a filed date is compared (never a promise). */
export function soonerNearby(p: RegisterProject, today: string = todayIso(), months = 12, most = 2): { name: string; slug: string; on: string; months: number }[] {
  const x = possessionOf(p)
  const mine = x.date ?? x.from
  if (!mine || completionPassedOf(p)) return []
  return (p.same_area ?? [])
    .map((s) => ({ name: s.name, slug: s.slug, on: s.completion_now ?? '', months: s.completion_now ? monthsBetween(s.completion_now, mine) : 0 }))
    .filter((s) => s.on && s.months >= months && s.on > today)
    .sort((a, b) => a.on.localeCompare(b.on))
    .slice(0, most)
}

function monthsBetween(from: string, to: string): number {
  const a = new Date(from), b = new Date(to)
  if (isNaN(a.getTime()) || isNaN(b.getTime())) return 0
  return (b.getUTCFullYear() - a.getUTCFullYear()) * 12 + (b.getUTCMonth() - a.getUTCMonth())
}

const todayIso = () => new Date().toISOString().slice(0, 10)
