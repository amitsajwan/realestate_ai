import React from 'react'
import SourceKind from './SourceKind'
import { formatDay } from '@/lib/site/projects'
import type { ProjectProfile as Profile } from '@/lib/site/profile'
import { Credit, Picture, distinctPhotos, sourceOf } from '@/components/site/ProfilePictures'
import FloorPlansLock, { type PlansLead } from '@/components/site/FloorPlansLock'
import type { Drawing } from '@/components/site/Plans3D'

/** Highlights, the builder's pictures and floor plans of a project still being built (backend areastats/profile.py). `part` shows
 * one of them, so a page can put the pictures first and the plans next to the prices. Floor plans are always behind a short
 * form (owner 2026-10-22: "floor plans locked, ask for the form"): shown only with `lead`, even when we have none yet. `skip` is a
 * picture already shown elsewhere on the page (the register page's hero), so the gallery does not repeat it. `omit` leaves out
 * highlight topics the page already says (the register page's hero names the BHK types, so its "homes" bullet would repeat them).
 * `plans3d`: our 3D drawings of the checked plans, shown in the plans' place after the form. */
const FACT_TOPICS = ['open_space', 'homes', 'towers', 'design']

/** One list of highlights. Where a point was read is said only when it matters: the builder's own site, or a single property site;
 *  the sources stay on the record (owner 2026-11-04: "(2 property sites)", do we need to give this detail?). */
function Points({ items }: { items: Profile['highlights'] }) {
  return (
    <ul className="mt-3 space-y-2">
      {items.map((h) => (
        <li key={h.topic} className="flex gap-2 text-slate-800">
          <span aria-hidden className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--site-primary,#0f2340)]" />
          <span>
            {h.text}.{' '}
            {h.official
              ? <span className="text-xs text-slate-500">(<SourceKind sources={h.sources.slice(0, 1)} official />)</span>
              : h.sources.length === 1 && <span className="text-xs text-slate-500">(one property site)</span>}
          </span>
        </li>
      ))}
    </ul>
  )
}

export default function ProjectProfile({ profile, name, part, lead, skip, omit = [], plans3d = [] }: {
  profile: Profile | null | undefined; name: string; part?: 'highlights' | 'photos' | 'plans'; lead?: PlansLead; skip?: string | null
  omit?: string[]; plans3d?: Drawing[]
}) {
  const showPlans = (!part || part === 'plans') && !!lead
  if (!profile) return showPlans && lead ? <FloorPlansLock plans={[]} drawn={plans3d} name={name} lead={lead} /> : null
  const highlights = !part || part === 'highlights' ? profile.highlights.filter((h) => !omit.includes(h.topic)) : []
  // land, towers and the like are facts about the project, not amenities; land first, it is what buyers ask (owner 2026-11-04)
  const projectFacts = FACT_TOPICS.flatMap((t) => highlights.filter((h) => h.topic === t))
  const amenities = highlights.filter((h) => !FACT_TOPICS.includes(h.topic))
  const photos = !part || part === 'photos' ? distinctPhotos(profile.photos ?? []).filter((x) => !skip || x.url !== skip) : []
  const drawn = photos.length > 0 && photos.every((p) => sourceOf(p) === 'ai')
  return (
    <>
      {highlights.length > 0 && (
        <section aria-labelledby="highlights-title" data-testid="highlights">
          {projectFacts.length > 0 && (
            <>
              <h2 id={amenities.length ? 'facts-title' : 'highlights-title'} className="text-xl font-bold">{name} project facts</h2>
              <Points items={projectFacts} />
            </>
          )}
          {amenities.length > 0 && (
            <>
              <h2 id="highlights-title" className={`text-xl font-bold${projectFacts.length ? ' mt-6' : ''}`}>{name} amenities</h2>
              <Points items={amenities} />
            </>
          )}
          <p className="mt-2 text-xs text-slate-600">
            From the builder&apos;s site and property sites{profile.read_at ? `, read on ${formatDay(profile.read_at)}` : ''}. Property sites can be wrong: confirm with the builder before you book.
            Dates and bookings come only from MahaRERA.
          </p>
        </section>
      )}
      {photos.length > 0 && (
        <section aria-labelledby="photos-title" data-testid="photos">
          <h2 id="photos-title" className="text-xl font-bold">{drawn ? `What ${name} could look like` : `Pictures of ${name}`}</h2>
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
            {photos.map((p, i) => (
              <div key={p.url} className={i === 0 ? 'col-span-2 aspect-[16/9] sm:col-span-3' : 'aspect-[4/3]'}>
                <Picture pic={p} eager={i === 0} />
              </div>
            ))}
          </div>
          <Credit pics={photos} name={name} />
        </section>
      )}
      {showPlans && lead && <FloorPlansLock plans={profile.plans} drawn={plans3d} name={name} lead={lead} />}
    </>
  )
}
