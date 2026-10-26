import React from 'react'
import Link from 'next/link'
import type { FacetRow } from '@/lib/site/facets'
import { formatPrice, readableName } from '@/lib/site/format'
import { monthYear } from '@/lib/site/register'
import OpenChatButton from './OpenChatButton'
import Skyline from './Skyline'

/** One project as a card, the same on the Top list, the area page's rows and the home page (docs/plan/area-intent-pages.md,
 *  "Top projects" redesign 2026-10-26): picture with where it came from, stage, price or "ask", possession filed, homes open.
 *  Facts only, from the list row the backend made (seo/facets.py _row); a missing fact is left out, never guessed. */

export const STAGE_TAG: Record<NonNullable<FacetRow['stage']>, string> = {
  'new-launch': 'New launch',
  'under-construction': 'Under construction',
  'possession-soon': 'Possession soon',
  // the filed date passed; MahaRERA does not show the occupancy certificate, so the card cannot say "ready" (owner review 2026-10-26)
  ready: 'Date passed',
}

/** The picture's tag: a passed date names the month and the check to make ("Due Dec 2025 · ask for OC"), in amber. */
function stageTag(r: FacetRow): string | null {
  if (!r.stage) return null
  if (r.stage === 'ready' && r.completion_now) return `Due ${monthYear(r.completion_now)} · ask for OC`
  return STAGE_TAG[r.stage]
}

/** A launch with nothing booked yet: "0 of 137 booked" reads as nobody wanting it, when booking has only just opened. */
function justOpened(r: FacetRow): boolean {
  return r.stage === 'new-launch' && r.units_booked === 0 && !!r.units_total
}

// a picture that is not the builder's own says so, as the project page does (ProfilePictures)
// ("Not checked by us" read as if the project's facts were not checked, on a site whose word is "checked": owner review 2026-10-26)
const PHOTO_NOTE: Record<string, string> = { ai: 'AI illustration', brochure: "Artist's impression", web: 'Photo from the web' }

export function cardPrice(r: FacetRow): string | null {
  // a size list's own price first: the cheapest of any size put a 1 BHK price on the 2 BHK row (96 Arrcade, 2026-10-26)
  if (r.price_from != null) return `${formatPrice(r.price_from)}${r.price_to ? ` to ${formatPrice(r.price_to)}` : ''}`
  if (r.price) return `${r.price.bhk} BHK ${formatPrice(r.price.from_inr)}${r.price.to_inr ? ` to ${formatPrice(r.price.to_inr)}` : ''}`
  return null
}

function Picture({ r, rank, tall }: { r: FacetRow; rank?: number; tall?: boolean }) {
  const note = r.photo ? PHOTO_NOTE[r.photo.source] : undefined
  const tag = stageTag(r)
  return (
    <div className={`relative overflow-hidden bg-slate-200 ${tall ? 'h-44 sm:h-full sm:min-h-[200px]' : 'h-32'}`}>
      {r.photo
        ? <img src={r.photo.url} alt={r.photo.alt || r.name} loading="lazy" className="absolute inset-0 h-full w-full object-cover" />
        // no picture: the skyline the listing cards use, not a lone first letter (it read as a broken image)
        : <span aria-hidden className="absolute inset-0 flex flex-col justify-end bg-gradient-to-b from-[#102340] to-[#183a5d]"><Skyline className="block h-1/2 w-full" /></span>}
      {rank != null && (
        <span className="absolute left-2 top-2 flex h-8 w-8 items-center justify-center rounded-full bg-[#0f2340] text-sm font-bold text-white">
          <span className="sr-only">Rank </span>{rank}
        </span>
      )}
      {tag && <span className={`absolute bottom-2 left-2 rounded-full px-2.5 py-1 text-xs font-bold ${r.stage === 'ready' ? 'bg-[#fdf0d3] text-[#6b4a0b]' : 'bg-white/95 text-[#0f2340]'}`}>{tag}</span>}
      {note && <span className="absolute bottom-2 right-2 rounded bg-black/60 px-1.5 py-0.5 text-[11px] text-white">{note}</span>}
    </div>
  )
}

function Booked({ r }: { r: FacetRow }) {
  if (r.units_total == null || r.units_booked == null || !r.units_total) return null
  if (justOpened(r)) return <p className="text-sm text-slate-700"><b className="text-slate-900">{r.units_total.toLocaleString('en-IN')} homes</b> · booking just opened</p>
  const pct = Math.round((100 * r.units_booked) / r.units_total)
  return (
    <div>
      <div className="h-1.5 overflow-hidden rounded-full bg-slate-200" aria-hidden><div className="h-full bg-[#0f2340]" style={{ width: `${pct}%` }} /></div>
      <p className="mt-1 text-sm text-slate-700">
        {r.units_open != null && <b className="text-slate-900">{r.units_open.toLocaleString('en-IN')} homes open</b>}
        {r.units_open != null ? ' · ' : ''}{r.units_booked.toLocaleString('en-IN')} of {r.units_total.toLocaleString('en-IN')} booked ({pct}%)
      </p>
    </div>
  )
}

