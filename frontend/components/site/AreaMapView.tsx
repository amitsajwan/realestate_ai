'use client'
import React, { useState } from 'react'
import Link from 'next/link'
import type { AreaMapData, AreaMapItem } from '@/lib/site/hubs'
import { formatPrice } from '@/lib/site/format'
import { formatDay } from '@/lib/site/projects'

/** The interactive part of the area map (AreaMap.tsx): pins on the drawn street map, the picked project's card and the numbered
 *  list. The server renders it with the first project picked, so it reads in full without JavaScript; picking a pin and lighting
 *  a pin from its list row are extras. The list is the content (links Google and screen readers follow); the pins only repeat it. */

export type Shown = AreaMapItem & { href: string; listed: boolean }

const MAP_W = 640                 // the map's width on a laptop, for deciding which labels fit
const PIN = 28
const CHAR = 7.2                  // text-xs Poppins, semibold, on average

type Box = { l: number; t: number; r: number; b: number }
const hits = (a: Box, b: Box) => a.l < b.r && b.l < a.r && a.t < b.b && b.t < a.b

/** Which pins get a name label beside them on a laptop, and on which side: most active first, right of the pin else left, never
 *  over another pin or label. Pins in a cluster keep only their number (the list says the name). */
export function placeLabels(items: Pick<AreaMapItem, 'n' | 'name' | 'x' | 'y'>[], width = MAP_W, height = MAP_W): Record<number, 'right' | 'left'> {
  const pins: Box[] = items.map((p) => ({ l: p.x * width - PIN / 2, t: p.y * height - PIN / 2, r: p.x * width + PIN / 2, b: p.y * height + PIN / 2 }))
  const placed: Box[] = []
  const out: Record<number, 'right' | 'left'> = {}
  items.forEach((p, i) => {
    const w = p.name.length * CHAR + 20, cx = p.x * width, cy = p.y * height
    for (const side of ['right', 'left'] as const) {
      const l = side === 'right' ? cx + PIN / 2 + 4 : cx - PIN / 2 - 4 - w
      const box = { l, t: cy - 12, r: l + w, b: cy + 12 }
      if (box.l < 4 || box.r > width - 4) continue
      if (pins.some((q, j) => j !== i && hits(box, q)) || placed.some((q) => hits(box, q))) continue
      placed.push(box)
      out[p.n] = side
      break
    }
  })
  return out
}

function pinColours(p: Shown, on: boolean): string {
  if (on) return 'bg-[#0f2340] text-white border-white'
  if (p.stage === 'new') return 'bg-[#f0b440] text-[#0f2340] border-white'
  if (p.stage === 'advanced' || p.stage === 'passed') return 'bg-white text-[#1f6b4f] border-[#1f6b4f]'
  return 'bg-[#2f5fa7] text-white border-white'
}

export const pct = (p: Pick<AreaMapItem, 'booked' | 'total'>): number | null =>
  p.booked != null && p.total ? Math.round((100 * p.booked) / p.total) : null

