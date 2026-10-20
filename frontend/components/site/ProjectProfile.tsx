import React from 'react'
import { formatDay } from '@/lib/site/projects'
import type { ProfilePicture, ProjectProfile as Profile } from '@/lib/site/profile'

function Picture({ pic, eager }: { pic: ProfilePicture; eager?: boolean }) {
  return (
    <a href={pic.url} target="_blank" rel="noopener" className="block overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={pic.url} alt={pic.alt} width={pic.width ?? undefined} height={pic.height ?? undefined}
        loading={eager ? 'eager' : 'lazy'} decoding="async" className="h-full w-full object-cover" />
    </a>
  )
}

function Credit({ pics }: { pics: ProfilePicture[] }) {
  const sites = Array.from(new Map(pics.filter((p) => p.site).map((p) => [p.site, p.page_url])).entries())
  if (!sites.length) return null
  return (
    <p className="mt-2 text-xs text-slate-600">
      From the builder&apos;s website:{' '}
      {sites.map(([site, url], i) => (
        <React.Fragment key={site}>
          {i > 0 && ', '}
          {url ? <a href={url} target="_blank" rel="noopener nofollow" className="underline underline-offset-2">{site}</a> : site}
        </React.Fragment>
      ))}
      . Renders are the builder&apos;s artist&apos;s impressions; the plans are indicative. Check the sanctioned plans before you book.
    </p>
  )
}

/** Highlights, the builder's pictures and floor plans of a project still being built (backend areastats/profile.py). `part` shows
 * one of them, so a page can put the pictures first and the plans next to the prices. */
export default function ProjectProfile({ profile, name, part }: { profile: Profile | null | undefined; name: string; part?: 'highlights' | 'photos' | 'plans' }) {
  if (!profile) return null
  const highlights = !part || part === 'highlights' ? profile.highlights : []
  const photos = !part || part === 'photos' ? profile.photos : []
  const plans = !part || part === 'plans' ? profile.plans : []
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
          <h2 id="photos-title" className="text-xl font-bold">Pictures of {name}</h2>
          <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
            {photos.map((p, i) => (
              <div key={p.url} className={i === 0 ? 'col-span-2 aspect-[16/9] sm:col-span-3' : 'aspect-[4/3]'}>
                <Picture pic={p} eager={i === 0} />
              </div>
            ))}
          </div>
          <Credit pics={photos} />
        </section>
      )}
      {plans.length > 0 && (
        <section aria-labelledby="plans-title" data-testid="plans">
          <h2 id="plans-title" className="text-xl font-bold">Floor plans of {name}</h2>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            {plans.map((p) => (
              <figure key={p.url}>
                <div className="aspect-[16/10] [&_img]:object-contain"><Picture pic={p} /></div>
                <figcaption className="mt-1 text-sm text-slate-700">{p.alt}</figcaption>
              </figure>
            ))}
          </div>
          <Credit pics={plans} />
        </section>
      )}
    </>
  )
}
