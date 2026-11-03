/**
 * What search engines read about a register project page (/projects/<slug> with no agent listing): the title, the description
 * and the structured data (docs/plan/project-page-v2.md, "SEO"). The visible page lives in components/site/RegisterProjectPage.
 *
 * Rules kept from docs/plan/seo-system.md and rank-loop.md: the name buyers search for (search_name) leads, MahaRERA's legal name
 * stays in the body and JSON-LD, the page doctor's search_description wins when it has one, and whole parts are dropped to fit,
 * never half a word. Every fact here is one the page shows; an empty one is left out rather than written as null.
 */
import { BRAND_NAME } from '@/lib/brand'
import { breadcrumbJsonLd } from '@/lib/marketing/seo'
import { clipWords, fitDescription } from './format'
import { areaName, askedPrices, displayName, monthYear, offerPrice, otherNames, placePath, unitWord } from './register'
import type { Faq, Offer, RegisterProject } from './register'

/** Titles longer than this get cut in Google's results on phones; the first option that fits is used. */
export const PROJECT_TITLE_MAX = 65

/** The price a page quotes: the agent's live sheet (offerPrice) when there is one, else the asked prices we publish. */
export type QuotedPrice = { from: string; bhks: string } | null | undefined

/** "3 & 4 BHK" from the asked price rows; rows that are not a BHK size ("All homes", "Shop") say nothing about sizes. */
export function priceRowBhks(p: Pick<RegisterProject, 'prices'>): string {
  const nums: string[] = []
  for (const r of p.prices?.rows ?? []) {
    const m = /^\s*(\d+(?:\.\d+)?)\s*BHK\s*$/i.exec(r.bhk || '')
    if (m && r.from_inr > 0 && !nums.includes(m[1])) nums.push(m[1])
  }
  nums.sort((a, b) => Number(a) - Number(b))
  if (!nums.length) return ''
  return (nums.length > 1 ? `${nums.slice(0, -1).join(', ')} & ${nums[nums.length - 1]}` : nums[0]) + ' BHK'
}

/** The page's price in words: the offer as given, else the lowest asked price with the BHK sizes that have a row of their own. */
function quoted(p: RegisterProject, price: QuotedPrice): { from: string; bhks: string } | null {
  if (price) return { from: price.from, bhks: price.bhks }
  const asked = askedPrices(p)
  return asked ? { from: asked.from, bhks: priceRowBhks(p) } : null
}

/** "Park Eden Kharadi": the searched name with the area after it, unless the name already says the area. */
function nameAt(p: RegisterProject): { shown: string; at: string } {
  const shown = displayName(p)
  const area = areaName(p)
  return { shown, at: area && !shown.toLowerCase().includes(area.toLowerCase()) ? `${shown} ${area}` : shown }
}

/** Search result title: "<name> <area>: 3 & 4 BHK from ₹1.99 Cr, possession Feb 2031". Without a price it is the MahaRERA number
 *  ("<name> <area>: MahaRERA P521..., possession Feb 2031"). Parts go in a fixed order to fit PROJECT_TITLE_MAX: the BHK sizes,
 *  then the possession date, then the area; the price stays while any title with it fits. `price`: offerPrice of the agent's
 *  sheet, so the title quotes the price the page shows. */
export function registerTitle(p: RegisterProject, price?: QuotedPrice): string {
  const { shown, at } = nameAt(p)
  const when = monthYear(p.completion_now)
  const q = quoted(p, price)
  const options: string[] = []
  if (q) {
    const sized = q.bhks ? `${q.bhks} from ${q.from}` : `from ${q.from}`
    const bare = `from ${q.from}`
    for (const name of [at, shown]) {
      if (when) options.push(`${name}: ${sized}, possession ${when}`, `${name}: ${bare}, possession ${when}`)
      options.push(`${name}: ${sized}`, `${name}: ${bare}`)
    }
  }
  for (const name of [at, shown]) {
    if (when) options.push(`${name}: MahaRERA ${p.regno}, possession ${when}`, `${name}: possession ${when}, MahaRERA`, `${name}: possession ${when}`)
    else options.push(`${name}: MahaRERA ${p.regno}`, `${name}: MahaRERA`)
  }
  return options.find((t) => t.length <= PROJECT_TITLE_MAX) ?? at
}

