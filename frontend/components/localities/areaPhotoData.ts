/**
 * Real photos of an area for its guide: GET /api/v1/public/areas/{slug}/photos (backend app/modules/areaphotos,
 * docs/plan/area-pictures.md step 4). Our own photos and free-licensed ones only, each with who took it and when; the owner
 * publishes them in Studio > Area photos. Server-side, revalidated like areaStats.ts. Anything unexpected (outage, 404, a
 * malformed body, a photo without its credit) gives no photo, and the page leaves the section out.
 */
import { fixturesForced, serverApiBase } from '@/lib/site/api'

export interface AreaPhoto {
  id: string
  /** our copy, at most 1600 px on its long side: /uploads/area_photos/<area>/<id>.webp */
  url: string
  /** the same at 640 px */
  small_url: string
  width: number
  height: number
  /** what and where, written by whoever uploaded it */
  caption: string
  /** YYYY-MM-DD */
  taken_on: string
  /** who took it (the author, for a licensed photo) */
  credit: string
  kind: 'own' | 'licensed'
  /** licensed only: "CC BY-SA 4.0", its deed and the page the photo came from */
  licence: string | null
  licence_url: string | null
  source_url: string | null
}

export const MAX_PHOTOS = 8
const OUR_COPY = /^\/uploads\/area_photos\/[a-z_]+\/[0-9a-f]{32}(-small)?\.webp$/
const DAY = /^\d{4}-\d{2}-\d{2}$/
const DEED = /^https:\/\/creativecommons\.org\/(publicdomain\/zero\/1\.0|licenses\/by(-sa)?\/[234]\.0)\/$/
const text = (v: unknown, max: number): v is string => typeof v === 'string' && v.trim() !== '' && v.length <= max
const size = (v: unknown): v is number => typeof v === 'number' && Number.isInteger(v) && v > 0 && v <= 4000

function https(v: unknown): v is string {
  if (typeof v !== 'string') return false
  try {
    return new URL(v).protocol === 'https:'
  } catch {
    return false
  }
}

/** Only photos that say everything a credited photo must: ours to show, with who, when, and for a licensed one its licence
 *  and source. The rest are dropped, never shown without their credit. */
export function cleanAreaPhotos(raw: unknown, slug: string): AreaPhoto[] {
  if (!raw || typeof raw !== 'object') return []
  const r = raw as { area?: { slug?: unknown }; photos?: unknown }
  if (r.area?.slug !== slug || !Array.isArray(r.photos)) return []
  return r.photos.filter((p): p is AreaPhoto => {
    if (!p || typeof p !== 'object') return false
    const x = p as Record<string, unknown>
    if (!text(x.id, 64) || typeof x.url !== 'string' || !OUR_COPY.test(x.url) || typeof x.small_url !== 'string'
      || !OUR_COPY.test(x.small_url) || !size(x.width) || !size(x.height) || !text(x.caption, 200) || !text(x.credit, 100)
      || typeof x.taken_on !== 'string' || !DAY.test(x.taken_on)) return false
    if (x.kind === 'own') return true
    return x.kind === 'licensed' && text(x.licence, 20) && typeof x.licence_url === 'string' && DEED.test(x.licence_url)
      && https(x.source_url)
  }).map((p) => ({ ...p, licence: p.kind === 'own' ? null : p.licence, licence_url: p.kind === 'own' ? null : p.licence_url,
    source_url: p.kind === 'own' ? null : p.source_url })).slice(0, MAX_PHOTOS)
}

export async function getAreaPhotos(slug: string): Promise<AreaPhoto[]> {
  if (fixturesForced()) return []
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 5000)
  try {
    const res = await fetch(serverApiBase() + '/api/v1/public/areas/' + encodeURIComponent(slug) + '/photos', {
      headers: { Accept: 'application/json' },
      next: { revalidate: 300 },
      signal: ctrl.signal,
    })
    if (!res.ok) return []
    return cleanAreaPhotos(await res.json(), slug)
  } catch {
    return []
  } finally {
    clearTimeout(timer)
  }
}

const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

/** "2026-11-10" -> "November 2026" (split, not parsed as a Date: no time zone surprises). */
export function monthYear(day: string): string {
  const m = /^(\d{4})-(\d{2})-\d{2}$/.exec(day)
  return m && +m[2] >= 1 && +m[2] <= 12 ? `${MONTHS[+m[2] - 1]} ${m[1]}` : ''
}

/** "Wikimedia Commons" for Commons, else the site's own name from its address ("flickr.com"). */
export function sourceName(url: string): string {
  try {
    const host = new URL(url).hostname.replace(/^www\./, '')
    if (host === 'commons.wikimedia.org') return 'Wikimedia Commons'
    if (host === 'flickr.com') return 'Flickr'
    return host
  } catch {
    return 'source'
  }
}

/** One ImageObject per photo, with what Google reads for an image's credit and licence (creditText, creator, license,
 *  acquireLicensePage) and where it was taken. Our own photos carry no licence: we do not offer one. */
export function areaPhotosJsonLd(photos: AreaPhoto[], siteUrl: string, areaName: string): Record<string, unknown> {
  const abs = (u: string) => siteUrl.replace(/\/+$/, '') + u
  return {
    '@context': 'https://schema.org',
    '@graph': photos.map((p) => ({
      '@type': 'ImageObject',
      contentUrl: abs(p.url),
      thumbnailUrl: abs(p.small_url),
      width: p.width,
      height: p.height,
      caption: p.caption,
      dateCreated: p.taken_on,
      creator: { '@type': 'Person', name: p.credit },
      creditText: p.credit,
      contentLocation: { '@type': 'Place', name: `${areaName}, Pune` },
      ...(p.kind === 'licensed' && p.licence_url && p.source_url ? { license: p.licence_url, acquireLicensePage: p.source_url } : {}),
    })),
  }
}

/** The first published photo as the guide's link preview when there is no picture from above (areaPictures.areaOgImage leads):
 *  a real, credited photo of the place is what a shared link should show. Undefined without one. */
export function areaPhotoOgImage(photos: AreaPhoto[]): { path: string; width: number; height: number; alt: string } | undefined {
  const p = photos[0]
  return p ? { path: p.url, width: p.width, height: p.height, alt: p.caption } : undefined
}
