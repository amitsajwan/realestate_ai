/**
 * Filtered project pages: "2 BHK in Wagholi" (/2-bhk/wagholi) and "75 lakh to 1 crore in Wagholi" (/price/75-lakh-1-crore/wagholi).
 * A page exists only when at least MIN_PROJECTS real, MahaRERA-checked projects in that area match, so there are no thin pages:
 * below that it is a 404 and it is not in the sitemap.
 */
import { LOCALITIES, type Locality } from '@/lib/marketing/localities'
import type { CatalogProject, ProjectConfiguration } from './types'

export const MIN_PROJECTS = 3

export const BHK_PAGES = [2, 3] as const
export type BhkPage = (typeof BHK_PAGES)[number]

export interface Band { slug: string; label: string; min: number; max: number }
const LAKH = 100_000
const CRORE = 10_000_000
export const BANDS: Band[] = [
  { slug: 'under-50-lakh', label: 'under 50 lakh', min: 0, max: 50 * LAKH },
  { slug: '50-75-lakh', label: '50 to 75 lakh', min: 50 * LAKH, max: 75 * LAKH },
  { slug: '75-lakh-1-crore', label: '75 lakh to 1 crore', min: 75 * LAKH, max: CRORE },
  { slug: '1-1.5-crore', label: '1 to 1.5 crore', min: CRORE, max: 1.5 * CRORE },
  { slug: '1.5-2-crore', label: '1.5 to 2 crore', min: 1.5 * CRORE, max: 2 * CRORE },
]

export interface Filter { kind: 'bhk'; bhk: BhkPage }
export interface BandFilter { kind: 'band'; band: Band }
export type AnyFilter = Filter | BandFilter

/** Which of a project's homes the filter is about: 2 BHK pages include 2.5 BHK; a band takes the price as quoted. */
export function matches(f: AnyFilter, c: ProjectConfiguration): boolean {
  return f.kind === 'bhk' ? c.bhk >= f.bhk && c.bhk < f.bhk + 1 : c.price_inr >= f.band.min && c.price_inr < f.band.max
}

export interface Match { project: CatalogProject; homes: ProjectConfiguration[] }

/** Projects in the area with at least one matching home, cheapest matching home first. */
export function filterProjects(items: CatalogProject[], area: Locality, f: AnyFilter): Match[] {
  const want = area.listingName.toLowerCase()
  return items
    .filter((p) => p.locality.trim().toLowerCase() === want)
    .map((p) => ({ project: p, homes: p.configurations.filter((c) => matches(f, c)) }))
    .filter((m) => m.homes.length > 0)
    .sort((a, b) => Math.min(...a.homes.map((h) => h.price_inr)) - Math.min(...b.homes.map((h) => h.price_inr)))
}

export function filterTitle(f: AnyFilter, area: Locality): string {
  return f.kind === 'bhk' ? `${f.bhk} BHK in ${area.name}, Pune` : `Homes ${f.band.label} in ${area.name}, Pune`
}

export function filterPath(f: AnyFilter, area: Locality): string {
  return f.kind === 'bhk' ? `/${f.bhk}-bhk/${area.slug}` : `/price/${f.band.slug}/${area.slug}`
}

/** Every filter page that has enough projects right now, for the sitemap and for links from area pages. */
export function livePages(items: CatalogProject[], areas: Locality[] = LOCALITIES): Array<{ path: string; title: string; area: Locality; count: number }> {
  const filters: AnyFilter[] = [...BHK_PAGES.map((bhk): AnyFilter => ({ kind: 'bhk', bhk })), ...BANDS.map((band): AnyFilter => ({ kind: 'band', band }))]
  const out = []
  for (const area of areas) {
    for (const f of filters) {
      const n = filterProjects(items, area, f).length
      if (n >= MIN_PROJECTS) out.push({ path: filterPath(f, area), title: filterTitle(f, area), area, count: n })
    }
  }
  return out
}
