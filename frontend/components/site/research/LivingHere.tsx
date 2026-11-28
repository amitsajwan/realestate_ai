import React from 'react'
import Link from 'next/link'
import { trackerPath } from '@/lib/news/trackers'
import { hubPath, researchPath } from '@/lib/site/research'
import type { PlaceResearch, ResearchKind } from '@/lib/site/research'
import { kmText, minutes, monthLabel, rupees } from '@/lib/site/researchPages'

/** "Living in <place>" on a place page: one card per research page worth indexing (schools, commute, rent) with the fact that
 *  sums it up, then the work hubs and the trackers that touch the place. Nothing is drawn without at least one of them. */
export default function LivingHere({ research, placeName }: { research: PlaceResearch | null | undefined; placeName: string }) {
  if (!research) return null
  const b = research.blocks ?? {}
  const cards: Array<{ kind: ResearchKind; title: string; fact: string }> = []
  if (research.pages?.schools && b.schools?.schools?.length) {
    const t = b.schools.total_within_km
    cards.push({ kind: 'schools', title: `Schools in ${placeName}`, fact: t?.count ? `${t.count} schools within ${kmText(t.km)}` : `${b.schools.schools.length} schools` })
  }
  if (research.pages?.commute && b.commute?.rows?.length) {
    const r = b.commute.rows[0]
    cards.push({ kind: 'commute', title: `Commute from ${placeName}`, fact: `${r.hub}: ${minutes(r.am)} at 9 am` })
  }
  if (research.pages?.rent && b.rent?.rows?.length) {
    const r = b.rent.rows.find((x) => /^2\b/.test(x.bhk)) ?? b.rent.rows[0]
    cards.push({ kind: 'rent', title: `Rent in ${placeName}`, fact: `${r.bhk} ${rupees(r.low)} to ${rupees(r.high)} asked, ${monthLabel(b.rent.month, true)}` })
  }
  const hubs = (b.jobs?.hubs ?? []).filter((h) => h.hub_slug)
  const changes = (research.changes ?? []).slice(0, 4)
  if (!cards.length && !hubs.length && !changes.length) return null
  return (
    <section aria-labelledby="living-title" className="mt-10" data-testid="living-here">
      <h2 id="living-title" className="text-2xl font-bold text-slate-900">Living in {placeName}</h2>
      {cards.length > 0 && (
        <ul className="mt-4 grid list-none gap-3 p-0 sm:grid-cols-3">
          {cards.map((c) => (
            <li key={c.kind}>
              <Link href={researchPath(research.place, c.kind)} className="block min-h-[44px] rounded-xl border border-slate-200 bg-white px-4 py-3 no-underline hover:border-[#0f2340]">
                <span className="block font-semibold text-[#0f2340]">{c.title}</span>
                <span className="text-sm text-slate-600">{c.fact}</span>
              </Link>
            </li>
          ))}
        </ul>
      )}
      {hubs.length > 0 && (
        <p className="mt-4 text-slate-800" data-testid="living-hubs">
          Work nearby:{' '}
          {hubs.map((h, i) => (
            <React.Fragment key={h.hub_slug}>
              {i > 0 && ', '}
              <Link href={hubPath(h.hub_slug as string)} className="font-semibold text-[#0f2340] underline underline-offset-2">{h.hub}</Link> ({kmText(h.km)})
            </React.Fragment>
          ))}
        </p>
      )}
      {changes.length > 0 && (
        <p className="mt-2 text-slate-800" data-testid="living-changes">
          Changing nearby:{' '}
          {changes.map((c, i) => (
            <React.Fragment key={c.slug}>
              {i > 0 && ', '}
              <Link href={trackerPath(c.slug)} className="font-semibold text-[#0f2340] underline underline-offset-2">{c.name}</Link>
            </React.Fragment>
          ))}
        </p>
      )}
    </section>
  )
}
