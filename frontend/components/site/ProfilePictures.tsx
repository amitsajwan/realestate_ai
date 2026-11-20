import React from 'react'
import type { ProfilePicture } from '@/lib/site/profile'

/** A project's pictures and where they came from (backend areastats/profile.py): used by ProjectProfile and FloorPlansLock.
 *  The builder's, the brochure's and AI illustrations only: pictures copied from other sites never reach a page (backend
 *  pages.shown_pictures, 2026-10-29). */
export const sourceOf = (p: ProfilePicture) => p.source ?? 'builder'

/** The dHash a saved picture is named by ("…/9d0e0e4d29202c29.webp"), as two 32-bit halves; null for brochure and AI files. */
const hashOf = (p: ProfilePicture): [number, number] | null => {
  const m = /\/([0-9a-f]{16})\.webp$/.exec(p.url)
  return m ? [parseInt(m[1].slice(0, 8), 16), parseInt(m[1].slice(8), 16)] : null
}
const bits = (n: number) => { let c = 0; for (let x = n >>> 0; x; x &= x - 1) c++; return c }
const RANK: Record<string, number> = { agent: 0, builder: 0, brochure: 1, ai: 3 }

/** Photos with near-duplicates dropped (the same render twice, under 21 of 64 bits apart), as the backend's
 * profile.distinct_photos does: profiles saved before that rule still hold both copies until they are read again. */
export function distinctPhotos(photos: ProfilePicture[]): ProfilePicture[] {
  const groups: ProfilePicture[][] = []
  for (const p of photos) {
    const h = hashOf(p)
    const g = h && groups.find((g) => g.some((x) => { const k = hashOf(x); return !!k && bits(h[0] ^ k[0]) + bits(h[1] ^ k[1]) < 21 }))
    if (g) g.push(p)
    else groups.push([p])
  }
  const score = (p: ProfilePicture) => (RANK[sourceOf(p)] ?? 9) * 1e9 - (p.width ?? 0) * (p.height ?? 0)
  return groups.map((g) => g.reduce((a, b) => (score(b) < score(a) ? b : a)))
}

export function Picture({ pic, eager }: { pic: ProfilePicture; eager?: boolean }) {
  return (
    <a href={pic.url} target="_blank" rel="noopener" className="relative block h-full overflow-hidden rounded-xl border border-slate-200 bg-slate-50">
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={pic.url} alt={pic.alt} width={pic.width ?? undefined} height={pic.height ?? undefined}
        loading={eager ? 'eager' : 'lazy'} decoding="async" className="h-full w-full object-cover" />
      {sourceOf(pic) !== 'builder' && sourceOf(pic) !== 'agent' && !(sourceOf(pic) === 'brochure' && !/artist/i.test(pic.alt)) && (
        <span className="absolute left-2 top-2 rounded bg-black/70 px-2 py-0.5 text-xs font-semibold text-white">
          {sourceOf(pic) === 'ai' ? 'AI illustration' : "Artist's impression"}
        </span>
      )}
    </a>
  )
}

/** Where the pictures came from, in one line, and the renders' warning once: a gallery from an agent's listing and the builder's
 *  site said the same warning twice, back to back (outside review of Godrej Ivara, 2026-11-20). AI illustrations keep their own
 *  line, since what it says is different: they are not pictures of the project at all. */
export function Credit({ pics, name }: { pics: ProfilePicture[]; name?: string }) {
  const drawn = pics.some((p) => sourceOf(p) === 'ai')
  const own = pics.filter((p) => sourceOf(p) === 'builder')
  const brochure = pics.some((p) => sourceOf(p) === 'brochure')
  const agent = pics.find((p) => sourceOf(p) === 'agent')?.site
  const url = own.find((p) => p.page_url)?.page_url
  const from: React.ReactNode[] = []
  if (agent) from.push(<>{agent}&apos;s listing</>)
  if (own.length) from.push(url ? <a href={url} target="_blank" rel="noopener nofollow" className="underline underline-offset-2">the builder&apos;s website</a> : <>the builder&apos;s website</>)
  if (brochure) from.push(<>the builder&apos;s brochure, shared by an agent</>)
  return (
    <>
      {from.length > 0 && (
        <p className="mt-2 text-xs text-slate-600" data-testid="pictures-credit">
          From {from.map((x, i) => <React.Fragment key={i}>{i === 0 ? '' : i === from.length - 1 ? ' and ' : ', '}{x}</React.Fragment>)}.
          {' '}Renders are the builder&apos;s artist&apos;s impressions and plans are indicative: check the sanctioned plans before you book.
        </p>
      )}
      {drawn && (
        <p className="mt-2 text-xs text-slate-600">
          Illustrations made by AI from the MahaRERA facts (towers, floors): they are not pictures of {name || 'the project'}. Ask us for the builder&apos;s pictures.
        </p>
      )}
    </>
  )
}