/** "1,310–1,720 sq ft" from the rows' sizes (each row's size is the one its lowest price is for); "" without any. */
function sqftRange(p: RegisterProject): string {
  const s = (p.prices?.rows ?? []).map((r) => r.sqft ?? 0).filter((x) => x > 0)
  if (!s.length) return ''
  const lo = Math.min(...s)
  const hi = Math.max(...s)
  const n = (x: number) => x.toLocaleString('en-IN')
  return lo === hi ? `${n(lo)} sq ft` : `${n(lo)}–${n(hi)} sq ft`
}

/** Search result description. The page doctor's search_description when it has one, unless the page quotes a price that text
 *  leaves out (an agent's sheet, or asked prices it does not mention): then the facts, "<name>, <area>, Pune: 3 & 4 BHK,
 *  1,310–1,720 sq ft, from ₹1.99 Cr. Possession Feb 2031, 27 of 249 homes booked. MahaRERA P521..., checked by Avasetu."
 *  Over 160 characters the legal name goes first, then the builder, the sizes in sq ft, "checked by", the bookings; the price,
 *  possession and MahaRERA number always stay. */
export function registerDescription(p: RegisterProject, price?: QuotedPrice): string {
  const q = quoted(p, price)
  const doctor = (p.search_description || '').trim()
  if (doctor && !price && (!q || doctor.includes('₹'))) return clipWords(doctor)
  const { shown } = nameAt(p)
  const legal = shown.toLowerCase() !== p.name.toLowerCase() ? ` (${p.name})` : ''
  const area = areaName(p)
  const by = p.builder?.name || p.promoter
  // the agent's sheet has its own sizes: the portals' square feet are not quoted beside its price
  const sqft = price ? '' : sqftRange(p)
  const when = monthYear(p.completion_now)
  return fitDescription((has) => {
    const head = `${shown}${has(1) ? legal : ''}${by && has(2) ? ` by ${by}` : ''}${area ? `, ${area}` : ''}, Pune`
    const sizes = [q?.bhks, has(3) ? sqft : ''].filter(Boolean)
    // "3 & 4 BHK from ₹1.99 Cr", or with the sizes "3 & 4 BHK, 1,310–1,720 sq ft, from ₹1.99 Cr"
    const offer = q ? `${sizes.join(', ')}${sizes.length > 1 || (sizes.length && !q.bhks) ? ',' : ''} from ${q.from}`.trim() : ''
    const homes = p.units_total
      ? (p.units_booked != null ? `${p.units_booked} of ${p.units_total} ${unitWord(p)} booked` : `${p.units_total} ${unitWord(p)}`) : ''
    const record = [when ? `Possession ${when}` : '', has(5) ? homes : ''].filter(Boolean).join(', ')
    const check = `MahaRERA ${p.regno}${has(4) ? `, checked by ${BRAND_NAME}` : ''}`
    return [`${head}${offer ? `: ${offer}` : ''}.`, record ? `${record}.` : '', `${check}.`].filter(Boolean).join(' ')
  })
}

export interface RegisterJsonLdInput {
  p: RegisterProject
  siteUrl: string
  /** the questions the page shows (projectFaq): FAQPage carries the same words */
  faq?: Faq[]
  /** the builder's pictures the page shows, best first (site-relative or absolute) */
  photos?: { url: string }[]
  /** the agent's offer from the property's fact sheet: when it has a sale price the page quotes it instead of the asked prices */
  offer?: Offer | null
  /** the page's last change (projectUpdated) */
  updated?: string | null
}

type Ld = Record<string, unknown>

/** Drops undefined, null, "" and empty lists so the data never states an empty fact. */
function clean<T extends Ld>(o: T): T {
  return Object.fromEntries(Object.entries(o).filter(([, v]) => v != null && v !== '' && !(Array.isArray(v) && !v.length))) as T
}

const floorSize = (sqft: number | null | undefined): Ld | undefined =>
  sqft && sqft > 0 ? { '@type': 'QuantitativeValue', value: sqft, unitCode: 'FTK' } : undefined

/** One Offer per home size the page prices: the agent's sheet when it has one, else the asked price rows. A row priced as a range
 *  is an AggregateOffer. The home is the itemOffered, so its floor size has a place to sit. */
