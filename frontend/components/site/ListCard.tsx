import React from 'react'
import Link from 'next/link'
import { builderLine, cardFacts } from '@/lib/site/facets'
import type { FacetRow } from '@/lib/site/facets'
import { formatPrice, readableName } from '@/lib/site/format'
import { monthYear } from '@/lib/site/register'
import OpenChatButton from './OpenChatButton'
import CardPicture from './CardPicture'

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

export function cardPrice(r: FacetRow): string | null {
  // a size list's own price first: the cheapest of any size put a 1 BHK price on the 2 BHK row (96 Arrcade, 2026-10-26)
  if (r.price_from != null) return `${formatPrice(r.price_from)}${r.price_to ? ` to ${formatPrice(r.price_to)}` : ''}`
  if (r.price) return `${r.price.bhk} BHK ${formatPrice(r.price.from_inr)}${r.price.to_inr ? ` to ${formatPrice(r.price.to_inr)}` : ''}`
  return null
}

/** The card's picture slot (CardPicture): its pictures as a slideshow, else the project page's map or logo, else the skyline. */
export function ListPicture({ r, rank, tall }: { r: FacetRow; rank?: number; tall?: boolean }) {
  return <CardPicture m={r} name={readableName(r.name)} href={`/projects/${r.slug}`} rank={rank} tag={stageTag(r)}
    tagTone={r.stage === 'ready' ? 'warn' : 'plain'} height={tall ? 'h-44 sm:h-full sm:min-h-[200px]' : 'h-32'} />
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
  const builder = builderLine(r)
  const facts = cardFacts(r.reason)
  return (
    <li className="overflow-hidden rounded-2xl border border-slate-200 bg-white sm:grid sm:grid-cols-[260px_1fr]" data-testid="ranked-card">
      <ListPicture r={r} rank={r.rank} tall />
      <div className="flex min-w-0 flex-col gap-2 p-4">
        <div>
          <Link href={`/projects/${r.slug}`} className="text-xl font-bold text-[#0f2340] underline-offset-2 hover:underline">{readableName(r.name)}</Link>
          {builder.name && (
            <span className="text-slate-700"> by {r.builder_slug
              ? <Link href={`/builders/${r.builder_slug}`} className="text-[#0f2340] underline underline-offset-2">{readableName(builder.name)}</Link>
              : readableName(builder.name)}</span>
          )}
        </div>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-1 text-sm sm:grid-cols-3">
          <div><dt className="text-xs text-slate-500">Price</dt><dd className="font-semibold text-slate-900">{price ?? 'Ask for price'}</dd></div>
          {r.completion_now && <div><dt className="text-xs text-slate-500">Possession filed</dt><dd>{monthYear(r.completion_now)}</dd></div>}
          {r.registered_on && <div><dt className="text-xs text-slate-500">Registered</dt><dd>{monthYear(r.registered_on)}</dd></div>}
        </dl>
        <Booked r={r} />
        {/* why it is ranked here and the builder's date record, as a sentence; the homes open part is the bar above */}
        {facts && <p className="text-sm text-slate-800" data-testid="card-facts">{facts}</p>}
        <p className="text-xs text-slate-500">MahaRERA {r.regno}{builder.filedBy ? ` · filed by ${readableName(builder.filedBy)}` : ''}</p>
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

/** A small card for a row of cards (ProjectRail): picture and name both link to the project. The line under the name is
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
      {/* the picture links itself: its slideshow's arrows are buttons, which may not sit inside a link */}
      <ListPicture r={r} rank={rank} />
      <Link href={`/projects/${r.slug}`} className="block no-underline">
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
            <OpenChatButton message={`What is the price of ${name}?`} context={{ page: 'project', project: r.slug }} label="Ask the price"
              className="inline-flex min-h-[44px] w-full items-center justify-center rounded-xl border border-[#0f2340] text-sm font-semibold text-[#0f2340]" />
          </div>
        )}
      </div>
    </div>
  )
}
