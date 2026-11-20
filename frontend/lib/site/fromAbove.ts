/**
 * A project's site from above, one Sentinel-2 picture a year, with the change measured and said in code
 * (docs/plan/satellite-view.md steps 3-4). The by-hand script backend/scripts/project_from_above.py writes
 * public/from-above/<slug>.json and the pictures beside it; this reads the file server-side. No file, a file that does not
 * match its slug, or a pin that has since moved: nothing is shown (the pictures would be of somebody else's ground).
 */
import { promises as fs } from 'fs'
import path from 'path'

export interface FromAboveFrame {
  year: number
  day: string // YYYY-MM-DD, the pass
  src: string // /from-above/<slug>-<year>.webp
  width: number
  height: number
  built: number // % of the 100 m circle: roofs and concrete
}

/** The month-by-month loop (--timelapse): one clear pass a dry month, made by the same script. */
export interface FromAboveVideo {
  src: string // /from-above/<slug>.mp4
  poster: string // /from-above/<slug>.webp
  width: number
  height: number
  from: string // YYYY-MM-DD, first month
  to: string // YYYY-MM-DD, last month
  months: number
}

export interface FromAbove {
  slug: string
  pin: { lat: number; lon: number }
  story: string
  where: string
  credit: string
  frames: FromAboveFrame[]
  video: FromAboveVideo | null
}

const DAY = /^(\d{4})-(\d{2})-\d{2}$/
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const num = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)
const size = (v: unknown): v is number => num(v) && Number.isInteger(v) && v > 0 && v <= 5000
const text = (v: unknown): v is string => typeof v === 'string' && v.trim().length > 0 && v.length < 1000

/** "2026-02-27" -> "Feb 2026" */
export const shortMonth = (day: string): string => {
  const m = DAY.exec(day)
  return m && +m[2] >= 1 && +m[2] <= 12 ? `${MONTHS[+m[2] - 1]} ${m[1]}` : ''
}

/** Metres between two points (equirectangular: plenty at a few hundred metres). */
export function metresApart(a: { lat: number; lon: number }, b: { lat: number; lon: number }): number {
  const k = 111320
  const dy = (a.lat - b.lat) * k
  const dx = (a.lon - b.lon) * k * Math.cos(((a.lat + b.lat) / 2) * (Math.PI / 180))
  return Math.sqrt(dx * dx + dy * dy)
}

/** A pin that moved this far since the pictures were made starts a new series: the old one is not shown. */
export const PIN_MOVED_M = 50

function cleanVideo(raw: unknown, slug: string): FromAboveVideo | null {
  if (!raw || typeof raw !== 'object') return null
  const v = raw as Record<string, unknown>
  if (v.src !== `/from-above/${slug}.mp4` || v.poster !== `/from-above/${slug}.webp`) return null
  if (!size(v.width) || !size(v.height) || !num(v.months) || v.months < 3) return null
  if (typeof v.from !== 'string' || typeof v.to !== 'string' || !shortMonth(v.from) || !shortMonth(v.to) || v.from >= v.to) return null
  return { src: v.src, poster: v.poster, width: v.width, height: v.height, from: v.from, to: v.to, months: Math.round(v.months) }
}

export function cleanFromAbove(raw: unknown, slug: string): FromAbove | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>
  const pin = r.pin as Record<string, unknown> | undefined
  if (r.slug !== slug || !pin || !num(pin.lat) || !num(pin.lon) || !text(r.story) || !text(r.where) || !text(r.credit)) return null
  if (!Array.isArray(r.frames)) return null
  const frames: FromAboveFrame[] = []
  for (const f of r.frames as Array<Record<string, unknown>>) {
    if (!f || typeof f !== 'object' || !num(f.year) || typeof f.day !== 'string' || !shortMonth(f.day)) continue
    if (+f.day.slice(0, 4) !== f.year || f.src !== `/from-above/${slug}-${f.year}.webp`) continue
    if (!size(f.width) || !size(f.height) || !num(f.built) || f.built < 0 || f.built > 100) continue
    frames.push({ year: f.year, day: f.day, src: f.src, width: f.width, height: f.height, built: Math.round(f.built) })
  }
  frames.sort((a, b) => a.year - b.year)
  if (frames.length < 3) return null
  return { slug, pin: { lat: pin.lat, lon: pin.lon }, story: r.story.trim(), where: r.where.trim(), credit: r.credit.trim(), frames,
    video: cleanVideo(r.video, slug) }
}

/** The project's pictures, only while its checked pin is where the pictures were taken. */
export function forPin(view: FromAbove | null, map: { lat: number; lon: number } | null | undefined): FromAbove | null {
  if (!view || !map) return null
  return metresApart(view.pin, map) <= PIN_MOVED_M ? view : null
}

export async function readFromAbove(slug: string, dir: string = path.join(process.cwd(), 'public', 'from-above')): Promise<FromAbove | null> {
  if (!/^[a-z0-9-]+$/.test(slug)) return null
  try {
    return cleanFromAbove(JSON.parse(await fs.readFile(path.join(dir, `${slug}.json`), 'utf8')), slug)
  } catch {
    return null
  }
}