function offers(p: RegisterProject, name: string, offer: Offer | null | undefined): Ld[] {
  const at = (label: string) => (/^\d+(\.\d+)?$/.test(label) ? `${label} BHK` : label) + ` at ${name}`
  const home = (label: string, sqft?: number | null): Ld => clean({ '@type': 'Apartment', name: at(label), floorSize: floorSize(sqft) })
  if (offerPrice(offer)) {
    const o = offer as Offer
    const sheet = o.homes && o.homes.length > 1 ? o.homes.filter((h) => h.price_inr && h.price_inr > 0) : null
    if (sheet?.length) {
      return sheet.map((h) => ({ '@type': 'Offer', name: at(h.label), price: h.price_inr, priceCurrency: 'INR', itemOffered: home(h.label, h.carpet_sqft) }))
    }
    const label = o.bhk ? `${o.bhk} BHK` : /plot/i.test(o.property_type || '') ? 'Plot' : 'Homes'
    return [{ '@type': 'Offer', name: at(label), price: o.price_inr, priceCurrency: 'INR', itemOffered: home(label, o.carpet_sqft) }]
  }
  return (p.prices?.rows ?? []).filter((r) => r.from_inr > 0).map((r) => {
    const label = /^all\b/i.test(r.bhk) ? 'Homes' : r.bhk
    const range = r.to_inr && r.to_inr > r.from_inr
    return clean({
      '@type': range ? 'AggregateOffer' : 'Offer', name: at(label),
      ...(range ? { lowPrice: r.from_inr, highPrice: r.to_inr } : { price: r.from_inr }),
      priceCurrency: 'INR',
      validFrom: p.prices?.read_at || undefined,
      itemOffered: home(label, r.sqft),
    })
  })
}

/** The structured data for a register project page, in render order: ApartmentComplex (with its offers and builder),
 *  BreadcrumbList (the trail the page shows), FAQPage when there are questions, WebPage when the page has a dated change. */
export function registerProjectJsonLd({ p, siteUrl, faq = [], photos = [], offer = null, updated = null }: RegisterJsonLdInput): Ld[] {
  const url = `${siteUrl}/projects/${p.slug}`
  const shown = displayName(p)
  const area = areaName(p)
  const builder = p.builder?.name || p.promoter
  const price = offerPrice(offer)
  const complex = clean({
    '@context': 'https://schema.org', '@type': 'ApartmentComplex', name: shown, url,
    alternateName: otherNames(p),
    description: registerDescription(p, price),
    address: clean({ '@type': 'PostalAddress', addressLocality: area ? `${area}, Pune` : 'Pune', addressRegion: 'Maharashtra', postalCode: p.pincode || undefined, addressCountry: 'IN' }),
    geo: p.map ? { '@type': 'GeoCoordinates', latitude: p.map.lat, longitude: p.map.lon } : undefined,
    numberOfAccommodationUnits: p.units_total || undefined,
    identifier: { '@type': 'PropertyValue', propertyID: 'MahaRERA registration', value: p.regno },
    builder: builder ? { '@type': 'Organization', name: builder } : undefined,
    // the builder's pictures we keep (profile): never illustrations or unchecked ones
    image: photos.filter((x) => !!x.url).slice(0, 6).map((x) => (x.url.startsWith('/') ? siteUrl + x.url : x.url)),
    offers: offers(p, shown, offer),
    sameAs: p.maharera_url || undefined,
    // one tower of a marketed project registered tower by tower: the whole project is the place this one is in
    containedInPlace: p.group ? { '@type': 'ApartmentComplex', name: p.group.name, url: siteUrl + p.group.path } : undefined,
  })
  // the same levels as the visible breadcrumb: the locality guide, else the Pune place list
  const placeCrumb = p.area ? { name: p.area.name, path: `/localities/${p.area.slug}` }
    : p.pune_place?.name ? { name: p.pune_place.name, path: placePath(p.pune_place.key.replace(/_/g, '-')) } : null
  const crumbs = [{ name: 'Home', path: '/' }, { name: 'Projects', path: '/projects' }, ...(placeCrumb ? [placeCrumb] : []),
    { name: shown, path: `/projects/${p.slug}` }]
  return [
    complex,
    breadcrumbJsonLd(siteUrl, crumbs),
    ...(faq.length ? [{ '@context': 'https://schema.org', '@type': 'FAQPage',
      mainEntity: faq.map((f) => ({ '@type': 'Question', name: f.q, acceptedAnswer: { '@type': 'Answer', text: f.a } })) }] : []),
    ...(updated ? [{ '@context': 'https://schema.org', '@type': 'WebPage', url, name: shown, dateModified: updated }] : []),
  ]
}
