/**
 * Esri's sharp past pictures of a place, about one a year over the last three years (backend areastats/esripast.py, owner
 * 2026-11-21: the Wayback viewer was not friendly, "can we not have screenshot last 3 years"). The backend finds which Esri
 * releases hold a different capture at the pin and sends their release numbers and capture dates; the page draws each
 * picture from Esri's own tiles in the reader's browser. Nothing is stored on our side.
 */
import { shortMonth } from '@/lib/site/fromAbove'

export interface EsriShot {
  release: number
  captured: string // YYYY-MM-DD, when the picture was taken
  source: string // the imagery provider Esri names (Vantor, Maxar)
  res: number | null // metres a pixel
}

export interface EsriPast {
  zoom: number
  shots: EsriShot[] // oldest first
}

const TILE = 'https://wayback.maptiles.arcgis.com/arcgis/rest/services/World_Imagery/WMTS/1.0.0/default028mm/MapServer/tile'
const DAY = /^\d{4}-\d{2}-\d{2}$/

/** The API's `esri_past`, checked: whole release numbers, real dates, a zoom we draw, two pictures or more. */
export function esriPastFrom(raw: unknown): EsriPast | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>
  const zoom = typeof r.zoom === 'number' && Number.isInteger(r.zoom) && r.zoom >= 12 && r.zoom <= 19 ? r.zoom : null
  if (zoom === null || !Array.isArray(r.shots)) return null
  const shots: EsriShot[] = []
  for (const s of r.shots as Array<Record<string, unknown>>) {
    if (!s || typeof s.release !== 'number' || !Number.isInteger(s.release) || s.release <= 0 || s.release > 1e7) continue
    if (typeof s.captured !== 'string' || !DAY.test(s.captured) || !shortMonth(s.captured)) continue
    shots.push({ release: s.release, captured: s.captured, source: typeof s.source === 'string' ? s.source.slice(0, 40) : '',
      res: typeof s.res === 'number' && s.res > 0 && s.res < 5 ? s.res : null })
  }
  shots.sort((a, b) => (a.captured < b.captured ? -1 : 1))
  return shots.length >= 2 ? { zoom, shots: shots.slice(-4) } : null
}

/** Where a point falls in Esri's tile grid at `zoom`: the tile it is in and how far into it (0 to 1). */
export function tileOf(lat: number, lon: number, zoom: number): { col: number; row: number; fx: number; fy: number } {
  const n = 2 ** zoom
  const x = ((lon + 180) / 360) * n
  const rad = (lat * Math.PI) / 180
  const y = ((1 - Math.asinh(Math.tan(rad)) / Math.PI) / 2) * n
  return { col: Math.floor(x), row: Math.floor(y), fx: x - Math.floor(x), fy: y - Math.floor(y) }
}

/** Metres across `tiles` tiles at `zoom` and this latitude. */
export const metresAcross = (lat: number, zoom: number, tiles = 2) =>
  (tiles * 256 * 156543.03392 * Math.cos((lat * Math.PI) / 180)) / 2 ** zoom

export const tileSrc = (release: number, zoom: number, row: number, col: number) => `${TILE}/${release}/${zoom}/${row}/${col}`

/** Esri's viewer at the place, for whoever wants every release. */
export const waybackLink = (lat: number, lon: number, zoom: number) =>
  `https://livingatlas.arcgis.com/wayback/#mapCenter=${lon.toFixed(6)}%2C${lat.toFixed(6)}%2C${zoom}&mode=swipe`

/** "Nov 2022, Jan 2024, Feb 2025 and Apr 2026" */
export function datesSaid(shots: EsriShot[]): string {
  const m = shots.map((s) => shortMonth(s.captured))
  return m.length < 2 ? m.join('') : `${m.slice(0, -1).join(', ')} and ${m[m.length - 1]}`
}
