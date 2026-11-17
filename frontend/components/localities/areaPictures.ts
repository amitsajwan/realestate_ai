/**
 * The area seen from above, then and now: Sentinel-2 pictures, judged by Gemini vision and kept live by the owner in Studio
 * (docs/plan/area-pictures.md step 3; backend `areastats.pictures`, the `area_pictures` background loop). Read server-side
 * from `GET /api/v1/public/areas/{slug}/pictures` (live pictures only), like `areaStats.ts`: a timeout, and any failure
 * gives []. The public/areas/<slug>.json file the by-hand script (backend/scripts/area_from_above.py) used to write is kept
 * as a fallback only, so a server not yet switched on, or an area still carrying only the hand-run pair, keeps its pictures.
 */
import { promises as fs } from 'fs'
import path from 'path'

import { fixturesForced, serverApiBase } from '@/lib/site/api'

export interface AreaPicture {
  year: number
  src: string // /areas/<slug>-<year>.webp
  width: number
  height: number
  day: string // the day of the pass, YYYY-MM-DD
  credit: string // "Contains modified Copernicus Sentinel data <year>"
}

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
const DAY = /^(\d{4})-(\d{2})-\d{2}$/
const size = (v: unknown): v is number => typeof v === 'number' && Number.isInteger(v) && v > 0 && v <= 5000

/** "2017-03-12" -> "March 2017" */
export function monthYear(day: string): string {
  const m = DAY.exec(day)
  return m && +m[2] >= 1 && +m[2] <= 12 ? `${MONTHS[+m[2] - 1]} ${m[1]}` : ''
}

/** The pictures the list names for this area, oldest first; only entries whose file name, size and day agree with each other. */
export function cleanAreaPictures(raw: unknown, slug: string): AreaPicture[] {
  if (!raw || typeof raw !== 'object') return []
  const r = raw as Record<string, unknown>
  if (r.area !== slug || !Array.isArray(r.pictures)) return []
  const byYear = new Map<number, AreaPicture>()
  for (const p of r.pictures as Array<Record<string, unknown>>) {
    if (!p || typeof p !== 'object') continue
    const year = p.year
    const day = (p.captured as { from?: unknown } | undefined)?.from
    if (typeof year !== 'number' || !Number.isInteger(year) || typeof day !== 'string' || !monthYear(day) || +day.slice(0, 4) !== year) continue
    if (p.src !== `/areas/${slug}-${year}.webp` || !size(p.width) || !size(p.height)) continue
    byYear.set(year, { year, src: p.src, width: p.width, height: p.height, day, credit: `Contains modified Copernicus Sentinel data ${year}` })
  }
  return [...byYear.values()].sort((a, b) => a.year - b.year)
}

/** The oldest and the newest picture, when there are two years to compare; null otherwise. */
export function thenAndNow(pictures: AreaPicture[]): [AreaPicture, AreaPicture] | null {
  return pictures.length >= 2 ? [pictures[0], pictures[pictures.length - 1]] : null
}

export const pictureAlt = (name: string, p: AreaPicture) => `${name} from above, ${monthYear(p.day)}, Sentinel-2 satellite`

/** The newest picture as the page's link-preview image (pageMetadata's `image`), when the page shows a pair. */
export function areaOgImage(name: string, pictures: AreaPicture[]): { path: string; width: number; height: number; alt: string } | undefined {
  const pair = thenAndNow(pictures)
  if (!pair) return undefined
  const p = pair[1]
  return { path: p.src, width: p.width, height: p.height, alt: pictureAlt(name, p) }
}

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+){0,8}$/
const API_SRC = /^\/uploads\/area_pictures\/[A-Za-z0-9_-]+\.webp$/

/** `GET /api/v1/public/areas/{slug}/pictures`'s live pictures, cleaned (areastats.pictures.public_view's shape); only entries
 *  whose year, day and file all agree. [] for anything unexpected: an outage, a 404, a malformed body. */
export function cleanApiPictures(raw: unknown, slug: string): AreaPicture[] {
  if (!raw || typeof raw !== 'object') return []
  const r = raw as { area?: { slug?: unknown }; pictures?: unknown }
  if (r.area?.slug !== slug || !Array.isArray(r.pictures)) return []
  const byYear = new Map<number, AreaPicture>()
  for (const p of r.pictures as Array<Record<string, unknown>>) {
    if (!p || typeof p !== 'object') continue
    const { year, captured_on: day, src, width, height } = p as Record<string, unknown>
    if (typeof year !== 'number' || !Number.isInteger(year) || typeof day !== 'string' || !monthYear(day) || +day.slice(0, 4) !== year) continue
    if (typeof src !== 'string' || !API_SRC.test(src) || !size(width) || !size(height)) continue
    byYear.set(year, { year, src, width, height, day, credit: `Contains modified Copernicus Sentinel data ${year}` })
  }
  return [...byYear.values()].sort((a, b) => a.year - b.year)
}

async function readApiPictures(slug: string): Promise<AreaPicture[]> {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 5000)
  try {
    const res = await fetch(serverApiBase() + '/api/v1/public/areas/' + encodeURIComponent(slug) + '/pictures', {
      headers: { Accept: 'application/json' },
      next: { revalidate: 300 },
      signal: ctrl.signal,
    })
    if (!res.ok) return []
    return cleanApiPictures(await res.json(), slug)
  } catch {
    return []
  } finally {
    clearTimeout(timer)
  }
}

/** The live pictures from the backend (areastats.pictures), else public/areas/<slug>.json (the by-hand script's file),
 *  cleaned; [] for an unknown slug or when neither has anything. */
export async function readAreaPictures(slug: string, dir: string = path.join(process.cwd(), 'public', 'areas')): Promise<AreaPicture[]> {
  if (!SLUG.test(slug)) return []
  if (!fixturesForced()) {
    const api = await readApiPictures(slug)
    if (api.length) return api
  }
  try {
    return cleanAreaPictures(JSON.parse(await fs.readFile(path.join(dir, `${slug}.json`), 'utf8')), slug)
  } catch {
    return []
  }
}
