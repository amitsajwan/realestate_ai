/**
 * An area from space, month by month (owner 2026-11-21: "for our areas why not have a similar project like from space"): the
 * project pages' satellite timeline made for a whole area by the backend's daily pass (areastats/areaspace.py), stored under
 * /uploads/area_space/<area slug>/ and sent by `GET /api/v1/public/areas/<slug>/from-space`. The area guide shows it as a
 * section, /localities/<slug>/from-space as a page of its own with the video first (the one the video sitemap names), and
 * /projects/from-space lists every area with one. Pictures stored for another area, or fewer than three years: nothing.
 */
import { fixturesForced, serverApiBase } from '@/lib/site/api'
import { shortMonth, type FromAboveFrame, type FromAboveSeason, type FromAboveVideo } from '@/lib/site/fromAbove'
import { esriPastFrom, type EsriPast } from '@/lib/site/esriPast'

export interface AreaFromSpace {
  slug: string
  name: string
  middle: { lat: number; lon: number }
  sideKm: number
  story: string
  where: string
  credit: string
  frames: FromAboveFrame[]
  seasons: FromAboveSeason[]
  video: FromAboveVideo | null
  updated: string | null // YYYY-MM-DD, the last look
  esriPast: EsriPast | null // Esri's sharp past pictures at the middle (areastats.esripast)
}

/** One area in the from-space list (backend areaspace.every): the hub and the video sitemap. */
export interface AreaFromSpaceItem {
  slug: string
  name: string
  story: string
  video: { src: string; poster: string; from: string; to: string; months: number } | null
  picture: string
  years: [number, number]
  updated: string | null
  seasons: number
}

const SLUG = /^[a-z0-9]+(?:-[a-z0-9]+){0,5}$/
const num = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)
const size = (v: unknown): v is number => num(v) && Number.isInteger(v) && v > 0 && v <= 5000
const text = (v: unknown): v is string => typeof v === 'string' && v.trim().length > 0 && v.length < 1000
const dir = (slug: string) => `/uploads/area_space/${slug}/`

/** The path of the watch page, where the video is the main thing. */
export const areaFromSpacePath = (slug: string) => `/localities/${slug}/from-space`

function cleanVideo(raw: unknown, slug: string): FromAboveVideo | null {
  if (!raw || typeof raw !== 'object') return null
  const v = raw as Record<string, unknown>
  if (v.src !== `${dir(slug)}months.mp4` || v.poster !== `${dir(slug)}months.webp`) return null
  if (!size(v.width) || !size(v.height) || !num(v.months) || v.months < 3) return null
  if (typeof v.from !== 'string' || typeof v.to !== 'string' || !shortMonth(v.from) || !shortMonth(v.to) || v.from >= v.to) return null
  return { src: v.src, poster: v.poster, width: v.width, height: v.height, from: v.from, to: v.to, months: Math.round(v.months) }
}

/** The API's answer for the area of `slug`, checked: only pictures stored for this area, three years or more. */
export function areaFromRecord(raw: unknown, slug: string): AreaFromSpace | null {
  if (!SLUG.test(slug) || !raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>
  const area = r.area as Record<string, unknown> | undefined
  const middle = r.middle as Record<string, unknown> | undefined
  if (!area || area.slug !== slug || !text(area.name)) return null
  if (!middle || !num(middle.lat) || !num(middle.lon) || !text(r.story) || !text(r.where) || !text(r.credit)) return null
  if (!Array.isArray(r.frames)) return null
  const frames: FromAboveFrame[] = []
  for (const f of r.frames as Array<Record<string, unknown>>) {
    if (!f || typeof f !== 'object' || !num(f.year) || typeof f.day !== 'string' || !shortMonth(f.day)) continue
    if (+f.day.slice(0, 4) !== f.year || f.src !== `${dir(slug)}${f.year}.webp`) continue
    if (!size(f.width) || !size(f.height)) continue
    frames.push({ year: f.year, day: f.day, src: f.src as string, width: f.width, height: f.height })
  }
  frames.sort((a, b) => a.year - b.year)
  if (frames.length < 3) return null
  const seasons: FromAboveSeason[] = Array.isArray(r.seasons)
    ? (r.seasons as Array<Record<string, unknown>>).filter((x) => x && text(x.label) && text(x.line) && typeof x.day === 'string'
      && shortMonth(x.day as string) && (x.label as string).length < 30 && (x.line as string).length < 200)
      .map((x) => ({ label: (x.label as string).trim(), day: x.day as string, line: (x.line as string).trim() }))
    : []
  return {
    slug, name: (area.name as string).trim(), middle: { lat: middle.lat, lon: middle.lon },
    sideKm: num(r.side_km) && r.side_km > 0 && r.side_km < 20 ? r.side_km : 0,
    story: r.story.trim(), where: r.where.trim(), credit: r.credit.trim(), frames, seasons, video: cleanVideo(r.video, slug),
    updated: typeof r.updated === 'string' && shortMonth(r.updated) ? r.updated : null,
    esriPast: esriPastFrom(r.esri_past),
  }
}

/** The list's entries that point only at their own area's files. */
export function cleanAreaItems(raw: unknown): AreaFromSpaceItem[] {
  if (!Array.isArray(raw)) return []
  return raw.filter((x): x is AreaFromSpaceItem => !!x && typeof x === 'object' && typeof x.slug === 'string' && SLUG.test(x.slug)
    && text(x.name) && text(x.story) && x.picture === `${dir(x.slug)}${x.years?.[1]}.webp`
    && Array.isArray(x.years) && num(x.years[0]) && num(x.years[1])
    && (x.video === null || (x.video?.src === `${dir(x.slug)}months.mp4` && x.video?.poster === `${dir(x.slug)}months.webp`)))
}

async function fetchJson(path: string): Promise<unknown> {
  if (fixturesForced()) return null
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 5000)
  try {
    const res = await fetch(serverApiBase() + path, { headers: { Accept: 'application/json' }, next: { revalidate: 600 }, signal: ctrl.signal })
    return res.ok ? await res.json() : null
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

export async function getAreaFromSpace(slug: string): Promise<AreaFromSpace | null> {
  if (!SLUG.test(slug)) return null
  return areaFromRecord(await fetchJson(`/api/v1/public/areas/${slug}/from-space`), slug)
}

export async function getAreasFromSpace(): Promise<AreaFromSpaceItem[]> {
  return cleanAreaItems(await fetchJson('/api/v1/public/areas/from-space'))
}
