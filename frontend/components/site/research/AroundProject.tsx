import React from 'react'
import { researchPath } from '@/lib/site/research'
import type { PlaceResearch, ProjectResearch } from '@/lib/site/research'
import { measuredFrom } from '@/lib/site/researchPages'
import { BeingBuilt, ChangesList, CommuteTable, RentTable, SchoolsList, WorkNearby } from './ResearchBlocks'

/** "Around <project>" after Location on a project page (docs/plan/pune-intelligence.md C): commute, what is changing nearby,
 *  being built, schools, asked rent, work nearby, in that order, each only when the backend measured it. Distances and drive
 *  times are from the project's own Google pin when it has one, else from the place's centre, and the block says which. A block
 *  links its place's page of the same kind only when that page is worth indexing (`pages`). */
export default function AroundProject({ research, name, placeName, pages = null }: {
  research: ProjectResearch | null | undefined; name: string; placeName: string; pages?: PlaceResearch['pages'] | null
}) {
  if (!research) return null
  const b = research.blocks ?? {}
  const changes = research.changes ?? []
  const any = !!(b.commute?.rows?.length || changes.length || b.being_built?.projects || b.schools?.schools?.length || b.rent?.rows?.length || b.jobs?.hubs?.length)
  if (!any) return null
  const from = measuredFrom(research.pinned, placeName)
  const more = (kind: 'schools' | 'commute' | 'rent', label: string) => (pages?.[kind] ? { href: researchPath(research.place, kind), label } : null)
  return (
    <section aria-labelledby="around-title" data-testid="around">
      <h2 id="around-title" className="text-xl font-semibold text-slate-900">Around {name}</h2>
      <p className="mt-1 text-sm text-slate-600">Measured {from}, each with its source and date.</p>
      <div className="mt-4 space-y-8">
        <CommuteTable b={b.commute} from={from} more={more('commute', `Commute from ${placeName}`)} />
        <ChangesList changes={changes} />
        <BeingBuilt b={b.being_built} />
        <SchoolsList b={b.schools} from={from} more={more('schools', `All schools in ${placeName}`)} />
        <RentTable b={b.rent} more={more('rent', `Rent in ${placeName}`)} />
        <WorkNearby b={b.jobs} />
      </div>
    </section>
  )
}
