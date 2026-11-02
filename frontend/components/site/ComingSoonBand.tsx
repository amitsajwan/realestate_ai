import React from 'react'
import Link from 'next/link'
import { getUpcomingBriefs, type UpcomingBrief } from '@/lib/site/hubs'
import { getRegisterPlaces, type RegisterPlace } from '@/lib/site/register'

/** The East Pune band: projects MahaRERA has not registered yet (backend areastats/upcoming.py). The RERA Act does not let anyone
 *  advertise or sell an unregistered project, so it stays this small: the builder's logo, the place and the home types, with
 *  "not yet registered" on it. Never a price, an offer or a booking; the one ask is to hear first. Hidden outside East Pune and
 *  when nothing is coming. East Pune pages carry it as a small corner card (ComingSoonDock); /projects/upcoming shows it in full. */
export const COMING_SOON_ZONE = 'East Pune'

/** Is this place, by its slug or key, one the band runs on? */
export function inComingSoonZone(places: RegisterPlace[], place?: string | null): boolean {
  return !!place && places.some((p) => (p.slug === place || p.key === place) && p.zone === COMING_SOON_ZONE)
}

/** The page's own area first. */
export function ownAreaFirst(items: UpcomingBrief[], place?: string | null): UpcomingBrief[] {
  const here = (u: UpcomingBrief) => u.area_slug === place || u.area === place
  return [...items.filter(here), ...items.filter((u) => !here(u))]
}

export function ComingSoonView({ items, place, className = '' }: { items: UpcomingBrief[]; place?: string | null; className?: string }) {
  if (!items.length) return null
  const sorted = ownAreaFirst(items, place)
  return (
    <section aria-labelledby="coming-soon-title" className={`rounded-2xl bg-[#0f2340] p-4 text-white sm:p-6 ${className}`} data-testid="coming-soon-band">
      <h2 id="coming-soon-title" className="text-xl font-bold">Launching soon in East Pune</h2>
      <p className="mt-1 text-sm text-slate-200">Be first to know. Price and any launch offer come out the day MahaRERA registers the project, and we tell you that day.</p>
      <ul className="mt-4 grid list-none gap-3 p-0 sm:grid-cols-3">
        {sorted.map((u) => (
          <li key={u.slug}>
            <Link href={`/projects/upcoming/${u.slug}#enquire`} className="flex h-full flex-col rounded-xl bg-white p-3 text-[#0f2340] no-underline hover:ring-2 hover:ring-amber-300">
              <span className="flex h-10 items-center">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                {u.logo ? <img src={u.logo} alt={`${u.builder} logo`} loading="lazy" decoding="async" className="max-h-10 w-auto max-w-[150px] object-contain" />
                  : <span className="font-bold">{u.builder}</span>}
              </span>
              <span className="mt-2 font-semibold">{u.name}</span>
              <span className="text-sm text-slate-700">{u.area_name}{u.note ? ` · ${u.note}` : ''}</span>
              <span className="mt-3 inline-flex min-h-[44px] items-center justify-center rounded-lg bg-amber-300 px-3 font-semibold text-[#0f2340]">Tell me first</span>
            </Link>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-xs text-slate-300">Not yet registered with MahaRERA. Not an offer to sell, and no bookings are taken. Do not pay anyone a token until it has a MahaRERA number.</p>
    </section>
  )
}

/** What a page's corner card shows: nothing outside East Pune. */
export async function comingSoonFor(place?: string | null): Promise<UpcomingBrief[]> {
  if (!inComingSoonZone(await getRegisterPlaces(), place)) return []
  return ownAreaFirst(await getUpcomingBriefs(), place)
}
