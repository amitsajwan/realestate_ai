import React from 'react'
import type { MapLandmark, MapLandmarkIcon } from '@/lib/site/hubs'

/** The landmarks and metro stations inside an area map's frame (backend areastats/landmarks.on_map), drawn as small square icons
 *  so they never read as the round, numbered project pins. They only repeat what the legend under the map says in words. */

const LOOK: Record<MapLandmarkIcon, { word: string; bg: string }> = {
  metro: { word: 'Metro station', bg: 'bg-[#0e7c86]' },
  office: { word: 'Office hub', bg: 'bg-[#4b5563]' },
  hospital: { word: 'Hospital', bg: 'bg-[#c0392b]' },
  shopping: { word: 'Shopping', bg: 'bg-[#8e44ad]' },
  airport: { word: 'Airport', bg: 'bg-[#1f4e8c]' },
  rail: { word: 'Railway station', bg: 'bg-[#1f4e8c]' },
  college: { word: 'College', bg: 'bg-[#7a5c12]' },
}

/** A 12x12 glyph in white: plain shapes, readable at the size of a map label. */
export function Glyph({ icon }: { icon: MapLandmarkIcon }) {
  const common = { width: 12, height: 12, viewBox: '0 0 12 12', 'aria-hidden': true, focusable: false } as const
  switch (icon) {
    case 'metro':
      return <svg {...common}><path d="M2 10V2h1.6L6 6l2.4-4H10v8H8.6V5L6 9 3.4 5v5z" fill="#fff" /></svg>
    case 'office':
      return <svg {...common}><path d="M3 1h6v10H7V9H5v2H3zM4 2.5v1.5h1.5V2.5zm2.5 0v1.5H8V2.5zM4 5.5V7h1.5V5.5zm2.5 0V7H8V5.5z" fill="#fff" fillRule="evenodd" /></svg>
    case 'hospital':
      return <svg {...common}><path d="M4.5 1.5h3v3h3v3h-3v3h-3v-3h-3v-3h3z" fill="#fff" /></svg>
    case 'shopping':
      return <svg {...common}><path d="M2 4h8l-.6 7H2.6zM4 4V3a2 2 0 0 1 4 0v1H7V3a1 1 0 0 0-2 0v1z" fill="#fff" /></svg>
    case 'airport':
      return <svg {...common}><path d="M5.3 1h1.4l.5 3.8L11 6.5v1.2L7.2 6.9 7 9.3l1.3 1V11L6 10.4 3.7 11v-.7L5 9.3l-.2-2.4L1 7.7V6.5l3.8-1.7z" fill="#fff" /></svg>
    case 'rail':
      return <svg {...common}><path d="M3 1.5h6a1 1 0 0 1 1 1V8a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V2.5a1 1 0 0 1 1-1zM3 3v2.5h6V3zm.2 7.5L4.5 9h1L4.4 10.5zm5.6 0L7.6 9h-1l1.1 1.5z" fill="#fff" fillRule="evenodd" /></svg>
    case 'college':
      return <svg {...common}><path d="M6 1.5 11.5 4 6 6.5.5 4zM3 5.6l3 1.4 3-1.4V8c0 .8-1.3 1.6-3 1.6S3 8.8 3 8z" fill="#fff" /></svg>
  }
}

export function Badge({ icon, className = '' }: { icon: MapLandmarkIcon; className?: string }) {
  return (
    <span aria-hidden="true" className={`flex h-5 w-5 flex-none items-center justify-center rounded-[5px] border border-white shadow ${LOOK[icon].bg} ${className}`}>
      <Glyph icon={icon} />
    </span>
  )
}

/** The icons on the map (inside its square frame). A label sits beside each on wider screens; a station being built is drawn
 *  faded and its label says so. */
export function MapLandmarkIcons({ items }: { items: MapLandmark[] }) {
  return (
    <>
      {items.map((m) => (
        <span key={`${m.icon}:${m.name}`} data-testid="area-map-landmark" title={m.label}
          className={`pointer-events-none absolute z-[5] flex -translate-x-1/2 -translate-y-1/2 items-center ${m.running === false ? 'opacity-70' : ''}`}
          style={{ left: `${m.x * 100}%`, top: `${m.y * 100}%` }}>
          <Badge icon={m.icon} />
          <span aria-hidden="true" className="absolute left-[24px] top-1/2 hidden -translate-y-1/2 whitespace-nowrap rounded bg-white/90 px-1.5 py-0.5 text-[10px] font-semibold text-slate-700 shadow-sm md:block">
            {m.label}
          </span>
        </span>
      ))}
    </>
  )
}

/** Under the map, in words: what each square icon is, by name. This is what screen readers and phones read. */
export function MapLandmarkLegend({ items }: { items: MapLandmark[] }) {
  if (!items.length) return null
  return (
    <p className="mt-2 text-xs text-slate-700" data-testid="area-map-landmark-legend">
      <span className="font-semibold">Also on the map (square icons):</span>{' '}
      {items.map((m, i) => (
        <span key={`${m.icon}:${m.name}`} className="mr-3 inline-flex items-center gap-1 align-middle">
          <Badge icon={m.icon} className="h-4 w-4" />
          <span>{m.label}{m.icon === 'metro' ? '' : ` (${LOOK[m.icon].word.toLowerCase()})`}{i < items.length - 1 ? ';' : ''}</span>
        </span>
      ))}
    </p>
  )
}
