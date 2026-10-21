import React from 'react'
import { formatDay } from '@/lib/site/projects'
import type { ProjectProfile as Profile } from '@/lib/site/profile'
import { Credit, Picture, sourceOf } from '@/components/site/ProfilePictures'
import FloorPlansLock, { type PlansLead } from '@/components/site/FloorPlansLock'

/** Highlights, the builder's pictures and floor plans of a project still being built (backend areastats/profile.py). `part` shows
 * one of them, so a page can put the pictures first and the plans next to the prices. Floor plans are always behind a short
 * form (owner 2026-10-22: "floor plans locked, ask for the form"): shown only with `lead`, even when we have none yet. */
export default function ProjectProfile({ profile, name, part, lead }: {
  profile: Profile | null | undefined; name: string; part?: 'highlights' | 'photos' | 'plans'; lead?: PlansLead
}) {
  const showPlans = (!part || part === 'plans') && !!lead
  if (!profile) return showPlans && lead ? <FloorPlansLock plans={[]} name={name} lead={lead} /> : null
  const highlights = !part || part === 'highlights' ? profile.highlights : []
  const photos = !part || part === 'photos' ? profile.photos : []
  const drawn = photos.length > 0 && photos.every((p) => sourceOf(p) === 'ai')
  return (
    <>
      {highlights.length > 0 && (
        <section aria-labelledby="highlights-title" data-testid="highlights">
          <h2 id="highlights-title" className="text-xl font-bold">{name} at a glance</h2>
          <ul className="mt-3 space-y-2">
            {highlights.map((h) => (
              <li key={h.topic} className="flex gap-2 text-slate-800">
                <span aria-hidden className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--site-primary,#0f2340)]" />
                <span>
                  {h.text}.{' '}
                  <span className="text-xs text-slate-500">
                    ({h.sources.map((s, i) => (
                      <React.Fragment key={s.url}>
                        {i > 0 && ', '}
                        {h.official ? <a href={s.url} target="_blank" rel="noopener nofollow" className="underline underline-offset-2">{s.site}</a> : s.site}
                      </React.Fragment>
                    ))})
                  </span>
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-2 text-xs text-slate-600">
            Each point is on the builder&apos;s own site or on two property sites{profile.read_at ? `; read on ${formatDay(profile.read_at)}` : ''}.
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
      {showPlans && lead && <FloorPlansLock plans={profile.plans} name={name} lead={lead} />}
    </>
  )
}
