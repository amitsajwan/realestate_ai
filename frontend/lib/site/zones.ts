import type { RegisterPlace } from './register'

// Pune's parts as the register groups its places (backend register places, in zone order): the home page's zone panel and its
// areas by zone.

/** One part of Pune as the register groups it (East Pune, Pimpri-Chinchwad, ...), with the projects being built there. */
export interface Zone { name: string; id: string; current: number; places: RegisterPlace[] }

// the district's towns (Lonavala, Shirur, ...) come after the city's zones whatever their count
const OUTSIDE = 'Pune district'
const EAST = 'East Pune'
export const placeNow = (p: RegisterPlace): number => p.current ?? p.projects

/** The register's places grouped by zone: East Pune first (where we work first), then the biggest, the district last. A zone's
 *  places are the ones whose list is in search (a noindex list is never linked from here), most projects being built first. */
export function zonesOf(places: RegisterPlace[]): Zone[] {
  const by = new Map<string, RegisterPlace[]>()
  for (const p of places) if (p.zone) by.set(p.zone, [...(by.get(p.zone) ?? []), p])
  const rank = (z: Zone) => (z.name === EAST ? 0 : z.name === OUTSIDE ? 2 : 1)
  return [...by].map(([name, ps]) => ({
    name, id: 'zone-' + name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, ''),
    current: ps.reduce((n, p) => n + placeNow(p), 0),
    places: ps.filter((p) => p.indexable > 0).sort((a, b) => placeNow(b) - placeNow(a)),
  })).filter((z) => z.places.length > 0).sort((a, b) => rank(a) - rank(b) || b.current - a.current)
}