export default function AreaMapView({ data, items }: { data: AreaMapData; items: Shown[] }) {
  const [picked, setPicked] = useState(items[0]?.n ?? 0)
  const [lit, setLit] = useState<number | null>(null)
  const labels = placeLabels(items)
  const p = items.find((x) => x.n === picked) ?? items[0]
  const share = pct(p)
  return (
    <div className="mt-4 flex flex-wrap items-start gap-5">
      <div className="min-w-0 flex-[999_1_520px]">
        <div className="relative w-full overflow-hidden rounded-2xl border border-[#e3d6b5] bg-[#f3eddf]" style={{ aspectRatio: '1 / 1' }}>
          {/* the streets are a picture: what it shows is said in the list beside it */}
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src={data.map} alt="" aria-hidden="true" className="absolute inset-0 h-full w-full" />
          {items.map((x) => {
            const on = x.n === p.n || x.n === lit
            const side = x.n === p.n ? (labels[x.n] ?? 'right') : labels[x.n]
            return (
              <button key={x.n} type="button" onClick={() => setPicked(x.n)} aria-pressed={x.n === p.n}
                aria-label={`${x.n}. ${x.name}${pct(x) != null ? `, ${pct(x)}% booked` : ''}`} data-testid="area-map-pin"
                className={`absolute flex min-h-[44px] min-w-[44px] -translate-x-1/2 -translate-y-1/2 items-center justify-center ${on ? 'z-20' : 'z-10'}`}
                style={{ left: `${x.x * 100}%`, top: `${x.y * 100}%` }}>
                <span aria-hidden="true" className={`flex h-7 w-7 items-center justify-center rounded-full border-2 text-xs font-bold shadow ${pinColours(x, on)} ${x.listed ? 'ring-[3px] ring-[#f0b440]' : ''} ${on ? 'scale-110' : ''}`}>{x.n}</span>
                {side && (
                  <span aria-hidden="true" className={`pointer-events-none absolute top-1/2 -translate-y-1/2 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold shadow ${side === 'right' ? 'left-[38px]' : 'right-[38px]'} ${x.n === p.n ? 'flex bg-[#0f2340] text-white' : `hidden md:flex ${on ? 'bg-[#0f2340] text-white' : 'bg-white/95 text-[#0f2340]'}`}`}>
                    {x.name}
                  </span>
                )}
              </button>
            )
          })}
        </div>
        <ul className="mt-3 flex list-none flex-wrap gap-x-5 gap-y-2 p-0 text-xs text-slate-700" aria-label="What the pins show">
          <li className="flex items-center gap-1.5"><span aria-hidden="true" className="h-3 w-3 rounded-full border-2 border-white bg-[#f0b440] shadow" />New launch</li>
          <li className="flex items-center gap-1.5"><span aria-hidden="true" className="h-3 w-3 rounded-full border-2 border-white bg-[#2f5fa7] shadow" />Being built</li>
          <li className="flex items-center gap-1.5"><span aria-hidden="true" className="h-3 w-3 rounded-full border-2 border-[#1f6b4f] bg-white" />Nearly ready</li>
          <li className="flex items-center gap-1.5"><span aria-hidden="true" className="h-3 w-3 rounded-full bg-[#2f5fa7] ring-2 ring-[#f0b440]" />Listed by a local agent</li>
          <li className="text-slate-600">{data.attribution}</li>
        </ul>
      </div>

      <div className="min-w-0 flex-[1_1_320px]">
        <article className="overflow-hidden rounded-2xl border-2 border-[#0f2340] bg-white" aria-live="polite" data-testid="area-map-card">
          {p.photo && (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={p.photo.url} alt={p.photo.alt || p.name} className="h-40 w-full object-cover" />
          )}
          <div className="p-4">
            <div className="flex items-baseline justify-between gap-2">
              <h3 className="m-0 text-lg font-bold text-[#0f2340]">{p.n}. {p.name}</h3>
              <span className="whitespace-nowrap rounded-full bg-[#fdf0d3] px-2 py-0.5 text-[11px] font-semibold text-[#6b4a0b]">{p.stage_label}</span>
            </div>
            {p.builder && <p className="m-0 mt-1 text-sm text-slate-600">{p.builder}</p>}
            <dl className="m-0 mt-3 grid grid-cols-3 gap-2">
              <div><dt className="text-[11px] text-slate-600">From</dt><dd className="m-0 font-semibold text-[#0f2340]">{p.price_from ? formatPrice(p.price_from) : 'Ask'}</dd></div>
              <div><dt className="text-[11px] text-slate-600">MahaRERA date</dt><dd className="m-0 font-semibold text-[#0f2340]">{formatDay(p.completion?.slice(0, 7)) || '–'}</dd></div>
              <div><dt className="text-[11px] text-slate-600">Booked</dt><dd className="m-0 font-semibold text-[#0f2340]">{share != null ? `${share}%` : '–'}</dd></div>
            </dl>
            {share != null && (
              <>
                <div className="mt-2 h-1.5 rounded-full bg-[#ece5d3]" aria-hidden="true"><div className="h-1.5 rounded-full bg-[#2f5fa7]" style={{ width: `${share}%` }} /></div>
                <p className="m-0 mt-1 text-xs text-slate-600">{p.booked!.toLocaleString('en-IN')} of {p.total!.toLocaleString('en-IN')} homes booked on MahaRERA</p>
              </>
            )}
            <Link href={p.href} className="mt-3 flex min-h-[44px] items-center justify-center rounded-xl bg-[#0f2340] text-sm font-semibold text-white no-underline hover:bg-[#16305a]">See {p.name}</Link>
            <a href={`https://www.google.com/maps/search/?api=1&query=${p.lat},${p.lon}`} target="_blank" rel="noopener noreferrer"
              className="mt-1 flex min-h-[44px] items-center justify-center text-sm font-semibold text-[#0f2340] underline underline-offset-2">Directions in Google Maps</a>
          </div>
        </article>
        <ol className="mt-3 flex list-none flex-col gap-1.5 p-0" data-testid="area-map-list">
          {items.map((x) => (
            <li key={x.n}>
              <Link href={x.href} onMouseEnter={() => setLit(x.n)} onMouseLeave={() => setLit(null)} onFocus={() => setLit(x.n)} onBlur={() => setLit(null)}
                className={`flex min-h-[48px] items-center gap-3 rounded-xl border bg-white px-3 py-2 no-underline ${x.n === p.n ? 'border-[#0f2340]' : 'border-[#ece2c8] hover:border-[#0f2340]'}`}>
                <span aria-hidden="true" className="flex h-6 w-6 flex-none items-center justify-center rounded-full bg-[#0f2340] text-[11px] font-bold text-white">{x.n}</span>
                <span className="min-w-0 flex-auto">
                  <span className="block text-sm font-semibold text-[#0f2340]">{x.name}</span>
                  {' '}<span className="block text-xs text-slate-600">{x.stage_label}{x.completion ? ` · MahaRERA ${formatDay(x.completion.slice(0, 7))}` : ''}</span>
                </span>
                {pct(x) != null && <span className="whitespace-nowrap text-sm font-semibold text-[#0f2340]">{pct(x)}% booked</span>}
              </Link>
            </li>
          ))}
        </ol>
      </div>
    </div>
  )
}
