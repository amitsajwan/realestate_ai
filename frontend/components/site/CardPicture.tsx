'use client'
import React, { useState } from 'react'
import Link from 'next/link'
import type { BuilderLogo } from '@/lib/site/register'
import Skyline from './Skyline'

export interface CardPhoto { url: string; alt: string; source: string }

/** What a project card's picture slot can draw, as the backend sends it (areastats/areamap.py card_pictures). `photo` is the
 *  older one-picture field, used when `photos` is not there. */
export interface CardMedia {
  photos?: CardPhoto[] | null
  photo?: CardPhoto | null
  location_picture?: { url: string; width: number; height: number } | null
  logo?: BuilderLogo | null
}

// a picture that is not the builder's own says so, as the project page does (ProfilePictures); pictures copied from other
// sites are never sent (backend pages.shown_pictures, 2026-10-29)
const PHOTO_NOTE: Record<string, string> = { ai: 'AI illustration', brochure: "Artist's impression" }

export function cardPhotos(m: CardMedia): CardPhoto[] {
  if (m.photos?.length) return m.photos
  return m.photo ? [m.photo] : []
}

/** A project card's picture. With several pictures it is a slideshow the buyer steps through with the arrows (owner
 *  2026-11-01, "if there are multiple photos how about a slide show"); it never moves by itself, like the rows of cards it
 *  sits in (ProjectRail), and the arrows rather than a swipe move it, since a swipe on a phone already moves the row. With no
 *  picture it draws what the project page draws (owner 2026-11-01, "places where we don't have images"): the street map around
 *  the project's pin with the builder's logo over it, else the logo alone, else the skyline. Picture and name are one link to
 *  the project; the picture's link is kept out of the tab order and screen readers, so the name is the one they meet. */
export default function CardPicture({ m, name, href, rank, tag, tagTone = 'plain', height = 'h-32' }: {
  m: CardMedia; name: string; href: string; rank?: number; tag?: string | null; tagTone?: 'plain' | 'warn'; height?: string
}) {
  const photos = cardPhotos(m)
  const [at, setAt] = useState(0)
  const many = photos.length > 1
  const shown = photos[at]
  const note = shown ? PHOTO_NOTE[shown.source] : undefined
  const map = photos.length ? null : m.location_picture ?? null
  const logo = photos.length ? null : m.logo ?? null
  const step = (by: number) => setAt((i) => (i + by + photos.length) % photos.length)
  // a 44px tap target round a small circle: always there on a touch screen, and with a mouse when the pointer is on the picture
  const arrow = 'absolute top-1/2 flex h-11 w-11 -translate-y-1/2 items-center justify-center text-[#0f2340] transition-opacity [@media(hover:hover)]:opacity-0 [@media(hover:hover)]:group-hover/pic:opacity-100 focus-visible:opacity-100'
  const dot = 'flex h-8 w-8 items-center justify-center rounded-full bg-white/85 shadow-sm backdrop-blur-sm'
  return (
    <div className={`group/pic relative overflow-hidden bg-slate-200 ${height}`} data-testid="card-picture">
      <Link href={href} tabIndex={-1} aria-hidden className="absolute inset-0 block">
        {photos.length > 0 && photos.map((p, i) => (
          // every picture is in the page, so the next one is there when the arrow is pressed; only the shown one is visible
          // eslint-disable-next-line @next/next/no-img-element
          <img key={p.url} src={p.url} alt={i === at ? p.alt || name : ''} loading="lazy"
            className={`absolute inset-0 h-full w-full object-cover transition-opacity duration-300 ${i === at ? 'opacity-100' : 'opacity-0'}`} />
        ))}
        {map && (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={map.url} alt={`Map: where ${name} is`} loading="lazy" className="absolute inset-0 h-full w-full object-cover" data-testid="card-map" />
        )}
        {!photos.length && !map && logo && (
          // the logo at a logo's size, centred on a quiet ground, not stretched to fill the slot (it read as unfinished)
          <span className={`absolute inset-0 flex items-center justify-center ${logo.tone === 'light' ? 'bg-[#16305a]' : 'bg-slate-50'}`} data-testid="card-logo">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={logo.url} alt={`${name}: the builder's logo`} loading="lazy" className="h-auto max-h-12 w-auto max-w-[55%] object-contain" />
          </span>
        )}
        {!photos.length && !map && !logo && (
          // nothing of the project's own: the skyline the listing cards use, not a lone first letter (it read as a broken image)
          <span className="absolute inset-0 flex flex-col justify-end bg-gradient-to-b from-[#102340] to-[#183a5d]"><Skyline className="block h-1/2 w-full" /></span>
        )}
      </Link>
      {map && logo && (
        <span className="pointer-events-none absolute right-2 top-2 flex h-9 max-w-[45%] items-center rounded-lg bg-white px-2 py-1 shadow" data-testid="card-map-logo">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={logo.url} alt="" loading="lazy" className={`max-h-full max-w-full object-contain ${logo.tone === 'light' ? 'rounded bg-[#0f2340] p-0.5' : ''}`} />
        </span>
      )}
      {rank != null && (
        <span className="pointer-events-none absolute left-2 top-2 flex h-8 w-8 items-center justify-center rounded-full bg-[#0f2340] text-sm font-bold text-white">
          <span className="sr-only">Rank </span>{rank}
        </span>
      )}
      {many && (
        <>
          <button type="button" onClick={() => step(-1)} aria-label={`Previous picture of ${name}`} className={arrow + ' left-0.5'}>
            <span className={dot}><svg aria-hidden viewBox="0 0 20 20" className="h-4 w-4"><path d="M12.5 4.5 7 10l5.5 5.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg></span>
          </button>
          <button type="button" onClick={() => step(1)} aria-label={`Next picture of ${name}`} className={arrow + ' right-0.5'}>
            <span className={dot}><svg aria-hidden viewBox="0 0 20 20" className="h-4 w-4"><path d="M7.5 4.5 13 10l-5.5 5.5" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg></span>
          </button>
          <span className="pointer-events-none absolute right-2 top-2 rounded-full bg-black/55 px-2 py-0.5 text-[11px] font-semibold text-white" aria-live="polite">
            <span className="sr-only">Picture </span>{at + 1} / {photos.length}
          </span>
        </>
      )}
      {tag && <span className={`pointer-events-none absolute bottom-2 left-2 rounded-full px-2.5 py-1 text-xs font-bold ${tagTone === 'warn' ? 'bg-[#fdf0d3] text-[#6b4a0b]' : 'bg-white/95 text-[#0f2340]'}`}>{tag}</span>}
      {note && <span className="pointer-events-none absolute bottom-2 right-2 rounded bg-black/60 px-1.5 py-0.5 text-[11px] text-white">{note}</span>}
      {map && <span className="sr-only">The project&apos;s position on the map</span>}
    </div>
  )
}
