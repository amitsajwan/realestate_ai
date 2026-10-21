import React from 'react'
import type { ProfilePicture } from '@/lib/site/profile'

/** A project's pictures and where they came from (backend areastats/profile.py): used by ProjectProfile and FloorPlansLock. */
export const sourceOf = (p: ProfilePicture) => p.source ?? 'builder'

export function Picture({ pic, eager }: { pic: ProfilePicture; eager?: boolean }) {
  return (
    <a href={pic.url} target="_blank" rel="noopener" className="relative block h-full overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={pic.url} alt={pic.alt} width={pic.width ?? undefined} height={pic.height ?? undefined}
        loading={eager ? 'eager' : 'lazy'} decoding="async" className="h-full w-full object-cover" />
      {sourceOf(pic) !== 'builder' && (
        <span className="absolute left-2 top-2 rounded bg-black/70 px-2 py-0.5 text-xs font-semibold text-white">
          {sourceOf(pic) === 'ai' ? 'AI illustration' : 'Not checked by us'}
        </span>
      )}
    </a>
  )
}

export function Credit({ pics, name }: { pics: ProfilePicture[]; name?: string }) {
  const drawn = pics.some((p) => sourceOf(p) === 'ai')
  const web = pics.filter((p) => sourceOf(p) === 'web')
  const own = pics.filter((p) => sourceOf(p) === 'builder')
  return (
    <>
      {drawn && (
        <p className="mt-2 text-xs text-slate-600">
          Illustrations made by AI from the MahaRERA facts (towers, floors): they are not pictures of {name || 'the project'}. Ask us for the builder&apos;s pictures.
        </p>
      )}
      {web.length > 0 && <Sites pics={web} lead="From other sites about the project, not checked by us:" end="Check with the builder before you rely on them." />}
      {own.length > 0 && <Sites pics={own} lead="From the builder's website:"
        end="Renders are the builder's artist's impressions; the plans are indicative. Check the sanctioned plans before you book." />}
    </>
  )
}

function Sites({ pics, lead, end }: { pics: ProfilePicture[]; lead: string; end: string }) {
  const sites = Array.from(new Map(pics.filter((p) => p.site).map((p) => [p.site, p.page_url])).entries())
  if (!sites.length) return null
  return (
    <p className="mt-2 text-xs text-slate-600">
      {lead}{' '}
      {sites.map(([site, url], i) => (
        <React.Fragment key={site}>
          {i > 0 && ', '}
          {url ? <a href={url} target="_blank" rel="noopener nofollow" className="underline underline-offset-2">{site}</a> : site}
        </React.Fragment>
      ))}
      . {end}
    </p>
  )
}