/** The Top list's ranked card: wide, with the reason it is here and two actions. */
export function RankedCard({ r }: { r: FacetRow }) {
  const price = cardPrice(r)
  return (
    <li className="overflow-hidden rounded-2xl border border-slate-200 bg-white sm:grid sm:grid-cols-[260px_1fr]" data-testid="ranked-card">
      <Picture r={r} rank={r.rank} tall />
      <div className="flex min-w-0 flex-col gap-2 p-4">
        <div>
          <Link href={`/projects/${r.slug}`} className="text-xl font-bold text-[#0f2340] underline-offset-2 hover:underline">{readableName(r.name)}</Link>
          {r.promoter && (
            <span className="text-slate-700"> by {r.builder_slug
              ? <Link href={`/builders/${r.builder_slug}`} className="text-[#0f2340] underline underline-offset-2">{readableName(r.promoter)}</Link>
              : readableName(r.promoter)}</span>
          )}
        </div>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm sm:grid-cols-3">
          <div><dt className="text-xs text-slate-500">Price</dt><dd className="font-semibold text-slate-900">{price ?? 'Ask for price'}</dd></div>
          {r.completion_now && <div><dt className="text-xs text-slate-500">Possession filed</dt><dd>{monthYear(r.completion_now)}</dd></div>}
          {r.registered_on && <div><dt className="text-xs text-slate-500">Registered</dt><dd>{monthYear(r.registered_on)}</dd></div>}
        </dl>
        <Booked r={r} />
        {/* the reason only when it adds something (homes booked lately); otherwise it is the line above again */}
        <p className="text-xs text-slate-500">{r.reason && !r.reason.startsWith(`${r.units_open} of `) ? `${r.reason} · ` : ''}MahaRERA {r.regno}</p>
        <div className="mt-1 flex flex-wrap gap-2">
          <Link href={`/projects/${r.slug}`} className="inline-flex min-h-[44px] items-center rounded-xl bg-[#0f2340] px-4 text-sm font-semibold text-white no-underline">See project</Link>
          <Link href={`/projects/${r.slug}#enquire`} className="inline-flex min-h-[44px] items-center rounded-xl border border-[#0f2340] px-4 text-sm font-semibold text-[#0f2340] no-underline">
            {price ? 'Ask about floor plans' : 'Get the price'}
          </Link>
        </div>
      </div>
    </li>
  )
}

/** A small card for a row of cards (ProjectRail): picture and name are one link to the project. The line under the name is
 *  the price when we have one; without one it is the homes booked (a bar, as on the Top list) and an "Ask the price" button
 *  that opens the chat about this project, so most cards no longer lead with the words "Ask for price" (owner review 2026-10-26). */
export function RailCard({ r, rank }: { r: FacetRow; rank?: number }) {
  const price = cardPrice(r)
  const name = readableName(r.name)
  const pct = r.units_total && r.units_booked != null ? Math.round((100 * r.units_booked) / r.units_total) : null
  const open = r.units_open != null && r.units_total
    ? (justOpened(r) ? `${r.units_total.toLocaleString('en-IN')} homes · booking just opened` : `${r.units_open.toLocaleString('en-IN')} of ${r.units_total.toLocaleString('en-IN')} homes open`)
    : null
  return (
    <div className="flex h-full flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white hover:border-[#0f2340]">
      <Link href={`/projects/${r.slug}`} className="block no-underline">
        <Picture r={r} rank={rank} />
        <span className="block px-3 pt-3">
          {/* underlined with an arrow: the card reads as a link at a glance on a phone (owner 2026-10-26) */}
          <span className="block font-bold leading-snug text-[#0f2340] underline decoration-[#f0b440] decoration-2 underline-offset-4">{name}<span aria-hidden className="ml-1">→</span></span>
          {price && <>{' '}<span className="mt-1 block text-sm font-semibold text-slate-900">{price}</span></>}
        </span>
      </Link>
      <div className="flex flex-1 flex-col px-3 pb-3">
        {!price && pct != null && !justOpened(r) && (
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-slate-200" aria-hidden><div className="h-full bg-[#0f2340]" style={{ width: `${pct}%` }} /></div>
        )}
        <p className="mt-1 text-xs text-slate-600">
          {[open, !price && pct != null && !justOpened(r) ? `${pct}% booked` : null, r.completion_now ? `possession ${monthYear(r.completion_now)}` : null].filter(Boolean).join(' · ')}
        </p>
        {!price && (
          <div className="mt-auto pt-3">
            <OpenChatButton message={`What is the price of ${name}?`} context={{ project: r.slug }} label="Ask the price"
              className="inline-flex min-h-[44px] w-full items-center justify-center rounded-xl border border-[#0f2340] text-sm font-semibold text-[#0f2340]" />
          </div>
        )}
      </div>
    </div>
  )
}
