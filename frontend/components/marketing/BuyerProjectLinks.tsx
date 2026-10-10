import React from 'react'
import Link from 'next/link'
import { LOCALITIES } from '@/lib/marketing/localities'
import { displayName, getRegisterPlaces, getRegisterProjects, placePath, projectSummary } from '@/lib/site/register'
import type { RegisterPlace } from '@/lib/site/register'

/** The homepage buyers' row: our localities' project hubs (/projects/area/{place}) and up to 8 of the biggest active projects in
 *  them. An outage gives empty lists, so the row shows only the area guides around it. */
export default async function BuyerProjectLinks({ eyebrow }: { eyebrow: string }) {
  const [places, register] = await Promise.all([getRegisterPlaces(), getRegisterProjects(undefined, true)])
  const ours = LOCALITIES.map((l) => places.find((p) => p.key === l.key || p.name.toLowerCase() === l.name.toLowerCase()))
    .filter((p): p is RegisterPlace => !!p && p.projects > 0)
  const hubs = ours.filter((p, i) => ours.findIndex((x) => x.slug === p.slug) === i)
  const keys = new Set(LOCALITIES.map((l) => l.key))
  const notable = register.filter((r) => r.area && keys.has(r.area) && r.indexable && r.active !== false)
    .sort((a, b) => (b.units_total ?? 0) - (a.units_total ?? 0)).slice(0, 8)
  return (
    <>
      {hubs.length > 0 && (
        <div className="mt-5">
          <h3 className={eyebrow}>New projects by area</h3>
          <ul className="mt-2 flex flex-wrap gap-2 p-0" data-testid="area-hubs">
            {hubs.map((h) => (
              <li key={h.slug} className="list-none">
                <Link href={placePath(h.slug)} className="inline-flex min-h-[44px] items-center rounded-full border border-[#0f2340]/40 bg-white px-4 text-[#0f2340] no-underline hover:border-[#0f2340]">
                  New projects in {h.name}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      )}
      {notable.length > 0 && (
        <div className="mt-5">
          <h3 className={eyebrow}>Projects buyers ask about</h3>
          <ul className="mt-2 grid gap-x-6 p-0 sm:grid-cols-2" data-testid="notable-projects">
            {notable.map((r) => (
              <li key={r.slug} className="list-none py-1">
                <Link href={`/projects/${r.slug}`} className="font-semibold text-[#0f2340] underline underline-offset-2">{displayName(r)}</Link>
                <span className="block text-sm text-slate-600">{projectSummary(r)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </>
  )
}
