/**
 * The area seen from above, then and now: Sentinel-2 pictures backend/scripts/area_from_above.py writes into public/areas/
 * (<slug>-<year>.webp, and <slug>.json listing them). Read on the server from the site's own public folder; a missing or
 * malformed list gives null and the page shows only the chart. Nothing here describes what the pictures show: the caption is
 * the place, the month and the credit, all from the list.
 */
import { promises as fs } from 'fs'
import path from 'path'

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

/** public/areas/<slug>.json, cleaned; [] when there is none. */
export async function readAreaPictures(slug: string, dir: string = path.join(process.cwd(), 'public', 'areas')): Promise<AreaPicture[]> {
  if (!SLUG.test(slug)) return []
  try {
    return cleanAreaPictures(JSON.parse(await fs.readFile(path.join(dir, `${slug}.json`), 'utf8')), slug)
  } catch {
    return []
  }
}
