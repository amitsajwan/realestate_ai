import React from 'react'
import { jsonLdString } from '@/lib/marketing/seo'
import { fixturesForced, serverApiBase } from '@/lib/site/api'

/**
 * "Landmarks near <area>" on an area guide (docs/plan/area-pictures.md, step 1): the nearest metro stations and the places buyers
 * know, each opening on Google Maps, with straight-line distances from the middle of the area. Data: GET
 * /api/v1/public/areas/{slug}/landmarks (backend areastats/landmarks.py). Like the MahaRERA counts (areaStats.ts), anything
 * unexpected (outage, 404, a malformed body) gives null and the page leaves the section out: never an error.
 */

export interface LandmarkRow {
  name: string; lat: number; lon: number; km: number; distance: string; maps: string; source: string
  kind: string; kind_label?: string
}

export interface MetroRow extends LandmarkRow {
  line: string; line_name: string; line_short: string; status: 'running' | 'being built'; running: boolean; tracker: string | null
}

export interface AreaLandmarksData {
  area: { key: string; name: string; slug: string }
  middle: { lat: number; lon: number; how: string; label: string }
  metro: MetroRow[]
  landmarks: LandmarkRow[]
  note: string
  attribution: string
}

const num = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)
const text = (v: unknown): v is string => typeof v === 'string' && v.trim() !== ''
const MAPS = /^https:\/\/www\.google\.com\/maps\/search\/\?api=1&query=-?\d+(\.\d+)?,-?\d+(\.\d+)?$/
const TRACKER = /^\/news\/track\/[a-z0-9-]+$/

function row(r: unknown): LandmarkRow | null {
  if (!r || typeof r !== 'object') return null
  const x = r as Record<string, unknown>
  if (!text(x.name) || !num(x.lat) || !num(x.lon) || !num(x.km) || !text(x.distance) || !text(x.maps) || !MAPS.test(x.maps)) return null
  return { name: x.name, lat: x.lat, lon: x.lon, km: x.km, distance: x.distance, maps: x.maps, source: text(x.source) ? x.source : '',
    kind: text(x.kind) ? x.kind : '', kind_label: text(x.kind_label) ? x.kind_label : undefined }
}

/** Keeps only what the page can say truthfully: a station is "running" only when the answer says so in both fields. Null when
 *  there is nothing to show. */
export function cleanAreaLandmarks(raw: unknown, slug: string): AreaLandmarksData | null {
  if (!raw || typeof raw !== 'object') return null
  const r = raw as Record<string, unknown>
  const area = r.area as AreaLandmarksData['area'] | undefined
  const middle = r.middle as AreaLandmarksData['middle'] | undefined
  if (!area || area.slug !== slug || !text(area.name) || !middle || !num(middle.lat) || !num(middle.lon)) return null
  const metro = (Array.isArray(r.metro) ? r.metro : []).flatMap((m): MetroRow[] => {
    const base = row(m)
    const x = m as Record<string, unknown>
    if (!base || !text(x.line) || !text(x.line_short) || (x.status !== 'running' && x.status !== 'being built')) return []
    const running = x.status === 'running' && x.running === true
    return [{ ...base, kind: 'metro', line: x.line, line_name: text(x.line_name) ? x.line_name : x.line_short,
      line_short: x.line_short, status: running ? 'running' : 'being built', running,
      tracker: !running && text(x.tracker) && TRACKER.test(x.tracker) ? x.tracker : null }]
  })
  const landmarks = (Array.isArray(r.landmarks) ? r.landmarks : []).map(row)
    .filter((x): x is LandmarkRow => x !== null && text(x.kind_label))
  if (!metro.length && !landmarks.length) return null
  return { area: { key: area.key, name: area.name, slug: area.slug }, middle: { lat: middle.lat, lon: middle.lon,
    how: text(middle.how) ? middle.how : '', label: `the middle of ${area.name}` }, metro, landmarks,
    note: text(r.note) ? r.note : `Straight-line distances from the middle of ${area.name}, rounded; not travel times.`,
    attribution: text(r.attribution) ? r.attribution : 'Positions © OpenStreetMap contributors' }
}

export async function getAreaLandmarks(slug: string): Promise<AreaLandmarksData | null> {
  if (fixturesForced()) return null
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), 5000)
  try {
    const res = await fetch(serverApiBase() + '/api/v1/public/areas/' + encodeURIComponent(slug) + '/landmarks', {
      headers: { Accept: 'application/json' },
      next: { revalidate: 3600 },
      signal: ctrl.signal,
    })
    if (!res.ok) return null
    return cleanAreaLandmarks(await res.json(), slug)
  } catch {
    return null
  } finally {
    clearTimeout(timer)
  }
}

