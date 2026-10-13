import { serverApiBase, fixturesForced } from './api'
import { formatPrice } from './format'
import { bhkRange, formatDay, priceRange } from './projects'
import type { CatalogProject } from './types'

/** What the builder's site and the sites ranking for a project say, checked (backend areastats/webfacts.py): a fact is here
 *  when the builder's own site states it, or two sites agree. MahaRERA's record always wins over these. */
export interface WebFact {
  key: string
  label: string
  /** how it reads on the page: "10 acres", "80%" */
  text: string
  /** the builder's own site says it */
  official: boolean
  sources: { site: string; url: string; quote: string }[]
}

export interface WebFacts {
  read_at: string | null
  facts: WebFact[]
}

/** The web facts for a registration (its tower group's), or null. Optional extra on a page: any failure just hides them. */
export async function getWebFacts(regno: string | null | undefined): Promise<WebFacts | null> {
  if (fixturesForced() || !regno) return null
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 4000)
  try {
    const res = await fetch(serverApiBase() + '/api/v1/public/register/web-facts/' + encodeURIComponent(regno), {
      headers: { Accept: 'application/json' }, next: { revalidate: 3600 }, signal: ctrl.signal,
    })
    if (!res.ok) return null
    const body = (await res.json()) as WebFacts
    return body && Array.isArray(body.facts) && body.facts.length ? body : null
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

export const webFact = (web: WebFacts | null | undefined, key: string): WebFact | undefined => web?.facts.find((f) => f.key === key)

/** "lodhagroup.com (the builder's site), nobroker.in" */
export function sourcesText(f: WebFact): string {
  return f.sources.map((s, i) => (i === 0 && f.official ? `${s.site} (the builder's site)` : s.site)).join(', ')
}

export interface Faq { q: string; a: string }

/** Questions buyers search for an agent-listed project, answered by code from the page's facts only (MahaRERA, the agent's
 *  price list, checked web facts); a question with no fact behind it is left out. */
export function catalogFaq(p: CatalogProject, web: WebFacts | null): Faq[] {
  const out: Faq[] = []
  const regs = p.registrations ?? []
  const prices = priceRange(p)
  if (prices) {
    const from = p.configurations.length
      ? ' ' + p.configurations.map((c) => `${c.label}: ${formatPrice(c.price_inr)} for ${c.carpet_sqft.toLocaleString('en-IN')} sq ft carpet`).join('; ') + '.'
      : ''
    out.push({ q: `What is the price of ${p.name}?`,
      a: `${prices} for ${bhkRange(p.bhk_options)} homes, as quoted by the agent.${from} Confirm the price and the extra charges before you book.` })
  }
  const dated = regs.filter((r) => r.completion)
  if (dated.length > 1) {
    out.push({ q: `What is the possession date of ${p.name}?`,
      a: `Each tower has its own completion date filed with MahaRERA: ` + dated.map((r) => `${r.tower} ${formatDay(r.completion)}`).join(', ') +
        '. Ask which tower a home is in, and get the possession date in your agreement for sale.' })
  } else if (p.rera?.completion_now) {
    const moved = p.rera.completion_at_registration && p.rera.completion_at_registration !== p.rera.completion_now
    out.push({ q: `What is the possession date of ${p.name}?`,
      a: `The completion date filed with MahaRERA is ${formatDay(p.rera.completion_now)}.` +
        (moved ? ` At registration it was ${formatDay(p.rera.completion_at_registration)}.` : '') +
        ' Get the possession date in your agreement for sale.' })
  }
  if (regs.length > 1) {
    out.push({ q: `Is ${p.name} RERA registered?`,
      a: `Yes. It is registered with MahaRERA as ${regs.length} projects, one per tower: ` + regs.map((r) => `${r.tower} ${r.regno}`).join(', ') + '.' })
  } else {
    out.push({ q: `Is ${p.name} RERA registered?`, a: `Yes. Its MahaRERA registration number is ${p.rera_no}.` })
  }
  if (p.rera?.units_total) {
    out.push({ q: `How many homes in ${p.name} are booked?`,
      a: `${p.rera.units_booked ?? 0} of ${p.rera.units_total} homes${regs.length > 1 && regs[0]?.tower ? ` in ${regs[0].tower}` : ''} were booked as reported to MahaRERA` +
        (p.rera.checked_at ? ` (read ${formatDay(p.rera.checked_at)}).` : '.') })
  }
  const land = webFact(web, 'land_acres'), open = webFact(web, 'open_space_pct')
  if (land || open) {
    const bits = [land ? `${land.text} of land` : '', open ? `${open.text} open space` : ''].filter(Boolean).join(' with ')
    const srcs = Array.from(new Set([land, open].filter(Boolean).flatMap((f) => sourcesText(f as WebFact).split(', '))))
    out.push({ q: `How big is ${p.name}?`, a: `${p.name} is on ${bits}, as stated on ${srcs.join(', ')}.` })
  }
  const towers = webFact(web, 'towers'), floors = webFact(web, 'floors')
  if (towers || floors) {
    out.push({ q: `How many towers and floors does ${p.name} have?`,
      a: [towers ? `${towers.text} towers (${sourcesText(towers)})` : '', floors ? `${floors.text} (${sourcesText(floors)})` : ''].filter(Boolean).join('; ') + '.' })
  }
  out.push({ q: `Who is the builder of ${p.name}?`,
    a: `${p.builder}` + (p.rera?.promoter && p.rera.promoter.toLowerCase() !== p.builder.toLowerCase() ? `; the promoter on MahaRERA is ${p.rera.promoter}.` : '.') })
  out.push({ q: `Where is ${p.name}?`, a: `${p.address || p.locality + ', Pune'}${p.pincode && !(p.address || '').includes(p.pincode) ? ` (pincode ${p.pincode})` : ''}.` })
  return out
}

/** "Jul 2030" for the earliest completion date filed with MahaRERA across the towers (or the project's one date). */
export function earliestPossession(p: CatalogProject): string {
  const dates = (p.registrations ?? []).map((r) => r.completion).filter(Boolean) as string[]
  const first = dates.length ? dates.sort()[0] : p.rera?.completion_now
  return first ? formatDay(first.slice(0, 7)) : ''
}
