import { getPropertyFacts } from './api'
import type { FinderItem } from './finder'
import { fromRegister } from './finderItems'
import type { Nearby } from './homeplan'
import { agentOffers } from './offers'
import { getRegisterPlaces, getRegisterProjects } from './register'

const EAST = 'East Pune'

/** East Pune projects still being sold, as finder items: every MahaRERA project whose Pune place is in the East Pune zone
 *  (app/core/pune_places.py), active, and not sold out unless a partner still lists it. `regnos` maps an item to its record. */
export async function eastItems(): Promise<{ items: FinderItem[]; regnos: Map<string, string> }> {
  const [all, places, offers] = await Promise.all([getRegisterProjects(undefined, true), getRegisterPlaces(), agentOffers()])
  const east = new Set(places.filter((p) => p.zone === EAST).map((p) => p.key))
  const selling = all.filter((r) => r.place && east.has(r.place) && r.active !== false
    && (!r.sold_out || offers.has(r.regno.toUpperCase())))
  return { items: fromRegister(selling, offers), regnos: new Map(selling.map((r) => [r.slug, r.regno])) }
}

/** The stored surroundings (schools, hospitals, ...) of a few picks, by item id; a project without them, or a failed read, has none. */
export async function nearbyOf(ids: string[], regnos: Map<string, string>): Promise<Map<string, Nearby[]>> {
  const got = await Promise.all(ids.map(async (id) => {
    const rera = regnos.get(id)
    const facts = rera ? await getPropertyFacts({ rera }).catch(() => null) : null
    return [id, (facts?.nearby ?? []) as Nearby[]] as const
  }))
  return new Map(got)
}