// schema.org type per kind: a page's nearby places with their positions
const LD_TYPE: Record<string, string> = { metro: 'TrainStation', shopping: 'ShoppingCenter', hospital: 'Hospital', study: 'CollegeOrUniversity' }
const ldType = (r: LandmarkRow) => (r.kind === 'travel' ? (/airport/i.test(r.name) ? 'Airport' : 'TrainStation') : LD_TYPE[r.kind] ?? 'Place')

export function landmarksJsonLd(d: AreaLandmarksData): Record<string, unknown> {
  const all: LandmarkRow[] = [...d.metro, ...d.landmarks]
  return {
    '@context': 'https://schema.org', '@type': 'ItemList', name: `Landmarks near ${d.area.name}, Pune`,
    itemListElement: all.map((r, i) => ({
      '@type': 'ListItem', position: i + 1,
      item: { '@type': ldType(r), name: r.kind === 'metro' ? `${r.name} metro station` : r.name, hasMap: r.maps,
        geo: { '@type': 'GeoCoordinates', latitude: r.lat, longitude: r.lon },
        description: r.kind === 'metro' ? `${(r as MetroRow).line_short}, ${(r as MetroRow).status}; ${r.distance}` : r.distance },
    })),
  }
}

const link = 'font-semibold text-[#0f2340] underline underline-offset-2'

function MapsLink({ r, label }: { r: LandmarkRow; label?: string }) {
  return (
    <a href={r.maps} target="_blank" rel="noopener noreferrer" className={link}>
      {label ?? r.name}<span className="sr-only"> (opens in a new tab)</span>
    </a>
  )
}

/** Renders nothing without data. Groups in the order the answer gives them (Work, Shopping, Hospitals, Colleges, Travel). */
export default function AreaLandmarks({ data }: { data: AreaLandmarksData | null }) {
  if (!data || (!data.metro.length && !data.landmarks.length)) return null
  const groups: { label: string; rows: LandmarkRow[] }[] = []
  for (const r of data.landmarks) {
    const g = groups.find((x) => x.label === r.kind_label)
    if (g) g.rows.push(r)
    else groups.push({ label: r.kind_label as string, rows: [r] })
  }
  const trackers = Array.from(new Set(data.metro.map((m) => m.tracker).filter((t): t is string => !!t)))
  return (
    <section className="mt-9" aria-labelledby="landmarks-title" data-testid="area-landmarks">
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: jsonLdString(landmarksJsonLd(data)) }} />
      <h2 id="landmarks-title" className="text-xl font-semibold text-slate-900">Landmarks near {data.area.name}</h2>
      <p className="mt-1 text-sm text-slate-600">{data.note} Each name opens the place on Google Maps.</p>

      {data.metro.length > 0 && (
        <div className="mt-4">
          <h3 className="font-semibold text-slate-900">Metro</h3>
          <ul className="mt-2 list-none space-y-2 p-0">
            {data.metro.map((m) => (
              <li key={`${m.line}:${m.name}`} className="rounded-xl border border-slate-200 p-3 leading-relaxed text-slate-800">
                <MapsLink r={m} label={`${m.name} station`} />
                <span className="mt-1 block text-sm text-slate-600">
                  {m.line_short}, {m.running ? 'running' : 'being built, not open yet'} · {m.distance}
                  {m.tracker && <> · <a href={m.tracker} className={link}>Follow its progress</a></>}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {groups.map((g) => (
        <div key={g.label} className="mt-4">
          <h3 className="font-semibold text-slate-900">{g.label}</h3>
          <ul className="mt-2 list-none space-y-1 p-0">
            {g.rows.map((r) => (
              <li key={r.name} className="leading-relaxed text-slate-800">
                <MapsLink r={r} /> <span className="text-sm text-slate-600">{r.distance}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}

      <p className="mt-4 text-sm text-slate-600">
        {data.attribution}. Metro status from Maha-Metro (Lines 1 and 2) and PMRDA (Line 3)
        {trackers.length === 0 ? '.' : <>; what is still being built is on <a href={trackers[0]} className={link}>our tracker</a>.</>}
      </p>
    </section>
  )
}
